"""Gera unified diff legível entre conteúdo original e resultante.

Usado para a prévia (GUI futura) e o output do CLI. Cores via colorama
(verde = adição, vermelho = remoção, ciano = cabeçalho), com degradação
graciosa: sem colorama instalado, sai texto puro.
"""

from __future__ import annotations

import difflib


def _color_funcs(enabled: bool):
    """Devolve (add, remove, header, reset) — funções de coloração ou identidade."""
    if not enabled:
        ident = lambda s: s  # noqa: E731
        return ident, ident, ident, ""
    try:
        from colorama import Fore, Style, just_fix_windows_console

        just_fix_windows_console()  # habilita ANSI no terminal do Windows
        return (
            lambda s: f"{Fore.GREEN}{s}{Style.RESET_ALL}",
            lambda s: f"{Fore.RED}{s}{Style.RESET_ALL}",
            lambda s: f"{Fore.CYAN}{s}{Style.RESET_ALL}",
            "",
        )
    except ImportError:  # pragma: no cover - sem colorama
        ident = lambda s: s  # noqa: E731
        return ident, ident, ident, ""


def render_diff(path: str, old: str, new: str, *, color: bool = True, context: int = 3) -> str:
    """Monta o unified diff de um arquivo.

    Args:
        path: Rótulo do arquivo (mostrado no cabeçalho do diff).
        old: Conteúdo original (``""`` para arquivo novo).
        new: Conteúdo resultante.
        color: Colorir a saída (terminal). Desligue para logs/arquivos.
        context: Linhas de contexto ao redor de cada mudança.

    Returns:
        O diff como string. Vazio se não houver diferença.
    """
    if old == new:
        return ""

    add, remove, header, _ = _color_funcs(color)
    diff_lines = difflib.unified_diff(
        old.splitlines(),
        new.splitlines(),
        fromfile=f"a/{path}",
        tofile=f"b/{path}",
        lineterm="",
        n=context,
    )

    out: list[str] = []
    for line in diff_lines:
        if line.startswith("+++") or line.startswith("---"):
            out.append(header(line))
        elif line.startswith("@@"):
            out.append(header(line))
        elif line.startswith("+"):
            out.append(add(line))
        elif line.startswith("-"):
            out.append(remove(line))
        else:
            out.append(line)
    return "\n".join(out)
