# CHANGELOG

> Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/) e versionamento [SemVer](https://semver.org/lang/pt-BR/).
> **Cresce**: entradas novas no topo. Registra só o que foi de fato concluído/entregue.

## [Não lançado]
### Adicionado
- *(nada ainda)*

---

## [0.5.1] — 2026-06-13
### Corrigido
- **FIX-008 (Windows) — backup estourava o MAX_PATH (260 chars):** o espelho de backup recriava o caminho ABSOLUTO inteiro do arquivo dentro de `backups/`, o que no Windows (com `AppData\Local\Temp` + pasta `_sandbox_`) ultrapassava o limite e quebrava com `WinError 3`. Atingia 5 testes e o `self-test` — invisível no Linux/CI (caminhos curtos). O espelho passou a ser **relativo à raiz** (`backups/<ts>/<caminho_relativo>`), o `manifest.txt` grava o espelho explícito, e o formato antigo segue legível. **Era o que derrubava o `python -m pytest` e o `self-test` na sua máquina.**

### Adicionado
- **Guia §8 "Verificação pós-aplicação" (DEC-016):** a IA, na sessão seguinte a uma instrução ASU, confere no disco cada arquivo tocado antes de seguir (em vez de confiar em "deu certo") — prática *outcome-based* validada por pesquisa. Item correspondente no `PROMPT_IA.md`.

### Kit de contexto
- CLAUDE.md alinhado à atualização do Kit (parágrafos: adaptar as Instruções do Projeto a este projeto; criar arquivo de doc ausente na primeira necessidade). Cabeçalhos dos templates atualizados ao formato novo, preservando o conteúdo do projeto.

---

## [0.5.0] — 2026-06-12
### Adicionado
- **`apply --sandbox` (DEC-015)** — o "modo seguro" virou comando: duplica a raiz numa pasta irmã `<nome>_sandbox_<ts>` (ignorando `.git`, `node_modules`, venvs, caches…), aplica NA CÓPIA e imprime o caminho; o projeto original não é tocado. Instruções com `path_mode: absolute` são recusadas nesse modo.
- **GUI: "Colar instrução"** — usa o YAML direto da área de transferência (sem salvar arquivo), via `load_instruction_from_string`.
- **GUI: "Copiar erro para a IA"** — em falha de validação/prévia/aplicação, copia um bloco pronto (erros + referência às §4/§6 do guia) para colar na IA geradora; fecha o loop de autocorreção na interface.
- **GUI: lembra os últimos caminhos** (raiz e instrução) entre sessões, via QSettings.

### Corrigido
- **FIX-007a (GUI):** o Desfazer usa a raiz CAPTURADA no momento da aplicação — trocar a pasta no campo depois de aplicar não quebra mais o rollback.
- **FIX-007b (GUI):** Aplicar exige que a instrução e a raiz sejam EXATAMENTE as da última prévia (impressão digital SHA-256); editar o YAML após revisar bloqueia com aviso e pede nova prévia.

### Qualidade
- Testes: 84 → **90** (4 da GUI nova + 2 do sandbox); ruff/black limpos; versão `0.5.0`.

---

## [0.4.0] — 2026-06-11
### Adicionado
- **GUI (F2 inicial, DEC-013)** — `python -m src.gui`: janela PySide6 fina sobre a mesma pilha do CLI. Pré-visualizar (dry-run) popula árvore de arquivos com indicador 🟢/🔴/⚪ e ✓/✗ por modificação (derivados do `ApplyReport`), diff colorido por arquivo, Aplicar com confirmação + backup, Desfazer última aplicação. Testes offscreen do circuito completo.
- **`python -m src self-test`** — valida a instalação ponta a ponta aplicando a demo embutida em diretório temporário (e revertendo). Nada do disco do usuário é tocado.
- **Dica acionável de whitespace nas âncoras (DEC-014)** — quando `before`/`after` não casa exato mas existe trecho equivalente módulo espaços/indentação, o erro aponta a linha e a forma exata do arquivo para copiar (estilo "did you mean" do Aider; estudo do apply_patch/V4A da OpenAI). Sem fuzzy matching silencioso.
- **Kit de ensino v2** — `INSTRUCTION_GUIDE.md` agora é 100% autocontido: exemplo completo embutido (a v1 apontava para um arquivo fora do contexto dos projetos consumidores — causa provável do desentendimento em campo), seção de formato de resposta + anti-padrões (YAML-only, nunca XML), regra de âncora exata/multilinha e **tabela erro→correção** que fecha o loop de autocorreção da IA geradora. `PROMPT_IA.md` v2 alinhado.
- README: seções "Interface gráfica", "Verificação rápida (self-test)" e "Modo seguro para os primeiros usos" (fluxo com duplicata e com Git).

### Qualidade
- Testes: 79 → **84** (dica de whitespace + 3 de GUI offscreen); ruff/black limpos; versão `0.4.0`.

---

## [0.3.0] — 2026-06-10
### Adicionado
- **Kit de ensino para a IA geradora (DEC-012)**: `docs/INSTRUCTION_GUIDE.md` (referência completa: estratégias, cinco regras de ouro, checklist de autovalidação) + `docs/PROMPT_IA.md` (bloco pronto para colar no contexto de outros projetos). Validado por dogfooding: instrução escrita só com o guia aplicou C# com BOM, Python decorado e TSX, com rollback íntegro. README ganhou a seção "Gerando instruções com IA".

### Corrigido
- **FIX-004:** modificações JSON preservam o estilo do arquivo original (indentação 2/4/tab, formato compacto e newline final) — antes tudo era reformatado com `indent=2`, explodindo o diff.
- **FIX-005:** `delete_json_path` agora remove chaves de valor `null` (o jmespath confundia `null` com "ausente"); `append_json_array` distingue os dois casos. Navegação 100% própria — **jmespath removido do núcleo** (requirements: PyYAML, jsonschema, libcst, colorama).
- **FIX-006:** intake endurecido — chave YAML duplicada vira erro de parse com linha/coluna (antes a primeira evaporava); IDs repetidos (`files[].id` / `modifications[].id`) rejeitados na validação; arquivo-alvo **binário** (byte NUL, incl. UTF-16 sem BOM) rejeitado com erro claro antes que um `replace_file` o sobrescrevesse.

### Qualidade
- Testes: 68 → **79**; ruff e black limpos; versão `0.3.0` em `__init__`/`pyproject`.

---

## [0.2.0] — 2026-06-10
### Modificado (comportamento)
- **DEC-011 — unicidade implícita de localizadores:** com `occurrence` ausente, padrões/âncoras que casam mais de uma vez agora são **rejeitados como ambíguos** antes de qualquer escrita (antes aplicavam na 1ª ocorrência silenciosamente). `occurrence` explícito segue sendo escolha posicional. Vale para `insert_after_pattern`, `insert_before_pattern`, `replace_line_pattern` e a âncora `before` do `replace_context_block`; `replace_section` rejeita heading duplicado.

### Corrigido
- **FIX-002 — encodings:** BOM UTF-8 detectado e **preservado** (roundtrip com `utf-8-sig`; arquivos `.cs` do Visual Studio agora localizam padrões na 1ª linha). UTF-16/32 rejeitados com erro claro (antes, cp1252 os "decodificava" como lixo, e `replace_file` converteria o encoding silenciosamente). Detecção de newline movida para o texto decodificado. Erros de leitura/decodificação agora entram no fluxo normal de falha por arquivo (status `failed` + stop/rollback) em vez de derrubar o processo.
- **FIX-003 — `replace_section` fence-aware:** headings dentro de blocos ``` / ~~~ deixam de ser tratados como seções (não são mais encontrados nem encerram a seção real no lugar errado).

### Adicionado
- **Suíte multilinguagem** (`tests/test_multilang.py`): prova do mecanismo universal em **C#, C++, Java, JSX, TSX e GDScript**, incluindo engine completo com C# + BOM e rejeição de UTF-16.
- **Suíte de bordas** (`tests/test_edge_cases.py`): unicidade implícita/explícita, fences, heading duplicado, última seção até EOF, chaves aninhadas no context block (semântica fixada), decorador removido se não repetido (semântica fixada), cp1252 roundtrip, CRLF preservado, arquivo sem newline final.
- Total de testes: 43 → **68**.

### Qualidade
- `ruff check` limpo (auto-fix + correções manuais de B904) e `black` aplicado em todo o código.
- Versão unificada em `0.2.0` (`src/__init__.py` e `pyproject.toml` estavam dessincronizados em 0.0.1).

---

## [0.1.1] — 2026-06-10
### Adicionado
- **Demo executável** (`examples/demo_project/` + `examples/demo.yaml`) — projeto-alvo real com arquivos `.py`, `.md`, `.json` e `.js` e uma instrução que aplica de verdade (cobre os 4 tipos + `create_file`). Permite testar `validate → apply --dry-run → apply → rollback` de ponta a ponta sem ter um projeto próprio.
- README com seção **Quickstart** (comandos copiáveis usando a demo) e seção "Uso no seu projeto" com placeholder explícito.

### Corrigido
- **FIX-001:** `replace_context_block` agora rejeita com erro claro quando o `new_content` inclui as próprias âncoras `before`/`after` (antes, isso duplicava as âncoras silenciosamente, corrompendo o arquivo sem sinalizar). Acrescentado teste de regressão.
- `examples/exemplo_instrucao.yaml` — corrigido o bloco JavaScript que continha as âncoras no `new_content` (agora só o miolo entre elas).

### Documentação
- README deixou de usar o nome genérico `instrucao.yaml` nos comandos (causava confusão de "arquivo não encontrado" no primeiro uso).

---

## [0.1.0] — 2026-06-08
### Adicionado
- **Motor de execução (F1) funcional via CLI** — fluxo completo instrução → validação → localização → aplicação → backup → diff → resultado, com rollback.
- `instruction_v1.schema.json` — JSON Schema Draft 7 completo (contrato do arquivo de instrução), com `$comment` idiomático.
- `instruction_parser.py` — carrega YAML/JSON com fallback de encoding utf-8→cp1252.
- `instruction_validator.py` — valida contra o schema e o `format_version`, acumulando todos os erros com o caminho do campo.
- Treze estratégias de modificação (padrão Strategy): `replace_function`, `replace_method`, `replace_class` (Python/libcst); `insert_after_pattern`, `insert_before_pattern`, `replace_line_pattern`, `replace_context_block` (texto universal); `replace_section` (markdown); `set_json_path`, `append_json_array`, `delete_json_path` (JSON/jmespath); `replace_file`, `create_file` (arquivo inteiro).
- `file_locator.py` — resolve caminhos relative/absolute com guarda de contenção (caminho relativo não escapa da raiz).
- `backup_manager.py` — backup timestampado espelhando a estrutura de pastas; rollback atômico e rollback por timestamp.
- `diff_renderer.py` — unified diff colorido (colorama, com degradação graciosa).
- `patch_engine.py` — orquestração com transação e rollback automático em falha, dry-run e precedência de configuração (padrões < settings < flags).
- CLI (`python -m src`): subcomandos `validate`, `apply` (prévia + confirmação) e `rollback`.
- Arquivos de projeto: `pyproject.toml`, `requirements.txt` (núcleo sem Qt), `requirements-gui.txt`, `requirements-dev.txt`, `.gitignore`, `README.md`, `examples/exemplo_instrucao.yaml`.
- 42 testes (parser/validator, estratégias, integração do engine), todos verdes.

### Decisões
- DEC-008 (estratégias `create_file`/`replace_file`), DEC-009 (`location.type` removido; papéis Python explícitos; interface da estratégia com `apply()` único), DEC-010 (independência de linguagem via contexto; `requirements` dividido).

---

## [0.0.1] — 2026-06-03
### Adicionado
- Concepção do projeto: visão, escopo e objetivos definidos.
- Stack tecnológica selecionada e justificada (Python 3.11+, PySide6, libcst, PyYAML, jsonschema, jmespath, PyInstaller).
- Arquitetura modular definida: `core/` (parser, validator, locator, engine, backup, diff), `strategies/` (python, text, json), `gui/`, `schemas/`.
- Onze estratégias de modificação especificadas para 4 tipos de arquivo (Python, Markdown, JSON, texto genérico).
- Schema conceitual do arquivo de instrução YAML v1.0 com hierarquia: cabeçalho, settings, files[], modifications[].
- Sete decisões arquiteturais documentadas em DECISIONS.md (DEC-001 a DEC-007).
- Roadmap em 5 fases documentado (F0 concluída, F1–F4 futuras).
- Documentação completa de contexto gerada: CONTEXT.md, STATUS.md, DECISIONS.md, ROADMAP.md, GLOSSARY.md, HISTORICO.md, IDEAS.md, LOG-TEMPLATE.md, logs/2026-06-03.md.
