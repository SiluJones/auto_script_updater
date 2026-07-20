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

from src.core.patch_engine import ApplyReport, FileResult, ModificationResult  # noqa: E402
from src.gui.main_window import (  # noqa: E402
    _CSS_ADD,
    MainWindow,
    _diff_to_html,
    _report_to_text,
)

_REPO = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module", autouse=True)
def _isolate_qsettings(tmp_path_factory):
    """Redireciona o QSettings da GUI para um .ini temporário.

    Sem isto, `MainWindow` grava em `QSettings("auto-script-updater", "gui")` —
    no Windows, o REGISTRO do usuário — e a suíte contamina a GUI real (foi o
    que injetou um caminho `pytest-of-*/.../meu_backup` no campo Backup de um
    usuário real). Ver DEC-032.
    """
    from PySide6.QtCore import QSettings

    destino = str(tmp_path_factory.mktemp("qsettings"))
    formato = QSettings.Format.IniFormat
    QSettings.setPath(formato, QSettings.Scope.UserScope, destino)
    QSettings.setDefaultFormat(formato)
    yield


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def demo_root(tmp_path):
    raiz = tmp_path / "demo_project"
    shutil.copytree(_REPO / "examples" / "demo_project", raiz)
    # Defesa em profundidade: a demo.yaml CRIA estes arquivos via create_file.
    # Se algum vazou para examples/demo_project/ numa execução anterior (e foi
    # versionado/copiado junto), o dry-run o encontraria já existindo e o
    # assert "não escreveu nada" falharia. Garante um ponto de partida limpo.
    for gerado in ("src/health.py",):
        alvo = raiz / gerado
        if alvo.exists():
            alvo.unlink()
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


def test_diff_to_html_sem_path_e_o_comportamento_antigo():
    """Regressão explícita: sem `path`, a saída é idêntica ao modo só-de-linha."""
    diff = "--- a/x\n+++ b/x\n@@ -1 +1 @@\n-velho\n+novo\n ctx"
    assert _diff_to_html(diff) == _diff_to_html(diff, None)


def test_diff_to_html_extensao_desconhecida_cai_no_fallback():
    """Extensão que o Pygments não mapeia → realce só-de-linha (foreground)."""
    diff = "--- a/x.zzz\n+++ b/x.zzz\n@@ -1 +1 @@\n-velho\n+novo\n ctx"
    htm = _diff_to_html(diff, "x.zzz")
    assert _CSS_ADD in htm  # marca a adição pelo foreground (fallback)


def test_diff_to_html_realca_python_quando_ha_pygments():
    """Com `path` .py e Pygments instalado: adição marca pelo FUNDO e há mais
    spans (realce de token). Pulado se o Pygments não estiver instalado."""
    pytest.importorskip("pygments")
    diff = "--- a/x.py\n+++ b/x.py\n@@ -0,0 +1 @@\n+def foo():\n"
    htm = _diff_to_html(diff, "src/x.py")
    assert "background-color" in htm  # adição marca pelo fundo
    assert htm.count("<span") > 4  # tokens realçados acrescentam spans


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


def test_gui_sandbox_checkbox_applies_on_copy(app, demo_root):
    """Checkbox de sandbox: aplica numa cópia irmã; o demo_root original fica intocado."""
    win = MainWindow()
    win.root_edit.setText(str(demo_root))
    win.instr_edit.setText(str(_REPO / "examples" / "demo.yaml"))
    win.chk_sandbox.setChecked(True)
    win.preview()
    win.apply_changes(confirm=False)
    # original intacto (health.py NÃO criado nele)
    assert not (demo_root / "src" / "health.py").exists()
    # a cópia irmã recebeu a mudança
    irmas = list(demo_root.parent.glob(f"{demo_root.name}_sandbox_*"))
    assert len(irmas) == 1
    assert (irmas[0] / "src" / "health.py").exists()


# ── WI-1: recentes e fixadas ──────────────────────────────────────────────


def _clear_recents(win: MainWindow) -> None:
    win._settings.remove("recent_roots")
    win._settings.remove("pinned_roots")


def test_push_recent_root_adds_and_deduplicates(app):
    """_push_recent_root: insere no topo e remove duplicata case-insensitive."""
    win = MainWindow()
    _clear_recents(win)
    try:
        win._push_recent_root("/proj/a")
        win._push_recent_root("/proj/b")
        win._push_recent_root("/proj/a")  # duplicata — sobe ao topo
        recentes = win._load_recent_roots()
        assert recentes[0] == "/proj/a"
        assert recentes[1] == "/proj/b"
        assert recentes.count("/proj/a") == 1
    finally:
        _clear_recents(win)


def test_push_recent_root_max_8(app):
    """_push_recent_root: lista nunca ultrapassa 8 itens."""
    win = MainWindow()
    _clear_recents(win)
    try:
        for i in range(10):
            win._push_recent_root(f"/proj/{i}")
        assert len(win._load_recent_roots()) == 8
    finally:
        _clear_recents(win)


def test_toggle_pin_root_add_and_remove(app):
    """_toggle_pin_root: adiciona e remove da lista de fixadas."""
    win = MainWindow()
    _clear_recents(win)
    try:
        win._toggle_pin_root("/proj/x")
        assert "/proj/x" in win._load_pinned_roots()
        win._toggle_pin_root("/proj/x")  # desafixar
        assert "/proj/x" not in win._load_pinned_roots()
    finally:
        _clear_recents(win)


def test_preview_pushes_recent_root(app, demo_root):
    """preview() bem-sucedido adiciona a raiz à lista de recentes."""
    win = MainWindow()
    _clear_recents(win)
    try:
        win.root_edit.setText(str(demo_root))
        win.instr_edit.setText(str(_REPO / "examples" / "demo.yaml"))
        win.preview()
        assert str(demo_root) in win._load_recent_roots()
    finally:
        _clear_recents(win)


# ── WI-2: argumentos de lançamento ──────────────────────────────────────


def test_mainwindow_root_arg_preenchido(app, demo_root):
    """--root pré-preenche o campo de raiz."""
    win = MainWindow(root=str(demo_root))
    assert win.root_edit.text() == str(demo_root)


def test_mainwindow_instruction_arg_preenchido(app, tmp_path):
    """--instruction pré-preenche o campo de instrução."""
    arq = tmp_path / "test.yaml"
    arq.write_text("x: 1")
    win = MainWindow(instruction=str(arq))
    assert win.instr_edit.text() == str(arq)


def test_mainwindow_instruction_dir_um_yaml(app, tmp_path):
    """--instruction-dir com 1 yaml pré-preenche o campo de instrução."""
    (tmp_path / "instr.yaml").write_text("x: 1")
    win = MainWindow(instruction_dir=str(tmp_path))
    assert win.instr_edit.text() == str(tmp_path / "instr.yaml")
    assert win._instruction_start_dir == str(tmp_path)


def test_mainwindow_instruction_dir_muitos_yamls(app, tmp_path):
    """--instruction-dir com 2+ yamls aponta o seletor mas nao auto-seleciona."""
    (tmp_path / "a.yaml").write_text("x: 1")
    (tmp_path / "b.yaml").write_text("y: 2")
    win = MainWindow(instruction_dir=str(tmp_path))
    assert win._instruction_start_dir == str(tmp_path)
    # nenhum yaml foi escolhido automaticamente
    instr = win.instr_edit.text()
    assert instr not in [str(tmp_path / "a.yaml"), str(tmp_path / "b.yaml")]


def test_btn_bat_habilitado_com_raiz(app, demo_root):
    """Botão .bat habilitado somente quando a raiz está preenchida."""
    win = MainWindow()
    win.root_edit.setText("")
    assert not win.btn_bat.isEnabled()
    win.root_edit.setText(str(demo_root))
    assert win.btn_bat.isEnabled()


# ── F3: campo de backup na GUI ────────────────────────────────────────────────


def test_gui_tem_campo_backup(app):
    """A janela instancia com o campo backup_edit."""
    win = MainWindow()
    assert hasattr(win, "backup_edit")
    assert win.backup_edit.placeholderText() != ""


def test_backup_dir_nao_e_persistido(app, tmp_path):
    """DEC-032: o backup-dir NÃO sobrevive à sessão — ele é derivado da raiz.

    Regressão do bug em que um caminho salvo (inclusive um tmp de teste vazado
    para o perfil real) 'grudava' e ignorava a troca de raiz.
    """
    pasta = str(tmp_path / "meu_backup")
    win = MainWindow()
    win.backup_edit.setText(pasta)
    win._save_last_paths()

    win2 = MainWindow()
    win2._settings = win._settings  # compartilha o mesmo QSettings
    win2._restore_last_paths()
    assert win2.backup_edit.text() == ""  # não restaurou nada


def test_placeholder_do_backup_segue_a_raiz(app, tmp_path):
    """O destino padrão exibido acompanha a raiz escolhida (pasta-pai/zz_backups)."""
    from src.core.backup_manager import BACKUP_DIRNAME

    projeto = tmp_path / "meu_projeto"
    projeto.mkdir()
    win = MainWindow()
    win.root_edit.setText(str(projeto))

    dica = win.backup_edit.placeholderText()
    assert BACKUP_DIRNAME in dica
    assert str(tmp_path.resolve()) in dica  # a pasta-PAI, não a raiz


def test_mainwindow_guarda_start_dir(app, tmp_path):
    """A janela aceita `start_dir` sem que isso preencha a raiz."""
    from PySide6.QtCore import QSettings

    # Estado limpo: o QSettings (isolado, escopo de módulo) pode reter um
    # `last_root` salvo por um teste anterior, o que faria `_restore_last_paths`
    # preencher a raiz. O que importa aqui é que `start_dir` NÃO vira raiz.
    QSettings("auto-script-updater", "gui").clear()
    win = MainWindow(start_dir=str(tmp_path))
    assert win._start_dir == str(tmp_path)
    assert win.root_edit.text() == ""


# ── spec 0002: indicador 🟡 "aplicado com ressalva" ───────────────────────


def test_tree_mostra_amarelo_com_ressalva(app):
    """Arquivo modified + has_warnings True → item de topo comeca com 🟡."""
    fr = FileResult(
        "f1",
        "a.py",
        "modified",
        modifications=[ModificationResult("m1", "create_file", ok=True, warnings=["aviso"])],
    )
    report = ApplyReport(ok=True, dry_run=True, files=[fr])
    win = MainWindow()
    win._populate_tree(report)
    assert win.tree.topLevelItem(0).text(0).startswith("🟡")


def test_tree_falha_vence_ressalva(app):
    """Arquivo failed com warnings ainda mostra 🔴 (falha vence ressalva)."""
    fr = FileResult(
        "f1",
        "a.py",
        "failed",
        error="deu ruim",
        modifications=[ModificationResult("m1", "create_file", ok=False, error="deu ruim")],
    )
    report = ApplyReport(ok=False, dry_run=True, files=[fr])
    win = MainWindow()
    win._populate_tree(report)
    assert win.tree.topLevelItem(0).text(0).startswith("🔴")


def test_modificacao_ressalva_mostra_warn(app):
    """Modificacao ok=True com warnings → filho comeca com ⚠ e rotulo 'ressalva'."""
    fr = FileResult(
        "f1",
        "a.py",
        "modified",
        modifications=[ModificationResult("m1", "create_file", ok=True, warnings=["aviso"])],
    )
    report = ApplyReport(ok=True, dry_run=True, files=[fr])
    win = MainWindow()
    win._populate_tree(report)
    filho = win.tree.topLevelItem(0).child(0)
    assert filho.text(0).strip().startswith("⚠")
    assert filho.text(1) == "ressalva"


def test_aplicar_habilitado_com_ressalva(app, demo_root):
    """create_file sobre arquivo existente emite warning; Aplicar segue habilitado."""
    import yaml

    alvo = demo_root / "src" / "calculator.py"
    assert alvo.exists()
    instr = {
        "format_version": "1.0",
        "description": "ressalva proposital",
        "files": [
            {
                "id": "f1",
                "path_mode": "relative",
                "relative_path": "src/calculator.py",
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
        ],
    }
    caminho = demo_root.parent / "instr_ressalva.yaml"
    caminho.write_text(yaml.safe_dump(instr, allow_unicode=True), encoding="utf-8")

    win = MainWindow()
    win.root_edit.setText(str(demo_root))
    win.instr_edit.setText(str(caminho))
    win.preview()
    assert win._preview_report.has_warnings is True
    assert win.btn_apply.isEnabled()
    assert win.tree.topLevelItem(0).text(0).startswith("🟡")


def test_report_to_text_despeja_relatorio_inteiro():
    """_report_to_text inclui status, avisos, erros e o diff — sucesso e falha."""
    report = ApplyReport(
        ok=False,
        dry_run=True,
        files=[
            FileResult(
                file_id="f1",
                path="src/x.py",
                status="modified",
                diff="--- a\n+++ b\n-old\n+new\n",
                modifications=[
                    ModificationResult(
                        "m1", "replace_function", ok=True, warnings=["match por whitespace"]
                    )
                ],
            ),
            FileResult(
                file_id="f2",
                path="src/y.py",
                status="failed",
                error="Modificacao 'm2' falhou",
                modifications=[
                    ModificationResult(
                        "m2", "replace_line_pattern", ok=False, error="casou 0 vez(es)"
                    )
                ],
            ),
        ],
    )
    texto = _report_to_text(report)
    assert "FALHOU" in texto
    assert "src/x.py" in texto and "src/y.py" in texto
    assert "aviso: match por whitespace" in texto
    assert "casou 0 vez(es)" in texto
    assert "+new" in texto  # o diff entra na saida
