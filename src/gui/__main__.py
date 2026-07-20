"""Entry point da GUI: ``python -m src.gui``."""

from __future__ import annotations

import argparse

from .main_window import run

if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser(
        prog="python -m src.gui", description="ASU -- interface grafica"
    )
    parser.add_argument("--root", metavar="PASTA", help="Pasta raiz do projeto")
    parser.add_argument(
        "--instruction-dir",
        metavar="PASTA",
        dest="instruction_dir",
        help="Pasta da instrucao (resolve para o .yaml ativo no topo)",
    )
    parser.add_argument(
        "--instruction",
        metavar="ARQUIVO",
        help="Arquivo de instrucao (.yaml/.json)",
    )
    parser.add_argument(
        "--start-dir",
        metavar="PASTA",
        dest="start_dir",
        help="Pasta onde os dialogos de escolha comecam (NAO define a raiz)",
    )
    args = parser.parse_args()
    raise SystemExit(
        run(
            root=args.root,
            instruction_dir=args.instruction_dir,
            instruction=args.instruction,
            start_dir=args.start_dir,
        )
    )
