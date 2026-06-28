"""Funcoes puras para o lancador por projeto: resolucao de instrucao e geracao de .bat.

Sem dependencia de Qt — testavel isoladamente.
"""

from __future__ import annotations

from pathlib import Path


def resolve_instruction_in_dir(directory: str | Path) -> tuple[str, list[Path]]:
    """Escaneia o TOPO de *directory* (nao recursivo) em busca de YAMLs.

    Retorna:
        ("one",  [arquivo]) — exatamente 1 encontrado
        ("none", [])        — nenhum
        ("many", [...])     — 2 ou mais (lista ordenada)
    """
    d = Path(directory)
    yamls = sorted(p for p in d.iterdir() if p.is_file() and p.suffix.lower() in {".yaml", ".yml"})
    n = len(yamls)
    if n == 0:
        return ("none", [])
    if n == 1:
        return ("one", yamls)
    return ("many", yamls)


def build_launcher_bat(*, asu_home: Path, project_root: Path, bat_dir: Path) -> str:
    """Gera o texto de um .bat que reabre a GUI ja apontada para *project_root*.

    Regras (D1/D4 da spec):
    - ASU_HOME e o caminho de python.exe sao absolutos.
    - --instruction-dir usa %~dp0 (pasta onde o .bat esta).
    - --root: relativo a %~dp0 se project_root for descendente de bat_dir; senao absoluto.
    - python.exe chamado diretamente do venv (sem 'activate').
    """
    asu_home = asu_home.resolve()
    project_root = project_root.resolve()
    bat_dir = bat_dir.resolve()

    try:
        rel = project_root.relative_to(bat_dir)
        root_arg = f"%~dp0{rel}"
    except ValueError:
        # project_root fora de bat_dir: caminho absoluto
        root_arg = str(project_root)

    # bat_dir eh %~dp0 em runtime; inclui no teste para cobrir acentos na pasta do .bat
    precisa_utf8 = not (str(asu_home).isascii() and root_arg.isascii() and str(bat_dir).isascii())
    chcp_line = "chcp 65001 >nul\n" if precisa_utf8 else ""
    return (
        "@echo off\n"
        + chcp_line
        + "REM Atalho gerado pelo ASU -- abre a interface ja apontada para este projeto.\n"
        + f'set "ASU_HOME={asu_home}"\n'
        + 'pushd "%ASU_HOME%"\n'
        # %~dp0 termina em \; o . evita \" que corrompe o argumento (BUG 1)
        + '".venv\\Scripts\\python.exe" -m src.gui'
        + f' --root "{root_arg}" --instruction-dir "%~dp0."\n'
        + "popd\n"
    )


def build_open_gui_bat(*, asu_home: Path) -> str:
    """Gera um .bat que abre a GUI sem raiz nem instrucao (atalho classico).

    Usa pythonw.exe (sem janela de console) e start /d para definir o diretorio
    de trabalho de forma robusta, sem depender de projeto especifico.
    """
    asu_home = asu_home.resolve()
    precisa_utf8 = not str(asu_home).isascii()
    chcp_line = "chcp 65001 >nul\n" if precisa_utf8 else ""
    return (
        "@echo off\n"
        + chcp_line
        + "REM Atalho gerado pelo ASU -- abre a interface (sem console).\n"
        + f'start "" /d "{asu_home}" "{asu_home}\\.venv\\Scripts\\pythonw.exe" -m src.gui\n'
    )
