"""Orquestrador da aplicação de instruções (o coração da F1).

Recebe uma instrução **já validada**, resolve caminhos, aplica as modificações
em ordem (reparseando o conteúdo entre modificações do mesmo arquivo — Armadilha
#4), cria backup antes de escrever (DEC-006) e, em falha com ``stop_on_error``,
reverte TUDO (atomicidade). Em ``dry_run``, nada é escrito: os diffs são
calculados como se a aplicação tivesse ocorrido.

Precedência de configuração: padrões < ``instruction.settings`` < argumentos
explícitos passados a :func:`apply_instruction`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..strategies import StrategyError, get_strategy
from . import diff_renderer
from .backup_manager import BackupManager
from .file_locator import FileLocatorError, ensure_ready, resolve_path

# Padrões dos settings (o schema documenta os mesmos defaults, mas jsonschema
# não os injeta — aplicamos aqui).
_DEFAULTS = {"backup": True, "dry_run": False, "stop_on_error": True, "encoding": "utf-8"}

# Encodings tentados ao ler arquivos-alvo (Armadilha #3).
_READ_FALLBACK = ("utf-8", "cp1252")

# BOMs que indicam encodings NÃO suportados (decodificá-los com cp1252 produziria
# lixo com NULs e, em estratégias sem localizador, conversão silenciosa de encoding).
_UNSUPPORTED_BOMS = (
    (b"\xff\xfe\x00\x00", "UTF-32 LE"),
    (b"\x00\x00\xfe\xff", "UTF-32 BE"),
    (b"\xff\xfe", "UTF-16 LE"),
    (b"\xfe\xff", "UTF-16 BE"),
)


@dataclass
class ModificationResult:
    """Resultado de uma única modificação."""

    mod_id: str
    strategy: str
    ok: bool
    error: str | None = None


@dataclass
class FileResult:
    """Resultado consolidado de um arquivo da instrução."""

    file_id: str
    path: str
    status: str  # "created" | "modified" | "unchanged" | "failed" | "skipped"
    diff: str = ""
    error: str | None = None
    modifications: list[ModificationResult] = field(default_factory=list)


@dataclass
class ApplyReport:
    """Relatório completo de uma execução."""

    ok: bool
    dry_run: bool
    files: list[FileResult] = field(default_factory=list)
    backup_dir: str | None = None
    rolled_back: bool = False


def _effective_settings(
    instruction: Mapping[str, Any], overrides: Mapping[str, Any]
) -> dict[str, Any]:
    """Funde padrões, settings da instrução e overrides explícitos (não-None)."""
    settings = dict(_DEFAULTS)
    settings.update({k: v for k, v in (instruction.get("settings") or {}).items() if v is not None})
    settings.update({k: v for k, v in overrides.items() if v is not None})
    return settings


def _read_target(path: Path, encoding: str) -> tuple[str, str, str]:
    """Lê o arquivo-alvo. Retorna (texto_em_\\n, encoding_usado, estilo_newline).

    Cuidados de encoding (Armadilha #3 + FIX-002):
    - **BOM UTF-8** (padrão do Visual Studio em ``.cs``, comum no Windows): sem
      tratamento, ``utf-8`` decodifica o BOM como ``\\ufeff`` no início do texto
      — invisível no diff, mas faz localizadores na primeira linha falharem
      misteriosamente. Detectamos o BOM e usamos ``utf-8-sig``; a gravação
      preserva o BOM (roundtrip fiel).
    - **UTF-16/32**: ``cp1252`` "decodificaria" os bytes sem erro, produzindo
      texto com NULs intercalados — e estratégias sem localizador
      (``replace_file``) converteriam o encoding do arquivo silenciosamente.
      Rejeitamos com erro claro pedindo conversão para UTF-8.
    - O estilo de newline é detectado no TEXTO decodificado (não nos bytes),
      o que é correto para qualquer encoding.
    """
    raw = path.read_bytes()

    for bom, nome in _UNSUPPORTED_BOMS:
        if raw.startswith(bom):
            raise FileLocatorError(
                f"{path}: arquivo em {nome} (BOM detectado). Encoding não suportado; "
                "converta o arquivo para UTF-8 antes de aplicar a instrução."
            )

    # Guarda de binário (FIX-006): cp1252 "decodifica" quase qualquer byte, então
    # um .png/.exe apontado por engano viraria "texto" — e um replace_file o
    # sobrescreveria silenciosamente. Byte NUL é o sinal universal de não-texto
    # (também pega UTF-16 SEM BOM, que intercala NULs).
    if b"\x00" in raw:
        raise FileLocatorError(
            f"{path}: o conteúdo contém bytes NUL — parece arquivo binário (ou texto "
            "UTF-16 sem BOM). A ferramenta só modifica arquivos de texto em "
            "UTF-8/CP-1252; verifique o caminho ou converta o arquivo."
        )

    has_utf8_bom = raw.startswith(b"\xef\xbb\xbf")
    candidatos = (
        ("utf-8-sig",)
        if has_utf8_bom
        else (encoding, *(_e for _e in _READ_FALLBACK if _e != encoding))
    )

    last_error: UnicodeDecodeError | None = None
    for enc in candidatos:
        try:
            text = raw.decode(enc)
        except UnicodeDecodeError as exc:
            last_error = exc
            continue
        # Detecta o estilo de quebra de linha no texto decodificado; normaliza
        # para \n no processamento e reaplica o estilo original ao gravar.
        newline = "\r\n" if "\r\n" in text else "\n"
        return text.replace("\r\n", "\n"), enc, newline
    raise FileLocatorError(
        f"Não foi possível decodificar {path} ({encoding}/cp1252)."
    ) from last_error


def _write_target(path: Path, text: str, encoding: str, newline: str) -> None:
    """Grava o conteúdo, recriando diretórios pais e reaplicando o estilo de newline."""
    path.parent.mkdir(parents=True, exist_ok=True)
    body = text.replace("\n", newline) if newline != "\n" else text
    # newline="" impede tradução automática da plataforma; controlamos o estilo nós mesmos.
    with open(path, "w", encoding=encoding, newline="") as fh:
        fh.write(body)


def apply_instruction(
    instruction: Mapping[str, Any],
    *,
    root_path: str | Path | None = None,
    dry_run: bool | None = None,
    backup: bool | None = None,
    stop_on_error: bool | None = None,
    color: bool = True,
) -> ApplyReport:
    """Aplica a instrução e retorna um :class:`ApplyReport`.

    A instrução deve ter passado por ``instruction_validator.validate`` antes.
    """
    settings = _effective_settings(
        instruction,
        {"dry_run": dry_run, "backup": backup, "stop_on_error": stop_on_error},
    )
    is_dry = bool(settings["dry_run"])
    use_backup = bool(settings["backup"]) and not is_dry
    stop = bool(settings["stop_on_error"])
    default_encoding = settings["encoding"]

    backup_root = Path(root_path) if root_path is not None else Path.cwd()
    backup_mgr = BackupManager(backup_root) if use_backup else None

    report = ApplyReport(ok=True, dry_run=is_dry)
    wrote_anything = False

    for file_entry in instruction.get("files", []):
        file_id = file_entry.get("id", "?")
        encoding = file_entry.get("encoding") or default_encoding

        # 1) Resolver e checar pré-condições.
        try:
            path = resolve_path(file_entry, root_path)
            ensure_ready(path, file_entry)
        except FileLocatorError as exc:
            report.ok = False
            report.files.append(FileResult(file_id, str(file_entry), "failed", error=str(exc)))
            if stop:
                _maybe_rollback(backup_mgr, wrote_anything, report)
                return report
            continue

        # 2) Ler conteúdo atual (ou vazio, se será criado).
        try:
            if path.exists():
                original, used_encoding, newline = _read_target(path, encoding)
                existed = True
            else:
                original, used_encoding, newline = "", encoding, "\n"
                existed = False
        except FileLocatorError as exc:
            report.ok = False
            report.files.append(FileResult(file_id, str(path), "failed", error=str(exc)))
            if stop:
                _maybe_rollback(backup_mgr, wrote_anything, report)
                return report
            continue

        # 3) Aplicar modificações em sequência (reparse implícito: cada passo recebe o texto atual).
        current = original
        mod_results: list[ModificationResult] = []
        file_failed = False
        for mod in file_entry.get("modifications", []):
            mod_id = mod.get("id", "?")
            strat_name = mod.get("strategy", "?")
            try:
                current = get_strategy(strat_name).apply(current, mod)
                mod_results.append(ModificationResult(mod_id, strat_name, ok=True))
            except StrategyError as exc:
                mod_results.append(ModificationResult(mod_id, strat_name, ok=False, error=str(exc)))
                file_failed = True
                report.ok = False
                if stop:
                    report.files.append(
                        FileResult(
                            file_id,
                            str(path),
                            "failed",
                            error=f"Modificação '{mod_id}' falhou: {exc}",
                            modifications=mod_results,
                        )
                    )
                    _maybe_rollback(backup_mgr, wrote_anything, report)
                    return report
                break  # stop_on_error=False: abandona este arquivo, segue para o próximo

        if file_failed:
            report.files.append(
                FileResult(
                    file_id,
                    str(path),
                    "failed",
                    error="Uma ou mais modificações falharam.",
                    modifications=mod_results,
                )
            )
            continue

        # 4) Determinar status e diff.
        if not existed:
            status = "created"
        elif current != original:
            status = "modified"
        else:
            status = "unchanged"
        diff = diff_renderer.render_diff(str(path), original, current, color=color)

        # 5) Escrever (exceto dry-run / unchanged).
        if not is_dry and status in {"created", "modified"}:
            if backup_mgr is not None:
                backup_mgr.register(path)
            try:
                _write_target(path, current, used_encoding, newline)
                wrote_anything = True
            except OSError as exc:
                report.ok = False
                report.files.append(
                    FileResult(
                        file_id,
                        str(path),
                        "failed",
                        error=f"Falha ao gravar: {exc}",
                        modifications=mod_results,
                    )
                )
                if stop:
                    _maybe_rollback(backup_mgr, wrote_anything, report)
                    return report
                continue

        report.files.append(
            FileResult(file_id, str(path), status, diff=diff, modifications=mod_results)
        )

    # 6) Manifesto do backup (se houve escrita real).
    if backup_mgr is not None and wrote_anything:
        backup_mgr.write_manifest()
        report.backup_dir = str(backup_mgr.session_dir)

    return report


def _maybe_rollback(
    backup_mgr: BackupManager | None, wrote_anything: bool, report: ApplyReport
) -> None:
    """Reverte escritas já feitas, se houver backup; marca o relatório."""
    if backup_mgr is not None and wrote_anything:
        backup_mgr.restore_all()
        report.rolled_back = True
        report.backup_dir = str(backup_mgr.session_dir)
