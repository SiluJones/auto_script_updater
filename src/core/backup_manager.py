"""Backup timestampado e rollback (DEC-006).

Antes de QUALQUER escrita, cada arquivo a ser tocado é registrado:

* se já existe → uma cópia vai para ``backups/<YYYYMMDD_HHMMSS>/<espelho>``, onde
  o espelho preserva o caminho **relativo à raiz do projeto** (FIX-008);
* se não existe (será criado) → registramos apenas a intenção de criação, para
  que o rollback possa apagá-lo.

:meth:`restore_all` desfaz a sessão inteira: restaura os modificados a partir da
cópia e remove os que foram criados. Isso dá atomicidade à instrução — em falha
com ``stop_on_error``, o projeto volta exatamente ao estado anterior.

FIX-008 (Windows): a versão anterior espelhava o caminho ABSOLUTO inteiro do
arquivo dentro de ``backups/``. No Linux os caminhos de teste eram curtos
(``/tmp/...``) e passavam; no Windows, ``C:\\Users\\...\\AppData\\Local\\Temp\\...``
recriado sob ``backups/`` estourava o limite de 260 caracteres do MAX_PATH →
``WinError 3`` em toda aplicação com backup (inclusive ``--sandbox`` e o
``self-test``). O espelho passou a ser RELATIVO à raiz, o que encurta o caminho
e é portável. O manifesto agora grava o caminho-espelho explicitamente, em vez
de recalculá-lo por heurística na hora do rollback.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class _Entry:
    """Registro de um arquivo na sessão de backup."""

    original: Path
    backup_copy: Path | None  # None = arquivo não existia (foi/será criado)
    existed: bool


def _relative_mirror(session_dir: Path, path: Path, root: Path | None) -> Path:
    """Caminho-espelho de ``path`` dentro de ``session_dir``.

    Preferimos o caminho RELATIVO à raiz do projeto (curto e portável). Quando o
    arquivo está fora da raiz (ou não há raiz — caso de ``path_mode=absolute``),
    caímos num esquema seguro e raso: ``_abs/<drive>/<resto>``, sem recriar o
    caminho absoluto inteiro (que no Windows estouraria o MAX_PATH).
    """
    path = Path(path)
    if root is not None:
        try:
            rel = path.resolve().relative_to(Path(root).resolve())
            return Path(session_dir).joinpath(*rel.parts)
        except ValueError:
            pass  # fora da raiz → trata como absoluto abaixo

    resolved = path.resolve()
    parts = resolved.parts
    if resolved.anchor and parts and parts[0] == resolved.anchor:
        parts = parts[1:]
    # Achata o drive em um único segmento curto (ex.: 'C:' -> 'C') para não
    # recriar a árvore absoluta inteira; o prefixo '_abs' evita colisão com
    # caminhos relativos legítimos.
    drive = resolved.drive.replace(":", "") or "_root"
    safe = [p.replace(":", "") for p in parts]
    return Path(session_dir).joinpath("_abs", drive, *safe)


@dataclass
class BackupManager:
    """Cria backups sob um diretório de sessão e restaura sob demanda.

    Args:
        backup_root: onde os backups são criados (raiz do projeto ou pasta externa).
        root: raiz do projeto, usada para encurtar os espelhos (caminhos
            relativos). Quando ``None``, cai no esquema ``_abs/`` (ver
            :func:`_relative_mirror`). Por padrão, igual a ``backup_root``.
        project_name: quando fornecido (backup externo), substitui ``backups/``
            como agrupador: sessão fica em ``<backup_root>/<project_name>/<ts>``
            e ``history.log`` em ``<backup_root>/<project_name>/``.
    """

    backup_root: Path
    root: Path | None = None
    project_name: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    _entries: list[_Entry] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        if self.root is None:
            self.root = self.backup_root

    @property
    def session_dir(self) -> Path:
        """Diretório desta sessão de backup."""
        if self.project_name:
            return Path(self.backup_root) / self.project_name / self.timestamp
        return Path(self.backup_root) / "backups" / self.timestamp

    def register(self, path: Path) -> None:
        """Registra (e copia, se existir) um arquivo antes de escrevê-lo."""
        path = Path(path)
        if path.exists():
            mirror = _relative_mirror(self.session_dir, path, self.root)
            mirror.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, mirror)
            self._entries.append(_Entry(path, mirror, existed=True))
        else:
            self._entries.append(_Entry(path, None, existed=False))

    def restore_all(self) -> None:
        """Reverte todos os arquivos registrados ao estado pré-sessão."""
        for entry in reversed(self._entries):
            if entry.existed and entry.backup_copy is not None:
                entry.original.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(entry.backup_copy, entry.original)
            elif not entry.existed and entry.original.exists():
                entry.original.unlink()

    def write_manifest(self) -> Path:
        """Escreve o manifesto da sessão.

        Formato por linha: ``[estado]<TAB>caminho_original<TAB>caminho_espelho``
        (o espelho fica vazio para arquivos criados). Gravar o espelho explícito
        torna o rollback independente de qualquer heurística de caminho.
        """
        self.session_dir.mkdir(parents=True, exist_ok=True)
        manifest = self.session_dir / "manifest.txt"
        linhas = [f"# Backup de {self.timestamp}", ""]
        for entry in self._entries:
            estado = "modificado" if entry.existed else "criado"
            espelho = str(entry.backup_copy) if entry.backup_copy is not None else ""
            linhas.append(f"{estado}\t{entry.original}\t{espelho}")
        manifest.write_text("\n".join(linhas) + "\n", encoding="utf-8")
        return manifest

    def append_history(self, description: str = "") -> Path:
        """Acrescenta uma linha ao log consolidado ``history.log``.

        Um único arquivo que cresce a cada aplicação, em vez de obrigar o usuário
        a abrir cada pasta de timestamp para saber o que aconteceu (ideia do
        usuário). Cada linha: ``<timestamp>  <n> arquivo(s)  <descrição>``. É
        complementar ao manifesto por sessão (que continua sendo a fonte para o
        rollback) — aqui é só leitura humana cronológica.
        """
        # Quando há project_name (backup externo), history.log fica ao lado das sessões.
        if self.project_name:
            backups_dir = Path(self.backup_root) / self.project_name
        else:
            backups_dir = Path(self.backup_root) / "backups"
        backups_dir.mkdir(parents=True, exist_ok=True)
        history = backups_dir / "history.log"
        n_mod = sum(1 for e in self._entries if e.existed)
        n_new = sum(1 for e in self._entries if not e.existed)
        resumo = f"{n_mod} modificado(s), {n_new} criado(s)"
        desc = f"  {description}" if description else ""
        linha = f"{self.timestamp}\t{resumo}{desc}\n"
        with history.open("a", encoding="utf-8") as fh:
            fh.write(linha)
        return history


def _append_rollback_history(session_dir: Path, n_reverted: int) -> None:
    """Registra um rollback no ``history.log`` (best-effort).

    O ``history.log`` fica no diretório-PAI da sessão — o que vale para os dois
    layouts: ``backups/<ts>`` (padrão, DEC-024c) e ``<project_name>/<ts>``
    (backup externo, DEC-024b). Assim o log cronológico deixa de conter só
    aplicações (``BackupManager.append_history``) e passa a registrar também os
    rollbacks manuais (Desfazer da GUI / ``rollback`` do CLI).

    É best-effort DE PROPÓSITO: se a linha de log não puder ser escrita, o
    rollback JÁ ocorreu e não deve ser abortado por causa do log — engolimos o
    ``OSError`` em vez de estourar uma operação já concluída.
    """
    history = Path(session_dir).parent / "history.log"
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    linha = f"{now}\trollback de {Path(session_dir).name} ({n_reverted} revertido(s))\n"
    try:
        history.parent.mkdir(parents=True, exist_ok=True)
        with history.open("a", encoding="utf-8") as fh:
            fh.write(linha)
    except OSError:
        pass  # log é secundário ao rollback já concluído


def rollback_from_dir(session_dir: Path) -> list[str]:
    """Desfaz uma sessao de backup dado o caminho completo do diretório de sessao.

    Lê ``<session_dir>/manifest.txt`` e, para cada arquivo: restaura os
    'modificado' a partir do espelho gravado; remove os 'criado'.

    Aceita também o formato ANTIGO de manifesto (``[estado] caminho``), por
    retrocompatibilidade com backups feitos antes do FIX-008.

    Returns:
        Lista de descrições do que foi revertido.

    Raises:
        FileNotFoundError: se o manifesto não existir.
    """
    session_dir = Path(session_dir)
    manifest = session_dir / "manifest.txt"
    if not manifest.is_file():
        raise FileNotFoundError(f"Manifesto de backup não encontrado: {manifest}")

    revertidos: list[str] = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue

        if "\t" in line:  # formato novo: estado<TAB>original<TAB>espelho
            campos = line.split("\t")
            estado = campos[0]
            original = Path(campos[1])
            espelho = Path(campos[2]) if len(campos) > 2 and campos[2] else None
            if estado == "modificado" and espelho is not None and espelho.exists():
                original.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(espelho, original)
                revertidos.append(f"restaurado: {original}")
            elif estado == "criado" and original.exists():
                original.unlink()
                revertidos.append(f"removido: {original}")
        elif line.startswith("[modificado] "):  # formato antigo (heurística)
            original = Path(line[len("[modificado] ") :])
            mirror = mirror_path(session_dir, original)
            if mirror.exists():
                original.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(mirror, original)
                revertidos.append(f"restaurado: {original}")
        elif line.startswith("[criado] "):
            original = Path(line[len("[criado] ") :])
            if original.exists():
                original.unlink()
                revertidos.append(f"removido: {original}")
    if revertidos:
        # Log cronológico: antes só continha aplicações; agora também rollbacks.
        _append_rollback_history(session_dir, len(revertidos))
    return revertidos


def rollback_session(backup_root: Path, timestamp: str) -> list[str]:
    """Desfaz uma sessão de backup a partir do seu manifesto (CLI ``rollback``).

    Lê ``backups/<timestamp>/manifest.txt``. Para backup externo com project_name,
    passe ``<backup_location>/<project_name>`` como ``backup_root``.

    Returns:
        Lista de descrições do que foi revertido.

    Raises:
        FileNotFoundError: se a sessão/manifesto não existir.
    """
    session_dir = Path(backup_root) / "backups" / timestamp
    return rollback_from_dir(session_dir)


def mirror_path(session_dir: Path, path: Path) -> Path:
    """[Legado] Espelho por caminho absoluto. Mantido só para ler manifestos antigos.

    Não use em código novo — ver :func:`_relative_mirror`. Preservado porque o
    ``rollback_session`` aceita manifestos no formato anterior ao FIX-008.
    """
    resolved = Path(path).resolve()
    parts = resolved.parts
    if resolved.anchor and parts and parts[0] == resolved.anchor:
        parts = parts[1:]
    safe = [p.replace(":", "") for p in parts]
    return Path(session_dir).joinpath(*safe)
