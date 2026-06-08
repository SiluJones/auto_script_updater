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

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from . import diff_renderer
from .backup_manager import BackupManager
from .file_locator import FileLocatorError, ensure_ready, resolve_path
from ..strategies import StrategyError, get_strategy

# Padrões dos settings (o schema documenta os mesmos defaults, mas jsonschema
# não os injeta — aplicamos aqui).
_DEFAULTS = {"backup": True, "dry_run": False, "stop_on_error": True, "encoding": "utf-8"}

# Encodings tentados ao ler arquivos-alvo (Armadilha #3).
_READ_FALLBACK = ("utf-8", "cp1252")


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


def _effective_settings(instruction: Mapping[str, Any], overrides: Mapping[str, Any]) -> dict[str, Any]:
    """Funde padrões, settings da instrução e overrides explícitos (não-None)."""
    settings = dict(_DEFAULTS)
    settings.update({k: v for k, v in (instruction.get("settings") or {}).items() if v is not None})
    settings.update({k: v for k, v in overrides.items() if v is not None})
    return settings


def _read_target(path: Path, encoding: str) -> tuple[str, str, str]:
    """Lê o arquivo-alvo. Retorna (texto_em_\\n, encoding_usado, estilo_newline)."""
    raw = path.read_bytes()
    newline = "\r\n" if b"\r\n" in raw else "\n"
    last_error: UnicodeDecodeError | None = None
    for enc in (encoding, *(_e for _e in _READ_FALLBACK if _e != encoding)):
        try:
            text = raw.decode(enc)
        except UnicodeDecodeError as exc:
            last_error = exc
            continue
        # Normaliza para \n no processamento; o estilo original é reaplicado ao gravar.
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
        if path.exists():
            original, used_encoding, newline = _read_target(path, encoding)
            existed = True
        else:
            original, used_encoding, newline = "", encoding, "\n"
            existed = False

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
                mod_results.append(
                    ModificationResult(mod_id, strat_name, ok=False, error=str(exc))
                )
                file_failed = True
                report.ok = False
                if stop:
                    report.files.append(
                        FileResult(
                            file_id, str(path), "failed",
                            error=f"Modificação '{mod_id}' falhou: {exc}",
                            modifications=mod_results,
                        )
                    )
                    _maybe_rollback(backup_mgr, wrote_anything, report)
                    return report
                break  # stop_on_error=False: abandona este arquivo, segue para o próximo

        if file_failed:
            report.files.append(
                FileResult(file_id, str(path), "failed", error="Uma ou mais modificações falharam.",
                           modifications=mod_results)
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
                    FileResult(file_id, str(path), "failed",
                               error=f"Falha ao gravar: {exc}", modifications=mod_results)
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


def _maybe_rollback(backup_mgr: BackupManager | None, wrote_anything: bool, report: ApplyReport) -> None:
    """Reverte escritas já feitas, se houver backup; marca o relatório."""
    if backup_mgr is not None and wrote_anything:
        backup_mgr.restore_all()
        report.rolled_back = True
        report.backup_dir = str(backup_mgr.session_dir)
