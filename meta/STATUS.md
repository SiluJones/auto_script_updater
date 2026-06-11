# STATUS.md — Estado Atual

> Arquivo **rolante**: descreve só o AGORA. Item resolvido SAI daqui — vai para o CHANGELOG.
> Médio e longo prazo NÃO ficam aqui — ficam no ROADMAP.

---

## Versão Atual
**[0.3.0-alpha]** — 2026-06-10 — F1 endurecida + **kit de ensino para a IA pronto** (docs/INSTRUCTION_GUIDE.md + docs/PROMPT_IA.md, validados por dogfooding). 79 testes verdes; JSON com estilo preservado (FIX-004); null deletável e jmespath fora do núcleo (FIX-005); intake estrito — YAML duplicado, IDs repetidos e binários rejeitados (FIX-006).

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
- **Demo executável** (`examples/demo_project/` + `examples/demo.yaml`): roda de ponta a ponta (`validate → apply --dry-run → apply → rollback`) sem precisar de um projeto próprio. README traz o Quickstart copiável.
- `replace_context_block` com guarda contra inclusão das âncoras no `new_content` (evita corrupção silenciosa — FIX-001).
- **Unicidade implícita de localizadores** (DEC-011): padrão/âncora ambíguos sem `occurrence` são bloqueados antes de escrever.
- **Encodings seguros** (FIX-002): UTF-8 com BOM preservado (roundtrip `.cs` do Visual Studio); cp1252 roundtrip; CRLF preservado; UTF-16/32 rejeitados com erro claro.
- **`replace_section` fence-aware** (FIX-003): headings dentro de ``` não são seções.
- **Multilinguagem comprovada por teste**: C#, C++, Java, JSX, TSX e GDScript via mecanismo universal (`type: text`).
- **Kit de ensino para a IA** (`docs/`): guia de referência + bloco de prompt para colar em outros projetos; dogfood aplicou C# (BOM), Python decorado e TSX só seguindo o guia.
- **JSON com roundtrip fiel** (FIX-004): indentação/compacto/newline final do original preservados; chaves `null` deletáveis (FIX-005).
- **Intake estrito** (FIX-006): chave YAML duplicada, IDs repetidos e arquivos binários são rejeitados com mensagens que ensinam.
- Núcleo com 4 dependências (PyYAML, jsonschema, libcst, colorama — jmespath removido).
- 79 testes unitários e de integração, todos verdes; `ruff` e `black` limpos.

## 🔧 Em Progresso
- Nada em progresso — F1 fechada; aguardando início da F2 (GUI).

## ❌ Quebrado / Com Problema
- Nenhum conhecido.

## 📋 Backlog (curto prazo — itens acionáveis)
- [ ] **Testar o kit em campo**: adotar o ASU num projeto real seu (copiar `docs/INSTRUCTION_GUIDE.md` + colar `docs/PROMPT_IA.md`), gerar 2–3 instruções de verdade e registrar fricções para refinar o guia.
- [ ] Iniciar F2: `src/gui/main_window.py` (esqueleto da janela + orquestração da pilha existente).
- [ ] Derivar indicador de confiança por modificação (🟢/🟡/🔴) a partir do dry-run por modificação (já há `ModificationResult.ok/error`).

## 📁 Arquivos Críticos (não mexer sem contexto)
- `src/schemas/instruction_v1.schema.json` — contrato do arquivo de instrução; mudanças quebram retrocompatibilidade com instruções já geradas → ver DEC-007 e DEC-009 antes de alterar.
- `src/core/patch_engine.py` — orquestra toda a execução; lógica de transação e rollback atômico; ponto central de risco.
- `src/core/backup_manager.py` — base do rollback; o formato do `manifest.txt` é lido pelo `rollback` do CLI.

## 💬 Última Sessão
**2026-06-10 (parte 3 — intake/JSON + kit de ensino)** — Auditoria das camadas restantes achou e corrigiu: JSON reformatado por inteiro (FIX-004 — estilo agora preservado), `null` indeletável por culpa do jmespath (FIX-005 — navegador próprio, dependência removida do núcleo) e três silêncios de entrada: chave YAML duplicada evaporando conteúdo, IDs repetidos e binários sobrescrevíveis (FIX-006). Entregue o **kit de ensino** (DEC-012): `docs/INSTRUCTION_GUIDE.md` + `docs/PROMPT_IA.md`, validados por dogfooding (C# com BOM real, Python decorado, TSX — aplicação e rollback íntegros). 79 testes, v0.3.0. Próximo: testar o kit num projeto real e F2 (GUI).
