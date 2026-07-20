"""Testes de integração: file_locator + patch_engine + backup_manager."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.core.backup_manager import BACKUP_DIRNAME, rollback_from_dir
from src.core.file_locator import FileLocatorError, resolve_path
from src.core.patch_engine import ModificationResult, apply_instruction
from src.strategies.base_strategy import split_apply_result

# ───────────────────────── file_locator ─────────────────────────


def test_relative_requires_root():
    with pytest.raises(FileLocatorError, match="pasta raiz|raiz"):
        resolve_path({"id": "f", "path_mode": "relative", "relative_path": "a.py"}, None)


def test_relative_escape_blocked(tmp_path):
    with pytest.raises(FileLocatorError, match="escapa"):
        resolve_path(
            {"id": "f", "path_mode": "relative", "relative_path": "../fora.py"},
            tmp_path,
        )


def test_absolute_path(tmp_path):
    alvo = tmp_path / "x.py"
    p = resolve_path({"id": "f", "path_mode": "absolute", "absolute_path": str(alvo)}, None)
    assert p == alvo


# ───────────────────────── helpers ─────────────────────────


def _instr(files, **settings):
    base = {"format_version": "1.0", "description": "teste", "files": files}
    if settings:
        base["settings"] = settings
    return base


def _py_file(rel, mods):
    return {
        "id": rel,
        "path_mode": "relative",
        "relative_path": rel,
        "type": "python",
        "modifications": mods,
    }


# ───────────────────────── patch_engine ─────────────────────────


def test_dry_run_writes_nothing(tmp_path):
    f = tmp_path / "m.py"
    f.write_text("def a():\n    return 1\n", encoding="utf-8")
    instr = _instr(
        [
            _py_file(
                "m.py",
                [
                    {
                        "id": "m1",
                        "description": "d",
                        "strategy": "replace_function",
                        "location": {"name": "a"},
                        "new_content": "def a():\n    return 99\n",
                    }
                ],
            )
        ]
    )
    report = apply_instruction(instr, root_path=tmp_path, dry_run=True, color=False)
    assert report.ok
    assert report.dry_run
    assert report.files[0].status == "modified"
    assert report.files[0].diff  # diff calculado
    # arquivo NÃO mudou
    assert f.read_text(encoding="utf-8") == "def a():\n    return 1\n"


def test_apply_writes_and_backs_up(tmp_path):
    f = tmp_path / "m.py"
    f.write_text("def a():\n    return 1\n", encoding="utf-8")
    instr = _instr(
        [
            _py_file(
                "m.py",
                [
                    {
                        "id": "m1",
                        "description": "d",
                        "strategy": "replace_function",
                        "location": {"name": "a"},
                        "new_content": "def a():\n    return 99\n",
                    }
                ],
            )
        ]
    )
    report = apply_instruction(instr, root_path=tmp_path, color=False)
    assert report.ok
    assert "return 99" in f.read_text(encoding="utf-8")
    assert report.backup_dir is not None
    # DEC-024c/DEC-032: padrão é parent(root)/zz_backups/<ts>
    assert Path(report.backup_dir).parent.parent == tmp_path.parent


def test_create_file_makes_dirs(tmp_path):
    instr = _instr(
        [
            {
                "id": "novo",
                "path_mode": "relative",
                "relative_path": "pkg/sub/new.py",
                "type": "python",
                "modifications": [
                    {
                        "id": "m1",
                        "description": "d",
                        "strategy": "create_file",
                        "content": "x = 1\n",
                    }
                ],
            }
        ]
    )
    report = apply_instruction(instr, root_path=tmp_path, color=False)
    assert report.ok
    assert report.files[0].status == "created"
    assert (tmp_path / "pkg" / "sub" / "new.py").read_text(encoding="utf-8") == "x = 1\n"


# ── Canal de warnings (spec 0001) ─────────────────────────────────────────


def test_split_apply_result_str():
    assert split_apply_result("x") == ("x", [])


def test_split_apply_result_tupla():
    assert split_apply_result(("x", ["a"])) == ("x", ["a"])


def test_modification_result_carrega_warnings():
    mr = ModificationResult("m1", "create_file", ok=True, warnings=["aviso"])
    assert mr.warnings == ["aviso"]


def test_engine_coleta_warning_do_piloto(tmp_path):
    """create_file sobre arquivo existente emite warning, mas continua ok."""
    f = tmp_path / "existente.txt"
    f.write_text("conteudo antigo\n", encoding="utf-8")
    instr = _instr(
        [
            {
                "id": "existente",
                "path_mode": "relative",
                "relative_path": "existente.txt",
                "type": "text",
                "modifications": [
                    {
                        "id": "m1",
                        "description": "d",
                        "strategy": "create_file",
                        "content": "conteudo novo\n",
                    }
                ],
            }
        ]
    )
    report = apply_instruction(instr, root_path=tmp_path, color=False)
    assert report.ok is True
    assert f.read_text(encoding="utf-8") == "conteudo novo\n"
    assert report.has_warnings is True
    assert report.files[0].has_warnings is True
    assert "substitu" in report.files[0].modifications[0].warnings[0]


def test_engine_sem_warning_fica_limpo(tmp_path):
    """Estrategia comum (sem emissao de warning) mantem has_warnings False."""
    f = tmp_path / "m.py"
    f.write_text("def a():\n    return 1\n", encoding="utf-8")
    instr = _instr(
        [
            _py_file(
                "m.py",
                [
                    {
                        "id": "m1",
                        "description": "d",
                        "strategy": "replace_function",
                        "location": {"name": "a"},
                        "new_content": "def a():\n    return 99\n",
                    }
                ],
            )
        ]
    )
    report = apply_instruction(instr, root_path=tmp_path, color=False)
    assert report.ok
    assert report.has_warnings is False
    assert report.files[0].modifications[0].warnings == []


def test_warning_nao_aborta_nem_reverte(tmp_path):
    """O warning do piloto nao vira erro: nao aborta, nao reverte, nao marca failed."""
    f = tmp_path / "existente.txt"
    f.write_text("antigo\n", encoding="utf-8")
    instr = _instr(
        [
            {
                "id": "existente",
                "path_mode": "relative",
                "relative_path": "existente.txt",
                "type": "text",
                "modifications": [
                    {
                        "id": "m1",
                        "description": "d",
                        "strategy": "create_file",
                        "content": "novo\n",
                    }
                ],
            }
        ]
    )
    report = apply_instruction(instr, root_path=tmp_path, color=False)
    assert report.ok is True
    assert report.rolled_back is False
    assert report.files[0].status != "failed"


def test_atomic_rollback_on_failure(tmp_path):
    # f1 aplica com sucesso; f2 falha; com stop_on_error tudo deve reverter.
    f1 = tmp_path / "a.py"
    f1.write_text("def a():\n    return 1\n", encoding="utf-8")
    f2 = tmp_path / "b.py"
    f2.write_text("def b():\n    return 2\n", encoding="utf-8")

    instr = _instr(
        [
            _py_file(
                "a.py",
                [
                    {
                        "id": "m1",
                        "description": "d",
                        "strategy": "replace_function",
                        "location": {"name": "a"},
                        "new_content": "def a():\n    return 11\n",
                    }
                ],
            ),
            _py_file(
                "b.py",
                [
                    {
                        "id": "m1",
                        "description": "d",
                        "strategy": "replace_function",
                        "location": {"name": "INEXISTENTE"},
                        "new_content": "def x():\n    return 0\n",
                    }
                ],
            ),
        ],
        stop_on_error=True,
    )
    report = apply_instruction(instr, root_path=tmp_path, color=False)
    assert not report.ok
    assert report.rolled_back
    # a.py foi revertido ao original apesar de ter sido escrito antes da falha
    assert f1.read_text(encoding="utf-8") == "def a():\n    return 1\n"


def test_continue_on_error_false_keeps_going(tmp_path):
    f1 = tmp_path / "a.py"
    f1.write_text("def a():\n    return 1\n", encoding="utf-8")
    f2 = tmp_path / "b.py"
    f2.write_text("def b():\n    return 2\n", encoding="utf-8")

    instr = _instr(
        [
            _py_file(
                "a.py",
                [
                    {
                        "id": "m1",
                        "description": "d",
                        "strategy": "replace_function",
                        "location": {"name": "NAO_EXISTE"},
                        "new_content": "def z():\n    return 0\n",
                    }
                ],
            ),
            _py_file(
                "b.py",
                [
                    {
                        "id": "m1",
                        "description": "d",
                        "strategy": "replace_function",
                        "location": {"name": "b"},
                        "new_content": "def b():\n    return 22\n",
                    }
                ],
            ),
        ],
        stop_on_error=False,
    )
    report = apply_instruction(instr, root_path=tmp_path, color=False)
    assert not report.ok  # houve uma falha
    assert report.files[0].status == "failed"
    assert report.files[1].status == "modified"
    assert "return 22" in f2.read_text(encoding="utf-8")  # f2 foi aplicado


def test_rollback_session_roundtrip(tmp_path):
    f = tmp_path / "cfg.json"
    f.write_text('{"v": 1}', encoding="utf-8")
    instr = _instr(
        [
            {
                "id": "cfg",
                "path_mode": "relative",
                "relative_path": "cfg.json",
                "type": "json",
                "modifications": [
                    {
                        "id": "m1",
                        "description": "d",
                        "strategy": "set_json_path",
                        "location": {"path": "v"},
                        "value": 2,
                    }
                ],
            }
        ]
    )
    report = apply_instruction(instr, root_path=tmp_path, color=False)
    assert json.loads(f.read_text(encoding="utf-8"))["v"] == 2

    # DEC-024c/DEC-032: backup em parent(root)/zz_backups/<ts>; rollback_from_dir usa o path direto.
    rollback_from_dir(Path(report.backup_dir))
    assert json.loads(f.read_text(encoding="utf-8"))["v"] == 1


# ─────────────── CLI: apply --sandbox (modo seguro) ───────────────


def test_cli_sandbox_applies_on_copy_not_original(tmp_path, monkeypatch):
    """--sandbox duplica a raiz e aplica na cópia; o original fica intacto."""
    import json as _json

    from src.__main__ import main

    raiz = tmp_path / "projeto"
    (raiz / "node_modules").mkdir(parents=True)  # deve ser ignorada na cópia
    (raiz / "node_modules" / "pesado.js").write_text("x", encoding="utf-8")
    (raiz / "cfg.json").write_text('{"v": 1}\n', encoding="utf-8")

    instr = tmp_path / "i.yaml"
    instr.write_text(
        "format_version: '1.0'\n"
        "description: sandbox test\n"
        "files:\n"
        "  - id: f1\n"
        "    path_mode: relative\n"
        "    relative_path: cfg.json\n"
        "    type: json\n"
        "    modifications:\n"
        "      - {id: m1, description: d, strategy: set_json_path,\n"
        "         location: {path: v}, value: 2}\n",
        encoding="utf-8",
    )

    rc = main(["apply", str(instr), "--root", str(raiz), "--sandbox", "--yes", "--no-color"])
    assert rc == 0
    # original intacto
    assert _json.loads((raiz / "cfg.json").read_text(encoding="utf-8"))["v"] == 1
    # sandbox criada como irmã, com a mudança aplicada e sem node_modules
    sandboxes = sorted(tmp_path.glob("projeto_sandbox_*"))
    assert len(sandboxes) == 1
    sb = sandboxes[0]
    assert _json.loads((sb / "cfg.json").read_text(encoding="utf-8"))["v"] == 2
    assert not (sb / "node_modules").exists()


def test_backup_usa_pasta_zz_backups(tmp_path):
    """DEC-032: a sessão de backup nasce em <backup_root>/zz_backups/<ts>."""
    from src.core.backup_manager import BACKUP_DIRNAME, BackupManager

    sess = BackupManager(backup_root=tmp_path)
    assert sess.session_dir.parent.name == BACKUP_DIRNAME


def test_rollback_encontra_layout_legado(tmp_path):
    """Backups criados até a 0.8.7 (pasta `backups/`) continuam restauráveis."""
    from src.core.backup_manager import LEGACY_BACKUP_DIRNAME, rollback_session

    ts = "20250101_000000"
    alvo = tmp_path / "arquivo.txt"
    alvo.write_text("novo", encoding="utf-8")

    sessao = tmp_path / LEGACY_BACKUP_DIRNAME / ts
    espelho = sessao / "arquivo.txt"
    espelho.parent.mkdir(parents=True, exist_ok=True)
    espelho.write_text("antigo", encoding="utf-8")
    (sessao / "manifest.txt").write_text(f"modificado\t{alvo}\t{espelho}\n", encoding="utf-8")

    rollback_session(tmp_path, ts)
    assert alvo.read_text(encoding="utf-8") == "antigo"


def test_cli_print_report_mostra_ressalva(capsys):
    """DEC-028/paridade: aviso não-fatal aparece por arquivo (`~`) e no resumo."""
    from src.__main__ import _print_report
    from src.core.patch_engine import ApplyReport, FileResult, ModificationResult

    mr = ModificationResult(mod_id="m1", strategy="create_file", ok=True)
    mr.warnings.append("arquivo já existia — sobrescrito")
    fr = FileResult(file_id="f1", path="x.py", status="created", modifications=[mr])
    _print_report(ApplyReport(ok=True, dry_run=False, files=[fr]))

    out = capsys.readouterr().out
    assert "~ arquivo já existia — sobrescrito" in out  # aviso por arquivo
    assert "1 com ressalva" in out  # contagem no resumo


def test_cli_print_report_sem_ressalva_nao_polui(capsys):
    """Sem avisos, a linha de resumo NÃO ganha o sufixo de ressalva."""
    from src.__main__ import _print_report
    from src.core.patch_engine import ApplyReport, FileResult

    fr = FileResult(file_id="f1", path="x.py", status="modified")
    _print_report(ApplyReport(ok=True, dry_run=False, files=[fr]))

    out = capsys.readouterr().out
    assert "com ressalva" not in out
    assert "1 modificado(s)" in out


def test_cli_sandbox_rejects_absolute_paths(tmp_path, capsys):
    from src.__main__ import main

    raiz = tmp_path / "projeto"
    raiz.mkdir()
    alvo = tmp_path / "fora.txt"
    alvo.write_text("x", encoding="utf-8")
    instr = tmp_path / "i.yaml"
    instr.write_text(
        "format_version: '1.0'\n"
        "description: abs\n"
        "files:\n"
        "  - id: f1\n"
        "    path_mode: absolute\n"
        f"    absolute_path: {alvo}\n"
        "    type: text\n"
        "    modifications:\n"
        "      - {id: m1, description: d, strategy: replace_file, new_content: y}\n",
        encoding="utf-8",
    )
    with pytest.raises(SystemExit) as exc:
        main(["apply", str(instr), "--root", str(raiz), "--sandbox", "--yes"])
    assert exc.value.code == 2
    assert "absolute" in capsys.readouterr().err
    assert alvo.read_text(encoding="utf-8") == "x"  # intocado


# ─────────────── backup_location + history.log (v0.6.0) ───────────────


def _txt_file(rel, mods):
    return {
        "id": rel,
        "path_mode": "relative",
        "relative_path": rel,
        "type": "text",
        "modifications": mods,
    }


def _replace_file_mod(new_content):
    return [
        {"id": "m1", "description": "d", "strategy": "replace_file", "new_content": new_content}
    ]


def test_backup_location_keeps_project_clean(tmp_path):
    """--backup-dir cria o backup fora do projeto; a arvore do projeto fica limpa."""
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "f.txt").write_text("antigo\n", encoding="utf-8")
    fora = tmp_path / "fora"
    fora.mkdir()
    instr = _instr([_txt_file("f.txt", _replace_file_mod("novo\n"))])

    report = apply_instruction(instr, root_path=proj, backup_location=fora, color=False)
    assert report.ok
    assert not (proj / BACKUP_DIRNAME).exists()  # projeto limpo
    # Estrutura nova: fora/<project_name>/<ts>  (sem subpasta de backup)
    assert Path(report.backup_dir).parent.parent == fora
    assert Path(report.backup_dir).parent.name == "proj"
    rollback_from_dir(Path(report.backup_dir))
    assert (proj / "f.txt").read_text(encoding="utf-8") == "antigo\n"


def test_history_log_accumulates(tmp_path):
    """Cada aplicacao acrescenta uma linha a zz_backups/history.log."""
    import time

    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "f.txt").write_text("v0\n", encoding="utf-8")

    for i in range(1, 3):
        instr = _instr([_txt_file("f.txt", _replace_file_mod(f"v{i}\n"))])
        instr["description"] = f"mudanca {i}"
        time.sleep(1.05)  # timestamps distintos (pasta por segundo)
        apply_instruction(instr, root_path=proj, color=False)

    # DEC-024c/DEC-032: padrão é parent(proj)/zz_backups/history.log
    history = (tmp_path / BACKUP_DIRNAME / "history.log").read_text(encoding="utf-8")
    assert history.count("\n") == 2
    assert "mudanca 1" in history and "mudanca 2" in history


# ── F3: backup externo com project_name (WI-1/WI-2) ──────────────────────────


def test_backup_padrao_pasta_pai(tmp_path):
    """Padrão DEC-024c/DEC-032: sem backup_location, backup em parent(root)/zz_backups/<ts>."""
    proj = tmp_path / "meu_projeto"
    proj.mkdir()
    (proj / "f.txt").write_text("antigo\n", encoding="utf-8")
    instr = _instr([_txt_file("f.txt", _replace_file_mod("novo\n"))])

    report = apply_instruction(instr, root_path=proj, color=False)
    assert report.ok
    session_dir = Path(report.backup_dir)
    # Estrutura esperada: tmp_path/zz_backups/<ts>  (parent do proj, sem aninhar por nome)
    assert session_dir.parent.parent == tmp_path
    assert session_dir.parent.name == BACKUP_DIRNAME
    assert not (proj / BACKUP_DIRNAME).exists()  # projeto limpo


def test_backup_externo_aninha_por_projeto(tmp_path):
    """Backup externo: usa <ext>/<project_name>/<ts>, sem pasta backups/ no projeto."""
    proj = tmp_path / "meu_projeto"
    proj.mkdir()
    (proj / "f.txt").write_text("antigo\n", encoding="utf-8")
    ext = tmp_path / "backup_externo"
    ext.mkdir()
    instr = _instr([_txt_file("f.txt", _replace_file_mod("novo\n"))])

    report = apply_instruction(instr, root_path=proj, backup_location=ext, color=False)
    assert report.ok
    session_dir = Path(report.backup_dir)
    # Estrutura esperada: ext/meu_projeto/<ts>
    assert session_dir.parent.parent == ext
    assert session_dir.parent.name == "meu_projeto"
    assert not (proj / BACKUP_DIRNAME).exists()


def test_backup_externo_history_por_projeto(tmp_path):
    """history.log fica em <ext>/<project_name>/ (ao lado das sessoes)."""
    proj = tmp_path / "meu_projeto"
    proj.mkdir()
    (proj / "f.txt").write_text("antigo\n", encoding="utf-8")
    ext = tmp_path / "backup_externo"
    ext.mkdir()
    instr = _instr([_txt_file("f.txt", _replace_file_mod("novo\n"))])
    instr["description"] = "teste history externo"

    apply_instruction(instr, root_path=proj, backup_location=ext, color=False)
    history = ext / "meu_projeto" / "history.log"
    assert history.is_file()
    assert "teste history externo" in history.read_text(encoding="utf-8")


def test_rollback_from_dir_backup_interno(tmp_path):
    """rollback_from_dir funciona com backup interno."""
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "f.txt").write_text("antigo\n", encoding="utf-8")
    instr = _instr([_txt_file("f.txt", _replace_file_mod("novo\n"))])

    report = apply_instruction(instr, root_path=proj, color=False)
    assert (proj / "f.txt").read_text(encoding="utf-8") == "novo\n"

    rollback_from_dir(Path(report.backup_dir))
    assert (proj / "f.txt").read_text(encoding="utf-8") == "antigo\n"


def test_rollback_registra_no_history(tmp_path):
    """Um rollback manual acrescenta uma linha 'rollback de <ts>' ao history.log."""
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "f.txt").write_text("antigo\n", encoding="utf-8")
    instr = _instr([_txt_file("f.txt", _replace_file_mod("novo\n"))])
    instr["description"] = "aplicacao 1"

    report = apply_instruction(instr, root_path=proj, color=False)
    session_dir = Path(report.backup_dir)
    history = session_dir.parent / "history.log"
    # Após a aplicação: 1 linha (a aplicação).
    assert history.read_text(encoding="utf-8").count("\n") == 1

    rollback_from_dir(session_dir)
    conteudo = history.read_text(encoding="utf-8")
    # Agora 2 linhas: a aplicação + o rollback.
    assert conteudo.count("\n") == 2
    assert f"rollback de {session_dir.name}" in conteudo
    assert (proj / "f.txt").read_text(encoding="utf-8") == "antigo\n"


def test_rollback_from_dir_backup_externo(tmp_path):
    """rollback_from_dir funciona com backup externo aninhado por projeto."""
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "f.txt").write_text("antigo\n", encoding="utf-8")
    ext = tmp_path / "ext"
    ext.mkdir()
    instr = _instr([_txt_file("f.txt", _replace_file_mod("novo\n"))])

    report = apply_instruction(instr, root_path=proj, backup_location=ext, color=False)
    assert (proj / "f.txt").read_text(encoding="utf-8") == "novo\n"

    rollback_from_dir(Path(report.backup_dir))
    assert (proj / "f.txt").read_text(encoding="utf-8") == "antigo\n"


# ── DEC-024c: padrão backup na pasta-pai ─────────────────────────────────────


def test_backup_padrao_rollback_via_cli(tmp_path):
    """rollback default (sem --backup-dir) acha o backup em parent(root)/zz_backups."""
    from src.__main__ import main

    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "f.txt").write_text("antigo\n", encoding="utf-8")
    instr = _instr([_txt_file("f.txt", _replace_file_mod("novo\n"))])
    instr_path = tmp_path / "i.yaml"
    import yaml

    instr_path.write_text(yaml.dump(instr), encoding="utf-8")

    rc = main(["apply", str(instr_path), "--root", str(proj), "--yes", "--no-color"])
    assert rc == 0
    assert (proj / "f.txt").read_text(encoding="utf-8") == "novo\n"
    # Backup em parent(proj)/zz_backups/<ts>
    backups = [p for p in (tmp_path / BACKUP_DIRNAME).iterdir() if p.is_dir()]
    assert len(backups) == 1
    ts = backups[0].name

    rc2 = main(["rollback", ts, "--root", str(proj)])
    assert rc2 == 0
    assert (proj / "f.txt").read_text(encoding="utf-8") == "antigo\n"


def test_backup_externo_nao_regride_dec024b(tmp_path):
    """--backup-dir explicito ainda aninha por projeto (DEC-024b nao regride)."""
    proj = tmp_path / "meu_proj"
    proj.mkdir()
    (proj / "f.txt").write_text("antigo\n", encoding="utf-8")
    ext = tmp_path / "backups_compartilhados"
    ext.mkdir()
    instr = _instr([_txt_file("f.txt", _replace_file_mod("novo\n"))])

    report = apply_instruction(instr, root_path=proj, backup_location=ext, color=False)
    assert report.ok
    session_dir = Path(report.backup_dir)
    # Estrutura esperada: ext/meu_proj/<ts>  (aninha por projeto quando externo)
    assert session_dir.parent.parent == ext
    assert session_dir.parent.name == "meu_proj"
    assert not (proj / BACKUP_DIRNAME).exists()
