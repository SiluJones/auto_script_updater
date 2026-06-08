"""Resolve o caminho de cada arquivo da instrução e verifica pré-condições.

Combina ``root_path`` + ``relative_path`` ou usa ``absolute_path`` diretamente
(ver CONTEXT.md / GLOSSARY.md). Para o modo *relative*, aplica uma guarda de
contenção: o caminho resolvido não pode escapar da pasta raiz (uma instrução de
IA não deve gravar fora do projeto sem o usuário ter escolhido o modo absoluto).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping


class FileLocatorError(Exception):
    """Caminho mal especificado, ausente, ou que escapa da raiz."""


# Estratégias que criam o arquivo: a inexistência é esperada, não um erro.
_CREATING_STRATEGIES = frozenset({"create_file", "replace_file"})


def resolve_path(file_entry: Mapping[str, Any], root_path: str | Path | None) -> Path:
    """Devolve o caminho em disco do arquivo descrito por ``file_entry``.

    Args:
        file_entry: Um item de ``files[]`` já validado.
        root_path: Pasta raiz do projeto (necessária para ``path_mode=relative``).

    Returns:
        ``Path`` resolvido (absoluto).

    Raises:
        FileLocatorError: campo ausente, raiz ausente no modo relativo, ou
            caminho relativo que escapa da raiz.
    """
    path_mode = file_entry.get("path_mode")

    if path_mode == "relative":
        relative = file_entry.get("relative_path")
        if not relative:
            raise FileLocatorError(
                f"Arquivo '{file_entry.get('id')}': path_mode=relative exige 'relative_path'."
            )
        if root_path is None:
            raise FileLocatorError(
                f"Arquivo '{file_entry.get('id')}': caminho relativo {relative!r} requer uma "
                "pasta raiz. Informe --root no CLI (ou selecione a raiz na GUI)."
            )
        root = Path(root_path).resolve()
        resolved = (root / relative).resolve()
        if not _is_within(resolved, root):
            raise FileLocatorError(
                f"Arquivo '{file_entry.get('id')}': o caminho {relative!r} escapa da pasta raiz "
                f"({root}). Use path_mode=absolute se isso for intencional."
            )
        return resolved

    if path_mode == "absolute":
        absolute = file_entry.get("absolute_path")
        if not absolute:
            raise FileLocatorError(
                f"Arquivo '{file_entry.get('id')}': path_mode=absolute exige 'absolute_path'."
            )
        return Path(absolute)

    raise FileLocatorError(
        f"Arquivo '{file_entry.get('id')}': path_mode inválido: {path_mode!r}."
    )


def ensure_ready(path: Path, file_entry: Mapping[str, Any]) -> None:
    """Verifica que o arquivo pode ser modificado pelas estratégias do arquivo.

    Exige existência, exceto quando *todas* as modificações criam o conteúdo do
    zero (``create_file``/``replace_file``), caso em que a ausência é aceitável.

    Raises:
        FileLocatorError: arquivo ausente quando alguma estratégia precisa lê-lo,
            ou caminho que existe mas não é um arquivo regular.
    """
    if path.exists():
        if not path.is_file():
            raise FileLocatorError(f"O caminho {path} existe mas não é um arquivo regular.")
        return

    strategies = {m.get("strategy") for m in file_entry.get("modifications", [])}
    if strategies <= _CREATING_STRATEGIES:
        return  # todas as modificações criam conteúdo; ausência é ok
    faltantes = strategies - _CREATING_STRATEGIES
    raise FileLocatorError(
        f"Arquivo não encontrado: {path}. As estratégias {sorted(faltantes)} precisam "
        "do conteúdo existente para localizar o ponto de modificação."
    )


def _is_within(path: Path, root: Path) -> bool:
    """True se ``path`` está dentro de ``root`` (inclui o próprio root)."""
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
