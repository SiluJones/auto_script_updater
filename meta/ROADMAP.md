# ROADMAP.md — Plano Intencional de Evolução

> Médio e longo prazo vivem AQUI, não no STATUS.
> **Opcional.** Use quando o projeto tem um plano em fases — não para tarefas soltas (isso é o Backlog do STATUS) nem para brainstorm (isso é o IDEAS).
> Cada fase tem um objetivo e um critério de conclusão. Marque o estado: 🟢 concluída · 🟡 em curso/próxima · 🔵 futura · 🚫 descartada.

---

## 🟢 F0 — Concepção e Design *(concluída — 2026-06-03)*
**Objetivo:** Definir o que a ferramenta é, como funciona, qual stack usar e documentar as decisões arquiteturais antes de escrever código.
**Critério de conclusão:** Documentação completa de contexto gerada; arquitetura, schema conceitual e estratégias definidos; nenhuma decisão crítica de design em aberto.
- [x] Stack selecionada e justificada (DEC-003 a DEC-005) com pesquisa de estado da arte.
- [x] Estratégias de modificação especificadas: 11 estratégias para 4 tipos de arquivo.
- [x] Schema conceitual do arquivo de instrução YAML v1.0 com hierarquia completa.
- [x] Sete decisões arquiteturais documentadas em ADR format (DEC-001 a DEC-007).
- [x] Documentação completa: CONTEXT, STATUS, DECISIONS, ROADMAP, GLOSSARY, HISTORICO, IDEAS.

---

## 🟢 F1 — Motor de Execução (Core Engine + CLI) *(concluída — 2026-06-08)*
**Objetivo:** Ferramenta funcional via linha de comando. Sem GUI. Carrega instrução YAML, localiza arquivos, aplica modificações, cria backup, reporta resultado em texto. Toda a lógica crítica implementada e testada antes de construir a GUI.
**Critério de conclusão:** `python -m src instrucao.yaml --root C:\meu_projeto` aplica modificações corretamente para todos os tipos suportados (py, md, json, txt), com backup criado e rollback via flag `--rollback <timestamp>`. ✅ Atingido (42 testes verdes + smoke test ponta a ponta).

- [x] Estrutura de pastas `auto_script_updater/` e `requirements.txt` / `requirements-gui.txt` / `requirements-dev.txt`.
- [x] `src/schemas/instruction_v1.schema.json` — schema JSON Schema completo e validável.
- [x] `src/core/instruction_parser.py` — carrega YAML/JSON, retorna dict (com fallback de encoding).
- [x] `src/core/instruction_validator.py` — valida dict contra schema; erros descritivos com caminho do campo.
- [x] `src/core/file_locator.py` — resolve `root + relative_path` ou `absolute_path`; guarda de contenção; verifica existência.
- [x] `src/core/backup_manager.py` — cria `backups/<YYYYMMDD_HHMMSS>/`; restaura por timestamp.
- [x] `src/strategies/base_strategy.py` — ABC com interface `apply()` (localiza+aplica).
- [x] `src/strategies/text_strategy.py` — `insert_after_pattern`, `insert_before_pattern`, `replace_context_block`, `replace_line_pattern`, `replace_section` (markdown).
- [x] `src/strategies/python_strategy.py` — `replace_function`, `replace_method`, `replace_class` via libcst.
- [x] `src/strategies/json_strategy.py` — `set_json_path`, `append_json_array`, `delete_json_path` via jmespath.
- [x] `src/strategies/file_strategy.py` — `create_file`, `replace_file` (DEC-008).
- [x] `src/core/diff_renderer.py` — unified diff colorido para terminal (colorama).
- [x] `src/core/patch_engine.py` — orquestração, seleção de strategy, transação com rollback automático em falha.
- [x] `src/__main__.py` — CLI com argparse: `validate`, `apply` (prévia+confirmação), `rollback`.
- [x] Testes unitários para cada strategy (`tests/test_strategies.py`).
- [x] Testes de integração do `patch_engine` (ciclo completo: instrução → modificação → backup → rollback).

---

## 🟡 F2 — Interface Gráfica Completa *(em andamento — iniciada 2026-06-11)*
**Objetivo:** GUI completa em PySide6. Usuário abre instrução, vê diff colorido por arquivo, define pasta raiz, aplica com um clique — sem usar terminal.
**Critério de conclusão:** Fluxo completo sem terminal: abrir instrução → validar e exibir confiança → configurar raiz → previsualizar diff → aplicar → ver resultado; rollback disponível via botão.

**✅ Increment "Acesso rápido a projetos" concluído (2026-06-23)** — spec `meta/specs/F2-acesso-rapido.md` implementada pelo Claude Code. 112 testes verdes; ruff/black limpos.
**✅ Polimento do launcher concluído (2026-06-28, 0.8.0)** — specs `F2-bat-ascii` + `F2-bat-fix-e-launcher-classico` (DEC-023). Endurecimento de encoding ASCII/UTF-8 do `.bat`; correção do BUG `--instruction-dir "%~dp0"` → `"%~dp0."` (o `%~dp0` cru quebrava o argumento); `chcp` ciente da pasta do `.bat`; **2º botão "Criar atalho .bat (abrir GUI)…"** (clássico, `pythonw`+`start /d`, sem console). 107 testes.
- [x] Pastas-raiz **recentes** (até 8) + **fixadas** (favoritas) num menu ao lado da raiz — substitui/expande o "histórico dos últimos 5" abaixo.
- [x] **Argumentos de linha de comando** da GUI (`--root`, `--instruction-dir`, `--instruction`) para abrir já apontada a um projeto.
- [x] Botão **"Criar atalho .bat…"** — gera um `.bat` por projeto (na pasta-pai da raiz) que reabre a GUI apontada para o projeto (chama o python do venv DIRETO, sem `activate` — DEC-022). [movido da F3]
- [x] Resolução **pasta→instrução** (escaneia só o topo; 1 yaml = pré-preenche, 2+ = abre o seletor na pasta) — lida com o "perigo de vários yaml" (DEC-022).

**Itens estruturais restantes da F2 (próximo increment):**
- [x] `src/gui/main_window.py` — janela principal, barra de menu, barra de status.
- [x] Árvore de arquivos afetados com ícone de status por arquivo (🟢/🟡/🔴/⚪) e por modificação (✓/⚠/✗) — integrada na main_window; **o 🟡 "aplicado com ressalva" chegou (0.8.3, specs 0001+0002): canal de warnings não-fatais no engine + indicador na GUI.**
- [x] Diff colorido por arquivo na main_window (HTML). Syntax-highlight por linguagem via Pygments opcional, com degradação graciosa (0.8.6, DEC-030).
- [~] Seletor de raiz lembra o ÚLTIMO uso (QSettings); recentes+fixadas chegam no increment ativo acima.
- [ ] Barra de progresso durante aplicação de instruções com muitos arquivos.
- [x] Modo dry-run na GUI — o botão "Pré-visualizar" É um dry-run (sempre antes de aplicar; desenho mais seguro que checkbox).
- [x] Botão "Copiar erro para a IA" — copia erros + ref. ao guia para colar na IA geradora (loop de autocorreção).
- [x] Checkbox "Aplicar em sandbox (cópia)" — paridade com `--sandbox` do CLI (DEC-019).
- [x] Proteção de estado entre prévia/aplicação/desfazer (fingerprint SHA-256 + raiz capturada — FIX-007).
- [~] Botão "Desfazer última aplicação" entregue (rollback do timestamp da sessão); seleção de timestamps antigos pendente.
- [ ] Indicador de confiança por modificação (🟢 único / 🟡 ambíguo / 🔴 não encontrado).
- [ ] Suporte a tema claro/escuro seguindo a preferência do sistema (Qt color scheme).
- [x] Botão "Colar instrução" — lê YAML da área de transferência (sem salvar arquivo).

---

## 🟡 F3 — Produtividade e Polimento *(parcialmente entregue — itens avulsos saíram junto da F2)*
**Objetivo:** Recursos que completam o fluxo IA→aplicação sem fricção e tornam a ferramenta "produto acabado".
**Critério de conclusão:** Fluxo completo sem consultar documentação; ferramenta empacotada como `.exe` standalone.

- [x] `self-test` (CLI) — valida a instalação aplicando a demo embutida em tempdir.
- [ ] Painel "Gerador de prompt" — prompt padrão para a IA com botão "Copiar".
- [ ] Histórico de instruções aplicadas (`applied_instructions.json`) com visualizador.
- [ ] Checksum SHA-256 dos arquivos antes/depois registrado no log.
- [ ] Modo comparação acumulada pós-aplicação (diff de todos os arquivos numa tela).
- [→] Gerador de `.bat` por projeto — **movido para a F2** (increment "Acesso rápido", spec `meta/specs/F2-acesso-rapido.md`), por estar acoplado aos args de lançamento e às pastas recentes que o usuário pediu junto.
- [x] Botão/flag para copiar a SAÍDA completa (não só erro), inclusive em sucesso — ver IDEAS. (spec0004, 0.8.5)
- [x] Backup configurável: `--backup-dir` + `history.log` (DEC-018); exposto na GUI + aninhado por projeto quando externo + `rollback_from_dir` (DEC-024 a/b, 0.8.0); **padrão `parent(root)/backups/<ts>` (DEC-024c, 0.8.1)**. PENDENTE: limpeza automática de backups antigos (manter últimos N/X dias).
- [ ] Packaging PyInstaller como `.exe` standalone Windows (UPX para compressão).
- [ ] README de usuário final com capturas de tela e guia de início rápido.

---

## 🔵 F4 — Extensibilidade *(futura, sem data)*
**Objetivo:** Abrir o motor para novos casos de uso além da GUI desktop Windows.

- [ ] Suporte a `.env` como tipo de arquivo (strategy própria: modificação por nome de variável).
- [ ] Suporte a `.sql` (strategy: anchor comment + inserção de blocos SQL).
- [ ] API pública de Strategy (plugin externo via entry_point sem fork do repositório).
- [ ] Migração de schema: ferramenta converte instrução v1.x → v2.0 automaticamente.
- [ ] Suporte ao formato `apply_patch` do OpenAI/Codex como formato de entrada alternativo.
- [ ] Core como biblioteca Python pura (sem PySide6) para uso em extensão VS Code ou scripts.
- [ ] Extensão VS Code usando o core sem GUI.

---

## 🚫 Itens descartados desta visão
- **Integração direta com API de IA (Claude, OpenAI)** — a ferramenta consome instruções pré-geradas; chamar a API diretamente criaria acoplamento com fornecedor específico e mudaria o escopo → fora de escopo. Pode viver em IDEAS se reavaliado.
