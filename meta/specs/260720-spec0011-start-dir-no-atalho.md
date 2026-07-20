# spec0011 — `.bat` "abrir GUI" semeia a navegação: `--start-dir` na pasta do próprio atalho

> **Tipo:** feat pequeno (GUI + launcher). **Autoria:** chat. **Execução:** Claude Code.
> **Âncoras são SEMÂNTICAS** — símbolo/atributo ou trecho literal único, **nunca número de linha**. Localize cada âncora EXATAMENTE; **se não achar uma, PARE e reporte**. Não toque em nada fora das edições nomeadas.
> **DEPENDÊNCIA:** aplicar **depois da spec0010** (ambas mexem em `main_window.py`, em pontos diferentes; a ordem evita confusão de contexto).
> **Versão-alvo:** 0.9.1 (inclui o `/wrap` no fim).

---

## Contexto e objetivo

O usuário copia o `.bat` "abrir GUI" (clássico, gerado por `build_open_gui_bat`) para dentro de pastas de projetos variados. Hoje esse atalho abre a GUI **sem nenhum contexto**: ao clicar em "Escolher...", o diálogo do Windows abre onde o Qt decidir, e é preciso navegar de novo até a pasta onde o próprio `.bat` está.

**Pedido:** que a navegação **comece na pasta onde o `.bat` foi aberto** — para entrar direto na pasta do projeto em vez de caçar com vários cliques.

**Viabilidade (pesquisada no próprio código):** alta e de baixo risco. Três fatos que sustentam:
1. Já existe **precedente na GUI**: `_pick_instruction` usa `self._instruction_start_dir` como diretório inicial do `QFileDialog`. Fazemos o mesmo para o seletor de raiz.
2. Já existe **precedente no `.bat`**: o gerador por projeto usa `--instruction-dir "%~dp0."`. O sufixo `.` é deliberado — `%~dp0` termina em `\`, e `"%~dp0"` faria a barra escapar a aspa; `"%~dp0."` produz `C:\pasta\.`, válido e seguro (correção já registrada na DEC-023).
3. `QFileDialog.getExistingDirectory` aceita o diretório inicial como 3º argumento — sem dependência nova.

**Desenho — semear, não fixar.** O novo `--start-dir` **não define a raiz**; só diz "comece a navegar por aqui". O atalho clássico continua propositalmente sem `--root` (é genérico, copiado para muitas pastas): o usuário ainda escolhe o projeto, mas com um clique em vez de vários. Sem o argumento, tudo se comporta como hoje.

---

## Edição 1 — `MainWindow` aceita e guarda o `start_dir`

**Âncora (bloco literal único):**

```python
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
```

**Substituir por:**

```python
    def __init__(
        self,
        *,
        root: str | None = None,
        instruction_dir: str | None = None,
        instruction: str | None = None,
        start_dir: str | None = None,
    ) -> None:
        super().__init__()
        self.setWindowTitle("Atualizador Automático de Scripts")
        self.resize(1000, 640)

        # Semente de navegação (spec0011): pasta onde os diálogos de "Escolher..."
        # ABREM quando não há nada melhor. Diferente de `root`, NÃO define a raiz —
        # o atalho .bat clássico é copiado para muitas pastas e continua genérico.
        self._start_dir = start_dir or ""
```

## Edição 2 — o seletor de raiz abre na semente

**Âncora (bloco literal único):**

```python
    def _pick_root(self) -> None:
        pasta = QFileDialog.getExistingDirectory(self, "Pasta raiz do projeto")
        if pasta:
            self.root_edit.setText(pasta)
```

**Substituir por:**

```python
    def _pick_root(self) -> None:
        # Começa na raiz atual, se houver; senão na semente do atalho (--start-dir).
        inicio = self.root_edit.text().strip() or self._start_dir
        pasta = QFileDialog.getExistingDirectory(self, "Pasta raiz do projeto", inicio)
        if pasta:
            self.root_edit.setText(pasta)
```

## Edição 3 — `run()` repassa o argumento

**Âncora (bloco literal único):**

```python
def run(
    root: str | None = None,
    instruction_dir: str | None = None,
    instruction: str | None = None,
) -> int:
    """Ponto de entrada da GUI (``python -m src.gui``)."""
    app = QApplication.instance() or QApplication([])
    win = MainWindow(root=root, instruction_dir=instruction_dir, instruction=instruction)
```

**Substituir por:**

```python
def run(
    root: str | None = None,
    instruction_dir: str | None = None,
    instruction: str | None = None,
    start_dir: str | None = None,
) -> int:
    """Ponto de entrada da GUI (``python -m src.gui``)."""
    app = QApplication.instance() or QApplication([])
    win = MainWindow(
        root=root,
        instruction_dir=instruction_dir,
        instruction=instruction,
        start_dir=start_dir,
    )
```

## Edição 4 — CLI da GUI (`src/gui/__main__.py`)

**Âncora (bloco literal único):**

```python
    parser.add_argument(
        "--instruction",
        metavar="ARQUIVO",
        help="Arquivo de instrucao (.yaml/.json)",
    )
    args = parser.parse_args()
    raise SystemExit(
        run(
            root=args.root,
            instruction_dir=args.instruction_dir,
            instruction=args.instruction,
        )
    )
```

**Substituir por:**

```python
    parser.add_argument(
        "--instruction",
        metavar="ARQUIVO",
        help="Arquivo de instrucao (.yaml/.json)",
    )
    parser.add_argument(
        "--start-dir",
        metavar="PASTA",
        dest="start_dir",
        help="Pasta onde os dialogos de escolha comecam (NAO define a raiz)",
    )
    args = parser.parse_args()
    raise SystemExit(
        run(
            root=args.root,
            instruction_dir=args.instruction_dir,
            instruction=args.instruction,
            start_dir=args.start_dir,
        )
    )
```

## Edição 5 — o `.bat` clássico passa a própria pasta

**Âncora (bloco literal único em `src/gui/launcher.py`):**

```python
def build_open_gui_bat(*, asu_home: Path) -> str:
    """Gera um .bat que abre a GUI sem raiz nem instrucao (atalho classico).

    Usa pythonw.exe (sem janela de console) e start /d para definir o diretorio
    de trabalho de forma robusta, sem depender de projeto especifico.
    """
    asu_home = asu_home.resolve()
    precisa_utf8 = not str(asu_home).isascii()
    chcp_line = "chcp 65001 >nul\n" if precisa_utf8 else ""
    return (
        "@echo off\n"
        + chcp_line
        + "REM Atalho gerado pelo ASU -- abre a interface (sem console).\n"
        + f'start "" /d "{asu_home}" "{asu_home}\\.venv\\Scripts\\pythonw.exe" -m src.gui\n'
    )
```

**Substituir por:**

```python
def build_open_gui_bat(*, asu_home: Path) -> str:
    """Gera um .bat que abre a GUI sem raiz nem instrucao (atalho classico).

    Usa pythonw.exe (sem janela de console) e start /d para definir o diretorio
    de trabalho de forma robusta, sem depender de projeto especifico.

    Passa ``--start-dir "%~dp0."`` (spec0011): os dialogos de "Escolher..." abrem
    na pasta ONDE O .BAT ESTA, que e para onde o usuario copia o atalho. Isso NAO
    define a raiz -- o atalho continua generico. O sufixo "." e obrigatorio:
    ``%~dp0`` termina em barra invertida e ``"%~dp0"`` escaparia a aspa (DEC-023).
    """
    asu_home = asu_home.resolve()
    precisa_utf8 = not str(asu_home).isascii()
    chcp_line = "chcp 65001 >nul\n" if precisa_utf8 else ""
    return (
        "@echo off\n"
        + chcp_line
        + "REM Atalho gerado pelo ASU -- abre a interface (sem console).\n"
        + f'start "" /d "{asu_home}" "{asu_home}\\.venv\\Scripts\\pythonw.exe" '
        + '-m src.gui --start-dir "%~dp0."\n'
    )
```

> **Atenção ao `%` em f-string:** a linha do `--start-dir` foi deixada FORA da f-string de propósito (concatenação simples), porque `%~dp0` não precisa de interpolação. Se optar por juntar tudo numa f-string, `%` não exige escape em f-string Python (só em `.format` de `%`-style), mas a separação acima é mais legível — mantenha.

---

## Edição 6 — testes

**Âncora (linha única em `tests/test_launcher.py` — localizar o primeiro teste que exercita `build_open_gui_bat`; a edição INSERE os novos ANTES dele).** Se o nome divergir, use como âncora a primeira ocorrência literal de `build_open_gui_bat(` dentro de um `def test_` e **reporte** o nome real usado.

**Acrescentar estes testes ao arquivo** (podem ir ao fim, se for mais seguro que inserir no meio):

```python
def test_open_gui_bat_semeia_start_dir():
    """spec0011: o atalho classico manda a pasta do proprio .bat como semente."""
    from pathlib import Path

    from src.gui.launcher import build_open_gui_bat

    conteudo = build_open_gui_bat(asu_home=Path("C:/asu"))
    assert '--start-dir "%~dp0."' in conteudo
    # Nao pode definir a raiz: o atalho classico segue generico.
    assert "--root" not in conteudo


def test_mainwindow_guarda_start_dir(app, tmp_path):
    """A janela aceita `start_dir` sem que isso preencha a raiz."""
    win = MainWindow(start_dir=str(tmp_path))
    assert win._start_dir == str(tmp_path)
    assert win.root_edit.text() == ""
```

> O segundo teste depende da fixture `app` e de `MainWindow` — se `tests/test_launcher.py` não tiver esse import/fixture, coloque-o em `tests/test_gui_smoke.py` (que já tem ambos) e mantenha só o primeiro em `test_launcher.py`. **Reporte onde cada um ficou.**

---

## /wrap 0.9.1

### W1 — bump
`src/__init__.py`: `__version__ = "0.9.0"` → `__version__ = "0.9.1"`.

### W2 — `meta/CHANGELOG.md` (acima de `## [0.9.0]`)

```markdown
## [0.9.1] — 2026-07-20
### Adicionado
- **`--start-dir` na GUI e no atalho "abrir GUI" (spec0011):** o `.bat` clássico passa a mandar `--start-dir "%~dp0."`, então os diálogos de "Escolher..." abrem **na pasta onde o `.bat` está** — que é para onde o usuário copia o atalho, junto dos projetos. O argumento apenas SEMEIA a navegação; **não define a raiz** (o atalho clássico continua genérico). O seletor de raiz usa, nesta ordem: a raiz já preenchida → a semente → o padrão do Qt. Sem o argumento, o comportamento é o de antes. Estende DEC-022/DEC-023 (incluindo o truque `"%~dp0."`, que evita a barra invertida escapando a aspa).
### Testes / Qualidade
- Testes novos: o `.bat` contém `--start-dir "%~dp0."` e não contém `--root`; `MainWindow(start_dir=...)` guarda a semente sem preencher a raiz. `ruff`/`black`/`self-test` limpos. `__version__` 0.9.0 → **0.9.1**.
```

### W3 — `meta/DECISIONS.md`
**Sem DEC nova** — estende DEC-022/023 (design do launcher). Não editar.

### W4 — `meta/STATUS.md`
- **Versão Atual** → `[0.9.1] — 2026-07-20 — Atalho "abrir GUI" semeia a navegação na própria pasta (--start-dir, spec0011).`; empurrar `[0.9.0]` para "Anterior".
- Atualizar a contagem de testes.
- No bullet dos atalhos `.bat`, acrescentar que o atalho clássico agora passa `--start-dir "%~dp0."`.

### W5 — `meta/IDEAS.md`
Marcar a ideia como concluída **se ela existir** com o título capturado nesta sessão; se não existir entrada correspondente, **não criar** — apenas reportar.

---

## Validação

- `python -m pytest`, `ruff check .`, `black --check .`, `python -m src self-test`.
- **Conferência manual (Windows, é o ponto da spec):** gerar o atalho clássico pela GUI, **copiar o `.bat` para dentro de uma pasta de projetos qualquer**, dar duplo clique e então clicar em "Escolher..." na Raiz — o diálogo deve abrir **naquela pasta**, não em Documentos/Downloads. Repetir com o `.bat` em outra pasta para confirmar que a semente acompanha o arquivo.
- Testar também o caminho com **acento/espaço** no nome da pasta (o `chcp` só entra quando o `asu_home` não é ASCII — a semente vem do `%~dp0`, resolvido pelo próprio CMD).
- `git diff`: só `src/gui/main_window.py`, `src/gui/__main__.py`, `src/gui/launcher.py`, os testes, `src/__init__.py` e os meta-docs.

## Commit + push

```
git add src\gui\main_window.py src\gui\__main__.py src\gui\launcher.py tests\test_launcher.py tests\test_gui_smoke.py src\__init__.py && git commit -m "feat: atalho abrir GUI semeia a navegacao na pasta do proprio bat" -m "Novo --start-dir apenas define onde os dialogos de Escolher comecam; nao define a raiz. Atalho classico passa --start-dir com %~dp0. conforme DEC-023. Bump 0.9.1."
```

```
git add meta\CHANGELOG.md meta\STATUS.md && git commit -m "docs: wrap 0.9.1 (start-dir no atalho da GUI)"
```

```
git log origin/main..HEAD --oneline && git push
```
