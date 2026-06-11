# DECISIONS.md — Registro de Decisões

> Guarda o PORQUÊ — o que o código sozinho não conta.
> Duas naturezas: **DEC** (decisões de arquitetura/design) e **FIX** (bugs graves resolvidos).
> Não reescreva entradas antigas; se uma decisão for substituída, marque «SUPERADA por DEC-N».

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
