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
        backup_root: onde a pasta ``backups/`` é criada (a raiz do projeto).
        root: raiz do projeto, usada para encurtar os espelhos (caminhos
            relativos). Quando ``None``, cai no esquema ``_abs/`` (ver
            :func:`_relative_mirror`). Por padrão, igual a ``backup_root``.
    """

    backup_root: Path
    root: Path | None = None
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    _entries: list[_Entry] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        if self.root is None:
            self.root = self.backup_root

    @property
    def session_dir(self) -> Path:
        """Diretório desta sessão de backup (``backups/<timestamp>/``)."""
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
        """Acrescenta uma linha ao log consolidado ``backups/history.log``.

        Um único arquivo que cresce a cada aplicação, em vez de obrigar o usuário
        a abrir cada pasta de timestamp para saber o que aconteceu (ideia do
        usuário). Cada linha: ``<timestamp>  <n> arquivo(s)  <descrição>``. É
        complementar ao manifesto por sessão (que continua sendo a fonte para o
        rollback) — aqui é só leitura humana cronológica.
        """
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


def rollback_session(backup_root: Path, timestamp: str) -> list[str]:
    """Desfaz uma sessão de backup a partir do seu manifesto (CLI ``rollback``).

    Lê ``backups/<timestamp>/manifest.txt`` e, para cada arquivo: restaura os
    'modificado' a partir do espelho gravado; remove os 'criado'.

    Aceita também o formato ANTIGO de manifesto (``[estado] caminho``), por
    retrocompatibilidade com backups feitos antes do FIX-008.

    Returns:
        Lista de descrições do que foi revertido.

    Raises:
        FileNotFoundError: se a sessão/manifesto não existir.
    """
    session_dir = Path(backup_root) / "backups" / timestamp
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
    return revertidos


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
