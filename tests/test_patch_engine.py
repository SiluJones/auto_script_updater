"""Testes de integração: file_locator + patch_engine + backup_manager."""
from __future__ import annotations

import json

import pytest

from src.core.patch_engine import apply_instruction
from src.core.backup_manager import rollback_session
from src.core.file_locator import FileLocatorError, resolve_path


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
    return {"id": rel, "path_mode": "relative", "relative_path": rel, "type": "python",
            "modifications": mods}


# ───────────────────────── patch_engine ─────────────────────────

def test_dry_run_writes_nothing(tmp_path):
    f = tmp_path / "m.py"
    f.write_text("def a():\n    return 1\n", encoding="utf-8")
    instr = _instr([_py_file("m.py", [{
        "id": "m1", "description": "d", "strategy": "replace_function",
        "location": {"name": "a"}, "new_content": "def a():\n    return 99\n",
    }])])
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
    instr = _instr([_py_file("m.py", [{
        "id": "m1", "description": "d", "strategy": "replace_function",
        "location": {"name": "a"}, "new_content": "def a():\n    return 99\n",
    }])])
    report = apply_instruction(instr, root_path=tmp_path, color=False)
    assert report.ok
    assert "return 99" in f.read_text(encoding="utf-8")
    assert report.backup_dir is not None
    assert (tmp_path / "backups").exists()


def test_create_file_makes_dirs(tmp_path):
    instr = _instr([{
        "id": "novo", "path_mode": "relative", "relative_path": "pkg/sub/new.py",
        "type": "python",
        "modifications": [{"id": "m1", "description": "d", "strategy": "create_file",
                           "content": "x = 1\n"}],
    }])
    report = apply_instruction(instr, root_path=tmp_path, color=False)
    assert report.ok
    assert report.files[0].status == "created"
    assert (tmp_path / "pkg" / "sub" / "new.py").read_text(encoding="utf-8") == "x = 1\n"


def test_atomic_rollback_on_failure(tmp_path):
    # f1 aplica com sucesso; f2 falha; com stop_on_error tudo deve reverter.
    f1 = tmp_path / "a.py"
    f1.write_text("def a():\n    return 1\n", encoding="utf-8")
    f2 = tmp_path / "b.py"
    f2.write_text("def b():\n    return 2\n", encoding="utf-8")

    instr = _instr(
        [
            _py_file("a.py", [{
                "id": "m1", "description": "d", "strategy": "replace_function",
                "location": {"name": "a"}, "new_content": "def a():\n    return 11\n",
            }]),
            _py_file("b.py", [{
                "id": "m1", "description": "d", "strategy": "replace_function",
                "location": {"name": "INEXISTENTE"}, "new_content": "def x():\n    return 0\n",
            }]),
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
            _py_file("a.py", [{
                "id": "m1", "description": "d", "strategy": "replace_function",
                "location": {"name": "NAO_EXISTE"}, "new_content": "def z():\n    return 0\n",
            }]),
            _py_file("b.py", [{
                "id": "m1", "description": "d", "strategy": "replace_function",
                "location": {"name": "b"}, "new_content": "def b():\n    return 22\n",
            }]),
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
    instr = _instr([{
        "id": "cfg", "path_mode": "relative", "relative_path": "cfg.json", "type": "json",
        "modifications": [{"id": "m1", "description": "d", "strategy": "set_json_path",
                           "location": {"path": "v"}, "value": 2}],
    }])
    report = apply_instruction(instr, root_path=tmp_path, color=False)
    assert json.loads(f.read_text(encoding="utf-8"))["v"] == 2

    ts = report.backup_dir.split("/")[-1].split("\\")[-1]
    rollback_session(tmp_path, ts)
    assert json.loads(f.read_text(encoding="utf-8"))["v"] == 1
