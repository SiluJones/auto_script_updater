# SPEC — F2 · Correção do .bat por projeto + atalho "abrir GUI" (clássico)

> **Tipo:** spec de FEATURE/FIX (código), para o Claude Code implementar.
> **Base atual:** `src/gui/launcher.py` (`build_launcher_bat`, `resolve_instruction_in_dir`) e `src/gui/main_window.py` (`_create_launcher_bat`, botão "Criar atalho .bat…"). O endurecimento ASCII já está no código (`precisa_utf8`/`chcp`), mas os docs (CHANGELOG/STATUS) ainda NÃO refletem o 0.7.1 — ver "Ao concluir".
> **Âncoras** são símbolos do código; `grep`-os antes de editar. Se um não bater, PARE e reporte.

## Contexto / bug observado
O usuário gerou um `.bat` por projeto (`abrir-asu-fileview.bat`) e ele **não abre a GUI apontada como esperado**. Causa-raiz encontrada na análise:

**BUG 1 — barra invertida final do `%~dp0` antes da aspa (quebra o argumento).** O `.bat` termina em `--instruction-dir "%~dp0"`. O `%~dp0` SEMPRE termina com `\`, então isso vira `"...\"`. A sequência `\"` é lida pela análise de linha de comando do Windows (regras do C runtime que o Python usa) como **aspa escapada** — o argumento fica corrompido (a pasta passa a conter um `"` literal, ou o parsing desanda). Resultado: `--instruction-dir` chega quebrado, a resolução pasta→instrução falha e o YAML não é pré-preenchido (e, dependendo, a GUI pode nem abrir). O `--root "%~dp0fileview"` NÃO sofre disso (não termina em `\`), por isso a raiz parecia ok e a instrução não.

**BUG 2 — `chcp` não considera a pasta do `.bat`.** Hoje `precisa_utf8` checa só `asu_home` e `root_arg`. Mas `%~dp0` vira o caminho REAL da pasta do `.bat` em tempo de execução; se essa pasta tiver acento (comum no Windows pt-BR), o `.bat` ASCII sem `chcp` lida mal com o caminho. A pasta do `.bat` (`bat_dir`) é conhecida na geração — dá para checá-la.

> Antes de concluir que é só o código: oriente o usuário a confirmar também que (a) o `fileview-instrucao.yaml` está NA MESMA pasta do `.bat` (é o que `--instruction-dir` aponta); (b) existe a subpasta `fileview` ali (é a raiz); (c) existe `.venv\Scripts\python.exe` sob o ASU_HOME. Mas o BUG 1 é real e deve ser corrigido independentemente.

## Itens de trabalho

### WI-1 — Corrigir o `%~dp0` final em `build_launcher_bat` (`src/gui/launcher.py`)
- Trocar `--instruction-dir "%~dp0"` por `--instruction-dir "%~dp0."` (o ponto evita a sequência `\"`; `Path("...\\.")` resolve para a mesma pasta).
- Conferir o caso `root_arg`: quando `project_root == bat_dir`, `rel` é `.` e `root_arg` vira `%~dp0.` (já tem o ponto — ok). Quando `rel` é subpasta, `root_arg` é `%~dp0fileview` (sem `\` final — ok). Nenhuma mudança extra no root.

### WI-2 — `chcp` também quando a pasta do `.bat` tem não-ASCII (`src/gui/launcher.py`)
- Em `build_launcher_bat`, incluir `bat_dir` no teste: `precisa_utf8 = not (str(asu_home).isascii() and root_arg.isascii() and str(bat_dir).isascii())`.
- Racional: `%~dp0` = `bat_dir` em runtime; se `bat_dir` tem acento, precisa de `chcp 65001` + arquivo UTF-8 (o `_create_launcher_bat` já escolhe o encoding por `texto.isascii()`, mas como o texto tem só `%~dp0` literal e não a pasta acentuada, force o caminho UTF-8 quando `precisa_utf8`: ver WI-4).

### WI-3 — Novo atalho "abrir GUI" (clássico, sem args) — função pura (`src/gui/launcher.py`)
Adicionar `build_open_gui_bat(*, asu_home: Path) -> str` — um `.bat` que só **abre a interface**, sem raiz nem instrução, para o usuário pôr em qualquer lugar (Área de Trabalho, uma pasta `launcher`, etc.) e abrir a GUI com 2 cliques.
- **Sem janela de console e destacado:** usar `pythonw.exe` do venv + `start "" /d "<asu_home>"` (o `/d` define o diretório de trabalho para `src` ser importável; absoluto e robusto). Modelo:
  ```bat
  @echo off
  REM Atalho gerado pelo ASU -- abre a interface (sem console).
  start "" /d "<asu_home>" "<asu_home>\.venv\Scripts\pythonw.exe" -m src.gui
  ```
- `precisa_utf8 = not str(asu_home).isascii()` → prefixar `chcp 65001 >nul` se o caminho do ASU tiver acento. Função PURA (retorna string).

### WI-4 — Botão "Criar atalho .bat (abrir GUI)…" na GUI (`src/gui/main_window.py`)
- Adicionar um segundo botão ao lado de "Criar atalho .bat…": **"Criar atalho .bat (abrir GUI)…"** chamando um novo `_create_open_gui_bat`.
- `_create_open_gui_bat`: descobre `asu_home` por `__file__` (igual ao `_create_launcher_bat`); chama `build_open_gui_bat`; `QFileDialog.getSaveFileName` com nome default `abrir-asu-gui.bat` e diretório default sugerido = pasta-pai do `asu_home` (mas o usuário pode salvar onde quiser — este atalho NÃO depende de projeto). Escrita: `enc = "ascii" if texto.isascii() else "utf-8"` (sem `errors=`), igual ao `_create_launcher_bat`.
- **Refinar o `_create_launcher_bat` (do BUG 2):** ao escrever, se o `build_launcher_bat` marcou `chcp` (porque `bat_dir` tem acento) o texto pode AINDA ser `.isascii()` (já que a pasta acentuada não aparece literal, só `%~dp0`). Para garantir, decida o encoding por "tem `chcp` no texto OU não é ascii": `enc = "utf-8" if ("chcp 65001" in texto or not texto.isascii()) else "ascii"`. Aplicar a mesma regra nos dois geradores.

### WI-5 — Testes (`tests/test_launcher.py`)
- `build_launcher_bat`: o texto **não** contém a sequência `%~dp0"` seguida de fim de argumento problemático; especificamente, contém `--instruction-dir "%~dp0."` (com ponto). (Trava o BUG 1.)
- `build_launcher_bat` com `bat_dir` acentuado (ex.: `tmp_path/"Área"`) → contém `chcp 65001`. (Trava o BUG 2.)
- `build_open_gui_bat`: contém `pythonw.exe`, contém `start "" /d`, NÃO contém `--root` nem `--instruction-dir`; com `asu_home` ASCII → `.isascii()` e sem `chcp`; com `asu_home` acentuado → contém `chcp 65001`.

## Critério de conclusão
- `python -m pytest` verde; `ruff`/`black` limpos.
- Gerar um `.bat` por projeto novo → abre a GUI com raiz E instrução pré-preenchidas (testar numa pasta com 1 yaml). Gerar o atalho "abrir GUI" → abre a GUI vazia, sem console.

## Ao concluir (raia do Code — via `/wrap`)
- **Reconciliar o doc-lag do ASCII:** o código já tem o endurecimento ASCII (0.7.1) mas o CHANGELOG está em "[Não lançado]" e o STATUS em 0.7.0. Registrar UMA entrada **CHANGELOG 0.7.1** cobrindo (a) o endurecimento ASCII já implementado E (b) estas correções de `.bat` (BUG 1, BUG 2, atalho "abrir GUI"). Atualizar a Versão Atual e a contagem de testes no STATUS.
- **DEC:** estender a DEC-022 (ou nova DEC-024) com: o `%~dp0` final exige `.` para não escapar a aspa; `%~dp0` = `bat_dir` em runtime, então o `chcp` depende de `bat_dir`; o atalho "abrir GUI" usa `pythonw` + `start /d` (sem console, destacado).
- Commit(s) com mensagem SEM acento.

## Fora do escopo
Backup-dir na GUI e nome do backup por projeto têm spec própria (`meta/specs/F3-backup-na-gui.md`). Não misturar.
