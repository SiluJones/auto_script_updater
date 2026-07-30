# spec0012 — Atalho "abrir GUI" começa LIMPO: com `--start-dir`, não restaura a última raiz

> **Tipo:** fix (precedência de comportamento) — ajuste da spec0011. **Autoria:** chat. **Execução:** Claude Code.
> **Âncoras são SEMÂNTICAS** — símbolo/atributo ou trecho literal único, **nunca número de linha**. Localize cada âncora EXATAMENTE; **se não achar uma, PARE e reporte**. Não toque em nada fora das edições nomeadas.
> **Versão-alvo:** 0.9.2 (patch — inclui o `/wrap` no fim).

---

## Contexto — o que o print revelou

A spec0011 acertou o mecanismo (`--start-dir` funciona), mas **errou a precedência**. Evidência do usuário (print 2026-07-20): o `.bat` "abrir GUI" foi acionado dentro da pasta `...\Artista`, mas o campo **Raiz já abriu preenchido** com `C:\Users\alexk\Tools\Lunada\lunada` (a última raiz usada, restaurada do `QSettings`), e por isso o "Escolher..." abriu no **Lunada**, não no Artista.

Causa: `_pick_root` usa `raiz atual → semente → padrão`. Como `_restore_last_paths` preenche `last_root` na abertura, a "raiz atual" sempre vence a semente. Para o atalho **clássico** — que é genérico e **copiado para pastas diferentes** — restaurar a última raiz é justamente o que atrapalha: leva o usuário de volta ao projeto anterior em vez da pasta onde ele abriu o atalho.

**Decisão do usuário (acatada):** quando a GUI é aberta pelo atalho "abrir GUI", ela deve **começar limpa** — sem restaurar a última raiz — e deixar o "Escolher..." abrir na pasta do `.bat`. O botão **Recentes ▾** continua ali para quem quiser voltar a um projeto anterior (nada se perde). Rodar `python -m src.gui` na mão (sem `--start-dir`) mantém o comportamento atual de restaurar a última sessão.

**Sinal usado:** a presença de `--start-dir` **é** a marca do atalho "abrir GUI" (só ele passa esse argumento). Então `start_dir` presente ⇒ sessão "limpa". Não é preciso argumento novo.

---

## Edição 1 — `_restore_last_paths` respeita o modo "limpo"

**Âncora (bloco literal único):**

```python
    def _restore_last_paths(self) -> None:
        raiz = self._settings.value("last_root", "")
        instr = self._settings.value("last_instruction", "")
        if raiz:
            self.root_edit.setText(str(raiz))
        if instr and instr != self.PASTED_MARK:
            self.instr_edit.setText(str(instr))
```

**Substituir por:**

```python
    def _restore_last_paths(self) -> None:
        # Atalho "abrir GUI" (--start-dir presente): começa LIMPO — não restaura a
        # última raiz/instrução. O atalho é genérico e copiado para pastas
        # diferentes; restaurar o projeto anterior atrapalhava (spec0012). Quem
        # quer voltar a um projeto usa o botão Recentes ▾. Sem --start-dir
        # (execução manual de `python -m src.gui`), restaura a sessão como antes.
        if self._start_dir:
            return
        raiz = self._settings.value("last_root", "")
        instr = self._settings.value("last_instruction", "")
        if raiz:
            self.root_edit.setText(str(raiz))
        if instr and instr != self.PASTED_MARK:
            self.instr_edit.setText(str(instr))
```

> `_save_last_paths` **não muda**: ao aplicar algo numa raiz escolhida pelo atalho, ela é salva normalmente e vira "recente"/"última" para as próximas aberturas manuais. O modo limpo afeta só a RESTAURAÇÃO na abertura via atalho, não o registro do que o usuário efetivamente usou.

---

## Edição 2 — teste

**Âncora (linha única — o teste da semente criado na spec0011; a edição INSERE depois dele; localize-o pelo nome real reportado, `test_mainwindow_guarda_start_dir`, em `tests/test_gui_smoke.py`):**

```python
def test_mainwindow_guarda_start_dir(app, tmp_path):
```

**Substituir por (mantém o teste existente e acrescenta o novo logo acima da sua assinatura):**

```python
def test_start_dir_nao_restaura_ultima_raiz(app, tmp_path):
    """spec0012: aberta com start_dir (atalho 'abrir GUI'), a janela começa LIMPA.

    Regressão do print onde o atalho aberto em Artista trazia a raiz do Lunada
    (last_root restaurado) e o 'Escolher...' abria no projeto errado.
    """
    from PySide6.QtCore import QSettings

    QSettings("auto-script-updater", "gui").setValue("last_root", str(tmp_path / "anterior"))

    win = MainWindow(start_dir=str(tmp_path))
    assert win.root_edit.text() == ""  # NÃO restaurou a última raiz

    # Sem start_dir, a restauração normal volta a valer.
    win2 = MainWindow()
    assert win2.root_edit.text() == str(tmp_path / "anterior")


def test_mainwindow_guarda_start_dir(app, tmp_path):
```

> **Cuidado com o `QSettings` de escopo de módulo** (isolado pela spec0010, mas compartilhado entre testes): este teste **grava e depende** de `last_root`. Para não interferir nos irmãos nem sofrer interferência, **limpe no fim** — adicione ao final do corpo do teste `QSettings("auto-script-updater", "gui").clear()`, seguindo o mesmo cuidado que a spec0011 registrou em `test_mainwindow_guarda_start_dir`. Se preferir, use `monkeypatch`/fixture de limpeza equivalente já presente no arquivo. **Reporte** a forma escolhida.

---

## /wrap 0.9.2

### W1 — bump
`src/__init__.py`: `__version__ = "0.9.1"` → `__version__ = "0.9.2"`.

### W2 — `meta/CHANGELOG.md` (acima de `## [0.9.1]`)

```markdown
## [0.9.2] — 2026-07-20
### Corrigido
- **Atalho "abrir GUI" começa limpo (spec0012, ajuste da spec0011).** Antes, a GUI restaurava a última raiz do `QSettings` mesmo quando aberta pelo atalho genérico — então clicar o `.bat` numa pasta nova ainda trazia o projeto anterior, e o "Escolher..." abria no lugar errado (relatado com print: atalho em `Artista`, raiz vinda de `Lunada`). Agora, quando a GUI é aberta com `--start-dir` (a marca do atalho "abrir GUI"), ela **não restaura** a última raiz/instrução e o "Escolher..." abre na pasta do próprio `.bat`. O botão **Recentes ▾** segue disponível para retomar um projeto anterior. Execução manual (`python -m src.gui`, sem `--start-dir`) continua restaurando a sessão como antes.
### Testes / Qualidade
- Teste novo: com `start_dir`, a janela não restaura `last_root`; sem ele, restaura. `ruff`/`black`/`self-test` limpos. `__version__` 0.9.1 → **0.9.2**.
```

### W3 — `meta/DECISIONS.md`
**Sem DEC nova** — refina o comportamento definido em DEC-022/023 + spec0011. Não editar. (Se preferir rastrear, uma linha pode ser anexada à DEC-032? **Não** — DEC-032 é backup; este é navegação. Deixe sem DEC.)

### W4 — `meta/STATUS.md`
- **Versão Atual** → `[0.9.2] — 2026-07-20 — Atalho "abrir GUI" começa limpo; não restaura a última raiz (spec0012).`; empurrar `[0.9.1]` para "Anterior".
- Atualizar a contagem de testes (157 → o que o `pytest` reportar).
- No bullet dos atalhos `.bat`, ajustar a redação: o atalho clássico passa `--start-dir "%~dp0."` **e** a GUI, quando recebe `--start-dir`, começa sem restaurar a última sessão.

### W5 — `meta/IDEAS.md`
Sem alteração.

---

## Validação

- `python -m pytest`, `ruff check .`, `black --check .`, `python -m src self-test`.
- **Conferência manual (Windows, é o ponto):** garantir que existe uma "última raiz" salva (abrir a GUI manualmente, escolher um projeto qualquer, aplicar/fechar). Depois **copiar o `.bat` 'abrir GUI' para uma pasta NOVA**, dar duplo clique: o campo Raiz deve abrir **vazio** e o "Escolher..." deve abrir **naquela pasta nova** — não no projeto anterior. Conferir que **Recentes ▾** ainda lista os projetos de antes. Por fim, rodar `python -m src.gui` na mão e confirmar que aí a última raiz **volta** a ser restaurada.
- `git diff`: só `src/gui/main_window.py`, `tests/test_gui_smoke.py`, `src/__init__.py` e os meta-docs (CHANGELOG/STATUS).

## Commit + push

```
git add src\gui\main_window.py tests\test_gui_smoke.py src\__init__.py && git commit -m "fix: atalho abrir GUI comeca limpo, sem restaurar a ultima raiz" -m "Com --start-dir (marca do atalho abrir GUI), a janela nao restaura last_root/last_instruction; o Escolher abre na pasta do bat. Recentes segue disponivel. Execucao manual continua restaurando. Ajuste da spec0011. Bump 0.9.2."
```

```
git add meta\CHANGELOG.md meta\STATUS.md && git commit -m "docs: wrap 0.9.2 (atalho abrir GUI comeca limpo)"
```

```
git log origin/main..HEAD --oneline && git push
```
