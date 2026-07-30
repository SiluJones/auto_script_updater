# spec0004 — GUI: botão "Copiar saída" (relatório completo, sucesso e falha)

> **Tipo:** feat pequeno (GUI). **Autoria:** chat. **Execução:** Claude Code.
> **Âncoras são SEMÂNTICAS** — símbolo/atributo ou trecho literal único, **nunca número de linha**. Localize cada âncora EXATAMENTE; **se não achar uma, PARE e reporte**. Não toque em nada fora das edições nomeadas. Rode `git diff` antes de commitar.
> **Versão-alvo:** 0.8.5 (patch — item único; no `/wrap` do chat).

---

## Contexto e objetivo

Hoje a GUI só tem **"Copiar erro para a IA"** (`copy_errors_for_ai`), que aparece apenas em falha e junta os erros para o loop de autocorreção. Falta um **"Copiar saída"** que despeje o relatório INTEIRO — todos os arquivos, status, avisos (🟡) e diffs — tanto no sucesso quanto na falha, útil para registro, chamado, ou revisão fora da GUI. Item já previsto no ROADMAP (F3, linha "copiar a SAÍDA completa… inclusive em sucesso") e no IDEAS.

Desenho: espelha o botão existente. O relatório é serializado por uma função pura de módulo (`_report_to_text`), testável sem Qt. O botão fica habilitado sempre que houver um relatório (prévia OU aplicação) — o gancho é `_populate_tree`, que é o único ponto por onde passam os dois fluxos, então **uma edição cobre preview e apply**.

Arquivo: `src/gui/main_window.py` (salvo onde indicado).

---

## Edição 1 — importar/estado: guardar o último relatório

**Âncora (linha única no `__init__`):**

```python
        self._last_errors: list[str] = []  # alimenta "Copiar erro para a IA"
```

**Substituir por:**

```python
        self._last_errors: list[str] = []  # alimenta "Copiar erro para a IA"
        self._last_report: ApplyReport | None = None  # alimenta "Copiar saída"
```

> `ApplyReport` já está importado no módulo (linha `from ..core.patch_engine import ApplyReport, ...`).

## Edição 2 — criar o botão

**Âncora (linha única — fim da configuração do botão de erro):**

```python
        self.btn_copy_err.clicked.connect(self.copy_errors_for_ai)
```

**Substituir por:**

```python
        self.btn_copy_err.clicked.connect(self.copy_errors_for_ai)
        self.btn_copy_out = QPushButton("Copiar saída")
        self.btn_copy_out.setToolTip(
            "Copia o relatório COMPLETO da última prévia/aplicação (todos os arquivos, "
            "status, avisos e diffs) para a área de transferência."
        )
        self.btn_copy_out.setEnabled(False)
        self.btn_copy_out.clicked.connect(self.copy_output)
```

## Edição 3 — adicionar ao layout, ao lado do "Copiar erro"

**Âncora (linha única):**

```python
        acoes.addWidget(self.btn_copy_err)
```

**Substituir por:**

```python
        acoes.addWidget(self.btn_copy_err)
        acoes.addWidget(self.btn_copy_out)
```

## Edição 4 — habilitar e guardar o relatório em `_populate_tree` (cobre preview E apply)

**Âncora (início de `_populate_tree` — trecho único):**

```python
    def _populate_tree(self, report: ApplyReport) -> None:
        self.tree.clear()
```

**Substituir por:**

```python
    def _populate_tree(self, report: ApplyReport) -> None:
        # Guarda o último relatório para o botão "Copiar saída" (sucesso E falha).
        self._last_report = report
        self.btn_copy_out.setEnabled(True)
        self.tree.clear()
```

## Edição 5 — handler `copy_output`

**Âncora (fim do método `copy_errors_for_ai` — trecho literal único):**

```python
        self.statusBar().showMessage(
            f"{len(self._last_errors)} erro(s) copiados — cole na conversa com a IA geradora."
        )
```

**Inserir LOGO APÓS esse método (novo método na classe):**

```python

    def copy_output(self) -> None:
        """Copia o relatório COMPLETO (sucesso ou falha) para a área de transferência."""
        if self._last_report is None:
            return
        QApplication.clipboard().setText(_report_to_text(self._last_report))
        n = len(self._last_report.files)
        self.statusBar().showMessage(f"Saída copiada — {n} arquivo(s) no relatório.")
```

## Edição 6 — função pura `_report_to_text` (módulo)

**Âncora (linha única — a definição da classe):**

```python
class MainWindow(QMainWindow):
```

**Inserir IMEDIATAMENTE ANTES dela (função de módulo + duas linhas em branco de separação):**

```python
def _report_to_text(report: ApplyReport) -> str:
    """Serializa um ApplyReport COMPLETO em texto plano para a área de transferência.

    Diferente de ``copy_errors_for_ai`` (que só junta os erros para a IA), aqui o
    relatório inteiro é despejado — todos os arquivos, status, avisos e diffs,
    tanto no sucesso quanto na falha. Marcadores em ASCII (`!`/`~`/`-`) para colar
    limpo em qualquer lugar. Função pura (sem Qt) → testável isoladamente.
    """
    modo = "Prévia (dry-run)" if report.dry_run else "Aplicação"
    situacao = "OK" if report.ok else "FALHOU"
    linhas: list[str] = [f"=== ASU — {modo}: {situacao} ==="]
    if report.rolled_back:
        linhas.append("(escritas revertidas pelo rollback)")
    if report.backup_dir:
        linhas.append(f"Backup: {report.backup_dir}")
    linhas.append("")
    for fr in report.files:
        marca = "!" if fr.status == "failed" else ("~" if fr.has_warnings else "-")
        linhas.append(f"[{marca}] {fr.status.upper()}  {fr.path}  (id: {fr.file_id})")
        if fr.error:
            linhas.append(f"    erro: {fr.error}")
        for mr in fr.modifications:
            estado = "OK" if mr.ok else "FALHOU"
            linhas.append(f"    - {mr.mod_id}/{mr.strategy}: {estado}")
            for aviso in mr.warnings:
                linhas.append(f"        aviso: {aviso}")
            if mr.error:
                linhas.append(f"        erro: {mr.error}")
        if fr.diff:
            linhas.append(fr.diff.rstrip("\n"))
        linhas.append("")
    return "\n".join(linhas).rstrip("\n") + "\n"


```

> O diff sempre chega sem ANSI: a GUI roda o engine com `color=False` (`_run` e o caminho sandbox). Por isso `_report_to_text` não precisa limpar códigos de cor.

## Edição 7 — teste

**Arquivo:** `tests/test_gui_smoke.py`

**Âncora 7a (linha de import — única):**

```python
from src.gui.main_window import MainWindow, _diff_to_html  # noqa: E402
```

**Substituir por:**

```python
from src.gui.main_window import MainWindow, _diff_to_html, _report_to_text  # noqa: E402
```

**Âncora 7b:** acrescente ao FIM do arquivo (não precisa da fixture `app` — a função é pura):

```python
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
                    ModificationResult("m2", "replace_line_pattern", ok=False, error="casou 0 vez(es)")
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
```

---

## Ao concluir (Code)

1. **Validação:** `python -m pytest` (suíte + 1 teste novo; o smoke pula sozinho se não houver PySide6), `ruff check .`, `black --check .`, `python -m src self-test`.
2. **Commit** (bloco único, sem acento). Sugestão:
   `git commit -m "feat(gui): botao Copiar saida com relatorio completo (spec0004)"`
3. **Deixar para o `/wrap` (chat):** versão **0.8.5**; CHANGELOG; STATUS (promover + marcar item do ROADMAP F3 "copiar SAIDA completa"); IDEAS (marcar a ideia "Copiar saída/console na GUI" como concluída). Sem DEC nova (feature pequena, dentro do padrão da GUI).
4. **README:** vale um print do novo botão quando a GUI estabilizar (não gerar imagem agora).
