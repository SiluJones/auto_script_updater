# IDEAS.md — Brainstorm e Visão

> **Segundo cérebro** do projeto. Captura TUDO que for mencionado, mesmo solto ou no meio de outro assunto.
> Nunca perde: ideia implementada vai para «Concluídas»; ideia recusada vai para «Descartadas» com o motivo.
> Separar por autor (você × assistente) ajuda a lembrar de onde veio cada coisa.

---

## 💡 Ideias Ativas — Usuário

### 2026-06-13 — Verificação pós-aplicação pela IA (na sessão seguinte) — ACEITA, ver DEC-016
Depois que o usuário aplica uma instrução ASU e reabre o projeto, a IA deve conferir cada arquivo tocado para ver se ficou como esperado, mesmo sem queixa — ajuda a achar discrepâncias nos primeiros pilotos. **Pesquisada e validada** (agentes de código emitem "linguagem de conclusão" independentemente do estado real; verificação confiável é *outcome-based*, lendo o disco, não o relato — DEV/CrisisCore; ReVeal; TDAD −70% regressões). Implementada como §8 do INSTRUCTION_GUIDE + item no PROMPT_IA. Ressalva aplicada: verificar LENDO o arquivo, nunca perguntando "deu certo?".

### 2026-06-13 — Refinamento por tipo/linguagem de arquivo (grupos) — PARCIAL, no momento certo
Pergunta do usuário: vale refinar o tratamento por tipo (.py, .json, .md, .tsx, .jsx, .java, .c, .cpp, .css, .cs, .gd, .js, .html), agrupados por linguagem/família? Resposta curta: **sim, mas sob demanda, guiado pelo uso real** — não especular agora. Hoje a cobertura é: semântica para .py (libcst) e .json (navegador próprio); contexto/regex universal para TODO o resto (provado em teste com C#, C++, Java, JSX, TSX, GDScript). O mecanismo universal JÁ edita .md/.txt/.css/.html/.gd etc. com segurança. Refinamento semântico por linguagem (ex.: tree-sitter para JS/TS/Java/C#) só compensa quando um caso real mostrar que o contexto não basta — e aí entra UMA família por vez (ver ideia tree-sitter do assistente). Famílias candidatas por prioridade de uso: web (ts/tsx/jsx/js/css/html) > JVM/C-like (java/c/cpp/cs) > nicho (gd). Decisão: aguardar o dogfooding em projetos reais apontar onde dói.


### 2026-06 — Ferramenta desktop de aplicação de instruções de IA
Ferramenta que lê arquivo de instrução gerado pela IA e aplica modificações a scripts e documentos do projeto automaticamente, com prévia e rollback. Núcleo do projeto.

### 2026-06 — Interface gráfica (não só CLI)
A ferramenta deve ter GUI para não exigir terminal. Usuário seleciona o arquivo de instrução e a pasta raiz visualmente, confere o diff, e aplica com um clique.

### 2026-06 — Suporte a múltiplos tipos de arquivo
Além de `.py`: `.md`, `.json`, `.txt` — e possivelmente mais no futuro.

### 2026-06 — Pasta raiz selecionável na GUI
Para caminhos relativos na instrução: usuário define a pasta raiz do projeto na interface; a ferramenta resolve `root + relative_path`.

### 2026-06 — Prévia de diff antes de aplicar
Mostrar o que vai mudar (antes/depois colorido) antes de qualquer escrita em disco. Usuário vê exatamente o que será modificado.

### 2026-06 — Schema / molde de instrução para a IA seguir
A ferramenta deve ter um formato de instrução bem definido que a IA aprende a gerar corretamente. O prompt padrão faz parte do produto.

---

## 🤖 Ideias Ativas — Assistente

### 2026-06-03 — Indicador de confiança por modificação na GUI
Durante a fase de validação, exibir um ícone de status para cada modificação: 🟢 localizador único e arquivo encontrado; 🟡 aviso (ex: arquivo encontrado mas regex é ambíguo); 🔴 erro (arquivo não encontrado, localizador inválido). Usuário não aplica sem ver todos os itens verdes.

### 2026-06-03 — Leitura de instrução direto da área de transferência
Botão "Colar instrução" que lê YAML diretamente da clipboard. Útil quando a IA gerou a instrução no chat e o usuário não quer salvar em arquivo separado — reduz fricção do fluxo principal.

### 2026-06-03 — Gerador de prompt de instrução embutido
Painel dentro da GUI com o prompt padrão que o usuário deve dar para a IA gerar um arquivo de instrução válido. Botão "Copiar prompt" para colar no chat. Elimina a necessidade de o usuário lembrar o formato.

### 2026-06-03 — Histórico de instruções aplicadas
Arquivo `applied_instructions.json` que registra: caminho do arquivo de instrução, data/hora, lista de arquivos afetados, resultado (sucesso/erro parcial). Permite auditoria futura sem precisar abrir logs individuais.

### 2026-06-03 — Checksum SHA-256 dos arquivos antes/depois
Calcular e registrar hash SHA-256 de cada arquivo afetado antes e depois da aplicação. Serve para: (1) detectar modificações externas concorrentes (arquivo mudou desde que a instrução foi gerada); (2) auditoria de integridade no log.

### 2026-06-03 — Suporte a `.env` como tipo de arquivo futuro
Modificar variáveis em arquivos `.env` por nome de variável (ex: `DATABASE_URL=nova_url`). Mais seguro do que regex genérico em arquivos de configuração. Entra como nova strategy em F4.

### 2026-06-03 — Suporte a `.sql` como tipo de arquivo futuro
Inserção de instruções SQL por marcador de comentário (ex: `-- PATCH_ANCHOR: migration_001`). Viável com a text_strategy + padrão de anchor comment. F4 ou além.

### 2026-06-03 — Extensão VS Code usando o core Python sem GUI
Empacotar o `src/core/` + `src/strategies/` como biblioteca Python pura (sem dependência de PySide6) e disponibilizar como extensão VS Code. O editor lê a instrução e aplica diretamente no workspace aberto. Reutiliza toda a lógica de modificação. Viável em F4.

### 2026-06-03 — Templates de prompt para diferentes IAs
Fornecer templates de prompt para Claude, GPT-4o, Gemini com as nuances de como cada modelo melhor gera o YAML de instrução (ex: Claude precisa de `<format>` tags; GPT prefere JSON Schema embutido no prompt). Documentação do produto, não código.

### 2026-06-03 — Modo comparação acumulada pós-aplicação
Após aplicar todas as modificações, mostrar numa única tela um diff acumulado de TODOS os arquivos modificados. Permite revisão rápida do resultado antes de fechar a ferramenta.

### 2026-06-03 — Suporte ao formato apply_patch do OpenAI/Codex como entrada alternativa
O formato `*** Begin Patch / *** End Patch` (usado por Codex, GPT-5.1, opencode) usa context-based patching similar ao nosso. Poderia ser aceito como formato alternativo de instrução (além do YAML estruturado). Útil se o usuário já usa ferramentas que emitem esse formato. Existe biblioteca Python `apply-patch-py` que já implementa o parser. Baixa prioridade (F3/F4), mas vale registrar.

### 2026-06-03 — Anchor comments opcionais no código-alvo
Modo opcional onde o usuário insere comentários especiais no código (`# ASU_ANCHOR: feature_login`) que servem como marcadores de localização ultra-estáveis. A IA referencia o anchor pelo nome; a ferramenta localiza por busca de string exata. Complementa as estratégias existentes para casos onde o código é muito dinâmico.

### 2026-06-08 — Localização semântica multilinguagem via tree-sitter (F4)
Hoje a precisão semântica existe só para Python (libcst) e JSON (jmespath); demais linguagens usam janela de contexto/regex. tree-sitter tem gramáticas para dezenas de linguagens e permitiria estratégias semânticas (`replace_function`/`replace_class`) em JS, Go, Rust, etc. Encaixa como reforço opcional sobre o mecanismo universal de contexto. Registrado a partir da DEC-010. Prioridade F4.

### 2026-06-10 — Canal de "aviso" (warning) no engine, além de ok/erro
Hoje cada modificação resulta em ok ou erro. Um terceiro nível de *aviso* permitiria sinalizar situações suspeitas que não justificam bloquear (ex.: regex casou num único lugar plausível mas frágil, contexto quase ambíguo, indentação inesperada). Casaria diretamente com o indicador de confiança 🟡 da GUI (F2) e tornaria o dry-run mais informativo. Surgiu ao implementar a guarda do FIX-001.

### 2026-06-10 — Flag opcional `include_anchors` no `replace_context_block`
Por padrão (convenção A, FIX-001) as âncoras `before`/`after` permanecem e o `new_content` é só o miolo. Uma flag opt-in `include_anchors: true` permitiria a convenção B (substituir o bloco INTEIRO, âncoras inclusas) para quem achar mais natural reescrever a função/bloco completo. Manter o default em A; só adicionar se o uso real pedir.

### 2026-06-11 — Workflow "sandbox por duplicata" (ideia do usuário)
Para os primeiros usos em projetos grandes: duplicar a pasta do projeto-alvo, aplicar a instrução na duplicata, validar (inclusive subindo o resultado para a IA revisar) e só então promover ao projeto real. Documentado no README ("Modo seguro"), junto do fluxo equivalente com Git (commit antes → apply → `git diff` → `git restore`). Possível evolução de ferramenta: um comando `apply --sandbox` que copia a raiz para um tempdir, aplica lá e imprime o caminho para inspeção.

### 2026-06-11 — Fuzzy matching de whitespace como OPT-IN explícito
O apply_patch/V4A da OpenAI usa correspondência progressiva (exato → sem line-endings → sem whitespace). A DEC-014 rejeitou isso como padrão (risco de aplicar no lugar errado em silêncio), preferindo erro com dica. Se o uso real mostrar fricção excessiva, considerar `location.allow_whitespace_fuzz: true` por modificação — nunca global, nunca default.

### 2026-06-11 — Anexo de erro pronto para a IA (loop de autocorreção)
Quando `validate`/`apply` falha, oferecer um bloco "copie isto para a IA geradora" contendo: o erro, a âncora/trecho real do arquivo e a referência da regra (§ do guia). Reduz a fricção do loop usuário↔IA que a tabela §6 do guia já habilita. Na GUI, um botão "Copiar erro para a IA".

### 2026-06-10 — Modo estrito opcional no `set_json_path` (`create_missing: false`)
Hoje `set_json_path` cria intermediários ausentes por design (útil para adicionar config nova), mas um typo no caminho (`aip.version`) cria um galho paralelo silenciosamente. Um campo opcional `create_missing: false` permitiria à IA marcar "este caminho DEVE existir" quando a intenção é atualizar valor existente. Default permanece `true` (compatibilidade). Surgiu na auditoria de erros silenciosos.

### 2026-06-10 — Suporte nativo a UTF-16 (se houver demanda)
FIX-002 rejeita UTF-16/32 com erro claro pedindo conversão. Se aparecerem projetos reais com UTF-16 (PowerShell, alguns .resx), implementar leitura/escrita com preservação de BOM e endianness — a detecção de newline já trabalha no texto decodificado, então a base está pronta.

---

## ✅ Concluídas
- **Modo dry run / simulação** — implementado em F1 (`--dry-run`; o `patch_engine` roda toda a lógica em memória e calcula os diffs sem escrever).
- **Modo transação com rollback automático em falha** — implementado em F1 (com `stop_on_error`, qualquer falha reverte tudo via `backup_manager.restore_all`).
- **Validação de unicidade/existência do localizador pré-escrita** — implementado em F1 (cada estratégia confere nº de ocorrências/match e bloqueia com erro acionável antes de gravar; falha de uma modificação não deixa o arquivo pela metade).
- **CLI funcional sem GUI (F1)** — implementado (`python -m src` com `validate`/`apply`/`rollback`).
- **`requirements` em camadas (núcleo sem Qt)** — implementado em F1 (DEC-010): `requirements.txt` + `requirements-gui.txt` + `requirements-dev.txt`.
- **Estratégias de arquivo inteiro (`create_file`/`replace_file`)** — implementadas em F1 (DEC-008): permitem criar um projeto do zero ou fazer patch cirúrgico na mesma instrução.
- **Kit de "ensino" para a IA geradora** — entregue em 2026-06-10 (DEC-012); **v2 autocontida em 2026-06-11** (exemplo embutido, anti-padrões, tabela erro→correção).
- **Modo `self-test`** — entregue em 2026-06-11: `python -m src self-test` aplica a demo em tempdir, confere e reverte.
- **GUI mínima viável (F2)** — entregue em 2026-06-11 (DEC-013): preview/aplicar/desfazer com indicadores derivados do dry-run.

---

## 📮 Feedback para o Kit

> Material que volta para evoluir o Kit de Contexto — o que ESTE projeto observou sobre o próprio kit.

### 2026-06-13 — Ideia de "arquivo de relatório de feedback da IA" — avaliada, recomendação: NÃO criar arquivo dedicado
O usuário perguntou se a IA deveria gerar um arquivo-relatório quando encontrar erros/feedback (reconhecendo que seria "mais um arquivo para popular"). **Análise + pesquisa:** a literatura de agentes valoriza um *trilho de verificação auditável* — mas os sistemas reais (Swarm Orchestrator, etc.) anexam verificação ao fluxo, não criam um doc paralelo que o humano precisa manter. No nosso caso, o canal de feedback **já existe e tem dono**: discrepâncias de aplicação → a IA reporta na conversa e, se for bug da ferramenta, vira FIX no DECISIONS; feedback sobre o próprio kit → esta seção «Feedback para o Kit» do IDEAS; ideias → IDEAS. Um `RELATORIO.md` dedicado seria uma quarta fonte de verdade sobreposta às três, violando a regra de higiene "uma fonte por dado" e o próprio receio do usuário (mais um arquivo para popular). **Recomendação:** não criar. Em vez disso, a §8 do guia já manda a IA reportar discrepâncias no fluxo. SE no futuro o volume de feedback justificar persistência, o lugar natural é uma seção no log da sessão (`logs/AAAA-MM-DD.md`), não um arquivo novo. Registrado aqui para não se reabrir a discussão.

### 2026-06-13 — Kit aplicado a um projeto Windows-first expôs lacuna de CI
Este projeto roda no Windows mas é desenvolvido/testado em container Linux. O FIX-008 (MAX_PATH) passou despercebido por 5 versões porque o CI só roda Linux. Feedback ao kit: para projetos marcados como Windows-first, o kit poderia sugerir no CONTEXT/ROADMAP um lembrete de "rodar a suíte no SO alvo antes de marcar verde". Pequeno, mas teria pego o bug antes do usuário.

## 🚫 Descartadas
- **Localização por número de linha absoluto** — frágil após modificações anteriores no mesmo arquivo; taxa de falha alta em instruções com múltiplas modificações → descartada em DEC-001.
- **ast stdlib para reescrita Python** — não preserva comentários e formatação ao serializar via `ast.unparse()` → descartada em DEC-003.
- **Tkinter como GUI** — aparência datada no Windows; widgets insuficientes para diff colorido → descartada em DEC-005.
- **PyQt6 como GUI** — API idêntica ao PySide6, mas licença GPL mais restritiva → descartada em DEC-005 em favor do PySide6 (LGPL).
- **Integração direta com API da IA** — criaria acoplamento a fornecedor específico e mudaria o escopo da ferramenta (ela consome instruções pré-geradas, não gera) → fora de escopo; pode ser reavaliada em F4+ como feature opcional.
