# SPEC — F2 · Endurecimento ASCII/encoding do gerador de .bat

> **Tipo:** spec de FEATURE (código), para o Claude Code implementar.
> **Base:** a feature "Acesso rápido" já está em produção (0.7.0): `src/gui/launcher.py` (`build_launcher_bat`) e `src/gui/main_window.py` (`_create_launcher_bat`). Esta spec ENDURECE a geração do `.bat`.
> **Âncoras** são símbolos do código; antes de editar, `grep`-os no arquivo. Se um não existir como descrito, **PARE e reporte**.

## Por quê
Validação de campo do usuário (o `.bat` de teste funcionou) + um aprendizado trazido de outro projeto: **`.bat` deve ser gerado em ASCII puro**. O CMD do Windows usa code page legada (cp850/cp437 por padrão); caractere fora de ASCII ou um BOM no `.bat` pode corromper a execução (ex.: um BOM UTF-8 faz a 1ª linha falhar com `'∩╗┐@echo' não é reconhecido`).

**O conteúdo ESTÁTICO do `.bat` já é ASCII** (a `build_launcher_bat` usa `--`, `ja`, sem acento) e a escrita atual usa `encoding="ascii"`. Mas há **dois problemas reais** a resolver:

1. **`errors="replace"` corrompe caminhos não-ASCII SILENCIOSAMENTE.** Hoje `_create_launcher_bat` faz `write_text(texto, encoding="ascii", errors="replace")`. Se a raiz do projeto (ou o caminho do ASU) contiver acento — comum no Windows pt-BR: `Área de Trabalho`, `Documentos`, ou um projeto `Café`, `São Paulo` — os bytes acentuados viram `?`, gerando um `--root` QUEBRADO. A GUI abriria apontando para uma pasta inexistente, sem aviso. Isso é pior que falhar.
2. **Não há teste travando a invariante "ASCII quando os caminhos são ASCII".** Sem teste, uma futura edição (ex.: alguém repõe o em-dash `—` no comentário) regride sem ninguém notar.

## Decisão de design
- **Caminhos ASCII (caso comum):** `.bat` 100% ASCII, escrito em `ascii`, sem BOM, sem `chcp`. (Comportamento de hoje, menos o `errors="replace"`.)
- **Algum caminho com não-ASCII:** o `.bat` precisa de duas coisas para o CMD resolver o acento: (a) **`chcp 65001 >nul`** logo após `@echo off` (muda o CMD para UTF-8 naquela sessão) e (b) o arquivo gravado em **UTF-8 SEM BOM**. Assim caminhos acentuados funcionam; nunca se corrompe nada em silêncio.
- **Nunca** usar `errors="replace"` (mascara o problema). O conteúdo estático permanece ASCII em qualquer caso.

> Racional do `chcp 65001` + UTF-8-sem-BOM: é a forma reconhecida de um `.bat` lidar com caminhos não-ASCII no CMD moderno. O BOM é proibido porque o CMD o trata como parte do primeiro comando.

## Itens de trabalho

### WI-1 — `build_launcher_bat` ganha o cabeçalho condicional (`src/gui/launcher.py`)
- Após montar `root_arg`/`asu_home`, decidir se o conteúdo dinâmico tem não-ASCII: `precisa_utf8 = not (str(asu_home).isascii() and root_arg.isascii())`.
- Se `precisa_utf8`, inserir a linha `chcp 65001 >nul` **entre** `@echo off` e o comentário `REM ...`. Senão, não inserir.
- O comentário e os demais comandos continuam ASCII (sem em-dash, sem acento) — manter como está (`--`, `ja`).
- A função continua PURA (retorna string). Não escreve em disco.

### WI-2 — `_create_launcher_bat` escolhe o encoding certo (`src/gui/main_window.py`)
- Substituir `destino_path.write_text(texto, encoding="ascii", errors="replace")` por:
  - `enc = "ascii" if texto.isascii() else "utf-8"` (o `"utf-8"` do Python **não** emite BOM — correto; **não** usar `"utf-8-sig"`).
  - `destino_path.write_text(texto, encoding=enc)` (sem `errors=`).
- Manter o resto (o aviso de `venv_python` inexistente, o `QMessageBox` de erro de escrita). Opcional: na mensagem de sucesso, se `enc == "utf-8"`, acrescentar uma nota curta ("(caminho com acento — .bat em UTF-8/chcp)") para o usuário saber por que aquele `.bat` não é ASCII.

### WI-3 — Testes (`tests/test_launcher.py`)
Acrescentar a `build_launcher_bat`:
- **Caminhos ASCII** → o texto retornado satisfaz `.isascii()` e NÃO contém `chcp`. (Trava a invariante do problema 2.)
- **Caminho com acento** (ex.: `project_root = tmp_path / "Café"`, ou um `bat_dir` acentuado) → o texto contém `chcp 65001` e contém o nome acentuado intacto (não vira `?`).
- (Já existem testes de WI-3 da spec anterior — apenas adicione estes; não remova os atuais.)

## Critério de conclusão
- `python -m pytest` verde (com os testes novos); `ruff check .` e `black --check .` limpos.
- Gerar um `.bat` para uma raiz ASCII → arquivo ASCII, sem `chcp`. Para uma raiz acentuada → arquivo UTF-8-sem-BOM com `chcp 65001` e o caminho intacto.

## Ao concluir (raia do Code — via `/wrap`)
- Registrar **DEC-023** em `meta/DECISIONS.md` (append): "`.bat` em ASCII quando os caminhos são ASCII; UTF-8-sem-BOM + `chcp 65001` quando um caminho tem não-ASCII; nunca `errors='replace'` (corromperia caminho acentuado em silêncio)". Contexto: aprendizado de campo + comum no Windows pt-BR.
- Acrescentar entrada no `CHANGELOG.md` (**0.7.1**, Corrigido/Modificado) e atualizar a **Versão Atual** + contagem de testes no `STATUS.md`.
- Commit (mensagem SEM acento), ex.: `fix(gui): gera .bat em ASCII; UTF-8+chcp para caminho com acento`.

## Fora do escopo
Não mexer na lógica de recentes/fixadas, args de lançamento ou resolução pasta→instrução (já entregues e testados). Só o encoding/ASCII do `.bat`.
