# spec0009 — Higiene de fechamento: DEC-031 (FlatDrop), sugestão `.docx`, backlog obsoleto e marco de pausa

> **Tipo:** registros/curadoria (meta apenas — SEM código). **Autoria:** chat. **Execução:** Claude Code.
> **Âncoras são SEMÂNTICAS** — trecho literal único, **nunca número de linha**. Localize cada âncora EXATAMENTE; **se não achar uma, PARE e reporte**. Não toque em nada fora das edições nomeadas.
> **Versão-alvo:** nenhuma (não há mudança de código; **não** bumpar, **não** mexer no CHANGELOG).

---

## Contexto

O projeto vai entrar em **pausa de maturação** na 0.8.7 (decisão do usuário, 2026-07-19). Auditoria de fechamento encontrou 4 lacunas de REGISTRO — nenhuma de código, nenhuma quebrada. Elas importam porque, depois de meses parado, quem retomar lê só os `meta/`:

1. **A política de ignore do FlatDrop está ATIVA mas não registrada.** O mount de 2026-07-19 não traz `logs/`, `meta/specs/*` nem `meta/DECISIONS-archive.md`, e o `_MANIFEST.md` lista `.flatdropignore.txt` — ou seja, funcionando. Mas não há DEC, e o IDEAS ainda diz "adoção pendente" (duas fontes divergindo sobre o mesmo fato).
2. **Sugestão do KCM não capturada** (nota `260717-1338.txt`): o template do CEREBRO deveria avisar que o ASU **não cobre `.docx`**. Regra do projeto: ideia nunca se perde.
3. **Backlog obsoleto no STATUS:** o rename `HISTORICO.md` → `HISTORY.md` está `[ ]`, mas o manifesto já mostra `meta/HISTORY.md` — feito.
4. **Falta o marco de pausa** no STATUS, para quem retomar saber que o silêncio é deliberado, não abandono.

---

## Parte A — `meta/DECISIONS.md`: registrar a DEC-031

**Acrescentar ao FINAL do arquivo** (a DEC-030 é a última; append puro, não reescrever nada acima):

```markdown

## DEC-031 — Política de ignore do FlatDrop: logs, specs aplicadas e archive ficam fora do MOUNT (não do git)
**Contexto.** O pacote enviado ao Projeto do Claude (mount) vinha crescendo e chegou a ~186k tokens. Três blocos respondiam por ~28% disso e eram redundantes com os `meta/` canônicos: `logs/` (~22k — e o CEREBRO já dizia que logs não ficam no Projeto, são lidos sob demanda), specs já aplicadas (~25k — cujo desfecho já vive em DECISIONS/CHANGELOG/STATUS) e `meta/DECISIONS-archive.md` (~7,5k — fundacional, consulta rara).
**Decisão.** Adotar um `.flatdropignore` na raiz do repo (arquivo real: **`.flatdropignore.txt`** — nome confirmado funcionando; o mount de 2026-07-19 já sai sem esses blocos) excluindo `logs/`, `meta/specs/*` e `meta/DECISIONS-archive.md`. **Escopo: apenas o MOUNT.** Tudo continua versionado no git e continua sendo lido pelo Claude Code, que tem o repositório inteiro — FlatDrop não é git nem deploy. A spec EM VOO do ciclo corrente é reincluída pontualmente com `!meta/specs/<arquivo>` (por isso o padrão é `meta/specs/*`, e não `meta/specs/`: só assim o `!` consegue reincluir).
**Consequências.** Mount de ~186k → ~132k tokens. **Trade-off aceito:** o chat deixa de conseguir listar `meta/specs/` para checar se uma spec já existe — a salvaguarda contra reautoria (lição das spec0003/0004) passa a apoiar-se em STATUS + CHANGELOG + DECISIONS, que citam cada spec por número. **Risco residual:** se uma spec em voo não for reincluída com `!`, o chat não a enxerga; ao abrir um ciclo novo, descomente/ajuste a linha de reinclusão. O Code não é afetado em nada.
```

## Parte B — `meta/IDEAS.md`: alinhar o status da política (fonte única)

**Âncora (linha única — título da ideia):**

```markdown
### 2026-07-17 — Política de ignore do FlatDrop (logs/specs/archive fora do mount) — ENTREGUE, adoção pendente
```

**Substituir por:**

```markdown
### 2026-07-17 — Política de ignore do FlatDrop (logs/specs/archive fora do mount) — ADOTADA (DEC-031, 2026-07-19)
```

> O corpo da ideia (que descreve o trade-off e os passos pendentes) **fica como está** — é o registro histórico de como se chegou lá. A DEC-031 passa a ser a fonte de verdade do estado atual.

## Parte C — `meta/IDEAS.md`: capturar a sugestão do `.docx` (feedback ao Kit)

**Âncora (bloco literal único — cabeçalho da seção + a linha de intenção):**

```markdown
## 📮 Feedback para o Kit

> Material que volta para evoluir o Kit de Contexto — o que ESTE projeto observou sobre o próprio kit.
```

**Substituir por:**

```markdown
## 📮 Feedback para o Kit

> Material que volta para evoluir o Kit de Contexto — o que ESTE projeto observou sobre o próprio kit.

### 2026-07-17 — O template do CEREBRO deveria avisar que o ASU NÃO cobre `.docx` (sugestão do usuário, via KCM)
Origem: nota `260717-1338.txt`. A diretriz «Saída de código via ASU», que o KCM injeta no CEREBRO dos projetos consumidores, não diz nada sobre os limites de TIPO de arquivo — e um projeto de escrita pode naturalmente tentar apontar o ASU para um `.docx`. **Fato técnico do ASU:** `.docx` é um contêiner ZIP binário; o intake estrito **rejeita arquivo binário** (FIX-006), então a tentativa falha com erro claro — não corrompe nada, mas o usuário só descobre o limite ao esbarrar nele. O ASU cobre texto puro: `.py` (libcst), `.md`, `.json` e **qualquer linguagem** via mecanismo universal `type: text`. **Sugestão ao KCM:** acrescentar à diretriz uma linha do tipo "o ASU edita arquivos de TEXTO; formatos binários/empacotados (`.docx`, `.xlsx`, `.pdf`) não são suportados". Relevante porque o toolchain já é usado em projeto de PROSA (Novelista), onde `.docx` é formato plausível. **Status:** a levar ao KCM (o usuário leva direto; o ASU não altera arquivo de outra frente).
```

## Parte D — `meta/STATUS.md`: fechar o backlog obsoleto

**Âncora (linha única):**

```markdown
- [ ] **Renomear `meta/HISTORICO.md` → `meta/HISTORY.md`** (padrão KCM): ajuste de nome de arquivo no repo (o conteúdo não muda). O Code faz `git mv` na próxima passada; o CEREBRO/painel já referenciam `HISTORY.md`.
```

**Substituir por:**

```markdown
- [x] **Renomear `meta/HISTORICO.md` → `meta/HISTORY.md`** (padrão KCM) — CONCLUÍDO: o `_MANIFEST.md` já lista `meta/HISTORY.md`. (Verificado na auditoria de 2026-07-19.)
```

## Parte E — `meta/STATUS.md`: marco de pausa de maturação

**Âncora (linha única — o cabeçalho da seção):**

```markdown
## 🔧 Em Progresso
```

**Substituir por:**

```markdown
## ⏸️ Pausa de maturação (desde 2026-07-19)
Decisão do usuário: o ASU entra em **pausa deliberada** na **0.8.7** para maturar em uso real, sem novas features. Nada está quebrado; nenhuma fase grande está em aberto (F0/F1 concluídas; F2 com só itens cosméticos; F3 parcial por escolha; F4 é futura). Os itens abaixo, em «Em Progresso», seguem válidos mas **não são bloqueadores** — o principal é a dívida de documentação de usuário (README/GUIA parados na 0.8.2 enquanto o produto está na 0.8.7). Ao retomar: ler o HANDOFF-BRIEF da sessão de 2026-07-19 e rodar o ritual normal. O uso real continua (projeto Novelista) e é a própria fonte de feedback da pausa — se aparecer atrito, ele vira ideia no IDEAS, não correção imediata.

## 🔧 Em Progresso
```

---

## Validação (Code)

- Nenhum código muda. Rodar `python -m src self-test` (sanidade) e conferir o `git diff`: **só** `meta/DECISIONS.md` (+DEC-031 no fim), `meta/IDEAS.md` (título ajustado + 1 entrada nova em Feedback) e `meta/STATUS.md` (1 linha de backlog + 1 seção nova). Nenhuma ideia ou DEC existente pode ter sumido.

## Commit + push (Claude Code)

```
git add meta\DECISIONS.md meta\IDEAS.md meta\STATUS.md && git commit -m "docs: registra DEC-031 flatdrop, captura sugestao docx e marca pausa de maturacao"
```

```
git log origin/main..HEAD --oneline && git push
```

## Pergunta ao usuário (não executar sem resposta)

As specs `260717-spec0007-*.md`, `260717-spec0008-*.md` e `260719-spec0009-*.md` estão **untracked** no repo (o Code sinalizou isso na nota de 07-18). Com a DEC-031, elas ficam fora do mount de qualquer forma — mas versioná-las preserva o histórico de COMO cada mudança foi especificada. Se o usuário confirmar, o passo é:

```
git add meta\specs && git commit -m "docs: versiona specs 0007-0009"
```
