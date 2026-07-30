# WO 0014 — migrar o vocabulario spec->WO e registrar a integracao do template-update v1.94.0

> **Tipo:** mista (uma acao de repo + edicoes de DOC/registro).
> **Config sugerida:** Sonnet, esforco medio. O diff e exato; o julgamento ja foi feito no chat.
> **Pre-requisito:** 0.9.2, commit `95900aa`, 158 testes verdes, arvore limpa.
> **Base:** template-update do KCM v1.94.0 (mount de 2026-07-30) + decisao do usuario na sessao de 2026-07-30 (DEC-033). A numeracao das WOs continua a serie das specs: a ultima foi `spec0013`, esta e a `wo0014`.
> **Ancora semantica:** se um trecho-ancora nao bater EXATAMENTE, **PARE e reporte** — nunca chute um lugar proximo.
> **Idempotencia:** antes de cada insercao, procure a frase-chave do texto NOVO. Se ja existir, **PULE** o item e diga no relatorio.

> **Canal dos meta neste ciclo = CODE.** Esta WO **E** o registro: aplique os appends previstos e **nao** espere doc do chat para STATUS, DECISIONS, CHANGELOG, IDEAS, GLOSSARY e CONTEXT. O chat entrega, em arquivo inteiro e separado, apenas: `meta/CEREBRO.md`, `CLAUDE.md`, `.flatdropignore.txt`, `meta/SPEC.md`, `meta/workorders/_TEMPLATE.md`, as duas skills e `logs/2026-07-30.md`.

---

## 1. Por que

O KCM v1.94.0 separou dois papeis que este projeto tratava com uma palavra so. Aqui "spec" era a **instrucao de aplicacao** (ancora + texto exato) e nao existia lugar para a **spec de feature** do Spec-Driven Development (o QUE construir e quando esta pronto). Sem separar, um dos dois papeis fica sem nome — e foi decisao do usuario alinhar com o kit, junto dos outros projetos que usam o KCM.

Junto vem uma migracao que **nao e escolha**: `.claude/commands/` e formato descontinuado; o formato atual e `.claude/skills/<nome>/SKILL.md` com front-matter.

## 2. Contexto factual

- **Medido no mount de 2026-07-30:** o repo tem `.claude/commands/apply-spec.md` e `.claude/commands/wrap.md` (confirmado pelo `_MANIFEST` do FlatDrop). Nao existe `.claude/skills/`, nem `meta/workorders/`, nem `meta/SPEC.md`, nem `meta/analises/`.
- **Medido:** a maior instrucao de aplicacao citada nos docs vivos e a `spec0013` (nota de 2026-07-20). Logo, a primeira WO e a `wo0014`.
- **Medido:** `meta/HUB.md` nao existe neste repo — a DEC-029 (2026-07-15) ja havia descontinuado o HUB, duas semanas antes do aviso do KCM de 2026-07-29. Nada a apagar.
- **Medido:** `meta/CHANGELOG.md` esta em CRLF; os outros docs de `meta/` estao em LF.
- **Deduzido:** as referencias a `meta/specs/<arquivo>` em CHANGELOG, ROADMAP, DECISIONS e logs sao texto datado e **nao se corrigem** — a sinalizacao unica entra no CONTEXT (Edicao 1).

---

## Edicao 0 — acao de repo (sem ancora)

Execute na raiz do repo, nesta ordem:

```
git mv meta/specs meta/workorders
```

Depois, coloque os arquivos que o chat entregou (o usuario os baixa e move; se ja estiverem no lugar, apenas confirme):

- `meta/CEREBRO.md` — SUBSTITUI o atual (merge do template v1.94.0 com a versao viva).
- `CLAUDE.md` — SUBSTITUI o atual.
- `.flatdropignore.txt` — SUBSTITUI o atual (formato de bloco do editor do FlatDrop).
- `meta/SPEC.md` — NOVO.
- `meta/workorders/_TEMPLATE.md` — NOVO (entra na pasta recem-renomeada, ao lado das instrucoes historicas).
- `.claude/skills/apply-wo/SKILL.md` — NOVO (crie as duas pastas).
- `.claude/skills/wrap/SKILL.md` — NOVO.
- `logs/2026-07-30.md` — NOVO.

E remova o formato descontinuado:

```
git rm .claude/commands/apply-spec.md .claude/commands/wrap.md
```

Confira que `.claude/commands/` ficou vazia/inexistente e que `.claude/` **nao** esta ignorado no `.gitignore`. Nada mais no `.gitignore` muda.

## Edicao 1 — `meta/CONTEXT.md` · raia atualizada + sinalizacao unica da pasta

**Ancora** (o bullet inteiro, na secao de armadilhas/ambiente):

```
- **Desenvolvimento com Claude Code (desde 2026-06-21, DEC-021):** além do chat de planejamento, o projeto usa o **Claude Code** (CLI/desktop). Duas raias — o **chat** AUTORA docs (arquivo inteiro p/ reescrita; **spec** em `meta/specs/` p/ delta em doc grande); o **Code** implementa `src/`/`tests/`, faz edições **append-only** nos `meta/`, aplica specs, roda validação (`python -m pytest`, `python -m src self-test`, `ruff`, `black`) e commita. O comportamento detalhado está em `meta/CEREBRO.md`; o `CLAUDE.md` da raiz é só o ponteiro curto que o Code lê a cada sessão.
```

**Substituir por:**

```
- **Desenvolvimento com Claude Code (desde 2026-06-21, DEC-021):** além do chat de planejamento, o projeto usa o **Claude Code** (CLI/desktop). Duas raias — o **chat** AUTORA docs (arquivo inteiro p/ reescrita; **WO** em `meta/workorders/` p/ delta em doc grande); o **Code** implementa `src/`/`tests/`, faz edições **append-only** nos `meta/`, aplica WOs, roda validação (`python -m pytest`, `python -m src self-test`, `ruff`, `black`) e commita. O comportamento detalhado está em `meta/CEREBRO.md`; o `CLAUDE.md` da raiz é só o ponteiro curto que o Code lê a cada sessão.
- **Vocabulário WO × spec (desde 2026-07-30, DEC-033) — leia antes de seguir um caminho antigo:** **WO** é a instrução de APLICAÇÃO (âncora + texto exato, `meta/workorders/AAMMDD-woNNNN-desc.md`, comando `/apply-wo`); **spec** é a spec de FEATURE do SDD (o QUE construir, modelo em `meta/SPEC.md`, uma por feature em `meta/specs/`, pasta que renasce no primeiro uso). As 13 instruções `AAMMDD-specNNNN-desc.md` e as legadas `F<n>-slug.md` **mudaram de pasta, não de nome**: estão em `meta/workorders/`. Portanto **toda citação a `meta/specs/<arquivo>` em texto datado** (CHANGELOG, ROADMAP, DECISIONS, logs) **vale para `meta/workorders/<arquivo>`** — esta é a sinalização única; texto datado não se corrige. A numeração é contínua: última spec = `spec0013`, primeira WO = `wo0014`.
```

## Edicao 2a — `meta/STATUS.md` · arranque agora e skills

**Ancora** (linha da secao «Estrutura / Modo Claude Code»):

```
- Novos arquivos de **arranque na raiz do repo**: `CLAUDE.md` (ponteiro curto p/ o Code, com ritual + comandos de build do ASU), `.claude/settings.json` (permissões) e `.claude/commands/` (`apply-spec.md`, `wrap.md`).
```

**Substituir por:**

```
- Novos arquivos de **arranque na raiz do repo**: `CLAUDE.md` (ponteiro curto p/ o Code, com ritual + comandos de build do ASU), `.claude/settings.json` (permissões) e os comandos `/`. **Atualizado 2026-07-30 (DEC-033):** os comandos migraram de `.claude/commands/*.md` (formato descontinuado) para `.claude/skills/apply-wo/SKILL.md` e `.claude/skills/wrap/SKILL.md`, com front-matter; `/apply-spec` passou a `/apply-wo`.
```

## Edicao 2b — `meta/STATUS.md` · raias com vocabulario WO

**Ancora:**

```
- Duas raias: chat AUTORA docs (arquivo inteiro ou **spec** em `meta/specs/`); Code implementa código, faz edições **append-only** nos `meta/`, aplica specs, valida e commita.
```

**Substituir por:**

```
- Duas raias: chat AUTORA docs (arquivo inteiro ou **WO** em `meta/workorders/`); Code implementa código, faz edições **append-only** nos `meta/`, aplica WOs, valida e commita. Um canal por doc por ciclo — a WO declara no cabeçalho se o canal dos meta é CHAT ou CODE.
```

## Edicao 2c — `meta/STATUS.md` · entrada nova de sessao

**Ancora** (o titulo da secao):

```
## 💬 Última Sessão
```

**Inserir IMEDIATAMENTE APOS** a linha da ancora (a entrada de 07-06 continua logo abaixo):

```
**2026-07-30 (chat — 3ª atualização do KCM: template-update v1.94.0; sem código).** Sessão de processo. Comparado o pacote `__template-update` (19 arquivos) contra o vivo, com o estado real do repo lido antes (0.9.2, `95900aa`). **Adotado por decisão do usuário:** (1) **vocabulário WO × spec** — `meta/specs/` → `meta/workorders/` por `git mv`, `/apply-spec` → `/apply-wo`, nomes dos arquivos históricos preservados, numeração contínua (`wo0014`), sinalização única no CONTEXT (DEC-033); (2) **migração obrigatória** `.claude/commands/` → `.claude/skills/<nome>/SKILL.md`; (3) CEREBRO mergeado com as seções novas do kit — «Técnicas específicas deste projeto» (preenchida com as 7 armadilhas reais do ASU), «Análise antes do compromisso» (`meta/analises/`, pasta nasce no primeiro uso), «Ao receber um template-update do KCM», «Bloco de fecho de turno», «Refino das Instruções», 3 regras de higiene novas e as caudas novas dos princípios 1/8/10/11; (4) `.flatdropignore` no formato de bloco do editor do FlatDrop (comentário fora, regra dentro, nada depois do `# <<<`; `logs/` → `logs/*`); (5) `meta/SPEC.md` e `meta/workorders/_TEMPLATE.md` criados; (6) painel refinado (6.172 → 7.255 caracteres, teto 7.450 com o modo Code). **Confirmado:** o HUB já não existia aqui (DEC-029 antecipou o aviso do KCM de 07-29) e o `LOG-TEMPLATE.md` é idêntico ao do kit. **Nada de código mudou** — 0.9.2 e os 158 testes seguem intactos; o repouso de maturação continua. **Próximo:** a dívida nº 1 segue sendo README/GUIA 0.8.6→0.9.2.
```

## Edicao 3 — `meta/DECISIONS.md` · marcador na DEC-021

**Ancora:**

```
**Data:** 2026-06-21 · **Status:** aceita · **Origem:** atualização do KCM ("update-code-mode")
```

**Inserir IMEDIATAMENTE APOS** a linha da ancora:

```
> **VOCABULÁRIO ATUALIZADO por DEC-033 (2026-07-30):** onde esta decisão diz «spec» como instrução de aplicação em `meta/specs/`, leia **WO** em `meta/workorders/`; o comando `/apply-spec` passou a `/apply-wo` e os comandos migraram de `.claude/commands/` para `.claude/skills/`. O resto da decisão segue de pé.
```

## Edicao 4 — `meta/DECISIONS.md` · marcador na DEC-031

**Ancora:**

```
## DEC-031 — Política de ignore do FlatDrop: logs, specs aplicadas e archive ficam fora do MOUNT (não do git)
```

**Inserir IMEDIATAMENTE APOS** a linha da ancora:

```
> **REFINADA por DEC-033 (2026-07-30):** a exclusão `meta/specs/*` passou a `meta/workorders/*` + `!meta/workorders/_TEMPLATE.md` (o modelo sempre sobe), `logs/` passou à forma-conteúdo `logs/*`, e o arquivo foi reorganizado no formato de bloco do editor do FlatDrop. A substância — logs, instruções aplicadas e archive fora do MOUNT, não do git — não mudou.
```

## Edicao 5 — `meta/DECISIONS.md` · nova DEC-033

**Criar ao FIM do arquivo** (append; sem ancora), separada por linha em branco:

```

---

## DEC-033 — Vocabulário WO × spec: as instruções de aplicação mudam de pasta, o nome «spec» passa à spec de feature
**Data:** 2026-07-30 · **Status:** aceita · **Origem:** template-update do KCM v1.94.0; decisão do usuário, alinhada aos demais projetos que usam o kit.

### Contexto
Até aqui «spec» nomeava, neste repo, a **instrução de aplicação** que o chat autora e o Code posiciona (âncora + texto exato), em `meta/specs/AAMMDD-specNNNN-desc.md`, com o comando `/apply-spec` (DEC-021, DEC-027). O KCM v1.94.0 passou a distinguir dois artefatos com papéis diferentes: a **WO** (work order), que diz **como aplicar**, e a **spec de feature** do Spec-Driven Development, que diz **o que** construir e **quando está pronto**. Com uma palavra só para os dois papéis, o segundo não tinha onde morar — e a divergência de vocabulário entre o kit e este repo tornaria confusa toda instrução futura vinda do kit. Somou-se uma migração que não é escolha: `.claude/commands/` é formato descontinuado desde 2026 em favor de `.claude/skills/<nome>/SKILL.md`.

### Decisão
1. **`git mv meta/specs meta/workorders`.** As 13 instruções `AAMMDD-specNNNN-desc.md` e as legadas `F<n>-slug.md` **mudam de pasta, não de nome** — renomear 13 arquivos históricos custaria caro e quebraria a rastreabilidade dos relatórios do Code.
2. **`spec` passa a significar spec de FEATURE** (modelo novo em `meta/SPEC.md`, uma por feature em `meta/specs/`, pasta liberada e que renasce no primeiro uso).
3. **Numeração contínua:** a última instrução de aplicação foi a `spec0013`, então a primeira WO é a **`wo0014`** — a série demonstra continuidade em vez de fingir que o processo começou agora.
4. **Sinalização única, não varredura:** uma nota no `meta/CONTEXT.md` diz que toda citação a `meta/specs/<arquivo>` em texto datado vale para `meta/workorders/<arquivo>`. Referências vivas (CEREBRO, CLAUDE.md, STATUS, `.flatdropignore`, skills) foram atualizadas; texto datado (CHANGELOG, ROADMAP, DECs antigas, logs) **não se corrige** — regra de higiene do carimbo de emissão.
5. **Migração das skills:** `.claude/commands/apply-spec.md` → `.claude/skills/apply-wo/SKILL.md` e `.claude/commands/wrap.md` → `.claude/skills/wrap/SKILL.md`, com front-matter (`name`, `description`, `disable-model-invocation: true`) e a validação do ASU embutida.
6. **`.flatdropignore` no formato de bloco** do editor do FlatDrop: comentário fora e acima, regra dentro de `# >>> flatdrop-editor` … `# <<<`, nada depois do `# <<<`, forma-conteúdo (`pasta/*`) e o par `meta/workorders/*` + `!meta/workorders/_TEMPLATE.md`.
7. **CEREBRO mergeado** com o template v1.94.0, preservando o que este projeto evoluiu (convenção de nome das instruções ASU, escopo das raias, nota «Saída de código deste projeto») e adotando o que faltava — inclusive a seção «Técnicas específicas deste projeto», que é do projeto e **não se sobrescreve** em update futuro.

### Alternativas consideradas
- **Manter o vocabulário do ASU e ignorar a renomeação** (recomendação inicial do chat, com registro de desvio) — descartada pelo usuário: a divergência de vocabulário com o kit é dívida permanente, e a decisão vale para todos os projetos do KCM na mesma situação, não só para este.
- **Renomear também os 13 arquivos históricos** (`spec0007` → `wo0007`) — descartada: custo alto, ganho estético, e quebraria a correspondência com os relatórios de aplicação e as DECs que os citam por nome.
- **Varrer todas as referências a `meta/specs/`** nos docs datados — descartada: contraria a regra de não corrigir texto datado e produziria um diff grande em arquivos históricos. A sinalização única no CONTEXT resolve a navegação.

### Consequências
- O chat e o Code passam a ter **dois artefatos com papéis explícitos**: WO (como aplicar) e spec de feature (o que construir). O funil do CEREBRO fica análise → WO/spec → DECISIONS.
- `meta/specs/` fica **vazia até a primeira spec de feature** — a pasta não é criada por antecipação.
- Quem ler uma DEC ou um CHANGELOG antigo vai ver `meta/specs/`; a nota do CONTEXT é o único lugar que traduz. Se ela for removida, a navegação histórica quebra.
- O `.flatdropignore` passa a ser editável pelo editor do FlatDrop sem perder a explicação (que agora vive fora do bloco).
- Nenhuma linha de código mudou: a 0.9.2 e os 158 testes seguem intactos, e o repouso de maturação continua.
```

## Edicao 6 — `meta/CHANGELOG.md` · entrada em [Nao lancado]

> **ATENCAO: este arquivo esta em CRLF.** Preserve o fim de linha ao inserir; nao converta o arquivo.

**Ancora:**

```
## [Não lançado]
```

**Substituir por:**

```
## [Não lançado]
### Alterado
- **Vocabulário WO × spec e migração das skills (3ª atualização do KCM, template-update v1.94.0 — DEC-033, wo0014).** As instruções de aplicação saíram de `meta/specs/` para **`meta/workorders/`** (`git mv`; nomes preservados, numeração contínua — a próxima é `wo0014`), e o nome «spec» passou a designar a **spec de feature** do SDD (novo modelo `meta/SPEC.md`, uma por feature em `meta/specs/`). Os comandos `/` migraram do formato descontinuado `.claude/commands/*.md` para **`.claude/skills/<nome>/SKILL.md`** com front-matter: `/apply-spec` → **`/apply-wo`**, e `/wrap` atualizado. `meta/CEREBRO.md` foi mergeado com o template do kit (seções novas: «Técnicas específicas deste projeto», «Análise antes do compromisso», «Ao receber um template-update do KCM», «Bloco de fecho de turno», «Refino das Instruções», 3 regras de higiene), o `CLAUDE.md` da raiz ganhou vocabulário, teto de tamanho e seção de config, e o `.flatdropignore` passou ao formato de bloco do editor do FlatDrop. Novo `meta/workorders/_TEMPLATE.md`. **Sem mudança de código** — 0.9.2 e os 158 testes intactos.
```

## Edicao 7a — `meta/IDEAS.md` · ideia do usuario ainda nao capturada

**Ancora:**

```
## 💡 Ideias Ativas — Usuário
```

**Inserir IMEDIATAMENTE APOS** a linha da ancora:

```

### 2026-07-23 — Registrar no backup QUAL instrução o gerou (`history.log` + `manifest.txt`) — ACEITA, a especificar
Pedido do usuário (nota de 07-23, capturada em 07-30): o `history.log` e o `manifest.txt` da sessão de backup deveriam gravar **o nome da instrução** que originou aquele backup. Hoje o par tem timestamp, estado e espelho, mas não a procedência — com várias instruções por projeto, saber qual delas gerou um backup é o que falta para escolher o timestamp certo no rollback. Encaixa na estrutura existente (`backup_manager`): uma coluna/campo a mais no `manifest.txt` e o nome na linha do `history.log`; o rollback antigo tem de continuar lendo manifesto sem o campo (fallback, como no layout `backups/` legado da DEC-032). Toca o backup, que é peça crítica — pede spec de feature (`meta/SPEC.md`) com critério de aceite explícito para o fallback, e um teste de manifesto legado. **Não é bloqueador do repouso.**
```

## Edicao 7b — `meta/IDEAS.md` · retorno do KCM sobre o guia e o prompt

**Ancora:**

```
## 🤖 Ideias Ativas — Assistente
```

**Inserir IMEDIATAMENTE APOS** a linha da ancora:

```

### 2026-07-30 — Três recomendações do KCM sobre o kit de ensino (`PROMPT_IA.md`, guia §0, `demo.yaml`) — ACEITAS em princípio, a implementar
Vieram na nota `260729-RECOMENDACOES-KCM-para-o-ASU.md`. São feedback de PRODUTO do ASU vindo de fora (terceiro vetor da DEC-017), não feedback do kit. (1) **Prioridade alta — `PROMPT_IA.md` conflita com projetos que usam o KCM:** o CEREBRO do kit já traz a diretriz do ASU, curada e divergente em dois pontos (entrega como **arquivo `.yaml` para baixar** em vez de bloco colado no chat; e não emitir comando de execução). Duas instruções concorrentes no mesmo Projeto viram sorteio — e colar YAML no chat é exatamente o que corrompe âncora acentuada, coisa que a §4.7 do próprio guia avisa. Sugerido um cabeçalho de duas linhas dizendo para NÃO colar o bloco quando o projeto usa o kit, subindo apenas o `INSTRUCTION_GUIDE.md`. (2) **§0 do guia assume linha de comando:** tornar o item do comando condicional («só se o usuário aplicar pela CLI») e promover a entrega por arquivo. (3) **`demo.yaml` sem rótulo:** um comentário nas primeiras linhas dizendo que ele é para leitura/teste e **não precisa subir ao Projeto** (a §2 do guia já traz o exemplo completo). Os três são de documentação, cabem numa leva só, e (1) resolve um conflito que já estava acontecendo em silêncio nos projetos consumidores.
```

## Edicao 7c — `meta/IDEAS.md` · feedback para o kit desta integracao

**Ancora:**

```
## 📮 Feedback para o Kit
```

**Inserir IMEDIATAMENTE APOS** a linha da ancora:

```

### 2026-07-30 — 3ª atualização do KCM (template-update v1.94.0): o que funcionou e o que este projeto devolve
**Funcionou bem:** o protocolo novo de update («liste o mount e diga a versão antes de comparar»; «template genérico nunca substitui vivo»; `.claude/commands/` como legado que sempre migra) evitou o modo de falha das levas anteriores — nada foi comparado de memória e nada vivo entrou em risco de ser sobrescrito. A seção «Técnicas específicas deste projeto» resolve uma lacuna real: as armadilhas operacionais do ASU (QSettings real do usuário nos testes, CRLF em âncora multi-linha, `"%~dp0."`) estavam espalhadas pelo DECISIONS, sem um lugar que o assistente lesse por padrão.
**Devolvido ao kit:**
1. **O template-update assume o vocabulário WO como se ele já existisse no destino.** Num projeto que usava «spec» para instrução de aplicação (como este até hoje), o pacote inteiro — `SPEC.md`, `_TEMPLATE.md`, a skill `apply-wo`, o CEREBRO — fala WO sem oferecer o passo de migração. Sugestão: o `_UPDATE-MANIFEST.md` poderia carregar uma linha «renomeações de vocabulário desta versão», do mesmo jeito que carrega o formato descontinuado das skills. Sem isso, cada projeto redescobre o problema e decide sozinho.
2. **A skill vem com o nome do kit, não do projeto.** `apply-wo` é o certo aqui **porque** adotamos WO; se tivéssemos mantido «spec», o nome da skill teria de ser `apply-spec`. Vale uma linha no template dizendo que o nome da skill segue o vocabulário do projeto, não o do kit.
3. **O teto das Instruções do Projeto é em caracteres, e é fácil medir bytes por engano.** Este projeto mediu 6.408 «caracteres» que eram bytes (o painel tinha 6.172 caracteres de verdade — 236 acentos). Num idioma acentuado a diferença é de ~4%, o que é material perto de um teto. Sugestão: dizer explicitamente «caracteres (code points), não bytes».
4. **`meta/analises/` chega com regra, sem gatilho de nascimento observável.** A regra diz «a pasta nasce no primeiro uso», o que é certo — mas o assistente não tem como saber que já deveria ter usado. O gatilho concreto que o próprio kit dá («mudar o formato de um artefato que outra pessoa vai ler ou editar pede análise») é o melhor pedaço da seção e merecia estar na primeira linha, não na sexta.
```

## Edicao 8 — `meta/GLOSSARY.md` · termos novos

**Ancora:**

```
## Identificadores
```

**Inserir IMEDIATAMENTE ANTES** da linha da ancora:

```
- **WO (work order)** — Instrução de APLICAÇÃO que o chat autora e o Code posiciona: âncora semântica + texto exato. Vive em `meta/workorders/AAMMDD-woNNNN-desc.md`; aplica-se com `/apply-wo`. Diz **como aplicar**. Até 2026-07-30 chamava-se «spec» neste repo (DEC-033).

- **Spec de feature** — Documento do Spec-Driven Development que diz **o que** construir e **quando está pronto**: problema, critérios de aceite verificáveis, decisões de design, fora de escopo. Modelo em `meta/SPEC.md`, uma por feature em `meta/specs/`. Não é a WO.

- **Análise** — Documento que precede o compromisso numa mudança não-trivial: problema, restrições medidas, opções (inclusive as descartadas), recomendação, riscos, ponto de decisão. Vive em `meta/analises/AAMMDD-ANALISE-<tema>.md`; a pasta nasce no primeiro uso. Gatilho concreto: mudar o formato de um artefato que outra pessoa vai ler ou editar, mesmo com diff pequeno.

```

---

## Fora de escopo

- **Não** renomear os arquivos históricos dentro de `meta/workorders/` (`spec0001`..`spec0013`, `F<n>-slug.md`).
- **Não** varrer `meta/specs/` nas referências datadas de CHANGELOG, ROADMAP, DECs antigas e logs.
- **Não** criar `meta/specs/` vazia nem `meta/analises/` vazia — ambas nascem no primeiro uso.
- **Não** tocar em `src/`, `tests/`, `docs/` nem `.gitignore`. As três recomendações do KCM sobre `docs/` (Edição 7b) ficam registradas como ideia, não como trabalho deste ciclo.
- **Não** mexer no ROADMAP: nenhuma fase mudou de estado.

## Armadilhas desta WO

- **`meta/CHANGELOG.md` está em CRLF** e os outros `meta/` em LF. Âncora de uma linha (como as desta WO) casa nos dois; texto inserido deve manter o fim de linha do arquivo.
- **A âncora da Edição 3 é a linha de `**Data:**` da DEC-021**, não o título — o título aparece com variações em outros lugares do arquivo. Confira que você está dentro da DEC-021 antes de inserir.
- **Ordem importa na Edição 0:** o `git mv` vem ANTES de colocar `meta/workorders/_TEMPLATE.md`, senão o mv reclama de pasta não vazia.
- **`.flatdropignore.txt` mantém o nome com `.txt`** (é o nome real no repo, confirmado funcionando na DEC-031). Não renomeie para `.flatdropignore`.
- **Idempotência:** se o repo já tiver `meta/workorders/`, o `git mv` falha — nesse caso PARE e reporte em vez de forçar.

---

## Depois de aplicar — conferencia antes do commit

- [ ] `git diff` (e `git status`) mostram **exatamente**: o rename de `meta/specs/` → `meta/workorders/`, a remoção dos dois arquivos de `.claude/commands/`, os arquivos novos/substituídos da Edição 0, e as edições em `CONTEXT.md`, `STATUS.md`, `DECISIONS.md`, `CHANGELOG.md`, `IDEAS.md`, `GLOSSARY.md`. Nada além.
- [ ] O rename aparece como **rename** no git (não como delete+add), preservando o histórico dos arquivos históricos.
- [ ] `grep -rn "apply-spec" .` não retorna nada fora de texto datado (CHANGELOG, DECs antigas, logs).
- [ ] `grep -rn "meta/specs" meta/CEREBRO.md CLAUDE.md .flatdropignore.txt` só retorna as menções deliberadas à pasta de **specs de feature**.
- [ ] `meta/DECISIONS.md` tem uma única DEC-033, e os dois marcadores `>` entraram nas DECs certas (021 e 031).
- [ ] **WO só de doc + um rename:** não precisa de build. Ainda assim, rode `python -m src self-test` uma vez — é barato e prova que o rename não tocou nada importável.
- [ ] **Teste manual que a validação não cobre:** abrir o Claude Code no repo e digitar `/apply-wo` e `/wrap` — as duas skills têm de aparecer com a descrição do front-matter. Se não aparecerem, o problema é o caminho (`.claude/skills/<nome>/SKILL.md`, uma pasta por skill), não o conteúdo.

## Relatorio de aplicacao *(quem aplica preenche ao terminar)*

O que foi feito · o que fugiu do texto literal da WO · arquivos tocados · resultado da validacao · o commit.

## Commit — blocos separados, mensagem SEM acento

```
git add -A
```

```
git commit -m "refactor(meta): renomeia specs para workorders e migra comandos para skills" -m "Adota o vocabulario do KCM v1.94.0: WO e a instrucao de aplicacao (meta/workorders/), spec passa a ser spec de feature (meta/SPEC.md). Arquivos historicos mudam de pasta, nao de nome; numeracao continua em wo0014. Comandos /apply-spec e /wrap migram de .claude/commands para .claude/skills com front-matter. CEREBRO mergeado com o template v1.94.0 e flatdropignore no formato de bloco. Ver DEC-033. Sem mudanca de codigo."
```

```
git push
```
