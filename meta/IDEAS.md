# IDEAS.md — Brainstorm e Visão

> **Segundo cérebro** do projeto. Captura TUDO que for mencionado, mesmo solto ou no meio de outro assunto.
> Nunca perde: ideia implementada vai para «Concluídas»; ideia recusada vai para «Descartadas» com o motivo.
> Separar por autor (você × assistente) ajuda a lembrar de onde veio cada coisa.

---

## 💡 Ideias Ativas — Usuário

### 2026-06-28 — Padrão do backup na pasta-PAI da raiz — ACEITA, a implementar (DEC-024c)
O usuário quer que o PADRÃO do ASU seja gerar o backup numa pasta ANTES da raiz (fora do repo), não dentro do projeto. Hoje o padrão é `root/backups/`; passa a ser `parent(root)/backups/<timestamp>/`. CUIDADO de design (já mapeado): NÃO aninhar por `<rootname>` no caso padrão — `parent(root)/<rootname>` É a própria raiz (colisão); usar `parent(root)/backups/<ts>` direto (a pasta-pai já é específica do projeto no layout do usuário). O `rollback` SEM `--backup-dir` precisa procurar no MESMO padrão novo (hoje usa `root`). Edge: raiz sem pai (drive root) → cair para dentro do projeto. Precisa de spec curta + fechar a DEC-024(c). Conecta com o aninhamento por projeto (DEC-024b), que vale para `--backup-dir` externo apontado para uma pasta COMPARTILHADA.

### 2026-06-19 — Onde o ASU dá medo: ESCRITA/ficção em .md/.txt, não código — PREOCUPAÇÃO REGISTRADA (não vira feature)
O usuário esclareceu (corrigindo uma leitura invertida do assistente) qual é o medo real: o ASU é **perigoso para escrita de história/ficção e prosa** em `.md`/`.txt`, porque um erro introduzido por um patch **não é perceptível até alguém ler** — não há nada que sinalize. Já em **código/scripts**, o medo é menor: se o patch quebrar, o **compilador/interpretador sinaliza** (e até aponta a linha), então o erro é cedo ou tarde identificado — não é o ASU que precisa pegá-lo. Inclui o medo de gerar os próprios `meta/*.md` incorretamente. **Decisão explícita do usuário:** NÃO adicionar verificação de sintaxe/compilação ao ASU — seria aumentar (ou mudar) o escopo, e é trabalho do compilador ou da IA que gerou a instrução, não da ferramenta de aplicação. CONFIRMAÇÃO EXTERNA (2026-06-21, txt do KCM): o KCM RETIROU a própria sugestão de checagem de sintaxe, concordando com este raciocínio — duas análises independentes convergindo. O que de fato mitiga o medo de prosa: (1) o **diff colorido** antes de aplicar, (2) a **§8 do guia** (a IA confere o disco na sessão seguinte) e (3) o **backup/rollback**. Não há — nem se quer — automação que julgue se a prosa "ficou certa": isso é revisão (humana/IA). Nota de processo: no fluxo atual, os `meta/*.md` são entregues pelo assistente como **arquivos completos** (o usuário baixa e substitui), NÃO via patch ASU — então esse risco específico não está ativo hoje.

### 2026-06-15 — Subir o PROMPT_IA.md ao projeto e referenciá-lo no CLAUDE.md — ACEITA (a documentar)
Em vez de colar o conteúdo do bloco de prompt em toda conversa, subir o `PROMPT_IA.md` aos arquivos do projeto consumidor e, no CLAUDE.md/instruções desse projeto, mandar a IA "dar uma olhada no PROMPT_IA.md (e no INSTRUCTION_GUIDE.md) para seguir o processo". Assim qualquer atualização é só trocar o arquivo, sem o usuário relembrar nada. É mais prático e recomendado. Falta documentar isso no GUIA/README (Backlog 0.6.0).

### 2026-06-15 — Local do backup junto da instrução + nome com prefixo da raiz — PARCIAL (DEC-018; a parte do NOME por projeto foi SPECADA em 2026-06-28)
O usuário deixa a instrução numa pasta antes da raiz do projeto e gostaria que o backup caísse ali também (fora do projeto), e que a pasta de backup tivesse o nome da raiz como prefixo + algo que a "empurre para o fundo" da listagem (ele brincou com "ZZbackup"). IMPLEMENTADO em 0.6.0: `--backup-dir` resolve o "backup fora do projeto" (pode apontar para a pasta da instrução). EVOLUÇÃO 2026-06-28: a parte do NOME por projeto foi specada (`meta/specs/F3-backup-na-gui.md`) na forma de aninhar `<backup-dir>/<nome-da-raiz>/<timestamp>/` SÓ quando o backup é externo — em vez de prefixar (que alongaria caminhos, MAX_PATH/FIX-008). Sobre "empurrar para o fundo": ponto-prefixo (`.backups`) some no Windows; um prefixo tipo `zz_` é factível se o usuário quiser ordenação visual sobre limpeza — manter em aberto. Nota: dentro de uma `backups/`, a ordenação por timestamp já é cronológica natural.

### 2026-06-15 — Log do rollback/aplicação na pasta da instrução; um arquivo único com todos os timestamps — PARCIAL (DEC-018)
Pedido de um log que caia onde a instrução está, e de um ÚNICO arquivo que incremente com cada timestamp e o que foi feito (em vez de abrir cada pasta de backup). IMPLEMENTADO em 0.6.0: `backups/history.log` é esse arquivo único append-only (timestamp + nº de arquivos + descrição). Combinado com `--backup-dir`, o history fica onde o usuário quiser (inclusive na pasta da instrução). Falta (se o usuário quiser): registrar também os ROLLBACKS no history (hoje só registra aplicações) — pequeno e natural; anotar como refinamento.

### 2026-06-15 — Opção de não gerar / excluir o backup depois — JÁ EXISTE (parcial) + a avaliar
"Seria interessante uma opção para não gerar ou excluir o backup depois?" O `--no-backup` já existe (não gera). FALTA: um comando/flag para LIMPAR backups antigos (ex.: `asu clean-backups --older-than N` ou manter só os últimos K). Útil para não acumular. Avaliar como feature de manutenção.

### 2026-06-15 — Copiar console/saída (não só erro) na GUI, e em massa — EM AVALIAÇÃO
Hoje a GUI tem "Copiar erro para a IA" (só em falha). O usuário quer um "Copiar console/saída" independente de erro (também útil para sucesso) e que funcione "em massa" quando a instrução tem vários blocos/arquivos. Viável: um botão "Copiar saída" que serializa o relatório inteiro (todos os arquivos/modificações, ok e falha) para a área de transferência. Alinha com o "trilho auditável" da pesquisa. Baixo risco.

### 2026-06-15 — Aplicar/desfazer/copiar EM MASSA e SELEÇÃO de blocos na GUI — EM AVALIAÇÃO (possível conflito com o objetivo)
O usuário pergunta se a GUI consegue dry-run/aplicar/desfazer/copiar em massa (instrução com vários scripts) e se daria para SELECIONAR só alguns para aplicar/desfazer. PESQUISA: seleção parcial é padrão consagrado (`git add -p`/`--patch`, seleção por hunk). PORÉM o próprio usuário levantou a ressalva certa: isso pode ir de encontro ao objetivo do ASU — a instrução é uma unidade atômica ("tudo ou nada", DEC pré-existentes); se o processo de geração não erra, selecionar específicos é desnecessário. POSIÇÃO: "aplicar em massa" já É o comportamento (uma instrução com N arquivos aplica os N de uma vez, com rollback atômico). "Selecionar um subconjunto" é o ponto sensível — adiar até o uso real mostrar necessidade; se vier, fazer como OPT-IN explícito que NÃO quebra a atomicidade padrão (ex.: gerar uma sub-instrução com os selecionados, mantendo o backup/rollback do subconjunto). O usuário mesmo disse que o que importa ele já descobriu e vai testar para ver se todas as conversas conseguem usar — então prioridade é o teste de campo, não a seleção.


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

### 2026-06-19 — Validação de sintaxe pós-aplicação (opt-in) — FORA DO FOCO por decisão do usuário; condicional para futuro distante
Proposta original do assistente: reparsear o resultado de uma edição em código e, se não compilar, tratar como falha (rollback). **O usuário decidiu NÃO seguir** — ver a ideia dele de 2026-06-19: adicionar isso aumentaria/mudaria o escopo do ASU, e detectar código quebrado é trabalho do compilador (que sinaliza) ou da IA que gerou a instrução, não da ferramenta de aplicação. Além disso, o medo real do usuário é com PROSA (.md/.txt), onde validação de sintaxe não ajudaria em nada (prosa não compila). CONFIRMAÇÃO EXTERNA (2026-06-21, txt do KCM): o KCM, que havia sugerido a mesma checagem, RETIROU a sugestão pelo mesmo motivo (duplicaria o compilador, mudaria o escopo). Portanto: **não implementar.** Fica registrado apenas como possibilidade condicional e de baixíssima prioridade — reconsiderar SÓ se um dia se mostrar "fácil, prático e recomendado" e sem alargar o escopo. Sem urgência e fora das fases atuais. Mantido aqui (não descartado) para não reabrir a discussão do zero, com o veredito atual claro: não agora.

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
- **Pastas-raiz recentes (até 8) + fixadas na GUI** — implementado em 0.7.0 (spec `meta/specs/F2-acesso-rapido.md`, WI-1): menu "Recentes ▾" + botão 📌, persistidos em QSettings. Era a "página de recentes ou salvas" pedida.
- **Atalho .bat por projeto + args de lançamento da GUI** — implementado em 0.7.0 (DEC-022): botão "Criar atalho .bat…" + `src/gui/launcher.py`; o .bat chama o python do venv direto (sem `activate`), passa a PASTA da instrução (resolvida no topo) e NÃO auto-aplica. (Correção de bug do `%~dp0` + atalho "abrir GUI" specados em 2026-06-28.)
- **Atalho .bat "abrir GUI" (clássico)** — implementado em 0.8.0 (DEC-023): botão "Criar atalho .bat (abrir GUI)…" + `build_open_gui_bat` (`pythonw`+`start /d`, sem console). Validado em campo (`abrir-asu-gui.bat`).
- **Correção do .bat por projeto + endurecimento de encoding** — implementado em 0.8.0 (DEC-023): `--instruction-dir "%~dp0."` (o `%~dp0` cru quebrava o argumento), `chcp` ciente da pasta do .bat, ASCII/UTF-8-sem-BOM. Validado (`abrir-asu-fileview.bat` agora abre apontado).
- **Backup pela GUI + nome por projeto quando externo** — implementado em 0.8.0 (DEC-024 a/b): campo "Backup:" expõe `--backup-dir`; externo aninha `<dir>/<projeto>/<ts>/`; `rollback_from_dir`. (Tornar o PADRÃO a pasta-pai segue em aberto — DEC-024c, ver Ativas.)
- **Política new-file→download (DEC-025)** — DECIDIDO ("fim de papo"): ASU edita arquivos existentes; arquivo novo entrega-se para baixar (exceto bundle com edições). Mensagem ao KCM preparada. O caso do `fileview-instrucao.yaml` (2 chars) é uso CORRETO do ASU (modificação) — o "engraçado" foi gerar a instrução inteira p/ 2 chars, mas é o esperado e bem mais barato que reentregar o arquivo.
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
- **Local do backup configurável (`--backup-dir`)** — entregue em 2026-06-15 (DEC-018): cria `backups/` fora do projeto, mantendo a árvore limpa.
- **Log consolidado de aplicações (`backups/history.log`)** — entregue em 2026-06-15 (DEC-018): um arquivo append-only com timestamp + nº de arquivos + descrição.
- **Checkbox de sandbox na GUI** — entregue em 2026-06-15 (DEC-019): paridade com `--sandbox` do CLI; `make_sandbox` migrado para o core.

## 📮 Feedback para o Kit

> Material que volta para evoluir o Kit de Contexto — o que ESTE projeto observou sobre o próprio kit.

### 2026-06-28 — Diretriz «Saída de código via ASU»: EDITAR (→ASU) vs CRIAR (→baixar) — DECIDIDO (DEC-025); mensagem ao KCM entregue
A diretriz que o KCM injeta (asuMode) diz "entrega mudanças de código como instrução do ASU — não arquivos inteiros … nunca arquivos soltos". Isso está certo para MODIFICAÇÕES e errado para ARQUIVOS NOVOS. Análise (confirmada com o usuário): editar arquivo existente via ASU é econômico (instrução = localizadores + linhas mudadas; mudar 2 chars num arquivo de 100 linhas ≈ 25 linhas de YAML, vs. reentregar o arquivo todo) — é onde o ASU brilha (ex.: o `fileview-instrucao.yaml`, que troca node 20→24 num deploy.yml, é uso CORRETO do ASU). MAS criar arquivo novo via ASU é mais CARO (instrução = arquivo inteiro embutido + esqueleto YAML + caminho, vs. só o arquivo para baixar) e mais FRÁGIL (escape de bloco YAML pode corromper o arquivo), sem ganho de localização. Sintoma real: um projeto, seguindo a diretriz, gerou a instrução no chat para o usuário copiar e criar o arquivo à mão — em vez de entregar para baixar. CAUSA: a diretriz do KCM (não "falta de imposição do ASU"). Mensagem completa para o KCM preparada em `kcm/mensagem-para-o-KCM-uso-do-ASU.md` (entregue ao usuário): reescrever o cabeçalho para "editar→ASU, novo→baixar (exceto create_file em instrução mista)", levar uma linha-gatilho de ASU para a instrução CURTA do painel (que hoje não menciona ASU), e aplicar o `format_version >= 1.0` já acordado. NB: às vezes o usuário PREFERE o arquivo para baixar mesmo numa modificação (para ler pela interface web / testar) — situacional e legítimo; a diretriz só fixa o padrão, sem proibir o contrário.

### 2026-06-22 — Convergência com o KCM (txt "260621-Sugestões do projeto KCM"): retorno da caixa de entrada do HUB
O KCM respondeu ao nosso feedback (é, na prática, um item de caixa de entrada do HUB processado). Pontos, todos CONVERGENTES com o que já tínhamos:
- **Checagem de sintaxe no ASU: o KCM RETIROU a sugestão.** Concordou com o raciocínio do ASU (scope creep; é trabalho do compilador/da IA geradora; o medo real é prosa). Duas análises independentes batendo — bom sinal. (Reflexo aplicado nas duas entradas de 2026-06-19 acima.)
- **Ancorar no `format_version >= 1.0`, não na versão da ferramenta:** o KCM dá endosso FORTE ao nosso "Refinar 2" (o HUB dizer "v0.4.0" é a prova viva). Graduou de "nossa sugestão" para "mudança de contrato acordada entre as frentes" — quando atualizarmos a diretriz ASU/o HUB, ancorar no formato.
- **Sequência (docs 0.6.0 → teste de campo → conveniências):** endossada.
- **Linha pendente no INSTRUCTION_GUIDE** (orientar a IA consumidora a sinalizar limitações do ASU): endossada; fecha o par com a «Feedback para o ASU» (entrada de 2026-06-15 abaixo).
- **Ambiguidade de autoria do HUB:** já resolvida do nosso lado (HUB é gerado pela conversa do KCM — DEC-020/CEREBRO). 

### 2026-06-21 — Atualização "update-code-mode" (CLAUDE→CEREBRO + modo Claude Code): o que observamos
A atualização do KCM introduz o modo Claude Code e renomeia o arquivo de comportamento `CLAUDE.md`→`CEREBRO.md`, reservando `CLAUDE.md` para um ponteiro curto na raiz do repo. Pontos:
- **Bom (manter):** a separação em duas camadas (CEREBRO detalhado em `meta/` × `CLAUDE.md` curto na raiz que o Code lê) é limpa e evita inchar o arquivo que custa token a cada turno do Code. As duas raias (chat AUTORA doc / Code POSICIONA via spec) e o "um canal por doc por ciclo" são uma boa formalização de quem escreve o quê. Os templates dos demais docs não mudarem de estrutura foi acertado (não força regeneração).
- **BUG do template (reportar):** o apêndice de arranque do CEREBRO (e o `wrap.md`) referenciam **`meta/DECISOES.md`** e **`REVISOES.md`** — nomes do nicho **Design Visual**, não do nicho **Desenvolvimento**, que usa `DECISIONS.md` (inglês) e não tem `REVISOES`. Num projeto Dev, copiar o starter literal aponta para arquivos que não existem. Tivemos de corrigir os nomes na adaptação. **Sugestão:** o KCM deveria gerar o starter do Claude Code com os nomes de doc DO NICHO selecionado (Dev → DECISIONS/CHANGELOG/ROADMAP; Design → DECISOES/REVISOES/MARCA), não fixos.
- **Refinar — bootstrap do rename nas Instruções do Projeto:** a atualização renomeia o arquivo, mas as **Instruções do Projeto** (painel, lidas em toda mensagem) continuam citando `CLAUDE.md` — e isso é ajuste MANUAL que o usuário tem de lembrar de fazer no painel. O KCM poderia incluir, no passo de atualização, um lembrete explícito "troque CLAUDE.md por CEREBRO.md também nas Instruções do Projeto", já que o assistente não consegue editar o painel.
- **Refinar — apêndice descartável:** o template diz "depois de criar, pode apagar este apêndice". Funciona, mas deixa o CEREBRO temporariamente inchado com blocos de starter. Como o assistente do chat já entrega os arquivos de arranque prontos, talvez o apêndice devesse ser entregue à PARTE (um doc de setup), não embutido no CEREBRO.

### 2026-06-19 — Integração do switch ASU (asuMode) no KCM: o que ficou bom e o que refinar
O KCM ganhou um switch *asuMode* (opt-in, off por padrão) que injeta a diretriz «Saída via ASU (patch)» no CLAUDE.md gerado, e o próprio switch foi adicionado ao KCM **via uma instrução ASU** (`asu-switch.yaml` — o ASU modificando o KCM; dogfooding real do toolchain). Avaliação:
- **Bom (manter):** a diretriz embutida (C4) APONTA para o `INSTRUCTION_GUIDE`/`PROMPT_IA` em vez de congelar o conteúdo do guia no kit — assim o guia versiona com a ferramenta e o kit não fica desatualizado. É a decisão de acoplamento certa (o kit guarda o gatilho condensado, a verdade do formato fica na frente dona, o ASU). Off-por-padrão e saída byte-idêntica com o switch desligado também é o comportamento correto para uma feature opcional.
- **Refinar 1 — pré-requisito frágil e não verificável:** a diretriz começa com "Pré-requisito: o `INSTRUCTION_GUIDE.md` está no conhecimento do Projeto e a ferramenta ASU está instalada." Isso é uma condição que o kit assume mas não garante. Sugestão ao KCM: quando o switch é ligado, a página do kit deveria LEMBRAR o usuário de subir o `INSTRUCTION_GUIDE.md`/`PROMPT_IA.md` ao Projeto consumidor (talvez listar isso no handoff), senão a IA consumidora recebe a diretriz mas não tem a referência do formato — exatamente o "desentendimento em campo" que o guia v2 já tentou resolver tornando-se autocontido.
- **Refinar 2 — versão do contrato C4 ↔ versão do guia:** o HUB trava C4 dependendo de C2 (`format_version "1.0"`) e apontando para C3 (guia v2, ferramenta v0.4.0 no texto do HUB — JÁ DESATUALIZADO: a ferramenta está em v0.6.0). Sintoma do risco de *drift* que o HUB existe para evitar, mas que ele mesmo sofre por ser cópia manual. Sugestão: quando o kit gera a diretriz ASU, embutir um marcador de versão mínima do formato (`format_version >= 1.0`) em vez de prosa, para a diretriz não precisar ser reescrita a cada bump da ferramenta que não muda o formato.
- **Refinar 3 — a seção de HUB genérica não cabe num HUB de infraestrutura.** O texto que o kit injeta para "Projeto em grupo" descreve um HUB gerado pela página HUB do kit, com exemplos de conteúdo (lore/visual/som). Quando o grupo é um TOOLCHAIN (ferramentas que se sincronizam por contratos, HUB manual), esse texto precisa ser reescrito à mão (foi o que esta sessão fez — DEC-020). Sugestão: o kit poderia oferecer DUAS variantes da seção de HUB — "grupo de conteúdo" (atual) e "toolchain/infra" (contratos + caixas + dono por interface) — ou ao menos generalizar os exemplos para não assumir domínio de conteúdo.

### 2026-06-15 — Esclarecimento: feedback do ASU vindo de OUTROS projetos que o usam (≠ feedback do Kit)
O usuário esclareceu o que quis dizer com "feedback sobre o ASU": é o caso de OUTROS projetos que usam o ASU terem feedback (bugs, sugestões) para melhorar a FERRAMENTA. Como tratar: esse feedback deve ser canalizado de volta a ESTE projeto (o repo do ASU) — vira FIX/DEC/IDEA aqui, conforme a natureza. Mecanismo prático sugerido: quando uma IA num projeto consumidor (seguindo o INSTRUCTION_GUIDE) detectar uma limitação ou bug do ASU durante o uso, ela deve registrar isso de forma que o usuário traga ao repo do ASU (ex.: uma nota no fim da resposta "isto parece limitação do ASU: X"). NÃO é "Feedback para o Kit" (que é sobre o meta-sistema de contexto); é feedback de PRODUTO do ASU, vindo de fora. Isto reforça a DEC-017 com um terceiro vetor: feedback do ASU pode nascer interno (esta conversa) OU externo (projetos consumidores) — ambos terminam como DEC/FIX/IDEA no repo do ASU. Possível item futuro: uma seção no INSTRUCTION_GUIDE orientando a IA consumidora a sinalizar limitações do ASU.


### 2026-06-14 — Distinção de canais: feedback do Kit ≠ feedback do produto (DEC-017)
Esclarecido a pedido do usuário: esta seção «Feedback para o Kit» é SÓ para o meta-sistema (princípios do CLAUDE.md, templates, regras, gatilhos do Kit de Contexto). Feedback sobre o ASU (a ferramenta deste projeto) NÃO entra aqui — flui pelos documentos normais do projeto: bug → FIX no DECISIONS; decisão → DEC; ideia → seções de IDEAS; estado → STATUS. Motivo: o ASU já é o objeto do projeto (tem destinos próprios); o Kit é externo e, sem seção dedicada, seu aprendizado se perderia. Regra prática ao capturar: "isto é sobre a FERRAMENTA ou sobre o SISTEMA QUE ORGANIZA O PROJETO?".

### 2026-06-14 — Demo que escreve no próprio repo é fonte de resíduo (vira armadilha)
O Kit poderia alertar: quando um projeto tem uma DEMO/exemplo que GERA arquivos dentro da própria árvore versionada, esses outputs precisam entrar no `.gitignore` e os testes que copiam a fixture devem limpá-los — senão um resíduo versionado quebra os testes de quem clona (foi o FIX-009 deste projeto). Boa candidata a virar item de checklist do Kit para projetos com demo executável.

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
