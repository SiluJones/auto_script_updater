# STATUS.md — Estado Atual

> Arquivo **rolante**: descreve só o AGORA. Item resolvido SAI daqui — vai para o CHANGELOG.
> Médio e longo prazo NÃO ficam aqui — ficam no ROADMAP.

---

## Versão Atual
**[0.1.0-alpha]** — 2026-06-08 — F1 concluída: motor de execução + CLI funcionais e testados (42/42 testes verdes).

## ✅ Funcionando
- **CLI completo** (`python -m src`): `validate`, `apply` (com prévia em dry-run + confirmação) e `rollback <timestamp>`.
- **Intake**: parser YAML/JSON (com fallback de encoding) + validador contra JSON Schema com `format_version` e erros descritivos por caminho de campo.
- **13 estratégias** aplicando corretamente:
  - Python (libcst): `replace_function`, `replace_method`, `replace_class` — escopo léxico correto e formatação preservada.
  - Texto universal (`re`): `insert_after_pattern`, `insert_before_pattern`, `replace_line_pattern`, `replace_context_block`.
  - Markdown: `replace_section`.
  - JSON (jmespath + navegador): `set_json_path`, `append_json_array`, `delete_json_path`.
  - Arquivo inteiro: `replace_file`, `create_file`.
- **Resolução de caminhos** relative/absolute com guarda de contenção (relativo não escapa da raiz).
- **Backup obrigatório** timestampado (DEC-006) + **rollback atômico** automático em falha e rollback manual por timestamp.
- **Diff colorido** (unified diff, colorama) na prévia e no resultado.
- 42 testes unitários e de integração, todos verdes.

## 🔧 Em Progresso
- Nada em progresso — F1 fechada; aguardando início da F2 (GUI).

## ❌ Quebrado / Com Problema
- Nenhum conhecido.

## 📋 Backlog (curto prazo — itens acionáveis)
- [ ] Rodar `ruff` + `black` no código (config já em `pyproject.toml`) e corrigir o que apontarem.
- [ ] Adicionar fixtures de borda em `tests/fixtures/`: arquivo CP-1252, arquivo com CRLF, regex com múltiplas ocorrências, contexto ambíguo.
- [ ] Iniciar F2: `src/gui/main_window.py` (esqueleto da janela + orquestração da pilha existente).
- [ ] Derivar indicador de confiança por modificação (🟢/🟡/🔴) a partir do dry-run por modificação (já há `ModificationResult.ok/error`).

## 📁 Arquivos Críticos (não mexer sem contexto)
- `src/schemas/instruction_v1.schema.json` — contrato do arquivo de instrução; mudanças quebram retrocompatibilidade com instruções já geradas → ver DEC-007 e DEC-009 antes de alterar.
- `src/core/patch_engine.py` — orquestra toda a execução; lógica de transação e rollback atômico; ponto central de risco.
- `src/core/backup_manager.py` — base do rollback; o formato do `manifest.txt` é lido pelo `rollback` do CLI.

## 💬 Última Sessão
**2026-06-08** — Implementada a F1 inteira: schema + parser + validator, as 13 estratégias (Python/libcst, texto/contexto universal, markdown, JSON/jmespath, arquivo inteiro), file_locator com guarda de contenção, backup_manager com rollback atômico e por timestamp, diff_renderer colorido, patch_engine (transação + dry-run + precedência de settings) e CLI (`validate`/`apply`/`rollback`). 42 testes verdes + smoke test ponta a ponta. Três decisões novas (DEC-008/009/010) e alinhamento dos nomes de módulo ao contrato F0. Próximo passo: F2 (GUI PySide6) reusando a mesma pilha.
