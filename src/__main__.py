"""Interface de linha de comando do Atualizador Automático de Scripts (F1).

Uso:
    python -m src validate INSTRUCAO
    python -m src apply INSTRUCAO --root C:\\meu_projeto [--dry-run] [--no-backup] [--yes]
    python -m src rollback TIMESTAMP --root C:\\meu_projeto

A GUI (F2) reusará exatamente esta mesma pilha (parser → validator → engine).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import diff_renderer  # noqa: F401 (mantém o pacote coeso)
from .core.backup_manager import rollback_session
from .core.instruction_parser import InstructionParseError, load_instruction
from .core.instruction_validator import InstructionValidationError, validate
from .core.patch_engine import ApplyReport, apply_instruction

_STATUS_LABEL = {
    "created": "criado",
    "modified": "modificado",
    "unchanged": "inalterado",
    "failed": "FALHOU",
    "skipped": "ignorado",
}


def _load_and_validate(instruction_path: str):
    """Carrega e valida; imprime erros e sai com código != 0 em falha."""
    try:
        instruction = load_instruction(instruction_path)
    except InstructionParseError as exc:
        print(f"Erro ao ler a instrução: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    try:
        validate(instruction)
    except InstructionValidationError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from exc
    return instruction


def _print_report(report: ApplyReport) -> None:
    """Imprime diffs e um resumo legível da execução."""
    for fr in report.files:
        rotulo = _STATUS_LABEL.get(fr.status, fr.status)
        print(f"\n=== [{rotulo}] {fr.path} ===")
        if fr.error:
            print(f"  ! {fr.error}")
        if fr.diff:
            print(fr.diff)
        elif fr.status == "unchanged":
            print("  (sem alterações)")

    criados = sum(1 for f in report.files if f.status == "created")
    modificados = sum(1 for f in report.files if f.status == "modified")
    inalterados = sum(1 for f in report.files if f.status == "unchanged")
    falhas = sum(1 for f in report.files if f.status == "failed")

    print("\n" + "-" * 60)
    modo = "SIMULAÇÃO (dry-run)" if report.dry_run else "APLICAÇÃO"
    print(
        f"{modo}: {criados} criado(s), {modificados} modificado(s), "
        f"{inalterados} inalterado(s), {falhas} falha(s)."
    )
    if report.rolled_back:
        print("ATENÇÃO: ocorreu falha — todas as escritas foram revertidas (rollback).")
    if report.backup_dir and not report.dry_run:
        print(f"Backup: {report.backup_dir}")


def _cmd_validate(args: argparse.Namespace) -> int:
    instruction = _load_and_validate(args.instruction)
    n_files = len(instruction.get("files", []))
    n_mods = sum(len(f.get("modifications", [])) for f in instruction.get("files", []))
    print(f"OK — instrução válida: {n_files} arquivo(s), {n_mods} modificação(ões).")
    return 0


def _cmd_apply(args: argparse.Namespace) -> int:
    instruction = _load_and_validate(args.instruction)
    color = not args.no_color

    # Pré-visualização sempre em dry-run, para o usuário conferir antes de confirmar.
    if not args.yes and not args.dry_run:
        preview = apply_instruction(
            instruction,
            root_path=args.root,
            dry_run=True,
            color=color,
        )
        _print_report(preview)
        if not preview.ok:
            print("\nHá problemas na instrução (veja acima). Nada foi escrito.", file=sys.stderr)
            return 1
        resposta = input("\nAplicar estas mudanças? [s/N] ").strip().lower()
        if resposta not in {"s", "sim", "y", "yes"}:
            print("Cancelado. Nada foi escrito.")
            return 0

    report = apply_instruction(
        instruction,
        root_path=args.root,
        dry_run=args.dry_run,
        backup=False if args.no_backup else None,
        color=color,
    )
    _print_report(report)
    return 0 if report.ok else 1


def _cmd_rollback(args: argparse.Namespace) -> int:
    root = args.root or str(Path.cwd())
    try:
        revertidos = rollback_session(root, args.timestamp)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if not revertidos:
        print("Nada a reverter (sessão vazia).")
        return 0
    print(f"Rollback de {args.timestamp}:")
    for item in revertidos:
        print(f"  - {item}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="auto-script-updater",
        description="Aplica instruções de modificação geradas por IA a arquivos do projeto.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_val = sub.add_parser("validate", help="Valida a instrução sem aplicar nada.")
    p_val.add_argument("instruction", help="Caminho do arquivo de instrução (YAML/JSON).")
    p_val.set_defaults(func=_cmd_validate)

    p_app = sub.add_parser("apply", help="Aplica a instrução (com prévia e confirmação).")
    p_app.add_argument("instruction", help="Caminho do arquivo de instrução (YAML/JSON).")
    p_app.add_argument("--root", help="Pasta raiz do projeto (para caminhos relativos).")
    p_app.add_argument("--dry-run", action="store_true", help="Simula sem escrever em disco.")
    p_app.add_argument(
        "--no-backup", action="store_true", help="Não criar backup (não recomendado)."
    )
    p_app.add_argument("--no-color", action="store_true", help="Saída sem cores ANSI.")
    p_app.add_argument("--yes", "-y", action="store_true", help="Aplica sem pedir confirmação.")
    p_app.set_defaults(func=_cmd_apply)

    p_rb = sub.add_parser("rollback", help="Desfaz uma aplicação a partir do timestamp do backup.")
    p_rb.add_argument("timestamp", help="Timestamp da sessão (ex.: 20260607_231500).")
    p_rb.add_argument("--root", help="Pasta raiz onde está a pasta backups/.")
    p_rb.set_defaults(func=_cmd_rollback)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
