# STATUS.md — Estado Atual

> Arquivo **rolante**: descreve só o AGORA. O assistente lê no início para saber onde retomar.
> Item resolvido SAI daqui — vai para o CHANGELOG (se foi entrega) e/ou para o log da sessão.
> Médio e longo prazo NÃO ficam aqui — ficam no ROADMAP.

---

## Versão Atual
**[0.6.0-alpha]** — 2026-06-15 — **conveniências de backup + paridade de sandbox na GUI.** Três features novas, todas validadas por teste: `--backup-dir` (cria `backups/` fora do projeto, mantendo a árvore limpa — DEC-018), `backups/history.log` (um arquivo append-only com o histórico de aplicações, em vez de abrir cada pasta de timestamp — DEC-018), e checkbox **"Aplicar em sandbox (cópia)"** na GUI (paridade com o `--sandbox` do CLI — DEC-019). A lógica de sandbox migrou para o core (`patch_engine.make_sandbox`), compartilhada por CLI e GUI. **93 testes verdes; self-test OK.** Estado confirmado funcionando no Windows do usuário (console-260614 - 2.txt: self-test, validate, dry-run e apply do projeto_teste todos OK).

> **Nota:** as sessões 06-19 e 06-21 não tocaram o CÓDIGO (segue em 0.6.0); foram mudanças de PROCESSO/estrutura — ver abaixo.

## 🛠️ Estrutura / Modo Claude Code (desde 2026-06-21 — DEC-021)
O projeto adotou o **modo Claude Code** (atualização do KCM "update-code-mode"). Mudanças:
- O antigo `meta/CLAUDE.md` (comportamento) foi **renomeado para `meta/CEREBRO.md`** — todo o conteúdo preservado (princípios, higiene, seção HUB) + nova seção «Desenvolvimento no Claude Code».
- Novos arquivos de **arranque na raiz do repo**: `CLAUDE.md` (ponteiro curto p/ o Code, com ritual + comandos de build do ASU), `.claude/settings.json` (permissões) e `.claude/commands/` (`apply-spec.md`, `wrap.md`).
- Duas raias: chat AUTORA docs (arquivo inteiro ou **spec** em `meta/specs/`); Code implementa código, faz edições **append-only** nos `meta/`, aplica specs, valida e commita.
- Os templates dos demais docs **não mudaram de estrutura** — nada a regenerar por causa do template.
- **Pendência (ajuste manual do usuário):** as **Instruções do Projeto** (painel do Projeto) ainda citam `CLAUDE.md` — apontar para `CEREBRO.md`.

## 🔗 Grupo / Toolchain (HUB)
Este repo agora integra o toolchain **KCM · ASU · FlatDrop**, coordenado por **um único** `HUB.md` — **gerado pela conversa do KCM** — que vive na **pasta-raiz comum** aos três projetos (não duplicado dentro de cada repo; sobe avulso ao Projeto quando preciso; opcionalmente versionado junto com o KCM). Registra os contratos C1–C4 e as caixas de entrada por frente. O `CEREBRO.md` tem a seção «Projeto em grupo (HUB compartilhado)» em **modo só-HUB** (DEC-020): o ASU participa do grupo mas NÃO usa a si mesmo como mecanismo de entrega (a diretriz «Saída via ASU» é para projetos consumidores, não para o repo do ASU). **Pendência de sincronia:** o `HUB.md` cita a ferramenta ASU em **v0.4.0** no status relâmpago — defasado (está em 0.6.0); atualizar o status relâmpago do ASU no HUB. Concorrência: se duas frentes gerarem o HUB na mesma janela, juntar e fazer um *merge* canônico via uma das frentes.

## ✅ Funcionando
- **CLI completo** (`python -m src`): `validate`, `apply` (prévia em dry-run + confirmação), `rollback <timestamp>` e `self-test`.
  - Flags do `apply`: `--root`, `--dry-run`, `--no-backup`, `--sandbox`, `--backup-dir PASTA`, `--no-color`, `--yes/-y`.
  - Flags do `rollback`: `--root`, `--backup-dir PASTA`.
- **Intake**: parser YAML/JSON (com fallback de encoding) + validador contra JSON Schema com `format_version` e erros descritivos por caminho de campo. Loader estrito rejeita chave YAML duplicada; validador rejeita IDs repetidos (FIX-006).
- **13 estratégias** aplicando corretamente:
  - Python (libcst): `replace_function`, `replace_method`, `replace_class` — escopo léxico correto e formatação/comentários preservados.
  - Texto universal (`re`): `insert_after_pattern`, `insert_before_pattern`, `replace_line_pattern`, `replace_context_block`.
  - Markdown: `replace_section` (fence-aware).
  - JSON (navegador de caminho próprio): `set_json_path`, `append_json_array`, `delete_json_path`.
  - Arquivo inteiro: `replace_file`, `create_file`.
- **Resolução de caminhos** relative/absolute com guarda de contenção (relativo não escapa da raiz).
- **Backup obrigatório** timestampado (DEC-006) + **rollback atômico** automático em falha e rollback manual por timestamp. Espelho relativo à raiz (FIX-008, não estoura o MAX_PATH do Windows). Manifesto por sessão com espelho explícito + `history.log` consolidado (DEC-018). Local do backup configurável via `--backup-dir` (DEC-018).
- **Diff colorido** (unified diff, colorama) na prévia e no resultado.
- **Demo executável** (`examples/demo_project/` + `examples/demo.yaml`): roda de ponta a ponta (`validate → apply --dry-run → apply → rollback`) sem precisar de um projeto próprio. A demo CRIA `src/health.py` via `create_file` — esse arquivo está no `.gitignore` e é limpo pelos testes/self-test (FIX-009).
- `replace_context_block` com guarda contra inclusão das âncoras no `new_content` (evita corrupção silenciosa — FIX-001) e **dica acionável de whitespace** quando a âncora não casa por indentação (DEC-014).
- **Unicidade implícita de localizadores** (DEC-011): padrão/âncora ambíguos sem `occurrence` são bloqueados antes de escrever.
- **Encodings seguros** (FIX-002): UTF-8 com BOM preservado (roundtrip `.cs` do Visual Studio); cp1252 roundtrip; CRLF preservado; UTF-16/32 rejeitados com erro claro.
- **Multilinguagem comprovada por teste**: C#, C++, Java, JSX, TSX e GDScript via mecanismo universal (`type: text`).
- **Kit de ensino para a IA** (`docs/`): `INSTRUCTION_GUIDE.md` (autocontido, com exemplo embutido, 6 regras de ouro, tabela erro→correção, §8 de verificação pós-aplicação) + `PROMPT_IA.md` (bloco para colar em projetos consumidores). Dogfood aplicou C# (BOM), Python decorado e TSX só seguindo o guia.
- **JSON com roundtrip fiel** (FIX-004): indentação/compacto/newline final do original preservados; chaves `null` deletáveis (FIX-005).
- **GUI (F2)** (`python -m src.gui`): Pré-visualizar (dry-run) com árvore 🟢/🔴/⚪ por arquivo e ✓/✗ por modificação + diff colorido; Aplicar com backup; Desfazer; Colar instrução (clipboard); Copiar erro para a IA; caminhos lembrados (QSettings); **checkbox de sandbox** (DEC-019). Estado entre prévia/aplicação/desfazer protegido por fingerprint SHA-256 e raiz capturada (FIX-007).
- **`apply --sandbox`** / checkbox de sandbox: aplica numa cópia irmã do projeto; original intocado (DEC-015, DEC-019).
- **`python -m src self-test`**: valida a instalação ponta a ponta em tempdir (nada do disco é tocado).
- Núcleo com 4 dependências (PyYAML, jsonschema, libcst, colorama). GUI adiciona PySide6; dev adiciona pytest, pytest-qt, ruff, black.
- **93 testes** unitários e de integração, todos verdes; `ruff` e `black` limpos.

## 🔧 Em Progresso
- **F2 (GUI) — increment ATIVO "Acesso rápido a projetos" (spec `meta/specs/F2-acesso-rapido.md`, p/ o Claude Code):** pastas-raiz recentes (até 8) + fixadas; args de lançamento da GUI (`--root`/`--instruction-dir`/`--instruction`); botão "Criar atalho .bat…" (gera .bat por projeto, python-do-venv direto — DEC-022); resolução pasta→instrução (só o topo; 1=pré-preenche, 2+=abre seletor). NÃO auto-aplica — só pré-preenche; dry-run+revisão seguem manuais.
- **F2 (GUI) — itens estruturais restantes** (próximo increment): validação VISUAL no Windows real (o usuário rodou `python -m src.gui` mas ainda não relatou a experiência da janela); highlight de sintaxe no diff; barra de progresso; tema claro/escuro; seleção de timestamps antigos no Desfazer; threads se surgir caso de lentidão.
- **Pendência de documentação (0.6.0):** README e GUIA_PASSO_A_PASSO ainda NÃO atualizados para as features 0.6.0 (--backup-dir, history.log, checkbox sandbox) nem as correções de clareza pedidas (ver Backlog). Código e docs de contexto estão atualizados; README/GUIA ficaram para depois.

## ❌ Quebrado / Com Problema
- Nenhum conhecido. (Os 5 bugs reportados nos consoles 06-13 e 06-14 — FIX-008 e FIX-009 — estão corrigidos e confirmados.)

## 📋 Backlog (curto prazo — itens acionáveis)
- [ ] **Atualizar README.md** para 0.6.0: documentar `--backup-dir`, `history.log`, checkbox de sandbox na GUI.
- [ ] **Atualizar/Reescrever GUIA_PASSO_A_PASSO.md** com as correções que o usuário pediu (ideia-260614):
  - corrigir a confusão sobre o local do `instrucao.yaml` (recomendar um local fixo; explicar que vários com mesmo nome em pastas diferentes NÃO dá problema — o que importa é o `--root`);
  - documentar a opção de subir o `PROMPT_IA.md` ao projeto e referenciá-lo no CEREBRO.md/instruções (em vez de colar o conteúdo toda vez);
  - documentar `--backup-dir`, `history.log` e o checkbox de sandbox na GUI;
  - documentar o `--no-backup` (já existe) como resposta à pergunta "dá para não gerar/excluir backup?".
- [x] **Setup do Claude Code concluído** (2026-06-21): arquivos de arranque no repo, `meta/CEREBRO.md` em uso. — RESTA: apontar as **Instruções do Projeto (painel)** de `CLAUDE.md` para `CEREBRO.md` (ajuste manual do usuário, fora dos arquivos).
- [ ] **▶ Implementar a spec `meta/specs/F2-acesso-rapido.md`** no Claude Code (recentes/fixadas + args de lançamento + gerador de .bat + resolução pasta→instrução). Rodar `pytest`/`ruff`/`black` e `python -m src.gui` ao final.
- [ ] **Arquivar os `.txt` processados:** `260619-ideias.txt` (transcrição já capturada) e `260621-Sugestões do KCM` (capturado em IDEAS › Feedback para o Kit). Sair do Projeto/raiz quando conveniente.
- [ ] **Testar o kit v2 em campo**: substituir guia/prompt no(s) projeto(s) consumidor(es), gerar 2–3 instruções reais — e usar sandbox no primeiro projeto médio.
- [ ] **Atualizar o HUB.md** — corrigir o status relâmpago do ASU (cita v0.4.0 → está em 0.6.0) e **ancorar a diretriz ASU no `format_version >= 1.0`** (endossado pelo KCM, ver IDEAS). É um único arquivo na raiz comum; entregar a versão nova substitui a anterior.
- [ ] Relatar a experiência VISUAL da GUI no Windows (usabilidade, diálogos, clipboard).
- [ ] Avaliar CI Windows (feedback ao Kit em IDEAS) e, sob demanda, refinamento semântico por família de linguagem (tree-sitter): web > JVM/C-like > nicho.

> Fora do backlog ativo (decisão do usuário 06-19): **validação de sintaxe pós-aplicação NÃO entra** — aumentaria o escopo; código quebrado é problema do compilador/da IA geradora, não do ASU. Fica como ideia condicional de baixíssima prioridade (ver IDEAS).

## 📁 Arquivos Críticos (não mexer sem contexto)
- `src/schemas/instruction_v1.schema.json` — contrato do arquivo de instrução; mudanças quebram retrocompatibilidade com instruções já geradas → ver DEC-007 e DEC-009 antes de alterar.
- `src/core/patch_engine.py` — orquestra toda a execução; lógica de transação, rollback atômico e sandbox (`make_sandbox`); ponto central de risco. Parâmetros-chave de `apply_instruction`: `root_path` (base dos caminhos), `backup_location` (onde criar `backups/`, DEC-018), `dry_run`, `backup`, `stop_on_error`, `color`.
- `src/core/backup_manager.py` — base do rollback; o formato do `manifest.txt` (`estado<TAB>original<TAB>espelho`) é lido pelo `rollback`; `_relative_mirror` é o coração do FIX-008; `append_history` mantém o `history.log`. Aceita `root=` (base dos caminhos relativos) separado de `backup_root` (onde fica `backups/`).
- `docs/INSTRUCTION_GUIDE.md` + `docs/PROMPT_IA.md` — o "produto" consumido pela IA geradora; toda regra nova de geração deve renetir aqui na mesma sessão.

## 💬 Última Sessão
**2026-06-22 — início do increment "Acesso rápido" da F2 + spec para o Claude Code (sem código ainda).** Lidos os dois `.txt` (agora no pacote): `260619-ideias.txt` é transcrição de mensagem antiga (já capturada → arquivar); `260621-Sugestões do KCM` é retorno da caixa do HUB — o KCM RETIRA a sugestão de checagem de sintaxe (convergindo conosco) e ENDOSSA ancorar no `format_version >= 1.0` (capturado em IDEAS). **Entregue:** a spec `meta/specs/F2-acesso-rapido.md` (recentes/fixadas + args de lançamento + gerador de .bat + resolução pasta→instrução), para o Claude Code implementar; ROADMAP com o increment ativo e o .bat movido da F3 p/ a F2; DEC-022 (design do launcher: .bat via python-do-venv direto — pesquisado; instrução por PASTA, não arquivo; escaneia só o topo). **Regressão corrigida:** o IDEAS no pacote tinha voltado à versão ANTIGA das duas entradas de validação de sintaxe (estava como "candidata forte/F3"); reescrito para "FORA DO FOCO" conforme a decisão do usuário (e agora com a confirmação do KCM). **Apresentadas todas as fases** (F2 ativa, F3, F4) no chat e no ROADMAP. **Pendente:** rodar o Claude Code com a spec p/ implementar; herdados (HUB status relâmpago, README/GUIA 0.6.0). Sessões anteriores:
**2026-06-21 — adoção do modo Claude Code; CLAUDE.md→CEREBRO.md (sem código).** Atualização do KCM ("update-code-mode") integrada. Entregue `meta/CEREBRO.md` (CLAUDE.md renomeado + seção «Desenvolvimento no Claude Code» + HUB preservada) e os arquivos de arranque na raiz (`CLAUDE.md` ponteiro, `.claude/`). DEC-021. Corrigido o bug de nomes de doc do starter do KCM (DECISIONS, não DECISOES). Sessões anteriores:
**2026-06-19 — integração ao toolchain (HUB) + CLAUDE.md em modo só-HUB (sem código); correções de entendimento.** Sessão de processo, não de produto: o ASU entrou no grupo KCM·ASU·FlatDrop coordenado pelo `HUB.md`. Compreendido o mecanismo: o `asu-switch.yaml` foi o ASU modificando o **KCM** (não a si mesmo) para adicionar o switch *asuMode*. Entregue o CLAUDE.md com a seção «Projeto em grupo» (DEC-020). Correções: HUB é gerado pelo KCM e é único na raiz comum; o medo do ASU é em PROSA, não em código; validação de sintaxe NÃO entra. Sessões anteriores:
**2026-06-15 — conveniências de backup + paridade de sandbox + processamento de muitas ideias.** O `console-260614 - 2.txt` confirmou que TUDO funciona no Windows do usuário (self-test, validate, dry-run, apply do projeto_teste — sem erro). Lidas e processadas as muitas ideias do `ideia-260614.txt`. Implementadas 3 de alto valor/baixo risco: `--backup-dir` (backup fora do projeto, DEC-018), `history.log` consolidado (DEC-018) e checkbox de sandbox na GUI (DEC-019, com `make_sandbox` migrado ao core). Pesquisa fundamentou as respostas (git add -p valida seleção parcial; backup naming valida prefixo+ordenável mas adiado; AI-patch safety REFUTA auto-aplicar sem revisão). 93 testes, v0.6.0. **Ficou pendente:** atualizar README e GUIA_PASSO_A_PASSO (ver Backlog) e responder formalmente, no chat/docs, às várias perguntas/ideias do usuário que não viraram código (estão capturadas em IDEAS).
**2026-06-14 — resíduo da demo + clareza nos canais de feedback.** `health.py` gerado pela demo vazou para `examples/demo_project/` e quebrava 4 testes de GUI + self-test no Windows (arquivos nos lugares certos — não foi erro de processo). Corrigido (FIX-009): `.gitignore` + limpeza defensiva. Esclarecida (DEC-017) a separação de canais de feedback (Kit × ASU). v0.5.2.
**2026-06-13 — bug de Windows (FIX-008) + verificação pós-aplicação (DEC-016) + atualização do Kit.** O `mirror_path` recriava o caminho absoluto sob `backups/`, estourando o MAX_PATH do Windows (260 chars). Espelho passou a ser relativo à raiz. §8 do guia (verificação outcome-based). v0.5.1.
**2026-06-12 — F2 polish + sandbox** (DEC-015 sandbox, FIX-007 estado da GUI, GUI colar/copiar-erro/caminhos lembrados). v0.5.0.
**2026-06-11 — F2 GUI inicial + pesquisa V4A + kit v2.** GUI fina sobre a pilha (DEC-013) com testes offscreen; self-test; DEC-014 (erro acionável, sem fuzzy silencioso); guia v2 autocontido. v0.4.0.
**2026-06-10 (parte 3 — intake/JSON + kit de ensino).** FIX-004 (JSON roundtrip), FIX-005 (null deletável, jmespath removido), FIX-006 (intake estrito), DEC-012 (kit de ensino). v0.3.0.
