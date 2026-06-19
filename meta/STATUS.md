# STATUS.md — Estado Atual

> Arquivo **rolante**: descreve só o AGORA. O assistente lê no início para saber onde retomar.
> Item resolvido SAI daqui — vai para o CHANGELOG (se foi entrega) e/ou para o log da sessão.
> Médio e longo prazo NÃO ficam aqui — ficam no ROADMAP.

---

## Versão Atual
**[0.6.0-alpha]** — 2026-06-15 — **conveniências de backup + paridade de sandbox na GUI.** Três features novas, todas validadas por teste: `--backup-dir` (cria `backups/` fora do projeto, mantendo a árvore limpa — DEC-018), `backups/history.log` (um arquivo append-only com o histórico de aplicações, em vez de abrir cada pasta de timestamp — DEC-018), e checkbox **"Aplicar em sandbox (cópia)"** na GUI (paridade com o `--sandbox` do CLI — DEC-019). A lógica de sandbox migrou para o core (`patch_engine.make_sandbox`), compartilhada por CLI e GUI. **93 testes verdes; self-test OK.** Estado confirmado funcionando no Windows do usuário (console-260614 - 2.txt: self-test, validate, dry-run e apply do projeto_teste todos OK).

> **Nota:** a sessão 06-19 não tocou o CÓDIGO (segue em 0.6.0); foi integração de PROCESSO — ver abaixo.

## 🔗 Grupo / Toolchain (HUB)
Este repo agora integra o toolchain **KCM · ASU · FlatDrop**, coordenado por um `HUB.md` (cópia idêntica nos três repos, sincronizada à mão; registra os contratos C1–C4 e as caixas de entrada por frente). O CLAUDE.md ganhou a seção «Projeto em grupo (HUB compartilhado)» em **modo só-HUB** (DEC-020): o ASU participa do grupo mas NÃO usa a si mesmo como mecanismo de entrega (a diretriz «Saída via ASU» é para projetos consumidores, não para o repo do ASU). Pendência de sincronia: o `HUB.md` cita a ferramenta em **v0.4.0** no status relâmpago do ASU — está defasado (ferramenta em 0.6.0); atualizar o status relâmpago do ASU no HUB e ressincronizar os três repos. O `HUB.md` ainda NÃO está versionado no repo do ASU (subiu avulso ao Projeto, fora do pacote FlatDrop) — decidir se entra em `meta/` ou na raiz dos três repos.

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
- **F2 (GUI)** — funcional e com paridade de sandbox. Falta: validação VISUAL no Windows real (o usuário rodou `python -m src.gui` mas ainda não relatou a experiência de uso da janela); highlight de sintaxe no diff; histórico de raízes (hoje lembra só a última); seleção/aplicação parcial (em avaliação — ver IDEAS, pode conflitar com o objetivo); threads se surgir caso de lentidão.
- **Pendência de documentação desta sessão (0.6.0):** o README e o GUIA_PASSO_A_PASSO ainda NÃO foram atualizados para renetir as features 0.6.0 (--backup-dir, history.log, checkbox sandbox) nem as correções de clareza que o usuário pediu (ver Backlog). O código e os docs de contexto (este STATUS, CHANGELOG, DECISIONS, IDEAS) estão atualizados; README/GUIA ficaram para a próxima sessão.

## ❌ Quebrado / Com Problema
- Nenhum conhecido. (Os 5 bugs reportados nos consoles 06-13 e 06-14 — FIX-008 e FIX-009 — estão corrigidos e confirmados.)

## 📋 Backlog (curto prazo — itens acionáveis)
- [ ] **Atualizar README.md** para 0.6.0: documentar `--backup-dir`, `history.log`, checkbox de sandbox na GUI.
- [ ] **Atualizar/Reescrever GUIA_PASSO_A_PASSO.md** com as correções que o usuário pediu (ideia-260614):
  - corrigir a confusão sobre o local do `instrucao.yaml` (recomendar um local fixo; explicar que vários com mesmo nome em pastas diferentes NÃO dá problema — o que importa é o `--root`);
  - documentar a opção de subir o `PROMPT_IA.md` ao projeto e referenciá-lo no CLAUDE.md/instruções (em vez de colar o conteúdo toda vez);
  - documentar `--backup-dir`, `history.log` e o checkbox de sandbox na GUI;
  - documentar o `--no-backup` (já existe) como resposta à pergunta "dá para não gerar/excluir backup?".
- [ ] **Implementar gerador de `.bat` (avaliar)** — ver IDEAS. Recomendação da pesquisa: NUNCA auto-aplicar sem revisão (43% dos patches passam no teste primário mas quebram em casos adversos). Propor `.bat` que faz dry-run e PAUSA para confirmação, + um `.bat` que só abre a GUI/ativa venv. Possivelmente um botão "Gerar .bat" na GUI após definir raiz+instrução.
- [ ] **Testar o kit v2 em campo**: substituir guia/prompt no(s) projeto(s) consumidor(es), gerar 2–3 instruções reais — e usar sandbox no primeiro projeto médio.
- [ ] **Sincronizar o HUB.md** — atualizar o status relâmpago do ASU (cita v0.4.0 → está em 0.6.0) e propagar a cópia idêntica aos 3 repos (KCM, ASU, FlatDrop). Decidir onde o `HUB.md` mora no repo do ASU (raiz ou `meta/`) e versioná-lo (hoje subiu avulso ao Projeto).
- [ ] **Avaliar a validação de sintaxe pós-aplicação** (opt-in, por tipo) — ver IDEAS. Resposta concreta ao risco "patch aplicou mas quebrou o código": `ast.parse`/`py_compile` no resultado de edições em `.py` via `type: text`; falha = rollback (reusa a transação existente). Valida sintaxe, não semântica — deixar esse limite explícito.
- [ ] Relatar a experiência VISUAL da GUI no Windows (usabilidade, diálogos, clipboard).
- [ ] Avaliar CI Windows (feedback ao Kit em IDEAS) e, sob demanda, refinamento semântico por família de linguagem (tree-sitter): web > JVM/C-like > nicho.

## 📁 Arquivos Críticos (não mexer sem contexto)
- `src/schemas/instruction_v1.schema.json` — contrato do arquivo de instrução; mudanças quebram retrocompatibilidade com instruções já geradas → ver DEC-007 e DEC-009 antes de alterar.
- `src/core/patch_engine.py` — orquestra toda a execução; lógica de transação, rollback atômico e sandbox (`make_sandbox`); ponto central de risco. Parâmetros-chave de `apply_instruction`: `root_path` (base dos caminhos), `backup_location` (onde criar `backups/`, DEC-018), `dry_run`, `backup`, `stop_on_error`, `color`.
- `src/core/backup_manager.py` — base do rollback; o formato do `manifest.txt` (`estado<TAB>original<TAB>espelho`) é lido pelo `rollback`; `_relative_mirror` é o coração do FIX-008; `append_history` mantém o `history.log`. Aceita `root=` (base dos caminhos relativos) separado de `backup_root` (onde fica `backups/`).
- `docs/INSTRUCTION_GUIDE.md` + `docs/PROMPT_IA.md` — o "produto" consumido pela IA geradora; toda regra nova de geração deve renetir aqui na mesma sessão.

## 💬 Última Sessão
**2026-06-19 — integração ao toolchain (HUB) + CLAUDE.md em modo só-HUB (sem código).** Sessão de processo, não de produto: o ASU entrou no grupo KCM·ASU·FlatDrop coordenado pelo `HUB.md`. Compreendido o mecanismo: o `asu-switch.yaml` foi o ASU modificando o **KCM** (não a si mesmo) para adicionar o switch *asuMode*, que injeta a diretriz «Saída via ASU» no CLAUDE.md de projetos consumidores; os arquivos `CLAUDE-HUB-Update.md` e `CLAUDE-HUB-ASU.md` são amostras (nicho Design Visual) do que o kit gera com/sem o switch. **Entregue:** CLAUDE.md do ASU com a seção «Projeto em grupo» adaptada ao toolchain (HUB manual de infraestrutura) em modo só-HUB — DEC-020. **Análises respondidas no chat** (capturadas em IDEAS): valor do HUB entre 3 ferramentas (vale; padrão de "contract doc" na escala onde manual basta; risco = drift da cópia manual); risco do ASU em código vs. segurança em .md narrativo (válido — vira a ideia de validação de sintaxe pós-patch); feedback ao KCM sobre a integração do switch ASU (4 pontos). **Pendente:** atualizar o status relâmpago do ASU no HUB (cita v0.4.0, defasado) e ressincronizar nos 3 repos; decidir onde o HUB.md mora no repo do ASU; README/GUIA_PASSO_A_PASSO (herdado da 06-15). Sessões anteriores:
**2026-06-15 — conveniências de backup + paridade de sandbox + processamento de muitas ideias.** O `console-260614 - 2.txt` confirmou que TUDO funciona no Windows do usuário (self-test, validate, dry-run, apply do projeto_teste — sem erro). Lidas e processadas as muitas ideias do `ideia-260614.txt`. Implementadas 3 de alto valor/baixo risco: `--backup-dir` (backup fora do projeto, DEC-018), `history.log` consolidado (DEC-018) e checkbox de sandbox na GUI (DEC-019, com `make_sandbox` migrado ao core). Pesquisa fundamentou as respostas (git add -p valida seleção parcial; backup naming valida prefixo+ordenável mas adiado; AI-patch safety REFUTA auto-aplicar sem revisão). 93 testes, v0.6.0. **Ficou pendente:** atualizar README e GUIA_PASSO_A_PASSO (ver Backlog) e responder formalmente, no chat/docs, às várias perguntas/ideias do usuário que não viraram código (estão capturadas em IDEAS).
**2026-06-14 — resíduo da demo + clareza nos canais de feedback.** `health.py` gerado pela demo vazou para `examples/demo_project/` e quebrava 4 testes de GUI + self-test no Windows (arquivos nos lugares certos — não foi erro de processo). Corrigido (FIX-009): `.gitignore` + limpeza defensiva. Esclarecida (DEC-017) a separação de canais de feedback (Kit × ASU). v0.5.2.
**2026-06-13 — bug de Windows (FIX-008) + verificação pós-aplicação (DEC-016) + atualização do Kit.** O `mirror_path` recriava o caminho absoluto sob `backups/`, estourando o MAX_PATH do Windows (260 chars). Espelho passou a ser relativo à raiz. §8 do guia (verificação outcome-based). v0.5.1.
**2026-06-12 — F2 polish + sandbox** (DEC-015 sandbox, FIX-007 estado da GUI, GUI colar/copiar-erro/caminhos lembrados). v0.5.0.
**2026-06-11 — F2 GUI inicial + pesquisa V4A + kit v2.** GUI fina sobre a pilha (DEC-013) com testes offscreen; self-test; DEC-014 (erro acionável, sem fuzzy silencioso); guia v2 autocontido. v0.4.0.
**2026-06-10 (parte 3 — intake/JSON + kit de ensino).** FIX-004 (JSON roundtrip), FIX-005 (null deletável, jmespath removido), FIX-006 (intake estrito), DEC-012 (kit de ensino). v0.3.0.
