# ROADMAP.md — Plano Intencional de Evolução

> Médio e longo prazo vivem AQUI, não no STATUS.
> Estado: 🟢 concluída · 🟡 em curso/próxima · 🔵 futura · 🚫 descartada.

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

## 🟡 F1 — Motor de Execução (Core Engine + CLI) *(próxima)*
**Objetivo:** Ferramenta funcional via linha de comando. Sem GUI. Carrega instrução YAML, localiza arquivos, aplica modificações, cria backup, reporta resultado em texto. Toda a lógica crítica implementada e testada antes de construir a GUI.
**Critério de conclusão:** `python -m src instrucao.yaml --root C:\meu_projeto` aplica modificações corretamente para todos os tipos suportados (py, md, json, txt), com backup criado e rollback via flag `--rollback <timestamp>`.

- [ ] Estrutura de pastas `auto_script_updater/` e `requirements.txt` / `requirements-dev.txt`.
- [ ] `src/schemas/instruction_v1.schema.json` — schema JSON Schema completo e validável.
- [ ] `src/core/instruction_parser.py` — carrega YAML/JSON, retorna dict.
- [ ] `src/core/instruction_validator.py` — valida dict contra schema; erros descritivos com caminho do campo.
- [ ] `src/core/file_locator.py` — resolve `root + relative_path` ou `absolute_path`; verifica existência.
- [ ] `src/core/backup_manager.py` — cria `backups/<YYYYMMDD_HHMMSS>/`; restaura por timestamp.
- [ ] `src/strategies/base_strategy.py` — ABC com interface `find_location()` e `apply()`.
- [ ] `src/strategies/text_strategy.py` — `insert_after_pattern`, `insert_before_pattern`, `replace_context_block`, `replace_line_pattern`, `replace_section` (markdown).
- [ ] `src/strategies/python_strategy.py` — `replace_function`, `replace_method`, `replace_class` via libcst.
- [ ] `src/strategies/json_strategy.py` — `set_json_path`, `append_json_array`, `delete_json_path` via jmespath.
- [ ] `src/core/diff_renderer.py` — unified diff colorido para terminal (colorama).
- [ ] `src/core/patch_engine.py` — orquestração, seleção de strategy, transação com rollback automático em falha.
- [ ] `src/__main__.py` — CLI com argparse: `instrucao.yaml`, `--root`, `--dry-run`, `--rollback`.
- [ ] Testes unitários para cada strategy (fixtures em `tests/fixtures/`).
- [ ] Testes de integração do `patch_engine` (ciclo completo: instrução → modificação → backup).

---

## 🔵 F2 — Interface Gráfica Completa *(futura)*
**Objetivo:** GUI completa em PySide6. Usuário abre instrução, vê diff colorido por arquivo, define pasta raiz, aplica com um clique — sem usar terminal.
**Critério de conclusão:** Fluxo completo sem terminal: abrir instrução → validar e exibir confiança → configurar raiz → previsualizar diff → aplicar → ver resultado; rollback disponível via botão.

- [ ] `src/gui/main_window.py` — janela principal, barra de menu, barra de status.
- [ ] `src/gui/file_tree_panel.py` — árvore de arquivos afetados com ícone de status (🟢/🟡/🔴) por modificação.
- [ ] `src/gui/diff_viewer.py` — visualizador de diff com syntax highlight (QSyntaxHighlighter; adições verde, remoções vermelho).
- [ ] `src/gui/root_picker.py` — seletor de pasta raiz com histórico dos últimos 5 usos.
- [ ] Barra de progresso durante aplicação de instruções com muitos arquivos.
- [ ] Modo dry-run acessível via checkbox na GUI.
- [ ] Botão "Rollback" para desfazer a última aplicação com seleção de timestamp.
- [ ] Indicador de confiança por modificação (🟢 único / 🟡 ambíguo / 🔴 não encontrado).
- [ ] Suporte a tema claro/escuro seguindo a preferência do sistema (Qt color scheme).
- [ ] Botão "Colar instrução" — lê YAML da área de transferência.

---

## 🔵 F3 — Produtividade e Polimento *(futura)*
**Objetivo:** Recursos que completam o fluxo IA→aplicação sem fricção e tornam a ferramenta "produto acabado".
**Critério de conclusão:** Fluxo completo sem consultar documentação; ferramenta empacotada como `.exe` standalone.

- [ ] Painel "Gerador de prompt" — prompt padrão para a IA com botão "Copiar".
- [ ] Histórico de instruções aplicadas (`applied_instructions.json`) com visualizador.
- [ ] Checksum SHA-256 dos arquivos antes/depois registrado no log.
- [ ] Modo comparação acumulada pós-aplicação (diff de todos os arquivos numa tela).
- [ ] Limpeza automática de backups antigos (política configurável: manter últimos N ou últimos X dias).
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
