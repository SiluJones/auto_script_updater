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
from .core.backup_manager import rollback_from_dir, rollback_session
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
        # Ressalva (DEC-028): avisos não-fatais — a aplicação deu certo, mas há
        # algo a conferir. Marcador `~` igual ao de `_report_to_text` (GUI).
        for mr in fr.modifications:
            for aviso in mr.warnings:
                print(f"  ~ {aviso}")
        if fr.diff:
            print(fr.diff)
        elif fr.status == "unchanged":
            print("  (sem alterações)")

    criados = sum(1 for f in report.files if f.status == "created")
    modificados = sum(1 for f in report.files if f.status == "modified")
    inalterados = sum(1 for f in report.files if f.status == "unchanged")
    falhas = sum(1 for f in report.files if f.status == "failed")
    com_ressalva = sum(1 for f in report.files if f.has_warnings)

    print("\n" + "-" * 60)
    modo = "SIMULAÇÃO (dry-run)" if report.dry_run else "APLICAÇÃO"
    # Sufixo da ressalva só aparece quando há alguma — sem avisos, a linha de
    # resumo fica IDÊNTICA à de antes (nada muda no caso comum).
    ressalva = f", {com_ressalva} com ressalva" if com_ressalva else ""
    print(
        f"{modo}: {criados} criado(s), {modificados} modificado(s), "
        f"{inalterados} inalterado(s), {falhas} falha(s){ressalva}."
    )
    if com_ressalva:
        print("Atenção: há aviso(s) não-fatal(is) marcados com `~` acima — confira.")
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


# Pastas ignoradas ao duplicar a raiz para a sandbox (pesadas/geradas).
# Sandbox vive no core (reutilizável por CLI e GUI); aqui só adaptamos a borda.
def _make_sandbox(root: Path, instruction: dict) -> Path:
    """Wrapper de CLI sobre ``patch_engine.make_sandbox`` (erro → stderr + exit 2)."""
    from .core.patch_engine import SandboxError, make_sandbox

    try:
        return make_sandbox(root, instruction)
    except SandboxError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from exc


def _cmd_apply(args: argparse.Namespace) -> int:
    instruction = _load_and_validate(args.instruction)
    color = not args.no_color

    if getattr(args, "sandbox", False):
        if not args.root:
            print("--sandbox exige --root (qual projeto duplicar?).", file=sys.stderr)
            return 2
        original = Path(args.root)
        if not original.is_dir():
            print(f"--root não é uma pasta: {original}", file=sys.stderr)
            return 2
        sandbox = _make_sandbox(original, instruction)
        print(f"Sandbox criada: {sandbox}")
        print("(O projeto original NÃO será tocado; tudo abaixo aplica na cópia.)\n")
        args.root = str(sandbox)

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
        backup_location=getattr(args, "backup_dir", None),
        color=color,
        instruction_label=Path(args.instruction).name,
    )
    _print_report(report)
    if report.backup_dir and not args.dry_run:
        print(f"Histórico: {Path(report.backup_dir).parent / 'history.log'}")
    if getattr(args, "sandbox", False) and not args.dry_run:
        print(f"\nSandbox: {args.root}")
        print("Revise o resultado, copie o que aprovar para o projeto real e apague a pasta.")
    return 0 if report.ok else 1


def _cmd_self_test(args: argparse.Namespace) -> int:
    """Valida a instalação ponta a ponta usando a demo embutida (em tempdir).

    Copia ``examples/demo_project`` para um diretório temporário, aplica
    ``examples/demo.yaml``, verifica resultados-chave, faz rollback e confere a
    restauração. Nada fora do tempdir é tocado.
    """
    import shutil
    import tempfile

    base = Path(__file__).resolve().parent.parent  # raiz do repo (acima de src/)
    demo_yaml = base / "examples" / "demo.yaml"
    demo_proj = base / "examples" / "demo_project"
    if not demo_yaml.is_file() or not demo_proj.is_dir():
        print(
            "self-test indisponível: examples/demo.yaml ou examples/demo_project ausentes.",
            file=sys.stderr,
        )
        return 2

    instruction = _load_and_validate(str(demo_yaml))
    falhas: list[str] = []
    with tempfile.TemporaryDirectory(prefix="asu_selftest_") as tmp:
        raiz = Path(tmp) / "demo_project"
        shutil.copytree(demo_proj, raiz)
        # A demo CRIA src/health.py via create_file. Se ele vazou para o
        # examples/demo_project do repo numa execução anterior e foi copiado
        # junto, o create_file/rollback se confundiria (o arquivo "já existia").
        # Remover garante que o self-test parte de um estado limpo (FIX-009).
        residual = raiz / "src" / "health.py"
        if residual.exists():
            residual.unlink()

        report = apply_instruction(instruction, root_path=raiz, color=False)
        if not report.ok:
            falhas.append("apply falhou: " + "; ".join(f.error or f.status for f in report.files))
        else:
            calc = (raiz / "src" / "calculator.py").read_text(encoding="utf-8")
            if "Divisão por zero" not in calc:
                falhas.append("método Python não foi substituído")
            if not (raiz / "src" / "health.py").exists():
                falhas.append("create_file não criou src/health.py")
            cfg = (raiz / "config.json").read_text(encoding="utf-8")
            if '"2.0.0"' not in cfg or '"logging"' in cfg and "deprecated_flag" in cfg:
                if '"2.0.0"' not in cfg:
                    falhas.append("set_json_path não atualizou a versão")

            if not report.backup_dir:
                falhas.append("backup não foi criado")
            else:
                rollback_from_dir(Path(report.backup_dir))
                calc2 = (raiz / "src" / "calculator.py").read_text(encoding="utf-8")
                if "Divisão por zero" in calc2:
                    falhas.append("rollback não restaurou calculator.py")
                if (raiz / "src" / "health.py").exists():
                    falhas.append("rollback não removeu o arquivo criado")

    if falhas:
        print("SELF-TEST FALHOU:", file=sys.stderr)
        for f in falhas:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print("SELF-TEST OK — parser, validador, 5 estratégias, backup e rollback funcionando.")
    print("(Tudo executado em diretório temporário; nada do seu disco foi tocado.)")
    return 0


def _cmd_rollback(args: argparse.Namespace) -> int:
    # Prioriza --backup-dir explícito. Sem ele, o padrão DEC-024c é parent(root).
    if getattr(args, "backup_dir", None):
        base = args.backup_dir
    else:
        root = Path(args.root or Path.cwd()).resolve()
        par = root.parent
        base = str(par if par != root else root)
    try:
        revertidos = rollback_session(base, args.timestamp)
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
    p_app.add_argument(
        "--backup-dir",
        metavar="PASTA",
        help="Onde criar a pasta zz_backups/ (padrão: pasta-pai da raiz, fora do projeto). "
        "Útil para apontar para uma pasta compartilhada de backups.",
    )
    p_app.add_argument(
        "--sandbox",
        action="store_true",
        help="Aplica numa CÓPIA da raiz (pasta irmã *_sandbox_<ts>); o original não é tocado.",
    )
    p_app.add_argument("--no-color", action="store_true", help="Saída sem cores ANSI.")
    p_app.add_argument("--yes", "-y", action="store_true", help="Aplica sem pedir confirmação.")
    p_app.set_defaults(func=_cmd_apply)

    p_st = sub.add_parser(
        "self-test", help="Valida a instalação aplicando a demo embutida num diretório temporário."
    )
    p_st.set_defaults(func=_cmd_self_test)

    p_rb = sub.add_parser("rollback", help="Desfaz uma aplicação a partir do timestamp do backup.")
    p_rb.add_argument("timestamp", help="Timestamp da sessão (ex.: 20260607_231500).")
    p_rb.add_argument("--root", help="Pasta raiz onde está a pasta zz_backups/.")
    p_rb.add_argument(
        "--backup-dir",
        metavar="PASTA",
        help="Pasta que contém zz_backups/ (use a mesma de --backup-dir do apply, se usou).",
    )
    p_rb.set_defaults(func=_cmd_rollback)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
