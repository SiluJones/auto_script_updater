# STATUS.md — Estado Atual

> Arquivo **rolante**: descreve só o AGORA. Item resolvido SAI daqui — vai para o CHANGELOG.
> Médio e longo prazo NÃO ficam aqui — ficam no ROADMAP.

---

## Versão Atual
**[0.0.1-alpha]** — 2026-06-03 — Concepção e design arquitetural concluídos; código zero.

## ✅ Funcionando
- Documentação completa de contexto gerada e pronta para uso nas próximas sessões.
- Arquitetura definida: módulos, responsabilidades, interfaces entre componentes.
- Stack tecnológica selecionada e justificada (Python 3.11, PySide6, libcst, PyYAML, jsonschema, jmespath).
- Schema conceitual do arquivo de instrução YAML v1.0 definido.
- Onze estratégias de modificação especificadas para 4 tipos de arquivo.
- Sete decisões arquiteturais documentadas (DEC-001 a DEC-007).
- Roadmap em 5 fases (F0–F4) com critérios de conclusão.

## 🔧 Em Progresso
- Nada em progresso — projeto em transição de design para implementação.

## ❌ Quebrado / Com Problema
- Nenhum — projeto não iniciado.

## 📋 Backlog (curto prazo — itens acionáveis)
- [ ] Criar estrutura de pastas `auto_script_updater/` conforme CONTEXT.md.
- [ ] Criar `requirements.txt` (PySide6, libcst, PyYAML, jsonschema, jmespath) e `requirements-dev.txt` (pytest, pytest-qt, ruff, black).
- [ ] Implementar `src/schemas/instruction_v1.schema.json` — schema JSON completo e validável.
- [ ] Implementar `src/core/instruction_parser.py` — carrega YAML, retorna dict validado.
- [ ] Implementar `src/core/instruction_validator.py` — valida dict contra schema.
- [ ] Implementar `src/core/file_locator.py` — resolve caminhos e verifica existência.
- [ ] Implementar `src/core/backup_manager.py` — backup timestampado e restauração.
- [ ] Implementar `src/strategies/text_strategy.py` — estratégias de texto genérico.
- [ ] Implementar `src/strategies/python_strategy.py` — estratégias libcst.
- [ ] Implementar `src/strategies/json_strategy.py` — estratégias jmespath.
- [ ] Implementar `src/core/patch_engine.py` — orquestrador com transação.
- [ ] Implementar `src/core/diff_renderer.py` — unified diff para prévia.
- [ ] Escrever fixtures de teste e testes unitários para cada strategy.
- [ ] Testar ciclo completo CLI: instrução YAML → modificações aplicadas → backup criado.

## 📁 Arquivos Críticos (não mexer sem contexto)
- `src/schemas/instruction_v1.schema.json` — contrato do arquivo de instrução; mudanças quebram retrocompatibilidade com todas as instruções já geradas → ver DEC-007 antes de alterar.
- `src/core/patch_engine.py` — orquestra toda a execução; lógica de transação e rollback; ponto central de risco.

## 💬 Última Sessão
**2026-06-03** — Sessão de concepção: projeto idealizado, stack pesquisada e validada, arquitetura definida, schema de instrução projetado, estratégias de modificação especificadas, 7 decisões ADR documentadas, roadmap completo criado, toda a documentação gerada. Próximo passo imediato: criar estrutura de pastas e iniciar pelo `instruction_v1.schema.json` + `instruction_parser.py`.
