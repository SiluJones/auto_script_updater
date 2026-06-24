"""Janela principal da GUI (F2) — camada FINA sobre a pilha da F1 (DEC-013).

Fluxo: escolher a raiz do projeto e o arquivo de instrução → **Pré-visualizar**
roda o ``patch_engine`` em *dry-run* e popula a árvore (um item por arquivo,
filhos por modificação) com o indicador de confiança derivado do resultado
(🟢 ok / 🔴 falha — o 🟡 chegará com o canal de warnings, ver IDEAS) →
**Aplicar** repete a execução escrevendo em disco (com backup) → **Desfazer**
reverte a última aplicação pelo timestamp do backup.

Decisões conscientes desta primeira versão:
- Execução síncrona (operações locais e rápidas); thread/worker fica para
  quando houver caso real de lentidão.
- O diff é renderizado pelo ``diff_renderer`` sem ANSI e colorido aqui via
  HTML (uma linha por ``<span>``), evitando dependência de highlighter.
"""

from __future__ import annotations

import hashlib
import html
from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..core.backup_manager import rollback_session
from ..core.instruction_parser import (
    InstructionParseError,
    load_instruction_from_string,
)
from ..core.instruction_validator import InstructionValidationError, validate
from ..core.patch_engine import ApplyReport, SandboxError, apply_instruction, make_sandbox

# Cores do diff (tema claro padrão do Qt). Mantidas suaves para legibilidade.
_CSS_ADD = "color:#0a7a2f;"
_CSS_DEL = "color:#b00020;"
_CSS_HDR = "color:#005a9e;font-weight:bold;"

_STATUS_LABEL = {
    "created": "criado",
    "modified": "modificado",
    "unchanged": "inalterado",
    "failed": "FALHOU",
    "skipped": "ignorado",
}

_MAX_RECENTS = 8


def _diff_to_html(diff: str) -> str:
    """Converte um unified diff (sem ANSI) em HTML colorido linha a linha."""
    linhas = []
    for ln in diff.split("\n"):
        esc = html.escape(ln) or "&nbsp;"
        if ln.startswith(("+++", "---", "@@")):
            linhas.append(f'<span style="{_CSS_HDR}">{esc}</span>')
        elif ln.startswith("+"):
            linhas.append(f'<span style="{_CSS_ADD}">{esc}</span>')
        elif ln.startswith("-"):
            linhas.append(f'<span style="{_CSS_DEL}">{esc}</span>')
        else:
            linhas.append(esc)
    corpo = "<br>".join(linhas)
    return f'<pre style="font-family:Consolas,monospace;font-size:10pt">{corpo}</pre>'


class MainWindow(QMainWindow):
    """Janela única do ASU: prévia, aplicação e rollback de instruções."""

    def __init__(
        self,
        *,
        root: str | None = None,
        instruction_dir: str | None = None,
        instruction: str | None = None,
    ) -> None:
        super().__init__()
        self.setWindowTitle("Atualizador Automático de Scripts")
        self.resize(1000, 640)

        self._preview_report: ApplyReport | None = None
        # (raiz_usada, timestamp) da última aplicação — o Desfazer usa a raiz
        # CAPTURADA no momento de aplicar, não o campo atual (FIX-007a).
        self._last_backup: tuple[str, str] | None = None
        # Impressão digital (instrução+raiz) da prévia: o Aplicar exige que
        # nada tenha mudado desde a revisão (FIX-007b).
        self._preview_fingerprint: str | None = None
        # Texto colado da área de transferência (instrução em memória).
        self._pasted_text: str | None = None
        self._last_errors: list[str] = []  # alimenta "Copiar erro para a IA"
        self._settings = QSettings("auto-script-updater", "gui")
        # Pasta-inicial do seletor de instrução (definida por --instruction-dir).
        self._instruction_start_dir: str | None = None

        # ── Linha 1: raiz do projeto ────────────────────────────────────────
        self.root_edit = QLineEdit()
        self.root_edit.setPlaceholderText("Pasta raiz do projeto (para caminhos relativos)")
        btn_root = QPushButton("Escolher…")
        btn_root.clicked.connect(self._pick_root)
        self.btn_recentes = QPushButton("Recentes ▾")
        self.btn_recentes.setToolTip("Pastas raiz recentes e fixadas")
        self.btn_recentes.clicked.connect(self._show_recents_menu)
        self.btn_pin = QPushButton("📌")
        self.btn_pin.setToolTip("Fixar/desafixar a pasta raiz atual")
        self.btn_pin.clicked.connect(self._toggle_current_pin)

        # ── Linha 2: arquivo de instrução ───────────────────────────────────
        self.instr_edit = QLineEdit()
        self.instr_edit.setPlaceholderText("Arquivo de instrução (.yaml / .json)")
        btn_instr = QPushButton("Abrir…")
        btn_instr.clicked.connect(self._pick_instruction)
        btn_paste = QPushButton("Colar instrução")
        btn_paste.setToolTip("Lê o YAML da área de transferência (sem salvar em arquivo).")
        btn_paste.clicked.connect(self._paste_instruction)
        # Editar o campo manualmente descarta a instrução colada.
        self.instr_edit.textChanged.connect(self._on_instr_text_changed)

        # ── Ações ───────────────────────────────────────────────────────────
        self.btn_preview = QPushButton("Pré-visualizar (dry-run)")
        self.btn_preview.clicked.connect(self.preview)
        self.btn_apply = QPushButton("Aplicar")
        self.btn_apply.setEnabled(False)  # só após uma prévia OK
        self.btn_apply.clicked.connect(self.apply_changes)
        self.btn_undo = QPushButton("Desfazer última aplicação")
        self.btn_undo.setEnabled(False)
        self.btn_undo.clicked.connect(self.undo_last)
        self.btn_copy_err = QPushButton("Copiar erro para a IA")
        self.btn_copy_err.setToolTip(
            "Copia os erros + instruções de correção (§6 do guia) para colar na IA geradora."
        )
        self.btn_copy_err.setEnabled(False)
        self.btn_copy_err.clicked.connect(self.copy_errors_for_ai)
        self.btn_bat = QPushButton("Criar atalho .bat…")
        self.btn_bat.setToolTip(
            "Gera um .bat que reabre a GUI já apontada para este projeto (python do venv direto)."
        )
        self.btn_bat.setEnabled(False)
        self.btn_bat.clicked.connect(self._create_launcher_bat)
        # Habilita/desabilita o botão .bat conforme a raiz é preenchida.
        self.root_edit.textChanged.connect(self._on_root_text_changed)

        # ── Árvore de arquivos + diff ───────────────────────────────────────
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Arquivo / Modificação", "Status"])
        self.tree.setColumnWidth(0, 380)
        self.tree.currentItemChanged.connect(self._show_selected_diff)

        self.diff_view = QTextEdit()
        self.diff_view.setReadOnly(True)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.tree)
        splitter.addWidget(self.diff_view)
        splitter.setStretchFactor(1, 1)

        # ── Montagem ────────────────────────────────────────────────────────
        topo1 = QHBoxLayout()
        topo1.addWidget(QLabel("Raiz:"))
        topo1.addWidget(self.root_edit, 1)
        topo1.addWidget(btn_root)
        topo1.addWidget(self.btn_recentes)
        topo1.addWidget(self.btn_pin)
        topo2 = QHBoxLayout()
        topo2.addWidget(QLabel("Instrução:"))
        topo2.addWidget(self.instr_edit, 1)
        topo2.addWidget(btn_instr)
        topo2.addWidget(btn_paste)
        acoes = QHBoxLayout()
        acoes.addWidget(self.btn_preview)
        acoes.addWidget(self.btn_apply)
        acoes.addWidget(self.btn_undo)
        acoes.addWidget(self.btn_copy_err)
        acoes.addWidget(self.btn_bat)
        self.chk_sandbox = QCheckBox("Aplicar em sandbox (cópia)")
        self.chk_sandbox.setToolTip(
            "Aplica numa CÓPIA do projeto (pasta irmã *_sandbox_<ts>); o original não é tocado."
        )
        acoes.addWidget(self.chk_sandbox)
        acoes.addStretch(1)

        raiz = QVBoxLayout()
        raiz.addLayout(topo1)
        raiz.addLayout(topo2)
        raiz.addLayout(acoes)
        raiz.addWidget(splitter, 1)
        central = QWidget()
        central.setLayout(raiz)
        self.setCentralWidget(central)
        self.statusBar().showMessage("Escolha a raiz e a instrução, depois pré-visualize.")
        self._restore_last_paths()

        # Sobrepõe com argumentos de lançamento (WI-2) — depois de _restore_last_paths.
        if root is not None:
            self.root_edit.setText(root)
        if instruction is not None:
            self._pasted_text = None
            self.instr_edit.setText(instruction)
        elif instruction_dir is not None:
            self._apply_instruction_dir(instruction_dir)

    # ── Seleção de caminhos ────────────────────────────────────────────────
    def _pick_root(self) -> None:
        pasta = QFileDialog.getExistingDirectory(self, "Pasta raiz do projeto")
        if pasta:
            self.root_edit.setText(pasta)

    def _pick_instruction(self) -> None:
        start = self._instruction_start_dir or ""
        arq, _ = QFileDialog.getOpenFileName(
            self, "Arquivo de instrução", start, "Instruções (*.yaml *.yml *.json)"
        )
        if arq:
            self._pasted_text = None
            self.instr_edit.setText(arq)

    PASTED_MARK = "⟨instrução colada da área de transferência⟩"

    def _paste_instruction(self) -> None:
        """Lê o YAML da área de transferência e o usa como instrução em memória."""
        texto = QApplication.clipboard().text()
        if not texto.strip():
            QMessageBox.warning(self, "Colar instrução", "A área de transferência está vazia.")
            return
        self._pasted_text = texto
        self.instr_edit.setText(self.PASTED_MARK)
        self.statusBar().showMessage(
            f"Instrução colada ({len(texto)} caracteres) — clique Pré-visualizar."
        )

    def _on_instr_text_changed(self, novo: str) -> None:
        # Digitar/abrir outro caminho invalida a instrução colada e a prévia.
        if novo != self.PASTED_MARK:
            self._pasted_text = None
        self._invalidate_preview()

    def _on_root_text_changed(self, text: str) -> None:
        self.btn_bat.setEnabled(bool(text.strip()))

    def _invalidate_preview(self) -> None:
        """Qualquer mudança de entrada exige nova prévia antes de aplicar."""
        self._preview_fingerprint = None
        self.btn_apply.setEnabled(False)

    def _instruction_text(self) -> str | None:
        """Conteúdo bruto da instrução (arquivo ou colada); None + diálogo em erro."""
        if self._pasted_text is not None and self.instr_edit.text() == self.PASTED_MARK:
            return self._pasted_text
        caminho = self.instr_edit.text().strip()
        if not caminho:
            QMessageBox.warning(self, "Instrução", "Informe (ou cole) o arquivo de instrução.")
            return None
        try:
            return Path(caminho).read_text(encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(self, "Instrução", f"Não foi possível ler {caminho}: {exc}")
            return None

    def _fingerprint(self, texto: str) -> str:
        """Impressão digital de (instrução, raiz) para casar prévia ↔ aplicação."""
        raiz = self.root_edit.text().strip()
        return hashlib.sha256((raiz + "\x00" + texto).encode("utf-8")).hexdigest()

    def _restore_last_paths(self) -> None:
        raiz = self._settings.value("last_root", "")
        instr = self._settings.value("last_instruction", "")
        if raiz:
            self.root_edit.setText(str(raiz))
        if instr and instr != self.PASTED_MARK:
            self.instr_edit.setText(str(instr))

    def _save_last_paths(self) -> None:
        self._settings.setValue("last_root", self.root_edit.text().strip())
        if self.instr_edit.text() != self.PASTED_MARK:
            self._settings.setValue("last_instruction", self.instr_edit.text().strip())

    # ── Recentes e fixadas (WI-1) ──────────────────────────────────────────
    def _load_recent_roots(self) -> list[str]:
        val = self._settings.value("recent_roots", [])
        if isinstance(val, str):
            val = [val] if val else []
        return [v for v in val if v]

    def _load_pinned_roots(self) -> list[str]:
        val = self._settings.value("pinned_roots", [])
        if isinstance(val, str):
            val = [val] if val else []
        return [v for v in val if v]

    def _push_recent_root(self, path: str) -> None:
        """Insere no topo, remove duplicata (case-insensitive), corta em 8 itens."""
        if not path:
            return
        recents = self._load_recent_roots()
        path_lower = path.lower()
        recents = [r for r in recents if r.lower() != path_lower]
        recents.insert(0, path)
        self._settings.setValue("recent_roots", recents[:_MAX_RECENTS])

    def _toggle_pin_root(self, path: str) -> None:
        """Adiciona ou remove *path* das fixadas."""
        if not path:
            return
        pinned = self._load_pinned_roots()
        path_lower = path.lower()
        if any(p.lower() == path_lower for p in pinned):
            pinned = [p for p in pinned if p.lower() != path_lower]
        else:
            pinned.append(path)
        self._settings.setValue("pinned_roots", pinned)

    def _show_recents_menu(self) -> None:
        menu = QMenu(self)
        pinned = self._load_pinned_roots()
        recents = self._load_recent_roots()
        if pinned:
            menu.addSection("Fixadas")
            for p in pinned:
                act = menu.addAction(f"📌 {p}")
                act.triggered.connect(lambda _checked=False, path=p: self.root_edit.setText(path))
        if recents:
            menu.addSection("Recentes")
            for r in recents:
                act = menu.addAction(r)
                act.triggered.connect(lambda _checked=False, path=r: self.root_edit.setText(path))
        if not pinned and not recents:
            menu.addAction("(sem histórico)").setEnabled(False)
        menu.exec(self.btn_recentes.mapToGlobal(self.btn_recentes.rect().bottomLeft()))

    def _toggle_current_pin(self) -> None:
        path = self.root_edit.text().strip()
        if path:
            self._toggle_pin_root(path)

    # ── Argumentos de lançamento (WI-2) ───────────────────────────────────
    def _apply_instruction_dir(self, directory: str) -> None:
        """Resolve a pasta de instrução (D3): 1 yaml → pré-preenche; 0 ou 2+ → aponta seletor."""
        from .launcher import resolve_instruction_in_dir

        self._instruction_start_dir = directory
        kind, files = resolve_instruction_in_dir(directory)
        if kind == "one":
            self._pasted_text = None
            self.instr_edit.setText(str(files[0]))
        else:
            n = len(files)
            dica = (
                f"{n} instrucoes nesta pasta -- clique Abrir para escolher"
                if n > 1
                else "Nenhuma instrucao nesta pasta -- clique Abrir para escolher"
            )
            self.statusBar().showMessage(dica)

    # ── Núcleo: carregar + executar ────────────────────────────────────────
    def _load_validated(self, texto: str) -> dict | None:
        """Parseia e valida o texto da instrução; diálogo + coleta de erros em falha."""
        origem = "área de transferência" if self._pasted_text is not None else "arquivo"
        try:
            instruction = load_instruction_from_string(texto, source=origem)
            validate(instruction)
        except (InstructionParseError, InstructionValidationError) as exc:
            self._set_errors([str(exc)])
            QMessageBox.critical(self, "Instrução inválida", str(exc))
            return None
        return instruction

    def _run(self, *, dry: bool) -> ApplyReport | None:
        texto = self._instruction_text()
        if texto is None:
            return None
        instruction = self._load_validated(texto)
        if instruction is None:
            return None
        root = self.root_edit.text().strip() or None
        return apply_instruction(instruction, root_path=root, dry_run=dry, color=False)

    # ── Ações principais (também usadas pelos testes offscreen) ───────────
    def preview(self) -> None:
        """Roda o dry-run e popula a árvore com os indicadores por arquivo/mod."""
        texto = self._instruction_text()
        if texto is None:
            return
        report = self._run(dry=True)
        if report is None:
            return
        self._preview_report = report
        self._populate_tree(report)
        ok = report.ok
        # A prévia "congela" (instrução, raiz): aplicar exige o mesmo par (FIX-007b).
        self._preview_fingerprint = self._fingerprint(texto) if ok else None
        self.btn_apply.setEnabled(ok)
        if ok:
            self._set_errors([])
            self._save_last_paths()
            self._push_recent_root(self.root_edit.text().strip())  # WI-1
        else:
            self._collect_report_errors(report)
        resumo = self._resumo(report)
        prefixo = (
            "Prévia OK — revise os diffs e clique Aplicar."
            if ok
            else "Prévia com FALHAS — corrija a instrução."
        )
        self.statusBar().showMessage(f"{prefixo}  {resumo}")

    def apply_changes(self, *, confirm: bool = True) -> None:
        """Aplica de verdade (com confirmação). ``confirm=False`` é usado nos testes."""
        if confirm:
            resp = QMessageBox.question(
                self,
                "Aplicar mudanças",
                "Aplicar as mudanças da prévia ao disco? (Um backup será criado.)",
            )
            if resp != QMessageBox.StandardButton.Yes:
                return
        texto = self._instruction_text()
        if texto is None:
            return
        # FIX-007b: a instrução/raiz não pode ter mudado desde a prévia revisada.
        if (
            self._preview_fingerprint is None
            or self._fingerprint(texto) != self._preview_fingerprint
        ):
            QMessageBox.warning(
                self,
                "Prévia desatualizada",
                "A instrução ou a raiz mudou desde a última prévia.\n"
                "Rode Pré-visualizar de novo e revise antes de aplicar.",
            )
            self._invalidate_preview()
            return
        root_original = self.root_edit.text().strip() or "."
        root_usada = root_original
        # Sandbox (paridade com o CLI): aplica numa cópia irmã; original intocado.
        if self.chk_sandbox.isChecked():
            instruction = self._load_validated(texto)
            if instruction is None:
                return
            try:
                sandbox = make_sandbox(Path(root_usada), instruction)
            except (SandboxError, OSError) as exc:
                QMessageBox.critical(self, "Sandbox", str(exc))
                return
            root_usada = str(sandbox)
            report = apply_instruction(
                instruction, root_path=root_usada, dry_run=False, color=False
            )
        else:
            report = self._run(dry=False)
        if report is None:
            return
        self._populate_tree(report)
        if report.ok:
            ts = Path(report.backup_dir).name if report.backup_dir else None
            # FIX-007a: o Desfazer usa a raiz capturada AGORA, não o campo futuro.
            self._last_backup = (root_usada, ts) if ts else None
            self.btn_undo.setEnabled(self._last_backup is not None)
            self.btn_apply.setEnabled(False)
            self._set_errors([])
            self._save_last_paths()
            self._push_recent_root(root_original)  # WI-1: push a raiz original (não a sandbox)
            if self.chk_sandbox.isChecked():
                self.statusBar().showMessage(
                    f"Aplicado na SANDBOX: {root_usada}  (original intocado; revise e promova)."
                )
            else:
                extra = f"  Backup: {report.backup_dir}" if report.backup_dir else ""
                self.statusBar().showMessage(f"Aplicado com sucesso.{extra}")
        else:
            self._collect_report_errors(report)
            sufixo = "  (escritas revertidas pelo rollback)" if report.rolled_back else ""
            self.statusBar().showMessage(f"Falha na aplicação.{sufixo}  {self._resumo(report)}")

    def undo_last(self, *, confirm: bool = True) -> None:
        """Desfaz a última aplicação desta sessão via rollback por timestamp."""
        if not self._last_backup:
            return
        root_usada, ts = self._last_backup
        if confirm:
            resp = QMessageBox.question(self, "Desfazer", f"Reverter a aplicação {ts}?")
            if resp != QMessageBox.StandardButton.Yes:
                return
        try:
            itens = rollback_session(root_usada, ts)
        except FileNotFoundError as exc:
            QMessageBox.critical(self, "Desfazer", str(exc))
            return
        self._last_backup = None
        self.btn_undo.setEnabled(False)
        self.statusBar().showMessage(f"Rollback concluído ({len(itens)} arquivo(s) revertido(s)).")

    # ── Loop de autocorreção: erros prontos para a IA geradora ─────────────
    def _set_errors(self, erros: list[str]) -> None:
        self._last_errors = erros
        self.btn_copy_err.setEnabled(bool(erros))

    def _collect_report_errors(self, report: ApplyReport) -> None:
        erros: list[str] = []
        for fr in report.files:
            if fr.error:
                erros.append(f"[{fr.path}] {fr.error}")
            for mr in fr.modifications:
                if mr.error:
                    erros.append(f"[{fr.path} · {mr.mod_id}/{mr.strategy}] {mr.error}")
        self._set_errors(erros)

    def copy_errors_for_ai(self) -> None:
        """Copia um bloco pronto para colar na IA geradora (tabela §6 do guia)."""
        if not self._last_errors:
            return
        linhas = "\n".join(f"- {e}" for e in self._last_errors)
        bloco = (
            "A instrução ASU falhou na validação/aplicação. Erros da ferramenta:\n"
            f"{linhas}\n\n"
            'Consulte a tabela "erro → correção" (§6) e as regras de ouro (§4) do '
            "INSTRUCTION_GUIDE.md e emita a instrução corrigida COMPLETA "
            "(um único bloco yaml)."
        )
        QApplication.clipboard().setText(bloco)
        self.statusBar().showMessage(
            f"{len(self._last_errors)} erro(s) copiados — cole na conversa com a IA geradora."
        )

    # ── Gerador de atalho por projeto (WI-4) ──────────────────────────────
    def _create_launcher_bat(self) -> None:
        """Gera um .bat que reabre a GUI já apontada para o projeto atual."""
        from .launcher import build_launcher_bat

        root_str = self.root_edit.text().strip()
        if not root_str:
            return
        project_root = Path(root_str)
        # asu_home: src/gui/main_window.py → src/gui → src → raiz do ASU
        asu_home = Path(__file__).resolve().parent.parent.parent
        venv_python = asu_home / ".venv" / "Scripts" / "python.exe"

        default_dir = project_root.parent
        default_name = f"abrir-asu-{project_root.name}.bat"
        destino, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar atalho .bat",
            str(default_dir / default_name),
            "Scripts batch (*.bat)",
        )
        if not destino:
            return

        destino_path = Path(destino)
        texto = build_launcher_bat(
            asu_home=asu_home, project_root=project_root, bat_dir=destino_path.parent
        )
        try:
            destino_path.write_text(texto, encoding="ascii", errors="replace")
        except OSError as exc:
            QMessageBox.critical(self, "Criar atalho", f"Nao foi possivel escrever: {exc}")
            return

        if not venv_python.exists():
            aviso = f"ATENCAO: {venv_python} nao encontrado -- confirme o caminho do venv."
            QMessageBox.information(
                self, "Atalho criado (aviso)", f"Atalho salvo em:\n{destino}\n\n{aviso}"
            )
            self.statusBar().showMessage(f"Atalho criado: {destino} -- {aviso}")
        else:
            self.statusBar().showMessage(f"Atalho criado: {destino}")

    # ── Apresentação ───────────────────────────────────────────────────────
    def _populate_tree(self, report: ApplyReport) -> None:
        self.tree.clear()
        for fr in report.files:
            # 🔴 falha; 🟢 mudança aplicável; ⚪ sem alteração.
            icone = "🔴" if fr.status == "failed" else ("⚪" if fr.status == "unchanged" else "🟢")
            item = QTreeWidgetItem([f"{icone} {fr.path}", _STATUS_LABEL.get(fr.status, fr.status)])
            item.setData(0, Qt.ItemDataRole.UserRole, fr)
            if fr.error:
                item.setToolTip(0, fr.error)
            for mr in fr.modifications:
                micone = "✓" if mr.ok else "✗"
                filho = QTreeWidgetItem(
                    [f"   {micone} {mr.mod_id} ({mr.strategy})", "" if mr.ok else "erro"]
                )
                if mr.error:
                    filho.setToolTip(0, mr.error)
                filho.setData(0, Qt.ItemDataRole.UserRole, fr)  # diff é por arquivo
                item.addChild(filho)
            self.tree.addTopLevelItem(item)
        self.tree.expandAll()
        if self.tree.topLevelItemCount():
            self.tree.setCurrentItem(self.tree.topLevelItem(0))

    def _show_selected_diff(self, atual: QTreeWidgetItem | None, _anterior=None) -> None:
        if atual is None:
            self.diff_view.clear()
            return
        fr = atual.data(0, Qt.ItemDataRole.UserRole)
        if fr is None:
            return
        if fr.error and not fr.diff:
            estilo = f"{_CSS_DEL}font-family:Consolas,monospace"
            self.diff_view.setHtml(f'<pre style="{estilo}">{html.escape(fr.error)}</pre>')
        else:
            self.diff_view.setHtml(_diff_to_html(fr.diff or "(sem alterações)"))

    @staticmethod
    def _resumo(report: ApplyReport) -> str:
        c = sum(1 for f in report.files if f.status == "created")
        m = sum(1 for f in report.files if f.status == "modified")
        u = sum(1 for f in report.files if f.status == "unchanged")
        x = sum(1 for f in report.files if f.status == "failed")
        return f"{c} criado(s), {m} modificado(s), {u} inalterado(s), {x} falha(s)."


def run(
    root: str | None = None,
    instruction_dir: str | None = None,
    instruction: str | None = None,
) -> int:
    """Ponto de entrada da GUI (``python -m src.gui``)."""
    app = QApplication.instance() or QApplication([])
    win = MainWindow(root=root, instruction_dir=instruction_dir, instruction=instruction)
    win.show()
    return app.exec()
