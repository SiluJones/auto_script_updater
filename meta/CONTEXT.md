# CONTEXT.md — Atualizador Automático de Scripts (ASU)

> Arquivo **estável**. O assistente lê no início de cada sessão para se ambientar.
> Muda pouco: só em alteração estrutural (stack, arquitetura, escopo, nova armadilha descoberta).
> Mantenha enxuto — descreve o que o projeto É, não o que está acontecendo agora (isso é o STATUS).

---

## Visão Geral
Ferramenta desktop em Python que aplica modificações a arquivos de projeto a partir de um **arquivo de instrução YAML gerado por IA**. Elimina o copia-e-cola manual de trechos de código entre sessões: ao fim de uma sessão de trabalho com IA, o assistente gera um YAML de instrução estruturado; o usuário valida, confere o diff colorido (dry-run) e aplica — com backup e rollback. O **consumidor real da ferramenta é a própria IA** que gera as instruções (por isso há um "kit de ensino" para ela em `docs/`). Meta: < 30 s do "IA gerou a instrução" ao "modificações aplicadas", com zero edição manual.

Apesar do nome ("Scripts"), a ferramenta modifica QUALQUER arquivo de texto — `.py`, `.json`, `.md`/`.txt` com estratégias dedicadas, e qualquer outra linguagem (`.cs`, `.cpp`, `.java`, `.js/.jsx/.tsx`, `.gd`, `.css`, `.html`, …) via o mecanismo universal de contexto/regex. Binários e UTF-16/32 são rejeitados.

## Stack Tecnológica
- **Linguagem:** Python 3.11+
- **GUI:** PySide6 6.x (binding oficial do Qt 6 — licença LGPL). Instalada via `requirements-gui.txt`.
- **Parsing de instrução:** PyYAML (com loader estrito anti-duplicata) + jsonschema (Draft 7)
- **Manipulação Python:** libcst 1.x (Concrete Syntax Tree — preserva comentários e espaçamento)
- **Manipulação texto/MD/TXT:** `re` + `difflib` (stdlib)
- **Manipulação JSON:** `json` (stdlib) + navegador de caminho próprio (`a.b[0].c`; distingue `null` de ausência — jmespath foi REMOVIDO no FIX-005)
- **Testes:** pytest + pytest-qt (testes de GUI rodam offscreen via `QT_QPA_PLATFORM=offscreen`)
- **Lint/format:** ruff + black (linha máx. 100)
- **Packaging futuro:** PyInstaller (`.exe` standalone Windows) — PLANEJADO, ainda não implementado (ver ROADMAP).
- **Núcleo enxuto:** apenas 4 dependências fora da stdlib — PyYAML, jsonschema, libcst, colorama. O core não importa Qt (pode virar biblioteca pura — meta de F4).

## Estrutura do Projeto (real — confirmada via manifest)
```
auto_script_updater/
├── src/
│   ├── __init__.py                    # __version__ (atual: "0.8.0")
│   ├── __main__.py                    # CLI: validate | apply | self-test | rollback
│   ├── core/
│   │   ├── instruction_parser.py      # load_instruction / load_instruction_from_string; _StrictLoader (rejeita YAML duplicado)
│   │   ├── instruction_validator.py   # validate() contra JSON Schema + _check_unique_ids
│   │   ├── file_locator.py            # resolve_path (relative/absolute), ensure_ready, guarda de contenção
│   │   ├── patch_engine.py            # ORQUESTRADOR: apply_instruction(); transação + rollback; make_sandbox + SandboxError + SANDBOX_IGNORES
│   │   ├── backup_manager.py          # BackupManager (espelho relativo à raiz — FIX-008), manifest.txt, history.log, rollback_session
│   │   └── diff_renderer.py           # unified diff colorido (colorama) p/ prévia e output
│   ├── strategies/
│   │   ├── __init__.py                # REGISTRY das 13 estratégias + get_strategy()
│   │   ├── base_strategy.py           # BaseStrategy (ABC), StrategyError, get_location()
│   │   ├── python_strategy.py         # libcst: replace_function / replace_method / replace_class
│   │   ├── text_strategy.py           # regex/contexto: insert_after/before_pattern, replace_line_pattern, replace_context_block, replace_section; _whitespace_hint (DEC-014)
│   │   ├── json_strategy.py           # navegador próprio: set/append/delete_json_path; _detect_style (FIX-004); _MISSING (FIX-005)
│   │   └── file_strategy.py           # create_file / replace_file (DEC-008)
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── __main__.py                # `python -m src.gui` (argparse: --root/--instruction-dir/--instruction → run() → MainWindow)
│   │   ├── main_window.py            # GUI (uma janela): MainWindow — preview/aplicar/desfazer/colar/copiar-erro/sandbox; recentes+fixadas; campo Backup; 2 botões de gerar .bat
│   │   └── launcher.py               # PURO (sem Qt): resolve_instruction_in_dir (escaneia topo da pasta) + build_launcher_bat (por projeto) + build_open_gui_bat (clássico)
│   └── schemas/
│       └── instruction_v1.schema.json # JSON Schema — contrato do arquivo de instrução (format_version)
├── tests/
│   ├── test_strategies.py             # unitários por strategy
│   ├── test_edge_cases.py             # bordas: FIX-001..006, dica de whitespace
│   ├── test_multilang.py              # C#, C++, Java, JSX, TSX, GDScript via type:text
│   ├── test_patch_engine.py           # integração: ciclo completo + sandbox + backup_location/history
│   ├── test_instruction_parser.py     # parser + validator (inclui anti-duplicata)
│   └── test_gui_smoke.py              # GUI offscreen: preview→aplicar→desfazer, fingerprint, sandbox
├── docs/
│   ├── INSTRUCTION_GUIDE.md           # kit de ensino da IA (autocontido): formato, 13 estratégias, 6 regras de ouro, tabela erro→correção, §8 verificação
│   └── PROMPT_IA.md                   # bloco para colar nas instruções de projetos consumidores
├── examples/
│   ├── demo.yaml                      # instrução de demo (CRIA src/health.py via create_file — gitignored, FIX-009)
│   ├── demo_project/                  # projeto de demo executável (src/calculator.py, config.json, web/app.js, README.md)
│   └── exemplo_instrucao.yaml
├── pyproject.toml                     # version, pytest/ruff/black config
├── requirements.txt / -gui.txt / -dev.txt   # dependências em camadas (núcleo / GUI / dev)
└── .gitignore                         # ignora backups/, examples/demo_project/src/health.py, *_sandbox_*/

# NÃO versionados no Projeto (vivem no Git): logs/AAAA-MM-DD.md (logs de sessão).
# Docs de contexto (meta/): CEREBRO (ex-CLAUDE), CONTEXT, STATUS, DECISIONS, CHANGELOG, IDEAS, ROADMAP, GLOSSARY, HISTORICO, LOG-TEMPLATE.
# Raiz do repo (modo Claude Code): CLAUDE.md (ponteiro curto p/ o Code) + .claude/ (settings.json + commands/). HUB.md do toolchain vive na pasta-raiz comum aos 3 projetos (não dentro deste repo).
```

## Ambiente e fluxo de trabalho com o Claude (CRÍTICO para a continuidade)
- **Usuário em Windows (CMD).** Todos os comandos de terminal devem ser sintaxe CMD: tudo numa linha, `-m` repetido no commit, caminhos com `\`, e mensagens de commit SEM acentos (o CMD corrompe).
- **Desenvolvimento em container Linux** → o código tem de ser cross-platform. Bugs de Windows (MAX_PATH — FIX-008) podem passar despercebidos no CI Linux; testar caminhos sensíveis com cuidado.
- **Pasta do projeto no Windows:** `C:\Users\alexk\Arquiteturas\ASU\auto_script_updater`.
- **Como o usuário sobe o projeto:** ACHATADO via FlatDrop, que gera um `_MANIFEST.md` mapeando nome-plano → caminho-real (arquivos em `/mnt/project/` sem subpastas, com sufixo `__pasta` em colisões). SEMPRE consultar o manifest antes de deduzir nomes/estrutura; entregar pelo nome/caminho REAL.
- **Onde o código vive no container:** `/home/claude/auto_script_updater/` (árvore íntegra, persiste entre compactações). Entregas vão para `/mnt/user-data/outputs/` (zips versionados `asu_vX.Y.Z.zip`, módulos avulsos em `src_changed/`, docs em `meta/`/`docs/`/`logs/`).
- **Desenvolvimento com Claude Code (desde 2026-06-21, DEC-021):** além do chat de planejamento, o projeto usa o **Claude Code** (CLI/desktop). Duas raias — o **chat** AUTORA docs (arquivo inteiro p/ reescrita; **spec** em `meta/specs/` p/ delta em doc grande); o **Code** implementa `src/`/`tests/`, faz edições **append-only** nos `meta/`, aplica specs, roda validação (`python -m pytest`, `python -m src self-test`, `ruff`, `black`) e commita. O comportamento detalhado está em `meta/CEREBRO.md`; o `CLAUDE.md` da raiz é só o ponteiro curto que o Code lê a cada sessão.
- **Princípios do trabalho (CEREBRO.md):** entregar arquivos COMPLETOS ao fim da sessão; uma fonte de verdade por dado; turnos densos (custam quota); PT-BR conciso; NÃO regenerar docs no meio da sessão; ir à causa raiz; pesquisar para refinar E refutar; mudança mínima que resolve.

## Como o Arquivo de Instrução Funciona (CRÍTICO)
O arquivo de instrução (`.yaml`; JSON também aceito) é gerado pela IA e consumido pela ferramenta. Hierarquia:

```
instrução
├── cabeçalho: format_version ("1.0"), generated_by?, generated_at?, description
├── settings?: backup, dry_run, stop_on_error, encoding   (todos opcionais; têm padrões)
└── files[]
    ├── id (único), path_mode ("relative" | "absolute"), relative_path|absolute_path
    ├── type ("python" | "markdown" | "json" | "text"), language? (informativo)
    └── modifications[]
        ├── id (único no arquivo), description, strategy (fonte ÚNICA de como ler o location)
        ├── location (conforme a strategy; SEM número de linha; ausente em create_file/replace_file)
        └── new_content (substituição) | content (inserção/criação) | value (JSON)
```

**Resolução de caminho:** `relative` → `root_path` (do `--root`/GUI) + `relative_path`; `absolute` → caminho completo já na instrução. Guarda de contenção: no modo relative, o caminho não pode escapar da raiz.

**Localização sem número de linha (DEC-001):** identificadores semânticos (nome de função, heading, caminho JSON) ou janela de contexto — nunca número de linha — para resistir a edições anteriores no mesmo arquivo.

## Estratégias de Modificação (13)
| Estratégia | Alvo | Como localiza | Conteúdo |
|---|---|---|---|
| `replace_function` | Python | nome da função (libcst; `class_name?` se aninhada) | `new_content` |
| `replace_method` | Python | `class_name` (OBRIGATÓRIO) + nome do método | `new_content` |
| `replace_class` | Python | nome da classe (libcst) | `new_content` |
| `insert_after_pattern` | Qualquer | regex de linha + `occurrence?` | `content` |
| `insert_before_pattern` | Qualquer | regex de linha + `occurrence?` | `content` |
| `replace_line_pattern` | Qualquer | regex que casa a linha + `occurrence?` | `new_content` |
| `replace_context_block` | Qualquer | âncoras literais `before`/`after` + `occurrence?` | `new_content` (SÓ O MIOLO — âncoras permanecem) |
| `replace_section` | Markdown | texto do heading (`include_heading?`) | `new_content` |
| `set_json_path` | JSON | caminho pontilhado (`a.b[0].c`; cria intermediários) | `value` |
| `append_json_array` | JSON | caminho pontilhado (deve existir) | `value` |
| `delete_json_path` | JSON | caminho pontilhado (`null` existe e é removível) | — |
| `create_file` | Qualquer | sem localização — cria arquivo novo | `content` |
| `replace_file` | Qualquer | sem localização — substitui o arquivo inteiro | `new_content` |

## Interface (CLI e GUI)
**CLI:** `python -m src {validate|apply|self-test|rollback}`.
- `apply INSTRUCAO`: flags `--root`, `--dry-run`, `--no-backup`, `--sandbox`, `--backup-dir PASTA`, `--no-color`, `--yes/-y`.
- `rollback TIMESTAMP`: flags `--root`, `--backup-dir PASTA`.
- Fluxo recomendado: `validate` → `apply --dry-run` (revisa diff) → `apply` (confirma s/N, cria backup, imprime `Backup: ...\<TIMESTAMP>` e `Histórico: ...\history.log`) → `rollback <TIMESTAMP>`.
- `self-test`: aplica a demo embutida num tempdir, confere e reverte (nada do disco é tocado).

**GUI:** `python -m src.gui` (camada FINA sobre a mesma pilha do CLI — DEC-013). Aceita argumentos de lançamento (`--root`, `--instruction-dir`, `--instruction`) para abrir já apontada a um projeto (DEC-022). Botões: Pré-visualizar (dry-run; árvore 🟢/🔴/⚪ + diff colorido), Aplicar (backup), Desfazer, Colar instrução (clipboard), Copiar erro para a IA; checkbox "Aplicar em sandbox". Campos: Raiz (com menu "Recentes ▾" até 8 + botão 📌 fixar — DEC-022), Instrução, **Backup** (opcional, expõe `--backup-dir` — DEC-024). Dois botões de atalho: "Criar atalho .bat…" (por projeto, pré-preenche raiz+instrução) e "Criar atalho .bat (abrir GUI)…" (clássico, só abre — DEC-023). Estado entre prévia/aplicação/desfazer protegido (FIX-007: fingerprint SHA-256 + raiz capturada).

## Arquitetura — Pontos-chave (ver DECISIONS para o porquê)
- Padrão Strategy (ABC) por tipo de arquivo — DEC-002.
- libcst (não ast) para Python — DEC-003.
- YAML como formato canônico — DEC-004.
- PySide6 como GUI — DEC-005.
- Backup obrigatório + rollback atômico — DEC-006; espelho relativo à raiz — FIX-008; local configurável + history.log — DEC-018; exposto na GUI + aninhado por projeto quando externo — DEC-024; `rollback_from_dir` aceita o caminho da sessão. **Padrão do backup migrando para a pasta-PAI da raiz — DEC-024(c), a implementar.**
- Schema versionado (`format_version`) — DEC-007.
- `create_file`/`replace_file` unificam criar e patchar — DEC-008.
- `strategy` é fonte única do `location`; interface `apply()` única — DEC-009.
- Independência de linguagem via contexto; requirements em camadas — DEC-010.
- Unicidade implícita de localizadores (ambíguo sem `occurrence` = erro) — DEC-011.
- Kit de ensino da IA como artefato do produto — DEC-012.
- GUI fina sobre a pilha; confiança via dry-run — DEC-013.
- Erro acionável, nunca fuzzy silencioso — DEC-014.
- Sandbox como cópia irmã (CLI e GUI; lógica no core) — DEC-015 + DEC-019.
- Verificação pós-aplicação pela IA (outcome-based, lê o disco) — DEC-016.
- Dois canais de feedback: Kit (no IDEAS) × ASU (DEC/FIX/IDEAS) — DEC-017.

## Armadilhas Conhecidas
1. **Número de linha como localizador** — linhas se deslocam após inserções/deleções; usar semântico ou janela de contexto (DEC-001).
2. **ast stdlib para reescrever Python** — `ast.unparse()` remove comentários e normaliza; sempre libcst (DEC-003).
3. **Encoding ambíguo no Windows** — abrir com `encoding="utf-8"`; BOM UTF-8 preservado; cp1252 como fallback; UTF-16/32 rejeitados (FIX-002).
4. **Modificações interdependentes no mesmo arquivo** — o engine reaplica em sequência, cada uma vendo o resultado da anterior; prefira independência.
5. **Pattern/âncora não-único** — bloqueado antes de escrever se casar ≠ 1 vez sem `occurrence` (DEC-011); a falha mais comum de IA é whitespace divergente na âncora — o erro dá dica acionável com a linha exata (DEC-014).
6. **Caminhos Windows no YAML** — `\` é escape; usar `\\` ou `/`.
7. **MAX_PATH no Windows (260 chars)** — caminhos sensíveis (backup/sandbox) devem ser curtos/relativos; o backup espelha relativo à raiz (FIX-008). Teste verde no Linux NÃO cobre isso.
8. **Demo que escreve no próprio repo** — `examples/demo.yaml` cria `src/health.py`; se vazar para o repo versionado, quebra os testes (FIX-009); está no `.gitignore` e é limpo nos testes/self-test.

## Contexto de Produto
- **Usuário-alvo:** desenvolvedor que usa IA intensivamente, em Windows, e cansa de copiar manualmente sugestões da IA entre sessões.
- **Dor que resolve:** risco de erro + tempo perdido com copia-e-cola de trechos em vários arquivos.
- **Sucesso:** IA gera instrução → ferramenta aplica → zero edição manual, < 30 s.
- **O que o ASU deliberadamente NÃO é:** editor de código, plugin de IDE, ferramenta de merge/conflito, sistema de controle de versão, nem agente com acesso direto à API da IA (consome instruções pré-geradas).
