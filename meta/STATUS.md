# STATUS.md — Estado Atual

> Arquivo **rolante**: descreve só o AGORA. Item resolvido SAI daqui — vai para o CHANGELOG.
> Médio e longo prazo NÃO ficam aqui — ficam no ROADMAP.

---

## Versão Atual
**[0.2.0-alpha]** — 2026-06-10 — F1 polida: 68 testes verdes, ruff/black limpos, multilinguagem provada (C#, C++, Java, JSX, TSX, GDScript), unicidade implícita de localizadores (DEC-011), BOM UTF-8 preservado e UTF-16 rejeitado (FIX-002), `replace_section` fence-aware (FIX-003).

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
- 68 testes unitários e de integração, todos verdes; `ruff` e `black` limpos.

## 🔧 Em Progresso
- Nada em progresso — F1 fechada; aguardando início da F2 (GUI).

## ❌ Quebrado / Com Problema
- Nenhum conhecido.

## 📋 Backlog (curto prazo — itens acionáveis)
- [ ] **Guia de geração para a IA** (`meta/INSTRUCTION_GUIDE.md` ou similar): documento que "ensina" qualquer IA a emitir instruções corretas — regras das âncoras (miolo sem âncoras, `after` distintivo p/ chaves aninhadas), decoradores no `new_content`, `occurrence` só quando intencional, caminhos Windows, encoding UTF-8. **Pré-requisito para usar a ferramenta como beta tester em outros projetos.**
- [ ] Iniciar F2: `src/gui/main_window.py` (esqueleto da janela + orquestração da pilha existente).
- [ ] Derivar indicador de confiança por modificação (🟢/🟡/🔴) a partir do dry-run por modificação (já há `ModificationResult.ok/error`).

## 📁 Arquivos Críticos (não mexer sem contexto)
- `src/schemas/instruction_v1.schema.json` — contrato do arquivo de instrução; mudanças quebram retrocompatibilidade com instruções já geradas → ver DEC-007 e DEC-009 antes de alterar.
- `src/core/patch_engine.py` — orquestra toda a execução; lógica de transação e rollback atômico; ponto central de risco.
- `src/core/backup_manager.py` — base do rollback; o formato do `manifest.txt` é lido pelo `rollback` do CLI.

## 💬 Última Sessão
**2026-06-10 (parte 2 — polimento F1)** — Caça sistemática a erros silenciosos com 3 achados graves corrigidos: localizadores ambíguos aplicando no lugar errado sem aviso (DEC-011), BOM UTF-8 quebrando localização em `.cs` e UTF-16 virando lixo via cp1252 (FIX-002), e headings dentro de code fences cortando seções markdown (FIX-003). Multilinguagem **provada por teste** em C#, C++, Java, JSX, TSX e GDScript. Semânticas fixadas em teste: decorador removido se não repetido; `after` fecha no 1º match (usar âncora distintiva). 68 testes, ruff/black limpos, versão unificada 0.2.0. Próximo passo: **guia de geração para a IA** (prioridade) e F2.
