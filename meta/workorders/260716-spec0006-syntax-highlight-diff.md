# spec0006 — GUI: syntax-highlight opcional no diff (Pygments, degradação graciosa)

> **Tipo:** feat (GUI). **Autoria:** chat. **Execução:** Claude Code.
> **Âncoras são SEMÂNTICAS** — símbolo/atributo ou trecho literal único, **nunca número de linha**. Localize cada âncora EXATAMENTE; **se não achar uma, PARE e reporte**. Não toque em nada fora das edições nomeadas. Rode `git diff` antes de commitar.
> **Versão-alvo:** 0.8.6 (feat de camada GUI — inclui o `/wrap` no fim desta spec).

---

## Contexto e objetivo

O diff da GUI (`_diff_to_html` em `src/gui/main_window.py`) hoje colore **só por linha** — verde (adição), vermelho (remoção), azul (cabeçalho) — sem realce de **sintaxe** por token. É item pendente da F2 (STATUS "itens estruturais restantes") e do ROADMAP (linha `[~]` do diff: "syntax highlight por linguagem ainda pendente").

**Desenho (DEC-030):**
- **Pygments** como dependência **opcional de GUI**. O lexer é escolhido pelo NOME do arquivo (`fr.path`). Sem Pygments, sem `path`, ou extensão desconhecida → cai no **realce só-de-linha antigo** — mesma degradação graciosa do colorama no core.
- Quando o realce está ativo, adição/remoção passam a marcar pelo **FUNDO** (verde/vermelho claros) e o **foreground** carrega as cores de sintaxe. Assim leem-se as duas dimensões ao mesmo tempo: *o que mudou* (fundo) + *estrutura do código* (cores dos tokens). Cabeçalhos seguem em azul-negrito, sem realce.
- Realce é **por linha** (o diff já vem quebrado): construções multi-linha (string/comentário atravessando linhas) não são detectadas — compromisso aceitável num visualizador de diff.
- **Núcleo/CLI intactos**: mudança só na camada GUI. `_diff_to_html` ganha um parâmetro `path` **opcional** (default `None` = comportamento e teste antigos preservados byte a byte).

Arquivos tocados: `src/gui/main_window.py`, `requirements-gui.txt`, `tests/test_gui_smoke.py`. Mais o `/wrap` (bump + meta) no fim.

---

## Edição 1 — CSS: acrescentar os fundos suaves do modo com realce

**Âncora (bloco literal único):**

```python
# Cores do diff (tema claro padrão do Qt). Mantidas suaves para legibilidade.
_CSS_ADD = "color:#0a7a2f;"
_CSS_DEL = "color:#b00020;"
_CSS_HDR = "color:#005a9e;font-weight:bold;"
```

**Substituir por:**

```python
# Cores do diff (tema claro padrão do Qt). Mantidas suaves para legibilidade.
_CSS_ADD = "color:#0a7a2f;"
_CSS_DEL = "color:#b00020;"
_CSS_HDR = "color:#005a9e;font-weight:bold;"
# Fundos suaves usados SÓ no modo com syntax-highlight: como o realce vem do
# foreground (cores por token), adição/remoção passam a marcar pelo FUNDO.
_CSS_ADD_BG = "background-color:#e6ffed;"
_CSS_DEL_BG = "background-color:#ffeef0;"
```

## Edição 2 — substituir `_diff_to_html` pelos helpers de lexer + a nova versão

**Âncora (a função `_diff_to_html` INTEIRA, bloco literal único):**

```python
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
```

**Substituir por:**

```python
def _lexer_for(path: str | None):
    """Devolve um lexer Pygments para o arquivo, ou ``None``.

    ``None`` significa "sem realce" (Pygments ausente ou extensão que o Pygments
    não mapeia) — o chamador cai no realce só-de-linha. O lexer é escolhido pelo
    NOME do arquivo, então é estável e resolvido UMA vez por diff.
    """
    if not path:
        return None
    try:
        from pygments.lexers import guess_lexer_for_filename
        from pygments.util import ClassNotFound
    except ImportError:  # pragma: no cover - sem Pygments
        return None
    try:
        return guess_lexer_for_filename(path, "")
    except ClassNotFound:
        return None


def _highlight_line(code: str, lexer) -> str:
    """Realça UMA linha de código como HTML inline. ``lexer`` já resolvido."""
    from pygments import highlight
    from pygments.formatters import HtmlFormatter

    # nowrap=True: sem <div>/<pre> ao redor; noclasses=True: estilos inline (o
    # QTextEdit não carrega CSS externo). rstrip: Pygments encerra com "\n".
    return highlight(code, lexer, HtmlFormatter(nowrap=True, noclasses=True)).rstrip("\n")


def _diff_to_html(diff: str, path: str | None = None) -> str:
    """Converte um unified diff (sem ANSI) em HTML colorido linha a linha.

    Com ``path`` E Pygments instalado, cada linha de código ganha **realce de
    sintaxe** (foreground) e adição/remoção marcam pelo FUNDO. Sem ``path`` ou
    sem Pygments, mantém-se o realce só-de-linha (foreground) — comportamento e
    testes originais preservados.
    """
    lexer = _lexer_for(path)
    linhas = []
    for ln in diff.split("\n"):
        esc = html.escape(ln) or "&nbsp;"
        if ln.startswith(("+++", "---", "@@")):
            linhas.append(f'<span style="{_CSS_HDR}">{esc}</span>')
            continue
        # Modo com realce: separa o marcador (+/-/espaço) do código e realça o
        # código; o marcador é reanexado e a linha inteira recebe o FUNDO.
        if lexer is not None and ln[:1] in ("+", "-", " "):
            corpo_ln = html.escape(ln[:1]) + _highlight_line(ln[1:], lexer)
            if ln[0] == "+":
                linhas.append(f'<span style="{_CSS_ADD_BG}">{corpo_ln}</span>')
            elif ln[0] == "-":
                linhas.append(f'<span style="{_CSS_DEL_BG}">{corpo_ln}</span>')
            else:
                linhas.append(corpo_ln)
            continue
        # Fallback (sem realce): coloração de linha original.
        if ln.startswith("+"):
            linhas.append(f'<span style="{_CSS_ADD}">{esc}</span>')
        elif ln.startswith("-"):
            linhas.append(f'<span style="{_CSS_DEL}">{esc}</span>')
        else:
            linhas.append(esc)
    corpo = "<br>".join(linhas)
    return f'<pre style="font-family:Consolas,monospace;font-size:10pt">{corpo}</pre>'
```

> Nota de regressão: com `path=None` o `lexer` é `None`, então TODA linha cai no
> bloco de fallback → a saída é idêntica à atual (o teste `test_diff_to_html_colors_lines`,
> que chama `_diff_to_html(diff)` e conta 5 `<span>`, continua passando).

## Edição 3 — passar `fr.path` no ponto de exibição do diff

**Âncora (linha única em `_show_selected_diff`):**

```python
            self.diff_view.setHtml(_diff_to_html(fr.diff or "(sem alterações)"))
```

**Substituir por:**

```python
            self.diff_view.setHtml(_diff_to_html(fr.diff or "(sem alterações)", fr.path))
```

## Edição 4 — atualizar a nota do docstring do módulo

**Âncora (bloco literal único no docstring de topo):**

```python
- O diff é renderizado pelo ``diff_renderer`` sem ANSI e colorido aqui via
  HTML (uma linha por ``<span>``), evitando dependência de highlighter.
```

**Substituir por:**

```python
- O diff é renderizado pelo ``diff_renderer`` sem ANSI e colorido aqui via
  HTML (uma linha por ``<span>``). O realce de SINTAXE é opcional: com Pygments
  instalado (dependência de GUI), cada linha ganha cores por token e adição/
  remoção passam a marcar pelo fundo; sem Pygments, cai no realce só-de-linha.
```

---

## Edição 5 — `requirements-gui.txt`: acrescentar Pygments

**Âncora (bloco literal único):**

```
-r requirements.txt
PySide6>=6.6
```

**Substituir por:**

```
-r requirements.txt
PySide6>=6.6
# Realce de sintaxe no diff da GUI (opcional — a GUI degrada sem ele).
Pygments>=2.17
```

---

## Edição 6 — testes (`tests/test_gui_smoke.py`)

### 6a — expor `_CSS_ADD` no import

**Âncora (linha única):**

```python
from src.gui.main_window import MainWindow, _diff_to_html, _report_to_text  # noqa: E402
```

**Substituir por:**

```python
from src.gui.main_window import (  # noqa: E402
    MainWindow,
    _CSS_ADD,
    _diff_to_html,
    _report_to_text,
)
```

### 6b — acrescentar os testes novos após `test_diff_to_html_colors_lines`

**Âncora (a função existente inteira, bloco literal único):**

```python
def test_diff_to_html_colors_lines():
    htm = _diff_to_html("--- a/x\n+++ b/x\n@@ -1 +1 @@\n-velho\n+novo\n ctx")
    assert htm.count("<span") == 5  # 3 cabeçalhos + 1 del + 1 add
    assert "novo" in htm and "velho" in htm
```

**Substituir por:**

```python
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
```

---

## /wrap 0.8.6 (executar após validar — Parte final)

### W1 — bump da versão

**Arquivo:** `src/__init__.py` — âncora `__version__ = "0.8.5"` → `__version__ = "0.8.6"`.

### W2 — `meta/CHANGELOG.md`

Inserir uma nova seção IMEDIATAMENTE ACIMA de `## [0.8.5] — 2026-07-15` (e o `---` correspondente):

```markdown
## [0.8.6] — 2026-07-16
### Adicionado
- **Syntax-highlight opcional no diff da GUI (spec0006, DEC-030):** com Pygments instalado (dependência de GUI), o diff da prévia/resultado ganha realce de sintaxe por token; o lexer é escolhido pelo nome do arquivo. Nesse modo, adição/remoção passam a marcar pelo FUNDO (verde/vermelho claros) e o foreground carrega as cores de sintaxe. Sem Pygments, sem caminho, ou extensão desconhecida → cai no realce só-de-linha antigo (degradação graciosa, como o colorama no core). Núcleo/CLI intactos. `_diff_to_html` ganhou parâmetro `path` opcional (default `None` = comportamento antigo).
### Testes / Qualidade
- 3 testes novos em `test_gui_smoke.py` (regressão sem `path`, fallback de extensão desconhecida, realce de Python sob `importorskip`); `ruff`/`black`/`self-test` limpos. `__version__` 0.8.5 → **0.8.6**.
```

### W3 — `meta/DECISIONS.md`

Acrescentar após a DEC-029 (é a última):

```markdown
## DEC-030 — Syntax-highlight opcional no diff da GUI via Pygments (degradação graciosa)
**Contexto.** O diff da GUI coloria só por linha (+/-/cabeçalho), sem realce de sintaxe — pendência da F2/ROADMAP. Realce multilíngue à mão seria frágil (o ASU cobre Python, JSON, Markdown e texto universal p/ C#/C++/Java/JSX/TSX/GDScript).
**Decisão.** Adotar **Pygments** como dependência **opcional de GUI** (`requirements-gui.txt`), com o lexer escolhido pelo NOME do arquivo (`fr.path`). Sem Pygments, sem `path`, ou extensão desconhecida → realce só-de-linha antigo (mesmo padrão do colorama no core). Com realce ativo, adição/remoção marcam pelo **fundo** (verde/vermelho claros) e o **foreground** carrega as cores de sintaxe — leem-se as duas dimensões (o que mudou + estrutura do código). O realce é **por linha** (o diff já vem quebrado): construções multilinha não são detectadas — compromisso aceitável num visualizador de diff.
**Consequências.** Núcleo/CLI intactos (mudança só na camada GUI). `_diff_to_html` ganhou `path` opcional (default `None` = comportamento e testes antigos preservados). **Risco a validar VISUALMENTE no Windows:** `background-color` inline em `<span>` dentro do `QTextEdit` pode não renderizar em toda versão do Qt — se não aparecer, trocar o container da linha por `<div style="...">` (sem `<br>` para essas linhas). Não supersede nada; estende a linha de diff da F2.
```

### W4 — `meta/STATUS.md` (rolante — o Code mantém)

- **Versão Atual** → `[0.8.6] — 2026-07-16 — Syntax-highlight opcional no diff da GUI (Pygments, DEC-030).` e empurrar `[0.8.5]` para a lista "Anterior".
- No item "F2 (GUI) — itens estruturais restantes", **remover** `highlight de sintaxe no diff; ` da enumeração (agora entregue).
- Corrigir a contagem de testes do bloco "✅ Funcionando" (o texto ainda diz **133 testes**; o real da suíte é 147, e passa a **150** com os 3 testes desta spec — deixe o número que o `pytest` reportar).

### W5 — `meta/ROADMAP.md`

**Âncora (linha única):**

```markdown
- [~] Diff colorido por arquivo integrado na main_window (HTML, verde/vermelho); syntax highlight por linguagem ainda pendente.
```

**Substituir por:**

```markdown
- [x] Diff colorido por arquivo na main_window (HTML). Syntax-highlight por linguagem via Pygments opcional, com degradação graciosa (0.8.6, DEC-030).
```

---

## Validação (antes de commitar)

- `python -m pytest` (suíte inteira verde; 3 testes novos).
- `ruff check .` e `black --check .` limpos.
- `python -m src self-test` OK (não toca no disco).
- `git diff` conferindo a forma esperada: só `src/gui/main_window.py`, `requirements-gui.txt`, `tests/test_gui_smoke.py`, `src/__init__.py` e os 4 meta-docs (CHANGELOG/DECISIONS/STATUS/ROADMAP).
- **Validação VISUAL (Windows, fora do CI):** abrir a GUI, carregar uma prévia de um `.py` e confirmar (1) cores de sintaxe nos tokens e (2) o fundo verde/vermelho nas linhas +/-. Se o fundo não aparecer, aplicar o fallback `<div>` da DEC-030.

## Commit + push (Claude Code)

Dois commits, mensagens em PT-BR imperativo curto e SEM acento; CMD Windows numa linha; depois o push:

```
git add src\gui\main_window.py requirements-gui.txt tests\test_gui_smoke.py src\__init__.py && git commit -m "feat: syntax-highlight opcional no diff da GUI (Pygments)" -m "Lexer pelo nome do arquivo; adicao/remocao marcam pelo fundo; degradacao graciosa sem Pygments. 3 testes novos. Bump 0.8.6."
```

```
git add meta\CHANGELOG.md meta\DECISIONS.md meta\STATUS.md meta\ROADMAP.md && git commit -m "docs: registra syntax-highlight (DEC-030, wrap 0.8.6)"
```

```
git log origin/main..HEAD --oneline && git push
```
