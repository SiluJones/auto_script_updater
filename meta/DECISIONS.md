# DECISIONS.md — Registro de Decisões

> Arquivo que **cresce devagar**. Guarda o PORQUÊ — o que o código sozinho não conta.
> Duas naturezas: **DEC** (decisões de arquitetura/design) e **FIX** (bugs graves resolvidos, para não repetir).
> Não reescreva entradas antigas; se uma decisão for substituída, marque «SUPERADA por DEC-N» e adicione a nova.
> Quando passar de ~700 linhas, mova as mais antigas para `DECISIONS-archive.md`.

---

## DEC-001 — Localização por identificador semântico, não por número de linha
**Data:** 2026-06-03 · **Status:** aceita

### Contexto
O arquivo de instrução precisa indicar exatamente onde no arquivo aplicar cada modificação. A opção mais óbvia — número de linha absoluto — é frágil: ao aplicar a modificação M1, que insere 3 linhas na linha 10, todos os números de linha seguintes ficam defasados. Em instruções com 5+ modificações no mesmo arquivo, a taxa de falha é alta.

Isso é confirmado por práticas da indústria: o OpenAI Codex e o GPT-5.1 `apply_patch` usam explicitamente linhas de contexto (código ao redor) para localizar hunks, nunca número de linha absoluto. O `apply-patch-py` (port Python do Codex) usa progressive fallback por contexto com normalização de espaços como contingência.

### Decisão
Modificações são localizadas por identificadores semânticos (nome de função, heading de seção, caminho JSON) ou por janela de contexto (N linhas únicas antes e depois do ponto de modificação). Número de linha absoluto nunca é usado como localizador primário.

### Alternativas consideradas
- **Número de linha absoluto** — simples para IA gerar, mas frágil após qualquer inserção/deleção prévia → descartado.
- **Número de linha + reparse após cada modificação** — mitigaria o drift, mas exige que a IA calcule posições finais com antecedência, o que é propenso a erro → descartado.
- **Hash SHA do bloco alvo** — estável até qualquer edição no bloco exato, útil como verificação secundária, mas não como localizador primário (qualquer edição manual quebra) → aceito como verificação opcional futura, não como localizador.

### Consequências
- A IA deve gerar localizadores semânticos (nomes de funções, headings) ou blocos de contexto únicos.
- O schema de instrução é mais verboso, mas robusto.
- O `patch_engine` precisa de uma strategy por tipo de arquivo.
- Validação de unicidade do localizador deve ocorrer antes de qualquer escrita.

---

## DEC-002 — Padrão Strategy para aplicação de patches por tipo de arquivo
**Data:** 2026-06-03 · **Status:** aceita

### Contexto
A ferramenta suporta múltiplos tipos de arquivo (Python, Markdown, JSON, texto genérico), cada um com mecânicas de localização e substituição distintas. Misturar toda a lógica em `patch_engine.py` tornaria o código rígido e difícil de estender.

### Decisão
Cada tipo de arquivo tem uma `Strategy` dedicada (subclasse de `BaseStrategy`) com a interface:
- `find_location(content: str, location_spec: dict) -> LocationResult`
- `apply(content: str, location_spec: dict, new_content: str) -> str`

O `patch_engine` seleciona a strategy pelo campo `type` do arquivo na instrução e delega.

### Alternativas consideradas
- **If-else no patch_engine** — simples inicialmente, mas escala muito mal → descartado.
- **Plugin dinâmico carregado em runtime** — excessivamente complexo para a fase atual → descartado para F1/F2; revisitar em F4.

### Consequências
- Adicionar suporte a novo tipo de arquivo = criar nova `Strategy` sem tocar no engine.
- Cada strategy pode ser testada de forma completamente isolada.
- Custo: mais arquivos, mais abstração; justificado pelo ganho de extensibilidade.

---

## DEC-003 — libcst para manipulação de arquivos Python
**Data:** 2026-06-03 · **Status:** aceita

### Contexto
Modificar arquivos Python exige parsear e reescrever código. A opção stdlib é `ast`, mas `ast.unparse()` (Python 3.9+) normaliza o código ao serializar: remove todos os comentários, altera espaçamento e pode trocar aspas. O código resultante parece ter sido reformatado por uma ferramenta — inaceitável para arquivos de usuário.

Pesquisa confirmou: libcst (Meta/Instagram) v1.8.6 (novembro 2025) é o padrão da indústria para modificação Python com preservação de formatação. Usado em produção pela Meta, Instawork, SeatGeek, Carta em codebases de 1M+ linhas. Suporta Python 3.0–3.14.

### Decisão
Usar `libcst` para toda modificação estrutural em arquivos `.py`. Ele preserva whitespace, comentários, aspas e espaçamento original ao reescrever apenas os nós alterados.

### Alternativas consideradas
- **ast stdlib** — não preserva comentários → descartado como primário.
- **rope** — focado em refatoração interativa; API diferente do necessário; overhead maior → descartado.
- **Regex puro em arquivos Python** — frágil para estruturas aninhadas (decoradores, funções aninhadas, lambdas) → aceito apenas para estratégias simples de texto (`insert_after_pattern`) mesmo em .py, onde não é necessário parsear a estrutura.
- **RedBaron / Bowler** — deprecados em favor do libcst → descartados.

### Consequências
- Dependência adicional: `libcst` (~5MB instalado, Rust nativo para performance).
- Operações estruturais em Python são robustas e preservam o estilo original.
- Para modificações que não exigem parsear AST (ex: inserir um import), `text_strategy` pode ser usada mesmo em `.py` por simplicidade.

---

## DEC-004 — YAML como formato canônico do arquivo de instrução
**Data:** 2026-06-03 · **Status:** aceita

### Contexto
O arquivo de instrução será gerado pela IA e lido/editado por humanos. Dois requisitos críticos: (1) blocos de código Python/Markdown multiline legíveis sem escapes; (2) possibilidade de comentar modificações no próprio arquivo.

### Decisão
Usar YAML 1.2 como formato canônico do arquivo de instrução. O parser aceita JSON como entrada alternativa válida (JSON é subconjunto de YAML).

### Alternativas consideradas
- **JSON puro** — sem comentários nativos; strings multiline exigem `\n` escapados — 50 linhas de Python no `new_content` ficam ilegíveis → descartado como canônico.
- **TOML** — boa legibilidade para valores simples, mas arrays de objetos complexos (`[[files.modifications]]`) ficam verbosos → descartado.
- **XML** — verboso demais; nenhuma vantagem sobre YAML para este caso → descartado.

### Consequências
- `PyYAML` como dependência (amplamente usada, estável).
- IA deve usar blocos literais YAML (`|`) para `new_content` com código multiline.
- Caminhos Windows com `\` precisam ser escritos como `\\` ou `/` no YAML — armadilha documentada no CONTEXT.
- Ferramenta valida o YAML parseado contra JSON Schema antes de qualquer execução.

---

## DEC-005 — PySide6 como framework GUI
**Data:** 2026-06-03 · **Status:** aceita

### Contexto
A ferramenta precisa de GUI desktop profissional para Windows com: seletor de arquivo/pasta, visualizador de diff com syntax highlight por cores, árvore de arquivos afetados com status, barra de progresso. A GUI precisa ser suficientemente rica para que usuários não-técnicos consigam usar sem terminal.

### Decisão
Usar PySide6 (binding oficial Qt 6 para Python, licença LGPL, mantido pela Qt Company).

### Alternativas consideradas
- **Tkinter** — stdlib, zero dependência, mas aparência datada no Windows e widgets limitados (diff colorido exigiria trabalho extra) → descartado.
- **PyQt6** — API idêntica ao PySide6, mas licença GPL (mais restritiva para distribuição) → descartado em favor do PySide6 (LGPL = sem restrição de distribuição).
- **Flet** — moderno (Flutter-based), visual atraente, mas menos maduro, documentação menor, menos controle sobre widgets de baixo nível → considerado como alternativa para F3+ se PySide6 se provar pesado.
- **Dear PyGui** — GPU-accelerated, bom para ferramentas de dev, mas mais voltado a dashboards técnicos; instalação não-trivial para usuário final → descartado.
- **wxPython** — aparência nativa, LGPL, mas API mais verbosa e ecossistema menor que Qt → descartado.

### Consequências
- Dependência: `PySide6` (~60MB instalado); executável PyInstaller ficará ~80–100MB após UPX.
- Acesso a: `QSyntaxHighlighter` (diff colorido), `QTreeWidget` (árvore de arquivos), `QFileDialog` nativo do Windows, `QProgressBar`.
- Curva de aprendizado moderada; documentação Qt6 excelente; comunidade grande.

---

## DEC-006 — Backup obrigatório antes de qualquer escrita em disco
**Data:** 2026-06-03 · **Status:** aceita

### Contexto
A ferramenta modifica arquivos diretamente no projeto do usuário. Um bug no patch engine ou uma instrução mal-gerada pode corromper arquivos. Sem proteção, uma instrução defeituosa poderia causar perda irreversível de trabalho.

### Decisão
O `backup_manager` copia todos os arquivos listados na instrução para `backups/<YYYYMMDD_HHMMSS>/` antes de qualquer escrita. O rollback restaura a partir desse diretório. O backup só é pulado quando `dry_run: true` (nenhuma escrita ocorre de qualquer forma).

### Alternativas consideradas
- **Confiar no Git do usuário** — usuário pode não ter Git, ou ter arquivos não-commitados → insuficiente como única proteção.
- **Backup opcional via flag** — reduz fricção, mas aumenta risco; segurança não deve ser opt-in → descartado.
- **Cópia para a lixeira do sistema** — API inconsistente entre plataformas; recuperação não-trivial → descartado.

### Consequências
- Execução ligeiramente mais lenta (cópia dos arquivos antes de iniciar).
- Rollback sempre disponível, independente do estado Git do projeto.
- `backups/` deve estar no `.gitignore` do projeto do usuário (ferramenta instrui sobre isso).
- Backups antigos acumulam; F2 deve incluir limpeza automática por política de retenção.

---

## DEC-007 — Versionamento do schema com campo `format_version`
**Data:** 2026-06-03 · **Status:** aceita

### Contexto
O schema do arquivo de instrução vai evoluir. Instruções geradas com versão antiga devem ser identificáveis para receber tratamento adequado (migração automática ou aviso claro). Sem versionamento, incompatibilidades causariam falhas silenciosas ou erros crípticos.

### Decisão
Toda instrução inclui o campo `format_version: "1.0"` no cabeçalho. A ferramenta verifica esse campo na abertura e rejeita versões incompatíveis com mensagem clara. Mudanças incompatíveis incrementam o major (1.0 → 2.0); adições compatíveis incrementam o minor (1.0 → 1.1).

### Alternativas consideradas
- **Sem versionamento** — simples agora, falhas silenciosas no futuro → descartado.
- **Versão no nome do arquivo** — frágil se o arquivo for renomeado → descartado.
- **Versionamento implícito por campos presentes** — frágil, difícil de detectar → descartado.

### Consequências
- Todo gerador de instrução (prompt da IA) deve incluir o campo `format_version: "1.0"`.
- O prompt padrão precisa ser atualizado ao mudar o schema.
- O `instruction_validator.py` verifica `format_version` como primeiro passo, antes de qualquer outra validação.
- Migração de schema (v1 → v2) é item de backlog para F4.

---

## DEC-008 — Estratégias `create_file` e `replace_file` (modos unificados)
**Data:** 2026-06-08 · **Status:** aceita

### Contexto
O consumidor real da ferramenta é o próprio fluxo de transferência de contexto: ao fim de uma sessão, a IA pode emitir uma instrução em vez de entregar código para colar à mão. Esse fluxo tem dois modos: (1) **criar** arquivos/projeto do zero; (2) aplicar **patch cirúrgico** em arquivos existentes. Sem uma estratégia de arquivo inteiro, só o modo (2) seria possível, e o usuário continuaria colando arquivos novos manualmente.

### Decisão
Adicionar duas estratégias ao schema v1: `create_file` (cria arquivo novo a partir de `content`) e `replace_file` (substitui todo o conteúdo por `new_content`). Nenhuma exige `location`. O `file_locator` passa a aceitar a inexistência do arquivo quando *todas* as modificações dele são de criação.

### Alternativas consideradas
- **Só patch (sem criação)** — manteria o copia-e-cola manual para arquivos novos → derrota parte do propósito.
- **Ferramenta separada para scaffolding** — duplicaria parsing/validação/backup → descartado; melhor unificar no mesmo schema e motor.

### Consequências
- Uma única instrução pode criar um projeto inteiro (vários `create_file`) ou fazer um patch fino — mesmo schema, mesmo motor, mesmo backup/rollback.
- `create_file` sobre arquivo existente é tratado como sobrescrita (com backup), tornando a reaplicação de uma instrução idempotente e segura.
- O total de estratégias passa de 11 (F0) para **13**.

---

## DEC-009 — `strategy` como fonte única do `location`; papéis Python explícitos; interface `apply()` única
**Data:** 2026-06-08 · **Status:** aceita · **Refina:** DEC-001, DEC-002

### Contexto
O schema conceitual da F0 (HISTORICO §5) previa um campo `location.type` redundante com o `strategy` (ex.: `strategy: replace_function` + `location.type: function_name`). Redundância gera divergência e bugs (os dois podem discordar). Além disso, a interface conceitual da estratégia (`find_location()` + `apply()`) foi pensada para alimentar o indicador de confiança da GUI antes de aplicar.

### Decisão
1. **Remover `location.type`.** O campo `strategy` é a fonte única de como interpretar `location`. O schema valida o formato de `location` por estratégia via ramos `allOf/if/then`.
2. **Papéis Python explícitos:** `replace_function` (função de módulo; `class_name` opcional para função aninhada em classe), `replace_method` (método; `class_name` **obrigatório**), `replace_class` (classe inteira).
3. **Interface única `apply(source, modification) -> str`** na `BaseStrategy` (localiza e aplica num passo). A pré-checagem de confiança da GUI (🟢/🟡/🔴, F2) será derivada de um **dry-run por modificação** (o `patch_engine` já produz `ModificationResult.ok/error`), evitando duplicar a lógica de localização.

### Alternativas consideradas
- **Manter `location.type`** — mais explícito no papel, mas redundante e propenso a discordar do `strategy` → descartado (princípio "uma fonte de verdade").
- **Manter `find_location()` separado** — necessário se a GUI precisasse localizar sem aplicar; mas o dry-run cobre isso sem duplicação → descartado por ora (revisitar se a GUI exigir granularidade maior).

### Consequências
- Schema mais enxuto e sem estado redundante; menos chance de instrução inconsistente.
- O nome da estratégia carrega semântica suficiente para a ferramenta e para a IA geradora.
- Divergência consciente do schema conceitual da F0: o prompt padrão da IA não deve emitir `location.type`.

---

## DEC-010 — Independência de linguagem via contexto; `requirements` em camadas
**Data:** 2026-06-08 · **Status:** aceita · **Refina:** DEC-003

### Contexto
Pergunta de produto: a ferramenta pode ser "independente do tipo de arquivo ou linguagem"? As estratégias de janela de contexto (`replace_context_block`) e regex operam sobre **texto cru** — funcionam em qualquer linguagem, exatamente como o *apply_patch* da OpenAI localiza por contexto. libcst (Python) e jmespath (JSON) dão precisão semântica, mas são reforços, não requisitos. Além disso, a meta de longo prazo (F4) inclui usar o core como biblioteca pura, sem a dependência pesada do Qt.

### Decisão
1. **Multilinguagem por contexto:** `type: "text"` é o caminho universal; qualquer linguagem usa `replace_context_block`/`*_pattern`. Um campo opcional `language` carrega a linguagem real (para syntax highlight futuro). Localização semântica multilinguagem (tree-sitter) fica para F4.
2. **`requirements` em camadas:** `requirements.txt` (núcleo, sem Qt: PyYAML, jsonschema, libcst, jmespath, colorama) + `requirements-gui.txt` (PySide6) + `requirements-dev.txt` (pytest, pytest-qt, ruff, black). Assim a F1 e os testes rodam leves e o core fica destacável do Qt.

### Alternativas consideradas
- **Exigir parser semântico por linguagem desde já** — inviável para N linguagens; tree-sitter é a via correta, mas é trabalho de F4 → adiado.
- **`requirements.txt` único com Qt** — acoplaria o núcleo ao Qt e pesaria os testes → descartado.

### Consequências
- A ferramenta aceita qualquer linguagem via contexto já na F1; o ponto forte do fluxo é que o mesmo modelo escreve o código e a instrução, então escolhe âncoras de contexto únicas com conhecimento perfeito.
- Instalação mínima (`requirements.txt`) basta para CLI e testes; a GUI é um opt-in (`requirements-gui.txt`).
- Abre caminho limpo para a extensão VS Code / core-as-library da F4.

---

## FIX-001 — Corrupção silenciosa no `replace_context_block` (âncoras duplicadas)
**Data:** 2026-06-10 · **Status:** corrigido

### Sintoma
Ao aplicar uma instrução com `replace_context_block` cujo `new_content` incluía as próprias âncoras `before`/`after`, o arquivo resultante ficava com as âncoras **duplicadas** (ex.: dois `function initApp() {` e duas `}`). O mais grave: o `apply` concluía **sem erro** — uma corrupção silenciosa. Detectado pelo `apply --dry-run` da nova demo, antes de qualquer escrita.

### Causa raiz
Por design (convenção alinhada ao *apply_patch*), em `replace_context_block` as âncoras `before` e `after` são **contexto** e permanecem no arquivo; apenas o conteúdo ENTRE elas (o miolo) é trocado pelo `new_content`. Quando o autor da instrução repete as âncoras dentro do `new_content`, elas são reinseridas — duplicando. A implementação estava correta para sua semântica, mas nada impedia esse erro de uso, e o resultado inválido passava despercebido. Os dois exemplos do repositório (`exemplo_instrucao.yaml` e a demo inicial) cometiam exatamente esse erro.

### Correção
1. **Guarda no código** (`text_strategy.py`): antes de aplicar, detecta a assinatura inequívoca do erro — primeira linha do `new_content` == `before` **e** última linha == `after` — e lança `StrategyError` com mensagem didática (explica que as âncoras permanecem e que o `new_content` deve conter só o miolo). Falso positivo é improvável (exigiria duplicar a âncora de propósito).
2. **Teste de regressão** em `tests/test_strategies.py` (`test_context_block_rejects_anchors_in_new_content`).
3. **Exemplos corrigidos:** `exemplo_instrucao.yaml` e `examples/demo.yaml` passam a usar `new_content` só com o miolo (e `|2` no YAML para preservar a indentação).

### Decisão de design embutida
Manteve-se a convenção A (âncoras preservadas, `new_content` = miolo) em vez de trocar a semântica para "substituir o bloco inteiro incluindo as âncoras". Motivos: alinhamento com o *apply_patch*, coerência com o nome ("context block"), e o fato de que a guarda transforma o erro silencioso em erro alto sem mudar o contrato já documentado. Uma flag opcional `include_anchors` foi registrada como ideia (IDEAS) caso o uso real peça o outro comportamento.

### Lição
Numa ferramenta de patch, **falhar alto é obrigatório**: um resultado errado que não levanta erro é pior que uma exceção. Estratégias devem bloquear quando o resultado provável é inválido.

---

## DEC-011 — Unicidade implícita de localizadores (occurrence ausente exige match único)
**Data:** 2026-06-10 · **Status:** aceita · **Implementa:** Armadilha #5 do CONTEXT

### Contexto
As estratégias por padrão/âncora (`insert_after_pattern`, `insert_before_pattern`, `replace_line_pattern`, `replace_context_block`) aceitavam um localizador que casasse N vezes e, com `occurrence` ausente (default 1), aplicavam na **primeira** ocorrência **silenciosamente**. Num arquivo com `import os` repetido ou duas funções `initApp`, a modificação podia cair no lugar errado sem nenhum sinal — exatamente o cenário que a Armadilha #5 do CONTEXT mandava bloquear, mas que nunca tinha virado código.

### Decisão
Semântica em duas vias, implementada no helper `_resolve_occurrence`:
- **`occurrence` AUSENTE** → o localizador deve ser **único**. Se casa >1 vez, erro de ambiguidade que informa a contagem e ensina a saída ("especifique occurrence (1..N) ou torne o localizador mais específico").
- **`occurrence` PRESENTE** (mesmo `= 1`) → escolha **posicional explícita**: valida apenas o intervalo. Quem escreve `occurrence: 1` está dizendo "a primeira, eu sei que há outras".
A mesma regra vale para a âncora `before` do `replace_context_block`. `replace_section` ganhou regra análoga: heading duplicado → erro (não há `occurrence` para seções).

### Alternativas consideradas
- **Sempre exigir unicidade** (mesmo com occurrence explícito) — quebraria o uso legítimo de posicionamento (ex.: 2ª ocorrência de um marcador repetido) → descartado.
- **Warning em vez de erro** — não existe canal de warning ainda (IDEAS); e silêncio com aviso perdido ainda corrompe → descartado por ora.

### Consequências
- Instruções antes "aceitas" com localizador ambíguo agora são **rejeitadas antes de escrever** — mudança de comportamento (por isso o salto para 0.2.0).
- O prompt/guia da IA geradora deve preferir localizadores únicos e usar `occurrence` apenas quando a repetição é intencional.

---

## FIX-002 — BOM UTF-8 corrompia localização; UTF-16 virava lixo via cp1252
**Data:** 2026-06-10 · **Status:** corrigido

### Sintoma
1. Arquivo UTF-8 **com BOM** (padrão do Visual Studio para `.cs`; comum no Windows): a leitura com `utf-8` decodificava o BOM como o caractere invisível `\ufeff` no início do texto. Consequência: localizadores na primeira linha (`^using System;$`, `^import os$`) **não casavam**, com erro confuso de "padrão não encontrado" — ou pior, modificações no início do arquivo posicionavam conteúdo em relação ao caractere fantasma.
2. Arquivo **UTF-16/32**: `utf-8` falha, mas o fallback `cp1252` "decodifica" qualquer byte — o texto virava lixo com NULs intercalados. Estratégias com localizador falhavam barulhento (ok), mas `replace_file`/`create_file` (sem localizador) **converteriam o encoding do arquivo silenciosamente** para cp1252.

### Causa raiz
`_read_target` não inspecionava BOMs e detectava o estilo de newline nos **bytes crus** (o que também seria errado para UTF-16, onde `\r\n` é `\r\x00\n\x00`).

### Correção (em `patch_engine._read_target`)
- BOM UTF-8 detectado → decodifica com `utf-8-sig` e grava de volta com `utf-8-sig` (**BOM preservado**, roundtrip fiel — teste com `.cs` real).
- BOMs UTF-16 LE/BE e UTF-32 LE/BE → **erro claro** pedindo conversão para UTF-8 (suporte nativo registrado em IDEAS se houver demanda).
- Detecção de newline movida para o **texto decodificado** (correto para qualquer encoding).
- De quebra, o engine passou a capturar erros de leitura/decodificação no fluxo normal de falha por arquivo (status `failed` + stop/rollback) — antes, a exceção **escapava** e derrubava o processo.

### Lição
O fallback permissivo (cp1252 aceita quase qualquer byte) é útil para legado, mas precisa de **portões na frente** (BOMs) para não transformar arquivos ilegíveis em "texto" plausível.

---

## FIX-003 — `replace_section` tratava headings dentro de code fences como seções
**Data:** 2026-06-10 · **Status:** corrigido

### Sintoma
Num markdown com bloco de código contendo `## Algo` (ex.: documentação que mostra exemplos de markdown, README com YAML/markdown embutido), o `replace_section`: (a) podia encontrar o "heading" dentro do fence e substituir a coisa errada; (b) podia **encerrar a seção cedo demais** ao topar com um `## X` fenced — cortando a seção real pela metade, silenciosamente.

### Correção
Rastreio de estado `in_fence` (linhas iniciando com ``` ou ~~~, até 3 espaços de indentação) tanto na **busca do heading** quanto na **detecção do fim da seção**; linhas dentro de fences são invisíveis para a estratégia. Aproveitando, heading duplicado (fora de fences) passou a ser erro de ambiguidade (DEC-011), e a substituição da **última seção** (até EOF) ganhou teste.

### Lição
Markdown "de verdade" carrega código dentro; qualquer parser de estrutura markdown precisa ser fence-aware desde o primeiro dia.

---

## DEC-012 — Kit de ensino para a IA geradora como artefato do produto (docs/)
**Data:** 2026-06-10 · **Status:** aceita

### Contexto
O consumidor real da ferramenta é a IA que gera as instruções. Sem um material que codifique as regras do formato (e as armadilhas descobertas em FIX-001/DEC-011/FIX-002…), cada novo projeto repetiria os mesmos erros de geração — inaceitável para usar a ferramenta como "beta tester" em vários projetos.

### Decisão
Criar e versionar **junto do código** (pasta `docs/`) dois artefatos autocontidos:
- `docs/INSTRUCTION_GUIDE.md` — referência completa: esqueleto, tabela das 13 estratégias, as cinco regras de ouro (miolo sem âncoras; `after` distintivo; ambiguidade sem `occurrence` rejeitada; decoradores no `new_content`; caminhos JSON conferidos), detalhes de YAML/encoding/Windows e checklist de autovalidação.
- `docs/PROMPT_IA.md` — bloco curto pronto para colar nas instruções de qualquer projeto (Claude Project / system prompt), apontando para o guia.
Fluxo de adoção por projeto: copiar o guia para a base de conhecimento + colar o bloco. O guia evolui NO repo da ferramenta (uma fonte de verdade) e os projetos consumidores recebem a versão nova quando atualizarem a cópia.

### Alternativas consideradas
- **Guia dentro do README** — misturaria público (usuário humano × IA geradora) e dificultaria copiar só o necessário → descartado.
- **Prompt gigante único** — um bloco enorme polui o contexto dos projetos; separar referência (sob demanda) de diretiva (sempre presente) é mais econômico → adotado o par guia+bloco.

### Consequências
- Validado por *dogfooding* nesta sessão: instrução escrita seguindo apenas o guia aplicou C# (BOM preservado, `after` no nível certo com aninhamento), Python decorado e TSX, com rollback íntegro.
- Toda regra nova (futuros FIX/DEC que afetem geração) deve ser refletida no guia na mesma sessão.

---

## FIX-004 — JSON era reformatado por inteiro (estilo do original destruído)
**Data:** 2026-06-10 · **Status:** corrigido

### Sintoma
Qualquer modificação JSON reserializava o arquivo com `indent=2` fixo. Um `config.json` com indent=4, tabs ou compacto (uma linha) saía **inteiramente reformatado**: diff explosivo (impossível revisar a mudança real), estilo do projeto destruído e newline final adicionado onde não existia. Silencioso — "funcionava".

### Correção
`_detect_style()` infere do original: indentação (nº de espaços ou tab) pela primeira linha indentada; formato compacto quando não há linha indentada; presença/ausência do newline final. `_dump_json(data, source)` reserializa fielmente. Fonte vazia (arquivo novo) usa o padrão indent=2 + newline. Testes: indent=4, tab, compacto sem `\n` final e vazio.

### Lição
Ferramenta de patch deve tocar **só o que mudou** — também na serialização. Roundtrip fiel é requisito, não cosmética.

---

## FIX-005 — `null` tratado como "não existe" no JSON (delete impossível) + jmespath removido do núcleo
**Data:** 2026-06-10 · **Status:** corrigido

### Sintoma
`delete_json_path` sobre `{"a": null}` falhava com "Caminho 'a' não existe" — era **impossível remover** uma chave de valor `null`. `append_json_array` sobre lista `null` dava a mesma mensagem enganosa.

### Causa raiz
A checagem de existência usava `jmespath.search()`, que retorna `None` tanto para caminho ausente quanto para valor `null` — indistinguíveis.

### Correção
Navegador próprio `_walk(data, tokens)` com sentinela `_MISSING`: ausência ≠ `null`. `delete` remove `null` normalmente; `append` distingue "não existe" de "existe mas vale null" (mensagem orienta usar `set_json_path` primeiro). Como o navegador próprio já cobria 100% do subset de caminhos (`a.b[0].c`), o **jmespath saiu do núcleo** (`requirements.txt` agora: PyYAML, jsonschema, libcst, colorama) — menos uma dependência, alinhado à meta de core como lib pura (F4). Menções em schema/docstrings atualizadas para "caminho pontilhado".

### Lição
Bibliotecas de consulta que sinalizam ausência com `None` são armadilha em JSON, onde `null` é valor legítimo. Sentinela própria resolve.

---

## FIX-006 — Intake endurecido: YAML duplicado, IDs repetidos e arquivo binário
**Data:** 2026-06-10 · **Status:** corrigido

### Sintomas (três silêncios da camada de entrada)
1. **Chave YAML duplicada**: `yaml.safe_load` aceita `files:` definido duas vezes — a primeira **evapora** sem aviso. Numa instrução gerada por IA, metade das mudanças sumiria.
2. **IDs repetidos** (`files[].id` entre arquivos; `modifications[].id` dentro do arquivo): o schema não expressa unicidade; relatórios/diffs ficavam ambíguos e qualquer referência futura por id (GUI, histórico) quebraria.
3. **Arquivo-alvo binário**: cp1252 "decodifica" quase qualquer byte; um `.png`/`.exe` apontado por engano virava "texto", e um `replace_file` o **sobrescreveria** silenciosamente.

### Correção
1. `_StrictLoader` (SafeLoader estendido) rejeita chave duplicada com linha/coluna do YAML.
2. Passo 3 do validator (`_check_unique_ids`) acusa cada duplicata com o índice das duas ocorrências.
3. Guarda no `_read_target`: byte NUL ⇒ erro "parece binário (ou UTF-16 sem BOM)" — pega também UTF-16 sem BOM, complementando o FIX-002.

### Lição
Camada de entrada permissiva é dívida: cada tolerância do parser/validator vira um modo de falha silencioso lá na aplicação. Endurecer cedo, com mensagens que ensinam.

---

## DEC-013 — GUI como camada fina sobre a pilha da F1; confiança via dry-run
**Data:** 2026-06-11 · **Status:** aceita

### Contexto
A F2 pedia uma interface gráfica. O risco clássico é a GUI desenvolver lógica própria (segunda implementação do fluxo) e divergir do CLI.

### Decisão
`src/gui/main_window.py` consome exatamente a mesma pilha do CLI (`instruction_parser → instruction_validator → patch_engine → backup_manager`), sem nenhuma regra de negócio própria: **Pré-visualizar** = `apply_instruction(dry_run=True)`; **Aplicar** = a mesma chamada com escrita; **Desfazer** = `rollback_session` pelo timestamp da última aplicação. O indicador por arquivo (🟢/🔴/⚪) e por modificação (✓/✗) deriva do `ApplyReport`/`ModificationResult` do dry-run, cumprindo o plano da DEC-009. O diff é o `diff_renderer` sem ANSI, colorido via HTML simples. Execução síncrona nesta versão (operações locais e rápidas); worker/thread só se um caso real de lentidão aparecer. Entry point: `python -m src.gui`. Testes offscreen (`QT_QPA_PLATFORM=offscreen`) cobrem o circuito preview→apply→undo e a marcação de falha; `pytest.importorskip` mantém o core testável sem PySide6.

### Consequências
- Zero duplicação de lógica: todo endurecimento do engine (DEC-011, FIX-002…) vale automaticamente na GUI.
- O 🟡 (aviso) entra quando existir canal de warnings no engine (IDEAS).

---

## DEC-014 — Falha com dica acionável; nunca fuzzy matching silencioso
**Data:** 2026-06-11 · **Status:** aceita · **Consolida:** FIX-001, DEC-011; informa o guia (§4.2/§6)

### Contexto
Estudo dos harnesses de patch existentes (apply_patch/V4A da OpenAI, Aider, Claude Code, Cursor): o V4A aplica *fuzzy matching progressivo* (exato → ignora line-endings → ignora whitespace) para tolerar âncoras imperfeitas; o Aider responde com sugestões "did you mean"; o Claude Code exige string exata e única. A falha nº 1 de âncoras geradas por IA é whitespace divergente (espaços × tab, 4 × 8 espaços).

### Decisão
O ASU **não aplica** correspondência aproximada silenciosa (poderia acertar o lugar errado sem sinal — a classe de bug que esta ferramenta combate). Em vez disso, adota o princípio do erro acionável: quando uma âncora (`before`/`after`) não casa exato mas existe trecho equivalente módulo whitespace, o `StrategyError` aponta **a linha** e mostra **a forma exata** do arquivo para o gerador copiar (`_whitespace_hint`). Combinado com a tabela "erro → correção" do guia (§6), isso fecha o loop de autocorreção: a IA geradora corrige a instrução no turno seguinte — mesmo desenho que faz o V4A funcionar, com a segurança do match exato do Claude Code.

### Alternativas consideradas
- **Fuzzy progressivo como o V4A** — máxima conveniência, mas reintroduz aplicação em local potencialmente errado sem aviso → rejeitado como padrão; registrado em IDEAS como possível *opt-in* explícito (`allow_whitespace_fuzz: true`) se o uso real implorar.

### Consequências
- Mensagens de erro são interface de produto: novas falhas comuns devem ganhar dica + linha na tabela §6 do guia.

---

## DEC-015 — Sandbox como cópia irmã visível (`apply --sandbox`)
**Data:** 2026-06-12 · **Status:** aceita · **Origem:** ideia do usuário (workflow de duplicata)

### Contexto
Para os primeiros usos em projetos grandes, o usuário propôs aplicar numa duplicata e só promover o resultado depois de validar. Fazer isso à mão funciona, mas é fricção repetida — e fricção de segurança tende a ser pulada.

### Decisão
Flag `--sandbox` no `apply`: duplica a raiz numa **pasta irmã visível** `<nome>_sandbox_<timestamp>` (não um tempdir autodeletável — o objetivo é inspecionar e comparar com calma), ignorando pesos mortos (`.git`, `node_modules`, venvs, `backups/`, caches, `dist/build`, IDE). Toda a aplicação (prévia, confirmação, backup, rollback) acontece na cópia; ao final, o CLI imprime o caminho e orienta revisar/promover/apagar. **Instruções com `path_mode: absolute` são recusadas** nesse modo: um caminho absoluto escaparia da cópia por definição — recusar é mais honesto que redirecionar magicamente.

### Alternativas consideradas
- **Tempdir autodeletável** — some antes da inspeção → descartado.
- **Redirecionar caminhos absolutos para dentro da sandbox** — reescrita mágica de caminhos é exatamente o tipo de surpresa que o projeto evita → recusar com erro claro.

### Consequências
- O "modo seguro" do README vira um comando; o fluxo manual e o fluxo Git continuam documentados como alternativas.
- Cópia de raízes muito grandes tem custo de disco/tempo mesmo com ignores — aceitável para a fase de confiança; não é o modo padrão.

---

## FIX-007 — GUI: estado entre prévia, aplicação e desfazer (2 bugs da v0.4.0)
**Data:** 2026-06-12 · **Status:** corrigido

### Sintomas
1. **(a) Desfazer com raiz errada:** `undo_last` lia a raiz do CAMPO no momento do clique. Se o usuário trocasse a pasta raiz entre Aplicar e Desfazer, o rollback procurava `backups/<ts>` no lugar errado (FileNotFound na melhor hipótese; em tese, num projeto com backups próprios, reverteria a sessão errada).
2. **(b) Prévia desatualizada aplicada:** `Aplicar` relia a instrução do disco. Editar o YAML (você ou a IA) entre a prévia e o clique aplicava **algo diferente do que foi revisado**, sem aviso — quebra a promessa central do fluxo "revise o diff antes".

### Correção
(a) A aplicação captura `(raiz_usada, timestamp)` no momento de escrever; o Desfazer usa o par capturado, ignorando o campo atual. (b) A prévia registra uma impressão digital SHA-256 de `(raiz + conteúdo da instrução)`; o Aplicar recalcula e, se divergir (ou não houver prévia), bloqueia com aviso e exige nova prévia. Qualquer edição dos campos invalida a prévia (botão Aplicar desabilita). Testes offscreen cobrem os dois cenários.

### Lição
GUI tem ESTADO entre cliques — todo dado usado por uma ação posterior deve ser capturado no momento do compromisso (aplicação), nunca relido da interface, que o usuário pode ter mudado.

---

## FIX-008 — Backup estourava o MAX_PATH no Windows (5 testes + self-test quebrados)
**Data:** 2026-06-13 · **Status:** corrigido

### Sintoma
No Windows, toda aplicação COM backup falhava com `FileNotFoundError: [WinError 3] O sistema não pode encontrar o caminho especificado`. Atingia 5 testes (`test_cli_sandbox_applies_on_copy_not_original`, os 4 de GUI que aplicam de verdade) e o `python -m src self-test` (que reportava "rollback não removeu o arquivo criado", porque a escrita falhava no meio). No Linux/CI tudo passava — o bug era invisível fora do Windows. (Relatado via `260613-console.txt`.)

### Causa raiz
O `backup_manager.mirror_path` espelhava o caminho **absoluto inteiro** do arquivo dentro de `backups/<ts>/`. Ex.: backup de `C:\...\Temp\...\projeto_sandbox_X\cfg.json` virava `...\projeto_sandbox_X\backups\<ts>\Users\alexk\AppData\Local\Temp\...\projeto_sandbox_X\cfg.json`. Esse aninhamento dobra o comprimento do caminho a cada nível; com o `AppData\Local\Temp` do pytest + a pasta `_sandbox_`, passava de 260 caracteres (limite MAX_PATH do Windows, ativo por padrão) e o `mkdir` falhava. No Linux os caminhos de teste (`/tmp/...`) eram curtos demais para atingir qualquer limite — por isso o CI no container nunca pegou. Falha de portabilidade clássica: o teste passava no ambiente errado.

### Correção
O espelho de backup passou a ser **relativo à raiz do projeto** (`backups/<ts>/<caminho_relativo>`), curto e portável. O `BackupManager` recebe a raiz (`root=`) e usa `relative_to`; arquivos fora da raiz (ou `path_mode=absolute`) caem num esquema raso `_abs/<drive>/<resto>` (sem recriar a árvore absoluta inteira). O `manifest.txt` agora grava o caminho-espelho EXPLÍCITO (`estado<TAB>original<TAB>espelho`), eliminando a heurística de recálculo no rollback; o formato antigo de manifesto ainda é lido por retrocompatibilidade. `mirror_path` permanece como função legada só para ler manifestos pré-FIX.

### Lição
Um teste verde no Linux não cobre o limite de caminho do Windows. Para um produto Windows-first, casos sensíveis a caminho (backup, cópia, sandbox) precisam (a) usar caminhos relativos/curtos por princípio e (b) idealmente rodar num CI Windows. Registrado em IDEAS o item de CI Windows.

---

## DEC-016 — Verificação pós-aplicação pela IA: olhar o disco, não o relato
**Data:** 2026-06-13 · **Status:** aceita · **Origem:** ideia do usuário (ideia-260613) + pesquisa

### Contexto
O usuário propôs que, após o usuário aplicar uma instrução ASU e reabrir o projeto numa sessão seguinte, a IA verifique se cada arquivo tocado ficou como esperado — mesmo sem queixa — para pegar discrepâncias nos primeiros pilotos. Antes de aceitar, pesquisei a prática da indústria (princípio "pesquisa para refinar E refutar").

### Evidência (pesquisa 2026-06-13)
A literatura é convergente e forte: agentes de código emitem "linguagem de conclusão" ('apliquei', 'tudo certo') como **padrão de saída, independentemente do estado real** dos arquivos (DEV/CrisisCore, "AI coding agents lie about their work"). A verificação confiável é **outcome-based**: cruzar a afirmação com o **arquivo no disco**, não com a transcrição. ReVeal e TDAD mostram ganho real de geração-com-verificação (TDAD: −70% de regressões surfacing *qual* verificar, vs. piora quando se prescreve processo sem contexto). Conclusão: a ideia do usuário é validada — com a ressalva de que a verificação deve LER o arquivo, não perguntar "deu certo?".

### Decisão
Adicionada a **§8 "Verificação pós-aplicação"** ao `INSTRUCTION_GUIDE.md` e um item ao `PROMPT_IA.md`: quando a IA emitiu uma instrução ASU e, na sessão seguinte, tem os arquivos à vista, deve conferir no disco cada arquivo/modificação tocado antes de seguir; se bateu, uma linha confirma; se não, aponta arquivo+modificação e propõe correção. Sem relatório quando está tudo certo (evita ruído).

### Alternativas consideradas
- **Perguntar ao usuário "funcionou?"** — não pega a discrepância sutil (mudança no lugar errado que o usuário não notou) → insuficiente, descartado como método principal.
- **Verificação automática pela ferramenta (pós-apply)** — a ferramenta já garante que aplicou o que o localizador casou; o que falta verificar é se o resultado é o que o usuário QUERIA (semântico) — isso é trabalho de IA com contexto, não do motor. Mantido no guia, não no código.

### Consequências
- A IA geradora vira parte do loop de verificação nos primeiros usos, onde a confiança se forma.
- A ideia de "arquivo de relatório de feedback" (parte da mesma proposta) foi avaliada à parte — ver IDEAS (recomendação: NÃO criar arquivo dedicado; usar o canal que já existe).

---

## FIX-009 — Artefato gerado pela demo (`health.py`) vazou para o repo e quebrou 4 testes + self-test
**Data:** 2026-06-14 · **Status:** corrigido

### Sintoma
No Windows, `python -m pytest` dava **4 failed, 86 passed** e o `self-test` falhava com "rollback não removeu o arquivo criado". Os 4 testes de GUI falhavam todos no mesmo ponto: após um `preview()` (dry-run), `assert not (demo_root/"src"/"health.py").exists()` dava `assert not True` — ou seja, `health.py` existia quando não deveria. Diferente do FIX-008, o código estava correto (os arquivos subidos eram idênticos aos do container, que passavam); o problema era de ESTADO do repositório.

### Causa raiz
`examples/demo.yaml` CRIA `examples/demo_project/src/health.py` via `create_file`. Numa execução anterior da demo/teste dentro do repo (provavelmente antes do FIX-008, quando o rollback falhava no Windows e não removia o arquivo criado), o `health.py` ficou como **resíduo** em `examples/demo_project/src/` e foi versionado/subido junto. Os testes de GUI e o self-test copiam `demo_project` para um tempdir com `copytree` — copiando o resíduo. Aí o dry-run encontra `health.py` já presente (veio na cópia) e o `assert "não escreveu nada"` falha; no self-test, o `create_file`/rollback se confunde porque o arquivo "já existia". O `.gitignore` ignorava `backups/` mas não os artefatos gerados pela demo. Confirmado: o `health.py` subido é byte a byte o output da `demo.yaml`.

### Correção
Três camadas: (1) `.gitignore` passou a ignorar `examples/demo_project/src/health.py` e `*_sandbox_*/`; (2) a fixture `demo_root` dos testes e (3) o `self-test` removem qualquer artefato gerado pela demo logo após o `copytree` (defesa em profundidade: mesmo que o resíduo volte a vazar, os testes partem de estado limpo). O `health.py` residual foi removido do pacote. Reproduzido o cenário (com o resíduo, o erro é idêntico ao do usuário; com a correção, 90 verdes + self-test OK).

### Lição
Demo que ESCREVE dentro da própria árvore do repo é uma fonte de resíduo: o output precisa estar no `.gitignore` E os testes que copiam a fixture devem limpar o que a demo gera. "Arquivos idênticos mas testes falham" aponta para estado do ambiente (resíduo, cache, caminho), não para o código.

---

## DEC-017 — Dois canais de feedback distintos: Kit (no IDEAS) e ASU (no fluxo do próprio projeto)
**Data:** 2026-06-14 · **Status:** aceita

### Contexto
Pergunta do usuário: o "Feedback para o Kit" (princípio das últimas atualizações do Kit de Contexto) é só para o Kit, ou deveria também haver feedback para o ASU "no embalo"? São coisas diferentes que estavam sendo confundidas por compartilharem a palavra "feedback".

### Decisão
São **dois canais separados, com destinos diferentes**, e ambos existem:

1. **Feedback sobre o KIT DE CONTEXTO** (o meta-sistema: princípios do CLAUDE.md, templates, regras de higiene, gatilhos). Vai para `IDEAS.md` › seção «Feedback para o Kit». É o material que volta para evoluir o Kit que gerou este e outros projetos. Ex.: "o Kit deveria sugerir CI no SO alvo para projetos Windows-first" (registrado).

2. **Feedback sobre o ASU** (o produto deste projeto: a ferramenta, suas estratégias, o kit de ensino da IA, a GUI). NÃO é "feedback de kit" — é trabalho normal do projeto e já tem destinos próprios pelas regras do CLAUDE.md:
   - bug do ASU → **FIX** no `DECISIONS.md` (+ correção no código);
   - decisão de design do ASU → **DEC** no `DECISIONS.md`;
   - ideia/melhoria do ASU → `IDEAS.md` (seções Ativas/Concluídas/Descartadas por autor);
   - estado do ASU → `STATUS.md`; histórico de versão → `CHANGELOG.md`.

Ou seja: o ASU não precisa (nem deve) de um canal de "feedback" paralelo — ele JÁ é o objeto do projeto, então todo feedback sobre ele flui pelos documentos normais. O "Feedback para o Kit" é exclusivo do meta-nível (o Kit), porque esse sim é externo ao projeto e, sem uma seção dedicada, seu aprendizado se perderia.

### Consequência / regra prática
Ao capturar um feedback, perguntar: "isto é sobre a FERRAMENTA (ASU) ou sobre o SISTEMA QUE ORGANIZA O PROJETO (Kit)?". ASU → DEC/FIX/IDEAS/STATUS normais. Kit → «Feedback para o Kit» no IDEAS. Isso evita tanto a duplicação quanto a perda de aprendizado de meta-nível. (Decorre da regra de higiene "uma fonte de verdade por dado".)

---

## DEC-018 — Local do backup configurável (`--backup-dir`) e log consolidado (`history.log`)
**Data:** 2026-06-15 · **Status:** aceita · **Origem:** ideias do usuário (ideia-260614)

### Contexto
Duas dores do usuário com o backup: (1) a pasta `backups/` nascia DENTRO do projeto, poluindo a árvore versionada; ele preferia deixá-la numa pasta-irmã, fora do projeto; (2) para saber o que cada aplicação fez, era preciso abrir cada pasta de timestamp e ler o manifesto — ele queria um arquivo ÚNICO que crescesse com o histórico.

### Decisão
1. **`--backup-dir PASTA`** no `apply` (e no `rollback`): define onde criar a pasta `backups/`. Padrão = raiz do projeto (comportamento anterior preservado). No engine, isso virou o parâmetro `backup_location` de `apply_instruction`, distinto de `root_path`: `root_path` continua sendo a base dos caminhos relativos (e o que encurta o espelho — FIX-008), enquanto `backup_location` é só onde a pasta `backups/` mora. O `rollback` ganhou `--backup-dir` (com `--root` como fallback) para achar a pasta quando ela está fora do projeto.
2. **`backups/history.log`**: um arquivo append-only que ganha uma linha por aplicação (`<timestamp>\t<n> modificado(s), <n> criado(s)>  <descrição da instrução>`). É complementar ao manifesto por sessão (que continua sendo a fonte para o rollback) — o history é só leitura humana cronológica. Implementado como `BackupManager.append_history()`, chamado pelo `patch_engine` ao finalizar uma aplicação real. O CLI imprime o caminho do history após aplicar.

### Alternativas consideradas
- **Mover o backup para fora por padrão** — quebraria projetos existentes e a expectativa de "o backup fica junto"; melhor deixar opcional com padrão atual → adotado opcional.
- **Só o manifesto por sessão (status quo)** — não atende à leitura cronológica rápida; o history não substitui o manifesto, soma a ele → adotados os dois.
- **Prefixo do nome da raiz na pasta de backup** (também pedido) — avaliado mas adiado: a pasta de sessão (`backups/<timestamp>`) já é inequívoca dentro de um projeto, e prefixar o nome da raiz alongaria caminhos (risco no Windows, ligado ao FIX-008) sem ganho real enquanto cada projeto tem sua própria pasta `backups/`. Registrado em IDEAS como ideia condicional (só faria sentido se vários projetos compartilhassem UMA pasta de backup).

### Consequências
- Projeto pode ficar 100% limpo de artefatos da ferramenta (`--backup-dir` fora + o `.gitignore` do FIX-009).
- O `history.log` dá uma trilha de auditoria barata, alinhada à pesquisa de "trilho auditável" (sem virar 4ª fonte de verdade — é derivado, não autoritativo).

---

## DEC-019 — Sandbox movido para o core; checkbox de sandbox na GUI (paridade CLI↔GUI)
**Data:** 2026-06-15 · **Status:** aceita · **Origem:** observação do usuário ("no GUI não vi o sandbox")

### Contexto
O `--sandbox` (DEC-015) só existia no CLI; sua lógica (`_make_sandbox`) vivia em `src/__main__.py` e usava `print`/`SystemExit` — inadequado para a GUI. O usuário notou a falta de paridade. Duplicar a lógica na GUI violaria a DEC-013 (GUI fina, sem regra de negócio própria).

### Decisão
Mover a lógica de sandbox para o core (`patch_engine.make_sandbox` + `SANDBOX_IGNORES` + exceção `SandboxError`), sinalizando erro por EXCEÇÃO em vez de encerrar o processo. O CLI passou a ser um wrapper fino (`_make_sandbox` captura `SandboxError` → stderr + exit 2, preservando o comportamento de linha de comando). A GUI ganhou o checkbox **"Aplicar em sandbox (cópia)"**: quando marcado, o `apply_changes` chama `make_sandbox`, aplica na cópia e reporta o caminho da sandbox no status bar (original intocado). Assim, uma única implementação serve as duas interfaces (cumpre DEC-013).

### Consequências
- Paridade: o modo seguro agora está nas duas interfaces.
- `make_sandbox` testável isoladamente e reutilizável (ex.: futura automação/.bat poderia chamá-lo).
- Lição reforçada: lógica compartilhável mora no core; as bordas (CLI/GUI) só adaptam entrada/saída.

---

## DEC-020 — ASU entra no toolchain via HUB compartilhado, em "modo só-HUB" (sem auto-aplicação do ASU sobre si)
**Data:** 2026-06-19 · **Status:** aceita · **Origem:** sessão de integração do toolchain KCM·ASU·FlatDrop

### Contexto
O ASU deixou de ser um projeto isolado: passou a integrar um toolchain de três ferramentas que se sincronizam — **KCM** (Kit de Contexto Modular, que gera os docs de contexto), **ASU** (este, que aplica patches) e **FlatDrop** (que achata o repo para upload). As três compartilham contratos: o formato da instrução ASU (C2), a referência do formato (`INSTRUCTION_GUIDE`, C3), o manifesto FlatDrop (C1) e uma diretriz ASU que o kit pode injetar no CLAUDE.md de projetos consumidores quando o switch *asuMode* está ligado (C4). Para coordenar isso sem que uma frente quebre a outra em silêncio, há um `HUB.md` — registro dos contratos e das caixas de entrada de cada frente. O HUB é **gerado pela própria conversa do KCM** (não escrito à mão) e existe como **um único arquivo na pasta-raiz comum** aos três projetos (não duplicado dentro de cada repo); opcionalmente versionado junto com o KCM por segurança de histórico.

Duas perguntas precisavam de decisão: (a) o ASU deve adotar o protocolo de HUB no seu CLAUDE.md? (b) o ASU deve usar a si mesmo (instrução ASU) como mecanismo de entrega do próprio código, agora que o switch existe?

### Decisão
1. **Adotar o protocolo de HUB** no CLAUDE.md do ASU: ler o `HUB.md` no ritual de início (após o STATUS), respeitar "não mexer na casa do outro" (toda mensagem a outra frente vira item na caixa dela, assinado `[ASU AAAA-MM-DD]`), e ao encerrar uma sessão que toque o grupo, processar a própria caixa, atualizar o status relâmpago e entregar o `HUB.md` completo (como há um só HUB na raiz comum, a versão nova substitui a anterior — sem cópias a sincronizar repo a repo; em caso de duas frentes gerarem o HUB na mesma janela, faz-se um *merge* canônico via uma das frentes). A seção foi **adaptada** à realidade deste toolchain (HUB de infraestrutura, só-gatilho), não copiada da versão genérica que o kit gera para grupos de conteúdo.
2. **Modo só-HUB (não usar o ASU sobre si):** o CLAUDE.md do ASU recebe a seção de HUB, mas NÃO a diretriz «Saída via ASU (patch)». O ASU continua sendo desenvolvido normalmente (arquivos Python inteiros / zips versionados pela ferramenta de código). A diretriz de saída-via-ASU é para projetos CONSUMIDORES do ASU, não para o repo do ASU. Auto-aplicar o ASU sobre o próprio motor concentraria o risco que o produto existe para mitigar (mudança aplicada sem validação semântica) no lugar mais sensível possível — o código que aplica as mudanças de todo mundo.

### Alternativas consideradas
- **Adotar a seção de HUB genérica do kit, sem adaptar** — descartado: ela fala em "HUB gerado pela página HUB do kit" e dá exemplos de domínio de conteúdo (lore, visual, som). O HUB deste toolchain é explicitamente manual e de infraestrutura; usar o texto genérico criaria descrição falsa do mecanismo.
- **Ligar o switch asuMode também no repo do ASU (dogfooding total)** — sedutor como prova de conceito, mas é decisão do usuário NÃO usar o ASU para atualizar o próprio sistema por ora. O dogfooding do toolchain já acontece em outro nível (o `asu-switch.yaml` foi o ASU modificando o **KCM**, não o ASU modificando o ASU), e concentrar no próprio motor o risco de aplicar mudança sem revisão é o pior lugar para esse risco morar. Reavaliável no futuro, sem urgência.
- **Não criar HUB; coordenar as três frentes ad hoc** — descartado: sem um registro de contratos, uma mudança de `format_version` ou de manifesto se aplicaria calada e quebraria a frente consumidora tarde, quando o conserto é mais caro (risco de *drift* confirmado na literatura de polyrepo).

### Consequências
- O ASU passa a ter uma dependência de processo (ler e manter atualizado o `HUB.md` único na raiz comum) — barata na escala atual (três frentes), a reavaliar se crescer.
- O CLAUDE.md cresceu com a seção de HUB + dois gatilhos novos na tabela + uma linha na lista de fim de sessão; nenhum princípio existente foi removido (mudança aditiva).
- Fica registrado o limite do dogfooding: o ASU pode modificar as OUTRAS frentes do toolchain (fez isso com o KCM), mas não a si mesmo por ora.

---

## DEC-021 — Adoção do modo Claude Code; CLAUDE.md (comportamento) renomeado para CEREBRO.md
**Data:** 2026-06-21 · **Status:** aceita · **Origem:** atualização do KCM ("update-code-mode")

### Contexto
O Kit de Contexto (KCM) lançou uma atualização que introduz um fluxo de desenvolvimento com **Claude Code** (CLI/desktop), além do chat de planejamento. A mudança estrutural: o antigo `CLAUDE.md` (arquivo de COMPORTAMENTO do assistente) passa a se chamar **`CEREBRO.md`**, e o nome `CLAUDE.md` fica reservado para um arquivo-raiz curto, que o Claude Code lê a cada sessão. Os templates dos demais docs (STATUS, CONTEXT, DECISIONS, IDEAS, ROADMAP, GLOSSARY, HISTORICO, CHANGELOG, LOG-TEMPLATE) **não mudaram de estrutura** — continuam idênticos; nossos arquivos já são instâncias mais ricas deles, então não foram regenerados por causa do template (só por conteúdo, como o rename de referências).

### Decisão
1. **Renomear** `meta/CLAUDE.md` → `meta/CEREBRO.md`, preservando todo o conteúdo do projeto (19 princípios, convenções, higiene, e a seção «Projeto em grupo (HUB compartilhado)» da DEC-020). Referências internas a `CLAUDE.md` viraram `CEREBRO.md`.
2. **Adotar o modo Claude Code** com duas raias: o **chat** AUTORA docs (arquivo inteiro p/ reescrita de fundo ou arquivo novo/pequeno; **spec** curta em `meta/specs/`, com texto exato + âncora semântica, p/ delta estruturado em doc grande); o **Code** implementa `src/`/`tests/`, faz edições **append-only** nos `meta/`, aplica as specs, roda a validação e commita. Método "doc por spec": o chat autora, o Code só posiciona; **um canal por doc por ciclo**.
3. **Criar os arquivos de arranque** na raiz do repo: `CLAUDE.md` (ponteiro curto com ritual + comandos de build do ASU), `.claude/settings.json` (permissões: Read/Edit/Grep/Glob, git, `python -m pytest`, `python -m src`, `ruff`, `black`; nega `rm -rf`) e `.claude/commands/` (`apply-spec.md`, `wrap.md`). O apêndice "starter" do template do KCM **não** entra no nosso CEREBRO — os arquivos já foram criados de fato.

### Alternativas consideradas
- **Passar a geração do CEREBRO ao próprio Claude Code (via spec)** — descartado para esta migração: CEREBRO é uma reescrita FUNDAMENTAL (rename + seção nova + curadoria), e o próprio método novo diz que reescrita de fundo é entregue como **arquivo inteiro pelo chat**; specs são para deltas pequenos em docs grandes, e o Code não autora prosa de curadoria. Além disso, o Claude Code ainda não estava configurado nesta sessão (problema de bootstrap).
- **Manter o nome `CLAUDE.md` para o comportamento** — não é opção: a convenção do Claude Code é ler um `CLAUDE.md` curto na raiz; manter o arquivo grande de comportamento com esse nome colidiria com o que o Code espera.
- **Regenerar todos os docs a partir dos templates novos** — descartado: os templates de doc não mudaram; regenerar só introduziria churn e risco de perder conteúdo do projeto (viola "mudança mínima" e a higiene de não encolher em silêncio).

### Consequências
- O comportamento detalhado mora em `meta/CEREBRO.md`; o `CLAUDE.md` da raiz é só o ponteiro curto — duas camadas, sem duplicar regra entre elas.
- A partir da próxima sessão, deltas pequenos em docs grandes (DECISIONS, CONTEXT, ROADMAP) podem ir por **spec** para o Code aplicar, em vez de o chat reentregar o arquivo inteiro — economiza tokens e dá um `git diff` limpo.
- Pendência de configuração fora dos arquivos: as **Instruções do Projeto** (no painel do Projeto, lidas em toda mensagem) ainda referenciam `CLAUDE.md` — precisam apontar para `CEREBRO.md`. Isso é ajuste manual do usuário no painel; não é um arquivo que o assistente entrega.
- Risco a vigiar: o medo já registrado (DEC-020/IDEAS) de o ASU editar `.md` de prosa sem sinalização agora tem um vizinho — o Code fazendo edições append-only nos `meta/`. Mitigação: append-only é de baixo risco (só acrescenta), e o `git diff` é a rede antes de cada commit.

---

## DEC-022 — Acesso rápido a projetos: args de lançamento, `.bat` via python-do-venv, e resolução pasta→instrução
**Data:** 2026-06-22 · **Status:** aceita · **Origem:** pedido do usuário (praticidade: recentes/fixadas + atalho .bat por projeto). Implementação specada em `meta/specs/F2-acesso-rapido.md`.

### Contexto
O usuário trabalha em vários projetos que consomem o ASU e quer reduzir o atrito de abrir a GUI já apontada para cada um. Pediu duas coisas: (a) pastas-raiz recentes/fixadas dentro da GUI; (b) um botão que gere um `.bat` "atalho", colocado na pasta-pai da raiz do projeto, que reabra a GUI com a raiz marcada e a instrução pronta. Surgiram três decisões de design não óbvias.

### Decisão
1. **A GUI passa a aceitar argumentos** (`--root`, `--instruction-dir`, `--instruction`) via `argparse` em `src/gui/__main__.py`, repassados a `run()`/`MainWindow`. Sem argumentos, comportamento idêntico ao atual.
2. **O `.bat` gerado chama `.venv\Scripts\python.exe -m src.gui` DIRETO, sem `call activate`.** Boas práticas de launcher no Windows (Python docs + comunidade): para um atalho que depende de libs do venv, apontar direto para o python do venv é mais robusto que ativar (sem efeitos colaterais de ativação; funciona de atalho/Task Scheduler).
3. **O `.bat` passa uma PASTA de instrução (`--instruction-dir`), não um arquivo**, porque os nomes das instruções mudam (arquivamento). A GUI resolve pasta→arquivo escaneando **só o topo** da pasta (não recursivo): exatamente 1 yaml → pré-preenche; 0 ou 2+ → abre o seletor já posicionado na pasta. Instruções arquivadas em SUBpastas são ignoradas de propósito. Isso responde ao "perigo de ter vários yaml na pasta" sem nunca escolher o errado em silêncio.
4. **Caminhos do `.bat`:** `ASU_HOME` absoluto (a GUI se localiza por `__file__`); `--instruction-dir "%~dp0"` (a própria pasta do `.bat`); `--root` relativo a `%~dp0` quando a raiz é descendente da pasta do `.bat` (caso do exemplo do usuário), senão absoluto — deixa o `.bat` portátil quando o layout permite.
5. **Recentes (até 8) e fixadas** persistem no `QSettings` já usado pela GUI (novas chaves `recent_roots`/`pinned_roots`); um menu "Recentes ▾" + botão "📌" ao lado da raiz.

### Alternativas consideradas
- **Fixar o caminho de um `.yaml` específico no `.bat`** — descartado: os nomes mudam; quebraria no primeiro arquivamento. Daí a PASTA + resolução.
- **`.bat` com `call .venv\Scripts\activate`** (como o usuário esboçou) — funciona, mas é menos robusto que o python-do-venv direto; trocado por D1.
- **Resolver instrução recursivamente / pegar a mais recente por mtime** — descartado: arrastaria as arquivadas das subpastas e poderia escolher a errada; o escaneamento só-do-topo + "1 ou escolha" é previsível e seguro.
- **Auto-aplicar a partir do `.bat`** — jamais: o usuário foi explícito ("não quero que pule o dry e eu checar"). O `.bat` só PRÉ-PREENCHE; o dry-run e a revisão continuam manuais. Mantém a regra de ouro do ASU.

### Consequências
- O ASU ganha uma porta de entrada por projeto sem terminal, sem comprometer a revisão humana.
- `python -m src.gui` deixa de ser argumento-zero — `__main__.py` passa a ter uma camada de CLI fina (mais um ponto a manter, trivial).
- As funções puras (`build_launcher_bat`, `resolve_instruction_in_dir`) são testáveis sem Qt — o grosso da cobertura desta feature mora nelas.
- O gerador de `.bat` saiu da F3 e entrou na F2 (acoplado aos args e às recentes); registrado no ROADMAP.

---

## DEC-023 — Launcher `.bat`: encoding ASCII/UTF-8, correção do `%~dp0` final, `chcp` ciente da pasta do `.bat`, e atalho "abrir GUI" clássico
**Data:** 2026-06-28 · **Status:** aceita (implementada) · **Origem:** aprendizado de campo (`.bat` em ASCII puro) + bug observado (`abrir-asu-fileview.bat` não abria apontado). Specas: `meta/specs/F2-bat-ascii.md`, `meta/specs/F2-bat-fix-e-launcher-classico.md`.

### Contexto
O gerador de `.bat` da DEC-022 (0.7.0) tinha três problemas que só apareceram no uso real no Windows.

### Decisão
1. **Encoding do `.bat`:** caminhos ASCII → `.bat` 100% ASCII (sem BOM, sem `chcp`). Algum caminho com não-ASCII (comum no Windows pt-BR: `Área de Trabalho`, `Café`) → prefixa `chcp 65001 >nul` e grava o arquivo em **UTF-8 SEM BOM** (o `"utf-8"` do Python não emite BOM; `"utf-8-sig"` é proibido — o CMD trata o BOM como parte do 1º comando). **Nunca** usar `errors="replace"` ao gravar (mascararia a corrupção de um caminho acentuado, virando `?`).
2. **BUG do `%~dp0` final (corrigido):** `%~dp0` SEMPRE termina em `\`, então `--instruction-dir "%~dp0"` virava `"...\"` e a sequência `\"` é lida pela análise de linha de comando do C runtime (que o Python usa) como **aspa escapada** → argumento corrompido → a resolução pasta→instrução falhava (e a GUI podia nem abrir apontada). Correção: emitir `--instruction-dir "%~dp0."` (o ponto evita o `\"`; `Path("...\\.")` resolve para a mesma pasta). O `--root "%~dp0fileview"` não sofria (não termina em `\`).
3. **`chcp` ciente da pasta do `.bat`:** como `%~dp0` resolve para a pasta do `.bat` (`bat_dir`) em runtime, o teste `precisa_utf8` passou a incluir `str(bat_dir).isascii()` — senão um `.bat` numa pasta acentuada nasceria ASCII (sem `chcp`) e o CMD lidaria mal com o `%~dp0` acentuado.
4. **Atalho "abrir GUI" (clássico):** novo botão "Criar atalho .bat (abrir GUI)…" + função pura `build_open_gui_bat`, gerando um `.bat` que SÓ abre a interface (sem `--root`/`--instruction`). Usa `pythonw.exe` do venv + `start "" /d "<asu_home>"` — **sem janela de console** e destacado do terminal, com o diretório de trabalho correto para `src` ser importável. Independente de projeto: o usuário salva onde quiser (Área de Trabalho, pasta `launcher`, etc.). Ideia trazida do `flatdrop-ui.bat` do FlatDrop.

### Consequências
- Os dois `.bat` do usuário (`abrir-asu-fileview.bat` com `%~dp0.` e `abrir-asu-gui.bat` clássico) passaram a funcionar.
- Cobertura: testes puros em `tests/test_launcher.py` travam o `%~dp0.` (BUG 1), o `chcp` por `bat_dir` (BUG 2), o atalho clássico (`pythonw`/`start /d`, sem `--root`) e a invariante "ASCII quando os caminhos são ASCII".
- Implementado pelo Claude Code (relatórios 06-28); entra no CHANGELOG 0.8.0.

---

## DEC-024 — Backup pela GUI, aninhamento por projeto quando externo, e PADRÃO na pasta-pai da raiz
**Data:** 2026-06-28 · **Status:** parcial — (a) e (b) implementadas; (c) ACEITA, a implementar · **Origem:** pedidos do usuário (260628: backup fora do repo; nome por projeto; e — fim da sessão — tornar o padrão a pasta-pai). Spec: `meta/specs/F3-backup-na-gui.md` (cobre (a)+(b); (c) precisa de uma spec curta de seguimento).

### Contexto
O núcleo já fazia backup fora do projeto via `backup_location`/`--backup-dir` (DEC-018), mas a GUI não expunha isso, e o backup nascia como `backups/<timestamp>/` — genérico, misturando projetos quando vários mandam para a mesma pasta externa. No fim da sessão o usuário pediu mais: que o PADRÃO do ASU seja gerar o backup numa pasta ANTES da raiz (fora do repo), não dentro.

### Decisão
- **(a) Expor backup-dir na GUI [implementado]:** linha "Backup:" com `QLineEdit` + "Escolher…" (`_pick_backup_dir`), persistida no `QSettings` (`last_backup_dir`); `apply_changes` passa `backup_location`. Vazio = padrão; preenchido = pasta escolhida.
- **(b) Nome por projeto quando externo [implementado]:** quando o backup vai para fora da raiz, aninhar `<backup_location>/<project_name>/<timestamp>/` (e o `history.log` em `<backup_location>/<project_name>/`). `project_name` = basename da raiz sanitizado (`_sanitize_name`, nome de pasta Windows válido). A lógica de rollback foi extraída para `rollback_from_dir(session_dir)` (aceita o caminho completo da sessão), e `_last_backup` na GUI guarda `(pai_do_session_dir, ts)` → funciona com backup interno e externo. Dentro do projeto, mantém `backups/<timestamp>` (sem aninhar; nome do projeto seria redundante e alongaria caminhos — MAX_PATH/FIX-008).
- **(c) PADRÃO na pasta-pai da raiz [a implementar]:** o padrão do backup passa a ser `parent(root)/backups/<timestamp>/`, não `root/backups/...`. **Cuidado de design:** NÃO aninhar por `<rootname>` no caso padrão — `parent(root)/<rootname>` É a própria raiz (colisão); usar `parent(root)/backups/<ts>` direto (a pasta-pai já é específica do projeto no layout do usuário). O `rollback` SEM `--backup-dir` precisa procurar no MESMO padrão novo (hoje usa `root`); manter CLI e GUI coerentes. Edge: raiz sem pai (drive root) → cair para dentro do projeto.

### Alternativas / cuidado
- **Prefixar cada arquivo/pasta com o nome do projeto** — descartado: alonga todos os caminhos (MAX_PATH). O aninhamento por 1 nível (só quando externo) é mais barato e o espelho já é raso (FIX-008).
- **Aninhar `<rootname>` também no padrão (pasta-pai)** — NÃO: colide com a própria raiz. Por isso o padrão é `parent/backups/<ts>` sem nome.

### Consequências
- (a)+(b) no CHANGELOG 0.8.0 (126 testes). (c) é a próxima tarefa de código (spec curta + DEC fechada quando implementar) — ver STATUS.
- Mudar o PADRÃO afeta o `rollback` sem `--backup-dir`: a busca default precisa migrar para a pasta-pai junto, senão o desfazer de CLI não acha o backup novo.

---

## DEC-025 — ASU é para EDITAR arquivos existentes; arquivo NOVO entrega-se para baixar (exceto em instrução mista)
**Data:** 2026-06-28 · **Status:** aceita (política de uso/produto) · **Origem:** análise pedida pelo usuário + decisão dele ("será como vc recomenda… fim de papo"). Mensagem ao KCM em `kcm/mensagem-para-o-KCM-uso-do-ASU.md`.

### Contexto
Surgiu a dúvida se vale usar o ASU para CRIAR arquivos novos. Análise: **modificar** arquivo existente via ASU é econômico (a instrução carrega só localizadores + linhas mudadas; mudar 2 caracteres num arquivo de 100 linhas ≈ 25 linhas de YAML, muito menos que reentregar o arquivo) — é onde o ASU brilha (ex.: o `fileview-instrucao.yaml`, que troca `node 20→24`, é uso CORRETO). Mas **criar** arquivo novo via ASU é mais CARO (a instrução embute o arquivo inteiro no `new_content` + esqueleto YAML + caminho, contra só o arquivo se entregue para baixar) e mais FRÁGIL (escape de bloco YAML `|` pode corromper o arquivo), SEM ganho de localização (não há o que localizar).

### Decisão
- **Editar arquivo existente → ASU** (instrução de patch). **Criar arquivo novo → entregar o arquivo pronto para baixar**, não montar instrução. **Exceção:** quando o arquivo novo faz parte de uma instrução que TAMBÉM altera arquivos existentes — aí `create_file` na mesma instrução se justifica (operação atômica com backup/rollback conjuntos).
- Isto é política de USO (como a ferramenta deve ser recomendada e como a IA consumidora deve se comportar), não muda o código do ASU — a estratégia `create_file` continua existindo (DEC-008) para o caso de bundle e para quem quiser.
- **Reflexo no KCM:** a diretriz «Saída de código via ASU» do kit diz hoje "não arquivos inteiros… nunca arquivos soltos" — manda ASU para tudo, inclusive arquivo novo, e foi por isso que um projeto gerou a instrução no chat para o usuário criar o arquivo à mão. Pedido ao KCM (mensagem entregue): reescrever para "editar→ASU, novo→baixar (exceto bundle)" e levar uma linha-gatilho de ASU para a instrução CURTA do painel (que hoje não menciona ASU). Nota: às vezes o usuário PREFERE o arquivo para baixar mesmo numa modificação (para ler pela interface web / testar) — situacional e legítimo; a política fixa o padrão, sem proibir o contrário.

### Consequências
- Decisão de produto registrada; orienta o GUIA/PROMPT_IA e o feedback ao KCM.
- Nenhuma mudança de código no ASU.
