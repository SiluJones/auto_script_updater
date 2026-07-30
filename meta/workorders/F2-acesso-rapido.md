# SPEC — F2 · Acesso rápido a projetos (GUI)

> **Tipo:** spec de FEATURE (código), para o Claude Code implementar.
> **Autoria:** chat (planejamento). **Execução:** Claude Code (`src/`, `tests/`), rodando `python -m pytest` e `python -m src.gui` ao final.
> **Âncoras** referem-se a SÍMBOLOS do código (função/método/atributo), nunca a número de linha. Antes de editar, `grep` o símbolo no arquivo indicado. Se um símbolo não existir como descrito, **PARE e reporte** — pode ser que o código tenha mudado desde esta spec.
> **Regra de ouro do ASU preservada:** nada nesta spec faz a GUI APLICAR sem o usuário rodar o dry-run e revisar. Todo caminho novo só PRÉ-PREENCHE campos; o usuário ainda clica Pré-visualizar e Aplicar.

## Objetivo
Tornar a GUI prática para o uso diário em vários projetos: (1) lembrar pastas-raiz recentes e permitir fixar as favoritas; (2) aceitar argumentos de linha de comando para abrir já apontada para um projeto; (3) um botão que gera um `.bat` "atalho" por projeto, que abre a GUI já com a raiz marcada e a pasta da instrução pronta para escolher.

## Critério de conclusão
- A GUI lembra e oferece pastas-raiz recentes + fixadas; selecionar uma preenche a raiz.
- `python -m src.gui --root <pasta> --instruction-dir <pasta>` abre com a raiz preenchida e a instrução resolvida pela heurística abaixo.
- Um botão "Criar atalho .bat…" gera um `.bat` funcional na pasta escolhida (por padrão, a pasta-PAI da raiz), que reabre a GUI apontada para o projeto.
- `pytest` verde (incluindo testes novos das funções puras); `python -m src.gui` abre sem erro.

---

## Decisões de design (já pesquisadas — implemente conforme)

**D1 — O `.bat` chama o python do venv DIRETAMENTE, sem `activate`.** Pesquisa de boas práticas de launcher no Windows: para um atalho que depende de libs do venv, é mais robusto chamar `.venv\Scripts\python.exe` direto do que `call activate` (evita efeitos colaterais de ativação, funciona de atalho/Task Scheduler). Então o `.bat` gerado NÃO usa `activate`.

**D2 — O `.bat` passa uma PASTA de instrução (`--instruction-dir`), não um arquivo.** Os nomes das instruções mudam (arquivamento/organização), então fixar o caminho de um `.yaml` específico no `.bat` quebraria. A GUI resolve a pasta → arquivo na inicialização (D3). A resposta à dúvida do usuário "esse caminho só aceita o arquivo yaml?": o CAMPO de instrução continua sendo um arquivo (o motor parseia um arquivo/texto), mas o LANÇAMENTO aceita uma pasta e resolve.

**D3 — Resolução pasta→instrução: escanear só o TOPO da pasta (não recursivo).** Instruções arquivadas ficam em SUBpastas da pasta do `.bat`; varrer só o nível de topo as ignora de propósito.
- Exatamente **1** arquivo `*.yaml`/`*.yml` no topo → pré-preenche o campo de instrução com ele (conveniência). O usuário ainda roda o dry-run.
- **0** ou **2+** no topo → NÃO escolhe nenhum; aponta o seletor "Abrir…" para essa pasta e mostra no status uma dica ("N instruções nesta pasta — clique Abrir para escolher"). Ao clicar Abrir, o diálogo já abre nessa pasta.
- Isto resolve o "perigo de ter mais de um yaml": o caso comum (uma instrução ativa na pasta, arquivadas em subpastas) vira 1-clique; o ambíguo fica seguro e explícito.

**D4 — Caminhos do `.bat`: raiz do ASU absoluta; instrução relativa ao próprio `.bat`; raiz do projeto relativa quando for descendente.**
- `ASU_HOME` (onde vivem `.venv` e `src`) é absoluto — a GUI sabe a própria localização por `__file__` (suba de `src/gui/main_window.py` até a pasta do projeto ASU).
- `--instruction-dir` usa `%~dp0` (a pasta onde o `.bat` está) — assim, se o usuário mover a pasta do projeto, a instrução continua resolvendo.
- `--root`: se a raiz do projeto for descendente da pasta do `.bat`, grava relativo a `%~dp0` (ex.: `%~dp0Cinzeiro-Game`); senão, absoluto. Isso torna o `.bat` portátil quando o layout é o do exemplo do usuário (`cinzeiro\` com o `.bat`, raiz em `cinzeiro\Cinzeiro-Game\`).

---

## Itens de trabalho

### WI-1 — Pastas-raiz recentes e fixadas (QSettings)
**Onde:** `src/gui/main_window.py` (classe `MainWindow`). A persistência hoje usa `self._settings = QSettings("auto-script-updater", "gui")` com as chaves `last_root`/`last_instruction` (ver `_restore_last_paths`/`_save_last_paths`).

- Adicionar duas chaves de LISTA no mesmo `QSettings`: `recent_roots` e `pinned_roots`. Use `QSettings` com listas de strings (grave/leia como lista; em caso de valor único legado, normalize para lista).
- Helpers puros o suficiente para teste onde der (mas QSettings é stateful — ver nota de teste):
  - `_load_recent_roots() -> list[str]`, `_load_pinned_roots() -> list[str]`.
  - `_push_recent_root(path)` — insere no topo, remove duplicata (case-insensitive no Windows), corta em **8** itens, persiste. Não inclui pasta vazia.
  - `_toggle_pin_root(path)` — adiciona/remove de `pinned_roots`; fixada nunca expira.
- Chamar `_push_recent_root` quando uma raiz for efetivamente USADA: em `preview()` (após dry-run sem erro de leitura) e em `apply_changes` (após aplicar). Não poluir recents com cada tecla digitada.
- **UI:** ao lado do campo "Raiz:" e do botão "Escolher…", adicionar:
  - um botão "Recentes ▾" que abre um `QMenu` com: seção **Fixadas** (cada uma com um marcador 📌) e seção **Recentes**; clicar numa entrada chama `self.root_edit.setText(...)`. Itens fixados aparecem primeiro.
  - um botão "📌" (toggle) que fixa/desafixa a raiz atual do campo (atualiza o menu).
- O `_restore_last_paths` continua restaurando o último uso; recentes/fixadas são um complemento, não substituem o comportamento atual.

**Aceitação WI-1:** abrir a GUI, escolher duas raízes diferentes e previsualizar em cada → ambas aparecem em "Recentes". Fixar uma → ela aparece na seção Fixadas e persiste após fechar/reabrir. A lista de recentes nunca passa de 8.

### WI-2 — Argumentos de linha de comando da GUI
**Onde:** `src/gui/__main__.py` (hoje: `from .main_window import run` + `raise SystemExit(run())`) e `run()`/`MainWindow.__init__` em `src/gui/main_window.py`.

- Em `src/gui/__main__.py`: parsear `sys.argv` com `argparse`:
  - `--root <pasta>` (opcional)
  - `--instruction-dir <pasta>` (opcional)
  - `--instruction <arquivo>` (opcional; conveniência, caso o usuário queira fixar um arquivo específico)
  - Passar os valores a `run(...)`.
- `run(root: str | None = None, instruction_dir: str | None = None, instruction: str | None = None) -> int` repassa a `MainWindow(...)`.
- `MainWindow.__init__(self, *, root=None, instruction_dir=None, instruction=None)`:
  - Mantém `_restore_last_paths()` (comportamento atual) e, DEPOIS, sobrepõe com os argumentos quando fornecidos: `--root` preenche `root_edit`; `--instruction` preenche `instr_edit`; `--instruction-dir` dispara a resolução D3.
  - Guardar a pasta de instrução para o seletor: novo atributo `self._instruction_start_dir: str | None` usado por `_pick_instruction`.
- Ajustar `_pick_instruction`: passar `self._instruction_start_dir or ""` como diretório inicial do `QFileDialog.getOpenFileName(...)` (3º argumento) em vez de `""`.

**Aceitação WI-2:** `python -m src.gui --root C:\tmp\proj --instruction-dir C:\tmp` abre com a raiz preenchida; se houver 1 yaml em `C:\tmp`, ele aparece no campo de instrução; se houver 2+, o campo fica vazio e "Abrir…" abre em `C:\tmp`. Sem argumentos, comporta-se como hoje.

### WI-3 — Funções puras: gerador de `.bat` e resolução de instrução
**Onde:** criar `src/gui/launcher.py` (módulo SEM dependência de Qt, para ser testável isoladamente). Se o Code julgar um lar melhor (ex.: `src/core/`), pode mover — mas mantenha-as PURAS.

- `resolve_instruction_in_dir(directory: str | Path) -> tuple[str, list[Path]]`:
  - Lista `*.yaml` + `*.yml` no TOPO de `directory` (não recursivo), ordenado.
  - Retorna `("one", [arquivo])` se exatamente 1; `("none", [])` se 0; `("many", [...])` se 2+. (A GUI decide o que fazer — D3.)
- `build_launcher_bat(*, asu_home: Path, project_root: Path, bat_dir: Path) -> str`:
  - Devolve o TEXTO do `.bat` conforme D1/D4. Use `python.exe` do venv direto; `--instruction-dir "%~dp0"`; `--root` relativo a `%~dp0` se `project_root` for descendente de `bat_dir`, senão absoluto.
  - Modelo do conteúdo (ajuste fino conforme D4):
    ```bat
    @echo off
    REM Atalho gerado pelo ASU — abre a interface ja apontada para este projeto.
    set "ASU_HOME=<asu_home absoluto>"
    pushd "%ASU_HOME%"
    ".venv\Scripts\python.exe" -m src.gui --root "<rel-ou-abs>" --instruction-dir "%~dp0"
    popd
    ```
  - Não escreve em disco aqui (função pura retorna string); a escrita fica na GUI (WI-4).

**Aceitação WI-3 (testes novos em `tests/`):**
- `resolve_instruction_in_dir`: tempdir com 0, 1 e 2 yamls no topo + 1 yaml numa subpasta → retorna `none`/`one`/`many` corretamente e IGNORA a subpasta.
- `build_launcher_bat`: com `project_root` descendente de `bat_dir` → contém `--root "%~dp0<nome>"`; com `project_root` fora → contém o caminho absoluto; sempre contém `python.exe` (e NÃO contém `activate`).

### WI-4 — Botão "Criar atalho .bat…" na GUI
**Onde:** `MainWindow` (`src/gui/main_window.py`), usando `build_launcher_bat` de WI-3.

- Adicionar botão "Criar atalho .bat…" (na linha de ações ou ao lado da raiz). Habilitado só com uma raiz preenchida.
- Ao clicar:
  1. Determinar `asu_home` a partir de `__file__` (subir de `src/gui/main_window.py` até a pasta do projeto ASU — onde existe `.venv`).
  2. `project_root` = `root_edit` atual.
  3. Sugerir como local de salvamento a pasta-PAI da raiz (`Path(project_root).parent`) — o usuário confirma/escolhe via `QFileDialog.getSaveFileName(...)` com nome default sugerido (ex.: `abrir-asu-<nome-da-raiz>.bat`).
  4. Gerar o texto com `build_launcher_bat(asu_home=..., project_root=..., bat_dir=<pasta escolhida>)` e escrever em UTF-8 (mais seguro: ASCII/`cp1252`; o conteúdo é só ASCII, então ok). Mensagem de sucesso no status com o caminho.
  - Tratar erros de escrita com `QMessageBox.critical`, como os outros fluxos.
- Validar que `.venv\Scripts\python.exe` existe sob `asu_home`; se não, avisar (o usuário pode não ter criado o venv) — não impedir a geração, mas sinalizar no status/diálogo.

**Aceitação WI-4:** com uma raiz marcada, clicar "Criar atalho .bat…", salvar na pasta-pai → arquivo `.bat` criado com o conteúdo de WI-3; rodar o `.bat` reabre a GUI apontada para o projeto. (A verificação manual do `.bat` é do usuário no Windows; o teste automatizado cobre `build_launcher_bat`, não a execução do `.bat`.)

---

## Notas de teste
- `tests/test_gui_smoke.py` roda offscreen; mantenha os novos testes de GUI no mesmo padrão (sem exibir janela). Para WI-1, instanciar `MainWindow` e exercitar `_push_recent_root`/`_toggle_pin_root` com um `QSettings` de escopo de teste (ex.: `QSettings` com organização/app de teste, ou `setValue` direto) — limpe ao final para não vazar estado entre testes.
- As funções de WI-3 são puras → testes diretos sem Qt (rápidos). São o coração da cobertura desta spec.
- Rode `python -m pytest`, `ruff check .`, `black --check .` antes de commitar. Sugestão de commits separados por WI (WI-1, WI-2+WI-3 juntos, WI-4) para `git diff` legível.

## Fora do escopo desta spec (continuam na F2/F3, ver ROADMAP)
Barra de progresso, tema claro/escuro, syntax highlight no diff, seleção de timestamps antigos no Desfazer (F2); copiar saída completa, packaging `.exe`, README (F3). Não implementar aqui.
