"""Backup timestampado e rollback (DEC-006).

Antes de QUALQUER escrita, cada arquivo a ser tocado é registrado:

* se já existe → uma cópia vai para ``backups/<YYYYMMDD_HHMMSS>/<espelho-do-caminho>``;
* se não existe (será criado) → registramos apenas a intenção de criação, para
  que o rollback possa apagá-lo.

:meth:`restore_all` desfaz a sessão inteira: restaura os modificados a partir da
cópia e remove os que foram criados. Isso dá atomicidade à instrução — em falha
com ``stop_on_error``, o projeto volta exatamente ao estado anterior.
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


@dataclass
class BackupManager:
    """Cria backups sob um diretório de sessão e restaura sob demanda."""

    backup_root: Path
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    _entries: list[_Entry] = field(default_factory=list, init=False)

    @property
    def session_dir(self) -> Path:
        """Diretório desta sessão de backup (``backups/<timestamp>/``)."""
        return Path(self.backup_root) / "backups" / self.timestamp

    def register(self, path: Path) -> None:
        """Registra (e copia, se existir) um arquivo antes de escrevê-lo."""
        path = Path(path)
        if path.exists():
            mirror = mirror_path(self.session_dir, path)
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
        """Escreve um manifesto simples (texto) listando o que foi salvo."""
        self.session_dir.mkdir(parents=True, exist_ok=True)
        manifest = self.session_dir / "manifest.txt"
        linhas = [f"Backup de {self.timestamp}", ""]
        for entry in self._entries:
            estado = "modificado" if entry.existed else "criado"
            linhas.append(f"[{estado}] {entry.original}")
        manifest.write_text("\n".join(linhas) + "\n", encoding="utf-8")
        return manifest


def mirror_path(session_dir: Path, path: Path) -> Path:
    """Caminho-espelho de ``path`` dentro de ``session_dir``, sem anchor (drive/raiz).

    Evita colisão entre arquivos de mesmo nome em pastas diferentes e preserva a
    estrutura: ``/home/x/a.py`` -> ``.../home/x/a.py``;
    ``C:\\p\\c.json`` -> ``.../p/c.json``.
    """
    resolved = Path(path).resolve()
    parts = resolved.parts
    anchor = resolved.anchor
    if anchor and parts and parts[0] == anchor:
        parts = parts[1:]
    safe = [p.replace(":", "") for p in parts]  # remove ':' de drives Windows
    return Path(session_dir).joinpath(*safe)


def rollback_session(backup_root: Path, timestamp: str) -> list[str]:
    """Desfaz uma sessão de backup a partir do seu manifesto (CLI --rollback).

    Lê ``backups/<timestamp>/manifest.txt`` e, para cada arquivo: restaura os
    'modificado' a partir do espelho; remove os 'criado'.

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
        if line.startswith("[modificado] "):
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
