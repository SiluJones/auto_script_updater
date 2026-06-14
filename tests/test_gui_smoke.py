"""Smoke da GUI em modo offscreen (sem display).

Valida o circuito completo da janela: preview (dry-run) popula a árvore e
habilita Aplicar; apply escreve em disco e habilita Desfazer; undo reverte.
Pulado automaticamente se PySide6 não estiver instalado (o core não depende
da GUI).
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

PySide6 = pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # roda sem servidor gráfico

from PySide6.QtWidgets import QApplication  # noqa: E402

from src.gui.main_window import MainWindow, _diff_to_html  # noqa: E402

_REPO = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def demo_root(tmp_path):
    raiz = tmp_path / "demo_project"
    shutil.copytree(_REPO / "examples" / "demo_project", raiz)
    return raiz


def test_gui_preview_apply_undo_roundtrip(app, demo_root):
    win = MainWindow()
    win.root_edit.setText(str(demo_root))
    win.instr_edit.setText(str(_REPO / "examples" / "demo.yaml"))

    # Preview: árvore populada, Aplicar habilitado, diffs renderizados.
    win.preview()
    assert win.tree.topLevelItemCount() == 5  # 5 arquivos na demo
    assert win.btn_apply.isEnabled()
    primeiro = win.tree.topLevelItem(0)
    assert primeiro.text(0).startswith("🟢")
    assert "+" in win.diff_view.toPlainText()  # diff do item selecionado
    # dry-run não escreveu nada
    assert not (demo_root / "src" / "health.py").exists()

    # Apply (sem diálogo): escreve, cria backup, habilita Desfazer.
    win.apply_changes(confirm=False)
    assert (demo_root / "src" / "health.py").exists()
    assert "Divisão por zero" in (demo_root / "src" / "calculator.py").read_text("utf-8")
    assert win.btn_undo.isEnabled()

    # Undo: reverte tudo.
    win.undo_last(confirm=False)
    assert not (demo_root / "src" / "health.py").exists()
    assert "Divisão por zero" not in (demo_root / "src" / "calculator.py").read_text("utf-8")
    assert not win.btn_undo.isEnabled()


def test_gui_preview_marks_failures(app, demo_root):
    """Instrução com âncora inexistente → item 🔴, Aplicar desabilitado."""
    import yaml

    instr = {
        "format_version": "1.0",
        "description": "falha proposital",
        "files": [
            {
                "id": "f1",
                "path_mode": "relative",
                "relative_path": "web/app.js",
                "type": "text",
                "modifications": [
                    {
                        "id": "m1",
                        "description": "d",
                        "strategy": "replace_context_block",
                        "location": {"before": "NAO_EXISTE_NO_ARQUIVO", "after": "}"},
                        "new_content": "x",
                    }
                ],
            }
        ],
    }
    caminho = demo_root.parent / "instr_falha.yaml"
    caminho.write_text(yaml.safe_dump(instr, allow_unicode=True), encoding="utf-8")

    win = MainWindow()
    win.root_edit.setText(str(demo_root))
    win.instr_edit.setText(str(caminho))
    win.preview()
    assert not win.btn_apply.isEnabled()
    assert win.tree.topLevelItem(0).text(0).startswith("🔴")


def test_diff_to_html_colors_lines():
    htm = _diff_to_html("--- a/x\n+++ b/x\n@@ -1 +1 @@\n-velho\n+novo\n ctx")
    assert htm.count("<span") == 5  # 3 cabeçalhos + 1 del + 1 add
    assert "novo" in htm and "velho" in htm


def test_gui_stale_preview_blocks_apply(app, demo_root, tmp_path, monkeypatch):
    """FIX-007b: editar a instrução após a prévia deve bloquear o Aplicar."""
    instr = tmp_path / "i.yaml"
    instr.write_text(
        (_REPO / "examples" / "demo.yaml").read_text(encoding="utf-8"), encoding="utf-8"
    )
    win = MainWindow()
    win.root_edit.setText(str(demo_root))
    win.instr_edit.setText(str(instr))
    win.preview()
    assert win.btn_apply.isEnabled()

    # Edita o YAML depois da prévia (muda a descrição — conteúdo diferente).
    instr.write_text(
        instr.read_text(encoding="utf-8").replace("Demo:", "Demo EDITADA:"), encoding="utf-8"
    )
    avisos = []
    monkeypatch.setattr(
        "src.gui.main_window.QMessageBox.warning",
        lambda *a, **k: avisos.append(a[2] if len(a) > 2 else ""),
    )
    win.apply_changes(confirm=False)
    assert avisos, "deveria avisar prévia desatualizada"
    assert not (demo_root / "src" / "health.py").exists()  # nada aplicado
    assert not win.btn_apply.isEnabled()  # exige nova prévia


def test_gui_paste_instruction_roundtrip(app, demo_root):
    """Colar do clipboard substitui o arquivo: preview e apply funcionam."""
    texto = (_REPO / "examples" / "demo.yaml").read_text(encoding="utf-8")
    QApplication.clipboard().setText(texto)
    win = MainWindow()
    win.root_edit.setText(str(demo_root))
    win._paste_instruction()
    assert win.instr_edit.text() == win.PASTED_MARK
    win.preview()
    assert win.btn_apply.isEnabled()
    win.apply_changes(confirm=False)
    assert (demo_root / "src" / "health.py").exists()
    win.undo_last(confirm=False)
    assert not (demo_root / "src" / "health.py").exists()


def test_gui_undo_uses_captured_root(app, demo_root, tmp_path):
    """FIX-007a: trocar a raiz após aplicar não pode quebrar o Desfazer."""
    win = MainWindow()
    win.root_edit.setText(str(demo_root))
    win.instr_edit.setText(str(_REPO / "examples" / "demo.yaml"))
    win.preview()
    win.apply_changes(confirm=False)
    assert (demo_root / "src" / "health.py").exists()

    # Usuário distraído muda a raiz para outra pasta qualquer…
    win.root_edit.setText(str(tmp_path / "outra_pasta_qualquer"))
    # …e o Desfazer ainda reverte no lugar certo (raiz capturada na aplicação).
    win.undo_last(confirm=False)
    assert not (demo_root / "src" / "health.py").exists()


def test_gui_copy_errors_for_ai(app, demo_root, tmp_path):
    """Falha na prévia habilita e preenche o 'Copiar erro para a IA'."""
    import yaml

    instr = {
        "format_version": "1.0",
        "description": "falha proposital",
        "files": [
            {
                "id": "f1",
                "path_mode": "relative",
                "relative_path": "web/app.js",
                "type": "text",
                "modifications": [
                    {
                        "id": "m1",
                        "description": "d",
                        "strategy": "replace_context_block",
                        "location": {"before": "NAO_EXISTE", "after": "}"},
                        "new_content": "x",
                    }
                ],
            }
        ],
    }
    caminho = tmp_path / "falha.yaml"
    caminho.write_text(yaml.safe_dump(instr, allow_unicode=True), encoding="utf-8")

    win = MainWindow()
    win.root_edit.setText(str(demo_root))
    win.instr_edit.setText(str(caminho))
    win.preview()
    assert win.btn_copy_err.isEnabled()
    win.copy_errors_for_ai()
    copiado = QApplication.clipboard().text()
    assert "NAO_EXISTE" in copiado and "INSTRUCTION_GUIDE" in copiado and "§6" in copiado
