# STATUS.md — Estado Atual

> Arquivo **rolante**: descreve só o AGORA. O assistente lê no início para saber onde retomar.
> Item resolvido SAI daqui — vai para o CHANGELOG (se foi entrega) e/ou para o log da sessão.
> Médio e longo prazo NÃO ficam aqui — ficam no ROADMAP.

---

## Versão Atual
**[0.5.1-alpha]** — 2026-06-13 — **bug crítico de Windows corrigido (FIX-008):** o backup estourava o limite de 260 caracteres de caminho e derrubava 5 testes + o `self-test` na máquina do usuário (era invisível no CI Linux). Espelho de backup agora é relativo à raiz. Também nesta leva (0.5.0): `apply --sandbox` (DEC-015), GUI com Colar instrução / Copiar erro para a IA / caminhos lembrados, e dois bugs de estado da GUI corrigidos (FIX-007). Guia ganhou §8 (verificação pós-aplicação pela IA, DEC-016, validada por pesquisa). 90 testes verdes; self-test OK.

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
- **GUI (F2)**: `python -m src.gui` — Pré-visualizar (dry-run) com árvore 🟢/🔴 e diff colorido, Aplicar com backup, Desfazer, Colar instrução (clipboard), Copiar erro para a IA, caminhos lembrados.
- **`apply --sandbox`**: aplica numa cópia irmã do projeto; original intocado.
- **`python -m src self-test`**: valida a instalação ponta a ponta em tempdir.
- **Backup portável (FIX-008)**: espelho relativo à raiz — não estoura o MAX_PATH do Windows.
- 90 testes unitários e de integração, todos verdes; `ruff` e `black` limpos.

## 🔧 Em Progresso
- **F2 (GUI)** — funcional com colar/aplicar/desfazer/copiar-erro e caminhos lembrados. Falta: validação visual no Windows real, highlight de sintaxe no diff, histórico de raízes, threads se necessário.

## ❌ Quebrado / Com Problema
- Nenhum conhecido.

## 📋 Backlog (curto prazo — itens acionáveis)
- [ ] **Aplicar v0.5.1 no Windows e confirmar 90 passed + self-test OK** (o FIX-008 deve ter resolvido as 5 falhas do `260613-console.txt`).
- [ ] **Testar o kit v2 em campo**: substituir guia/prompt no(s) projeto(s) consumidor(es), gerar 2–3 instruções reais — e usar `apply --sandbox` no primeiro projeto médio.
- [ ] Testar a GUI no Windows real (`pip install -r requirements-gui.txt` → `python -m src.gui`) e listar ajustes de usabilidade.
- [ ] Avaliar CI Windows (feedback ao kit em IDEAS) e, sob demanda, refinamento semântico por família de linguagem.

## 📁 Arquivos Críticos (não mexer sem contexto)
- `src/schemas/instruction_v1.schema.json` — contrato do arquivo de instrução; mudanças quebram retrocompatibilidade com instruções já geradas → ver DEC-007 e DEC-009 antes de alterar.
- `src/core/patch_engine.py` — orquestra toda a execução; lógica de transação e rollback atômico; ponto central de risco.
- `src/core/backup_manager.py` — base do rollback; o formato do `manifest.txt` é lido pelo `rollback` do CLI.

## 💬 Última Sessão
**2026-06-13 — bug de Windows + verificação pós-aplicação + atualização do Kit.** Diagnosticado pelo `260613-console.txt`: o `mirror_path` do backup recriava o caminho absoluto inteiro sob `backups/`, estourando o MAX_PATH do Windows (260 chars) — quebrava 5 testes e o self-test, sem aparecer no Linux. Corrigido (FIX-008): espelho relativo à raiz + manifesto com espelho explícito. Pesquisada e validada a ideia do usuário de verificação pós-aplicação (outcome-based; agentes mentem sobre o próprio trabalho) → §8 do guia + DEC-016. Avaliada a ideia de arquivo de relatório (recomendado NÃO criar — ver IDEAS › Feedback para o Kit). Kit de contexto atualizado (CLAUDE.md + cabeçalhos de template). v0.5.1, 90 testes. Sessões anteriores:
**2026-06-12 — F2 polish + sandbox** (DEC-015, FIX-007, GUI colar/copiar-erro). 
**2026-06-11 — F2 + pesquisa V4A + kit v2.** GUI PySide6 entregue como camada fina sobre a pilha (DEC-013) com testes offscreen; `self-test`; estudo do apply_patch/V4A e concorrentes virou a DEC-014 (erro acionável com dica de whitespace, sem fuzzy silencioso) e o guia v2 autocontido (exemplo embutido, anti-padrões YAML-only, tabela erro→correção). 84 testes, v0.4.0. Sessão anterior:
**2026-06-10 (parte 3 — intake/JSON + kit de ensino)** — Auditoria das camadas restantes achou e corrigiu: JSON reformatado por inteiro (FIX-004 — estilo agora preservado), `null` indeletável por culpa do jmespath (FIX-005 — navegador próprio, dependência removida do núcleo) e três silêncios de entrada: chave YAML duplicada evaporando conteúdo, IDs repetidos e binários sobrescrevíveis (FIX-006). Entregue o **kit de ensino** (DEC-012): `docs/INSTRUCTION_GUIDE.md` + `docs/PROMPT_IA.md`, validados por dogfooding (C# com BOM real, Python decorado, TSX — aplicação e rollback íntegros). 79 testes, v0.3.0. Próximo: testar o kit num projeto real e F2 (GUI).
