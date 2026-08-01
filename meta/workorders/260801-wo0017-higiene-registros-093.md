# WO 0017 — higiene de registros pos-0.9.3 e feedback do gatilho de analise ao KCM

> **Tipo:** DOC (meta/ + docs de usuario).
> **Config sugerida:** Sonnet, `/effort` baixo. Texto exato, nenhum julgamento pendente.
> **Pre-requisito:** 0.9.3, commit `54a0c74`, 165 testes verdes, arvore limpa, wo0015 e wo0016 aplicadas e empurradas.
> **Base:** auditoria de fechamento do chat em 2026-08-01, sobre o mount de 2026-08-01 17:24.
> **Ancora semantica:** se um trecho-ancora nao bater EXATAMENTE, **PARE e reporte**.
> **Idempotencia:** procure a frase-chave do texto NOVO antes de inserir; se ja existir, PULE e diga.

> **Canal dos meta neste ciclo = CODE.** Esta WO e o registro. O chat nao entrega nenhum doc inteiro nesta rodada.

> **Por que os docs de usuario vao por WO, e nao inteiros:** a regra do CEREBRO diz que README e GUIA sao autorados inteiros pelo chat. Aqui o delta e de tres frases; baixar 11 KB para trocar tres frases seria o mesmo desperdicio que a spec da wo0015 foi. Mudanca minima que resolve.

---

## 1. Por que

A 0.9.3 saiu, mas os registros ficaram na 0.9.2: o README anuncia versao e contagem de testes velhas, o `_TEMPLATE.md` de WO carrega um pre-requisito congelado, e o `history.log` documentado no GUIA nao menciona o campo novo que a propria 0.9.3 criou. Alem disso, o STATUS acumulou itens `[x]` que a regra de higiene manda tirar («o resolvido sai»).

E ha um feedback ao KCM a registrar, a pedido do usuario: o **gatilho de analise/spec da v1.94.0 disparou onde nao devia**, e o modo de falha e util para o kit.

## 2. Contexto factual (medido no mount de 2026-08-01 17:24)

- `src/__init__.py` = **0.9.3**; suite = **165 testes** (era 158 na 0.9.2).
- `README.md` diz «Estado atual — 0.9.2» e «158 testes».
- `meta/workorders/_TEMPLATE.md` diz «Este repo esta em 0.9.2 / 158 testes» — dado congelado num MODELO, que e exatamente onde dado congelado envelhece pior.
- `meta/STATUS.md` linha ~49 traz a serie historica de contagem de testes, terminando em «158 em 0.9.2».
- `meta/STATUS.md` §Backlog tem **8 itens `[x]`** de 2026-07-03 e anteriores, ja concluidos, e so **2 itens `[ ]`** abertos.
- `meta/CHANGELOG.md`: `## [Não lançado]` esta **vazia** e a entrada `### Alterado` da wo0014 ficou **dentro** da `## [0.9.3]`. Foi acidente de ancoragem (a wo0015 inseriu a versao logo depois de `[Não lançado]`), mas o resultado esta **correto** — a migracao de vocabulario saiu junto da 0.9.3. **Nada a corrigir**; anotado aqui para nao ser "consertado" por engano numa proxima auditoria.
- `meta/IDEAS.md` linha ~11: a ideia de 2026-07-23 segue como «ACEITA, a especificar» — mas foi entregue na 0.9.3.

---

## Edicao 1 — `meta/IDEAS.md` · fechar a ideia de 2026-07-23

**Ancora:**

```
### 2026-07-23 — Registrar no backup QUAL instrução o gerou (`history.log` + `manifest.txt`) — ACEITA, a especificar
```

**Substituir por:**

```
### 2026-07-23 — Registrar no backup QUAL instrução o gerou (`history.log` + `manifest.txt`) — CONCLUÍDA (0.9.3, wo0015, commit `54a0c74`)
> **Entregue em 2026-07-30.** Saiu mais barata do que a captura previa: a leitura da fonte mostrou que o `manifest.txt` já abria com `# Backup de <ts>` e que o parser do rollback já ignorava linhas `#` — então a origem entrou como **cabeçalho**, não como coluna, e **não houve mudança de formato nem fallback a escrever**. No `history.log` virou terceiro campo tab, escrito sempre (vazio quando desconhecida) para a coluna ter posição estável. Colagem grava `(colado da área de transferência)`. Regressão de rollback sobre manifesto antigo coberta por teste. Spec: `meta/specs/260730-origem-do-backup.md`.
```

## Edicao 2 — `meta/IDEAS.md` · feedback do gatilho ao KCM

**Ancora** (o fim do item 4 da entrada de feedback da v1.94.0):

```
4. **`meta/analises/` chega com regra, sem gatilho de nascimento observável.** A regra diz «a pasta nasce no primeiro uso», o que é certo — mas o assistente não tem como saber que já deveria ter usado. O gatilho concreto que o próprio kit dá («mudar o formato de um artefato que outra pessoa vai ler ou editar pede análise») é o melhor pedaço da seção e merecia estar na primeira linha, não na sexta.
```

**Substituir por:**

```
4. **`meta/analises/` chega com regra, sem gatilho de nascimento observável.** A regra diz «a pasta nasce no primeiro uso», o que é certo — mas o assistente não tem como saber que já deveria ter usado. O gatilho concreto que o próprio kit dá («mudar o formato de um artefato que outra pessoa vai ler ou editar pede análise») é o melhor pedaço da seção e merecia estar na primeira linha, não na sexta.
5. **OCORRÊNCIA REAL — o gatilho de análise/spec disparou onde não devia, e o assistente não voltou atrás (2026-07-30).** Vale como caso de teste para o kit, porque o modo de falha não é "esqueceu de usar a ferramenta nova": é o oposto. Pedido do usuário: gravar o nome da instrução no `history.log`/`manifest.txt` — mudança pequena. O assistente invocou o gatilho «mudar o formato de um artefato que outra pessoa vai ler pede análise», foi à fonte para escrever a spec e **descobriu ali que o formato não mudava** (o manifesto já tinha cabeçalho `#`; o parser já ignorava). Registrou o fato **dentro da própria spec** — e continuou escrevendo o documento assim mesmo. Constatou a premissa caindo e não atualizou a conclusão. Pior: devolveu ao usuário um "ponto de decisão" que era escolha técnica do assistente, custando um turno de ida e volta, sobre um pedido que o usuário já havia dito não precisar de spec. **O que teve valor foi ler a fonte, não escrever a spec** — a leitura achou o cabeçalho, achou o caso da colagem e matou a ideia de quarta coluna; nada disso precisava de documento prévio, porque o modelo de WO já tem critério de aceite e armadilhas. **Sugestão ao kit:** o gatilho é uma pergunta a **refazer depois** de ler a fonte, não uma senha para começar a escrever — e a seção poderia dizer explicitamente que *constatar que o gatilho não se aplica é motivo para abandonar a análise no meio*, além do teste barato «o usuário já decidiu o QUÊ? então isto é execução, não análise». Ferramenta recém-instalada puxa para ser usada; o kit é o lugar de contrapesar isso.
```

## Edicao 3 — `meta/STATUS.md` · contagem de testes

**Ancora:**

```
- **158 testes** unitários e de integração, todos verdes; `ruff` e `black --check` limpos. (Era 93 em 0.6.0, 112 em 0.7.0, 126 em 0.8.0, 128 em 0.8.1, 133 em 0.8.2, 147 em 0.8.5, 150 em 0.8.6, 152 em 0.8.7, 155 em 0.9.0, 157 em 0.9.1, 158 em 0.9.2.)
```

**Substituir por:**

```
- **165 testes** unitários e de integração, todos verdes; `ruff` e `black --check` limpos. (Era 93 em 0.6.0, 112 em 0.7.0, 126 em 0.8.0, 128 em 0.8.1, 133 em 0.8.2, 147 em 0.8.5, 150 em 0.8.6, 152 em 0.8.7, 155 em 0.9.0, 157 em 0.9.1, 158 em 0.9.2, 165 em 0.9.3.)
```

## Edicao 4 — `meta/STATUS.md` · funcionalidade nova na lista do que funciona

**Ancora:**

```
- **`apply --sandbox`** / checkbox de sandbox: aplica numa cópia irmã do projeto; original intocado (DEC-015, DEC-019). `SandboxError` quando a instrução é `path_mode=absolute`.
```

**Inserir IMEDIATAMENTE ANTES** da linha da ancora:

```
- **Origem do backup registrada** (0.9.3): o `manifest.txt` abre com `# Instrução: <arquivo>` e o `history.log` traz o nome do arquivo num terceiro campo tab. Cabeçalho, não coluna — o parser do rollback já ignorava `#`, então manifestos antigos seguem restauráveis (regressão coberta). Colagem vira `(colado da área de transferência)`.
```

## Edicao 5 — `meta/STATUS.md` · repouso na versao certa

**Ancora:**

```
## ⏸️ Repouso de maturação (retomado em 2026-07-20, na 0.9.2)
```

**Substituir por:**

```
## ⏸️ Repouso de maturação (retomado em 2026-07-20, na 0.9.2 · segue na 0.9.3)
```

## Edicao 6 — `meta/STATUS.md` · higiene do backlog (o resolvido sai)

**Ancora** — os OITO itens `[x]` do backlog, do primeiro ao ultimo. Cada linha comeca por `- [x] **` e esta entre o titulo `## 📋 Backlog (curto prazo — itens acionáveis)` e a linha `- [ ] **Sugestões para o KCM`. **Remova as oito linhas `[x]`**, preservando o titulo da secao e as duas linhas `[ ]` que ficam.

Depois da remocao, a secao deve comecar assim:

```
## 📋 Backlog (curto prazo — itens acionáveis)
> Concluídos saem daqui (regra do arquivo). O histórico de cada entrega vive no `meta/CHANGELOG.md`; o porquê, no `meta/DECISIONS.md`.
- [ ] **Sugestões para o KCM
```

> Se algum dos oito `[x]` citar algo que **não** esteja registrado no CHANGELOG nem no DECISIONS, **PARE e reporte** em vez de remover — a regra é «o resolvido sai», não «o resolvido some».

## Edicao 7 — `README.md` · estado atual

> `README.md` fica na **raiz** do repo.

**Ancora:**

```
## Estado atual — 0.9.2

O núcleo (CLI) e a interface gráfica (PySide6) estão funcionais e testados
(**158 testes**). A GUI reusa exatamente a mesma pilha do CLI
(`parser → validator → engine`), sem lógica própria.
```

**Substituir por:**

```
## Estado atual — 0.9.3

O núcleo (CLI) e a interface gráfica (PySide6) estão funcionais e testados
(**165 testes**). A GUI reusa exatamente a mesma pilha do CLI
(`parser → validator → engine`), sem lógica própria.
```

## Edicao 8 — `README.md` · o history.log ganhou a origem

**Ancora:**

```
- Log consolidado `history.log`: uma linha por aplicação **e também por rollback
  manual** (Desfazer na GUI, `rollback` no CLI, `self-test`).
```

**Substituir por:**

```
- Log consolidado `history.log`: uma linha por aplicação **e também por rollback
  manual** (Desfazer na GUI, `rollback` no CLI, `self-test`). Cada linha de
  aplicação traz **qual instrução a gerou** (o nome do arquivo), e o
  `manifest.txt` da sessão repete a origem no cabeçalho — com várias instruções
  circulando pelo mesmo projeto, é o que permite escolher o timestamp certo no
  Desfazer sem abrir cada pasta.
```

## Edicao 9 — `docs/GUIA_PASSO_A_PASSO.md` · histórico rápido

**Ancora:**

```
- **Histórico rápido:** dentro da pasta de backups há um `history.log` — uma
  linha por aplicação (data, nº de arquivos, descrição) **e também uma linha
  quando você faz o Desfazer/rollback manual**, para acompanhar o histórico sem
  abrir cada pasta de timestamp.
```

**Substituir por:**

```
- **Histórico rápido:** dentro da pasta de backups há um `history.log` — uma
  linha por aplicação (data, nº de arquivos, **qual instrução gerou aquela
  leva**, descrição) **e também uma linha quando você faz o Desfazer/rollback
  manual**, para acompanhar o histórico sem abrir cada pasta de timestamp. O
  nome da instrução é o que resolve a dúvida real na hora de desfazer: com dois
  ou três `.yaml` aplicados no mesmo dia, é ele que diz qual timestamp é o que
  você quer. Dentro de cada pasta de sessão, o `manifest.txt` repete a origem na
  primeira linha. Instrução colada da área de transferência aparece como
  `(colado da área de transferência)`.
```

## Edicao 10 — `meta/workorders/_TEMPLATE.md` · tirar o dado congelado

**Ancora:**

```
> **Pre-requisito:** versao/commit em que esta WO foi escrita, e o estado esperado (testes verdes, arvore limpa). Este repo esta em 0.9.2 / 158 testes.
```

**Substituir por:**

```
> **Pre-requisito:** versao/commit em que esta WO foi escrita, e o estado esperado (testes verdes, arvore limpa). Leia a versao no `src/__init__.py` e a contagem de testes no `meta/STATUS.md` na hora de escrever — nao copie do modelo, que envelhece.
```

---

## Fora de escopo

- **Nao** mexer na estrutura do `meta/CHANGELOG.md`. A `[Não lançado]` vazia e a entrada da wo0014 dentro da `[0.9.3]` estao **corretas**: a migracao de vocabulario saiu junto daquela versao.
- **Nao** bumpar versao: nada de codigo muda aqui.
- **Nao** criar entrada nova no CHANGELOG — higiene de registro nao e entrega.
- **Nao** tocar em `meta/DECISIONS.md`: a mencao a «0.9.2 e os 158 testes» na DEC-033 e **texto datado** e descreve corretamente o estado no momento da decisao.
- **Nao** tocar no `meta/ROADMAP.md`: nenhuma fase mudou de estado (a 0.9.3 e item avulso de backup, nao um marco de F2/F3).

## Armadilhas desta WO

- **A Edicao 6 e a unica que REMOVE conteudo.** Confira antes que cada `[x]` removido tem registro no CHANGELOG ou no DECISIONS — a regra e «o resolvido sai», nao «o resolvido some». Na duvida sobre uma linha, PARE e reporte em vez de remover.
- **`README.md` na raiz, `GUIA_PASSO_A_PASSO.md` em `docs/`.** Nao inverta.
- **`meta/CHANGELOG.md` esta em CRLF** — esta WO nao o toca, mas se voce abrir para conferir, nao salve.
- A Edicao 2 e uma substituicao de **um paragrafo inteiro por dois**: o item 4 e reescrito identico e o 5 vem em seguida. Confira que o item 4 nao foi alterado no processo.

---

## Depois de aplicar — conferencia antes do commit

- [ ] `git diff` mostra exatamente: `meta/IDEAS.md`, `meta/STATUS.md`, `README.md`, `docs/GUIA_PASSO_A_PASSO.md`, `meta/workorders/_TEMPLATE.md`. Nada alem.
- [ ] `grep -rn "158 testes" README.md meta/STATUS.md meta/workorders/_TEMPLATE.md` nao retorna nada.
- [ ] `grep -n "0.9.2" README.md` nao retorna nada.
- [ ] A secao Backlog do STATUS tem so as duas linhas `[ ]` e a nota nova.
- [ ] **Nao precisa de build** (so doc). Ainda assim, `python -m pytest` para provar que nada foi tocado por engano.

## Relatorio de aplicacao *(quem aplica preenche)*

O que foi feito · o que fugiu do texto literal da WO · arquivos tocados · resultado da validacao · o commit.

## Commit — blocos separados, mensagem SEM acento

```
git add -A
```

```
git commit -m "docs: alinha registros a 0.9.3 e fecha a ideia da origem do backup" -m "README e GUIA passam a 0.9.3 e documentam a origem no history.log e no manifest.txt. STATUS: 165 testes, funcionalidade nova listada, backlog limpo dos itens ja concluidos. IDEAS: ideia de 2026-07-23 fechada como entregue, e registrada ao KCM a ocorrencia do gatilho de analise que disparou onde nao devia. Modelo de WO deixa de carregar versao congelada."
```

```
git push
```
