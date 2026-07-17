# DECISIONS.md — Registro de Decisões

> Arquivo que **cresce devagar**. Guarda o PORQUÊ — o que o código sozinho não conta.
> Duas naturezas: **DEC** (decisões de arquitetura/design) e **FIX** (bugs graves resolvidos, para não repetir).
> Não reescreva entradas antigas; se uma decisão for substituída, marque «SUPERADA por DEC-N» e adicione a nova.
> Quando passar de ~700 linhas, mova as mais antigas para `DECISIONS-archive.md`.

---

> **Arquivamento (2026-07-03):** as entradas DEC-001..DEC-012 e FIX-001..FIX-006 (fundacionais, F0–F1) foram movidas para `DECISIONS-archive.md` quando este arquivo passou de ~700 linhas. Referências a elas continuam válidas (busque o ID no arquivo-baú). As ativas seguem abaixo, a partir da DEC-013.

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
> **SUPERSEDIDA por DEC-029 (2026-07-15):** o HUB foi descontinuado; mantida aqui como registro histórico.
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
**Data:** 2026-06-28 · **Status:** aceita (implementada completa — a/b/c) · **Origem:** pedidos do usuário (260628: backup fora do repo; nome por projeto; padrão na pasta-pai). Specs: `meta/specs/F3-backup-na-gui.md` (a+b) e `meta/specs/F3-backup-padrao-pai.md` (c, 0.8.1).

### Contexto
O núcleo já fazia backup fora do projeto via `backup_location`/`--backup-dir` (DEC-018), mas a GUI não expunha isso, e o backup nascia como `backups/<timestamp>/` — genérico, misturando projetos quando vários mandam para a mesma pasta externa. No fim da sessão o usuário pediu mais: que o PADRÃO do ASU seja gerar o backup numa pasta ANTES da raiz (fora do repo), não dentro.

### Decisão
- **(a) Expor backup-dir na GUI [implementado]:** linha "Backup:" com `QLineEdit` + "Escolher…" (`_pick_backup_dir`), persistida no `QSettings` (`last_backup_dir`); `apply_changes` passa `backup_location`. Vazio = padrão; preenchido = pasta escolhida.
- **(b) Nome por projeto quando externo [implementado]:** quando o backup vai para fora da raiz, aninhar `<backup_location>/<project_name>/<timestamp>/` (e o `history.log` em `<backup_location>/<project_name>/`). `project_name` = basename da raiz sanitizado (`_sanitize_name`, nome de pasta Windows válido). A lógica de rollback foi extraída para `rollback_from_dir(session_dir)` (aceita o caminho completo da sessão), e `_last_backup` na GUI guarda `(pai_do_session_dir, ts)` → funciona com backup interno e externo. Dentro do projeto, mantém `backups/<timestamp>` (sem aninhar; nome do projeto seria redundante e alongaria caminhos — MAX_PATH/FIX-008).
- **(c) PADRÃO na pasta-pai da raiz [implementado — 0.8.1]:** o padrão do backup é `parent(root)/backups/<timestamp>/`. NÃO aninha por `<rootname>` (colidiria com a própria raiz). `rollback` sem `--backup-dir` procura em `parent(root)`. Edge: raiz sem pai (`parent == root`) → fallback para `root/backups/<ts>`. `_cmd_self_test` usa `rollback_from_dir(Path(report.backup_dir))` (agnóstico à localização).

### Alternativas / cuidado
- **Prefixar cada arquivo/pasta com o nome do projeto** — descartado: alonga todos os caminhos (MAX_PATH). O aninhamento por 1 nível (só quando externo) é mais barato e o espelho já é raso (FIX-008).
- **Aninhar `<rootname>` também no padrão (pasta-pai)** — NÃO: colide com a própria raiz. Por isso o padrão é `parent/backups/<ts>` sem nome.

### Consequências
- (a)+(b) no CHANGELOG 0.8.0 (126 testes). (c) no CHANGELOG 0.8.1 (128 testes); `__version__ = "0.8.1"`.
- O `rollback` default migrou junto com o padrão — CLI e GUI coerentes.

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

---

## DEC-026 — Dicas de âncora "já aplicado?" (substring + presença do new_content), sem ledger
**Data:** 2026-06-30 · **Status:** aceita (implementada) · **Origem:** feedback do VectorForge (260630), spec `meta/specs/F5-hints-ja-aplicado.md`. Referencia [[DEC-014]].

### Contexto
O erro de âncora "casou 0 vez(es)" já tinha a dica de **whitespace** (DEC-014). Faltavam dois diagnósticos comuns: (1) a âncora é **substring** de um identificador maior no arquivo (`doGen(` ⊂ `doGenRandom()`), provável erro de escopo/digitação; (2) a âncora não casa, mas o `new_content`/`content` que a modificação QUER escrever **já está presente** no arquivo — forte sinal de que a modificação já foi aplicada antes. A proposta original de resolver (2) com um arquivo de estado (`.asu-applied.json`, um "ledger") foi REJEITADA — quebraria o ASU *stateless* no projeto-alvo.

### Decisão
- Detecção de "já aplicado" feita **em memória, só no caminho de erro**, comparando o `new_content`/`content` da própria modificação com o conteúdo do arquivo (tolerante a whitespace) — espelha o `patch(1)` do Unix ("reversed/already applied" por inspeção de conteúdo, sem diário). **Nenhum arquivo de estado é criado.**
- Três funções puras novas em `text_strategy.py`: `_substring_hint`, `_already_applied_hint`, agregadas por `_anchor_hints` (que também chama `_whitespace_hint`) — ponto único que as estratégias chamam ao falhar uma âncora.
- `_substring_hint` só dispara para needles com ≥ 4 caracteres úteis (guarda anti-ruído: evita `id`, `(` casando em qualquer lugar).
- Ambas são DICAS anexadas à mensagem de erro existente; a modificação continua sendo rejeitada — o ASU nunca aplica no lugar "parecido" ou já aplicado (filosofia preservada de DEC-014).
- Cobertura: bem suportada em `text`/`pattern`/`context_block`. NÃO cobre `set_json_path`/`append_json_array` (estruturais) nem garante 100% de `replace_function` (libcst) — deixado em aberto para refino futuro (ver IDEAS).

### Consequências
- `text_strategy.py`: `_InsertPattern.apply`/`ReplaceLinePattern.apply` agora levantam erro com dicas já no caminho de 0 matches (antes, esse caminho não tinha `source`/`new_content` em escopo para dar dica nenhuma); `ReplaceContextBlock.apply` troca o `_whitespace_hint` solto pelo agregador.
- `docs/INSTRUCTION_GUIDE.md` §6 ganhou duas linhas novas na tabela erro→correção.
- 133 testes verdes (128 + 5 novos); `ruff` limpo. `__version__` 0.8.2.

---

## DEC-027 — 2ª atualização do KCM: config-no-Code, convenção de spec do KCM, HISTORICO→HISTORY, painel atualizado; DECISIONS arquivado
**Data:** 2026-07-03 · **Status:** aceita · **Origem:** atualização do KCM (conjunto completo de template-updates no mount) + manutenção acumulada aprovada pelo usuário.

### Contexto
O KCM lançou uma segunda atualização, desta vez com o conjunto completo de `*__template-update.md` (não só o CEREBRO) e o `instrucoes-dev__template-update.txt` (o template do painel das Instruções do Projeto). Ao cruzar com o nosso CEREBRO — já bastante alinhado pelas sessões anteriores — o delta real ficou pequeno. Em paralelo, o `DECISIONS.md` passou de 700 linhas (715), gatilho de arquivamento definido no próprio arquivo.

### Decisão
1. **Config-no-Code** na seção «Recomendação de configuração» do CEREBRO: distinguir os controles do chat (modelo + esforço + pensamento, três independentes) dos do Claude Code (modelo + `/effort`/`ultracode`; **sem toggle de pensamento** — usar `ultrathink` no prompt para um turno difícil). Nunca recomendar "ligar pensamento" no Code.
2. **Convenção de nome de specs do KCM** (decisão do usuário): specs seguem `AAMMDD-specNNNN-desc.md` e instruções ASU `AAMMDD-asuNNNN.yaml`; numeração sequencial estável, data de criação. O padrão legado `F<n>-slug.md` (specs F2/F3/F5 já existentes) é mantido como está; o novo vale a partir daqui.
3. **`HISTORICO.md` → `HISTORY.md`** (o kit padronizou o nome em inglês). CEREBRO e painel já referenciam `HISTORY.md`; falta o `git mv` do arquivo no repo (pendência no STATUS).
4. **Painel (Instruções do Projeto) atualizado** com o template novo do KCM: releitura do mount ao sinalizar upload (mesmo sem nomear o arquivo); nome de download simples (`IDEAS.md`, não `meta_IDEAS.md`); config no Code; entrega de `.gitignore` na primeira leva e README quando a estrutura estabiliza.
5. **DECISIONS arquivado:** DEC-001..012 e FIX-001..006 (fundacionais, F0–F1, período 06-03 a 06-10) movidas para `meta/DECISIONS-archive.md`; principal reduzido de 715 → ~346 linhas, mantendo DEC-013..027 + FIX-007/008/009. Numeração preservada (referências apontam por ID).

### Alternativas consideradas
- **Regenerar todos os docs a partir dos templates novos** — descartado: os templates de doc não mudaram de estrutura (nossos são instâncias mais ricas); regenerar só introduziria churn e risco de perder conteúdo do projeto.
- **Manter a nossa convenção `F<n>-slug`** — o usuário optou por seguir o padrão do KCM para alinhamento com o toolchain; legado mantido para não renomear specs já aplicadas.
- **Renomear as entradas ao arquivar / renumerar** — descartado: quebraria as referências cruzadas (DEC-014→DEC-011, etc.); o baú preserva os IDs.

### Consequências
- CEREBRO cresceu ~2 linhas (config-no-Code) e teve a convenção de spec trocada; `HISTORICO`→`HISTORY` numa referência. HUB e seção «Desenvolvimento no Claude Code» preservados na versão rica do projeto (não regredidos ao molde genérico do kit — reforça o Feedback ao Kit de 06-19/06-30 sobre a seção de HUB genérica).
- Documentação de usuário (README/GUIA) saiu da pendência herdada — atualizada nesta sessão.
- Feedback ao Kit registrado (IDEAS): a geração do template-update depende dos modos ligados (a 1ª tentativa saiu com modo errado); a seção de HUB do kit ainda vem no molde de "grupo de conteúdo".

---

## DEC-028 — Canal de warnings: terceiro estado "aplicado com ressalva" (engine + GUI)
**Data:** 2026-07-03 · **Status:** aceita · **Origem:** specs `260703-spec0001-canal-warnings-engine.md` e `260703-spec0002-indicador-amarelo-gui.md` (fase F2). Commits `fd80104` (engine) e `d2e187a` (GUI).

### Contexto
Até aqui o engine era binário por modificação: `strategy.apply()` devolvia a string nova (sucesso) ou levantava `StrategyError` (falha → aborta/reverte). Faltava um terceiro estado para "aplicou, mas com uma ressalva que o usuário deve ver" — casos como `create_file` sobrescrevendo um arquivo existente, ou (futuro) âncora casada por fuzzy de whitespace. Essas ressalvas ou viravam erro (drástico demais) ou passavam caladas (informação perdida). A GUI já tinha 🟢/🔴/⚪ mas o 🟡 não tinha dado que o alimentasse.

### Decisão
Criar um **canal de warnings não-fatais** que sobe pelo engine e chega à GUI, em duas camadas:
1. **Engine (spec0001):** o retorno de `apply()` passa a ser **opcional em tupla** — `str` (como antes) OU `(str, list[str])` quando a estratégia quer avisar. `split_apply_result` normaliza. `ModificationResult.warnings` carrega os avisos; `FileResult.has_warnings`/`ApplyReport.has_warnings` derivam a presença. O laço do engine coleta. **Um piloto** real: `create_file` sobre arquivo existente emite aviso de sobrescrita. O warning NÃO altera `report.ok`, NÃO aborta, NÃO reverte.
2. **GUI (spec0002):** a árvore ganha 🟡 por arquivo (precedência 🔴 > 🟡 > 🟢 > ⚪) e ⚠ por modificação, com os avisos no tooltip. O botão Aplicar permanece habilitado (ressalva não bloqueia). Resumo da barra indica "(N ressalva(s))".

### Alternativas consideradas
- **Mudar a assinatura de `apply()` para sempre retornar tupla** — descartado: quebraria as 13 estratégias e todos os seus testes. O retorno opcional é retrocompatível — estratégias que não avisam continuam devolvendo `str` puro.
- **Emitir warnings em massa nas 13 estratégias já** — descartado: o canal nasce com UM piloto testável; emissões adicionais entram sob demanda, cada uma com seu teste (follow-up no IDEAS).
- **Fazer o 🟡 na GUI primeiro** — impossível: sem o canal produzindo/carregando avisos, o 🟡 não teria o que exibir. Ordem correta: cano (0001) antes da torneira (0002).

### Consequências
- Preserva a filosofia DEC-014 (erro = dica acionável): o warning é o degrau ANTES do erro, para casos onde aplicar é aceitável mas o usuário merece saber. Coexiste com o binário sucesso/erro sem alterá-lo.
- `patch_engine.py` e `base_strategy.py` ganham o mecanismo; `main_window.py` passa a exibir 🟡/⚠. ~11 testes novos (specs 0001+0002); suíte em ~144 funções `test_`, verdes; ruff/black limpos.
- Base para futuras ressalvas (fuzzy de whitespace no caminho de sucesso, `occurrence` implícito, âncora Unicode-adjacente) sem novo encanamento — só emitir.
- `__version__` 0.8.2 → **0.8.3**.

---

## DEC-029 — HUB descontinuado; coordenação entre frentes passa a ser direta (supersede DEC-020)
**Contexto.** O toolchain **KCM · ASU · FlatDrop** era coordenado por um `HUB.md` único (gerado pela conversa do KCM), que registrava contratos entre as frentes e "caixas de entrada" por frente (ver DEC-020, "modo só-HUB").
**Decisão.** Descontinuar o uso do HUB. A troca de informação entre frentes passa a ser **direta** — arquivo ou trecho colado — quando necessária. O **KCM segue sendo usado no ASU** (e projetos que usam o KCM são instruídos a usar o ASU); o **FlatDrop segue** organizando/movendo/subindo os arquivos. Sugestões para o KCM vão ao `IDEAS.md` e/ou são levadas pelo usuário.
**Motivo.** O HUB não vinha de fato sendo usado para coordenar — ficava defasado (chegou a citar a ferramenta em v0.4.0 estando ela em 0.8.x). Um documento de coordenação meio-mantido gera mais confusão do que a sua ausência, e a coordenação de 3 frentes pequenas se resolve bem na mão. Não se automatiza (nem se monitora) o que não está sendo usado.
**Consequências.** O assistente não lê mais o HUB no ritual, não monitora nem aponta "HUB defasado", e não instrui KCM/FlatDrop sobre o HUB. A história é preservada: DEC-020 (e a menção em DEC-021) permanecem como registro — esta DEC apenas as **supersede** na parte operacional. As referências operacionais ao HUB saem dos docs (ver C2–C5).

---

## DEC-030 — Syntax-highlight opcional no diff da GUI via Pygments (degradação graciosa)
**Contexto.** O diff da GUI coloria só por linha (+/-/cabeçalho), sem realce de sintaxe — pendência da F2/ROADMAP. Realce multilíngue à mão seria frágil (o ASU cobre Python, JSON, Markdown e texto universal p/ C#/C++/Java/JSX/TSX/GDScript).
**Decisão.** Adotar **Pygments** como dependência **opcional de GUI** (`requirements-gui.txt`), com o lexer escolhido pelo NOME do arquivo (`fr.path`). Sem Pygments, sem `path`, ou extensão desconhecida → realce só-de-linha antigo (mesmo padrão do colorama no core). Com realce ativo, adição/remoção marcam pelo **fundo** (verde/vermelho claros) e o **foreground** carrega as cores de sintaxe — leem-se as duas dimensões (o que mudou + estrutura do código). O realce é **por linha** (o diff já vem quebrado): construções multilinha não são detectadas — compromisso aceitável num visualizador de diff.
**Consequências.** Núcleo/CLI intactos (mudança só na camada GUI). `_diff_to_html` ganhou `path` opcional (default `None` = comportamento e testes antigos preservados). **Risco a validar VISUALMENTE no Windows:** `background-color` inline em `<span>` dentro do `QTextEdit` pode não renderizar em toda versão do Qt — se não aparecer, trocar o container da linha por `<div style="...">` (sem `<br>` para essas linhas). Não supersede nada; estende a linha de diff da F2.
