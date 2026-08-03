# WO 0018 — fechar ideias ja entregues, registrar achados dos prints e o desfecho da mensagem do KCM

> **Tipo:** DOC (meta/ apenas).
> **Config sugerida:** Sonnet, `/effort` baixo. Texto exato, nenhum julgamento pendente.
> **Pre-requisito:** 0.9.3, wo0017 aplicada, arvore limpa. Se a wo0017 ainda nao foi aplicada, **aplique-a antes** — as Edicoes 1 e 2 desta WO ancoram em texto que ela cria.
> **Base:** prints de 2026-07-17 e 2026-08-03 conferidos pelo chat; `260801-mensagem-do-KCM-para-o-ASU.md`; auditoria das ideias ativas do usuario.
> **Ancora semantica:** se um trecho-ancora nao bater EXATAMENTE, **PARE e reporte**.
> **Idempotencia:** procure a frase-chave do texto NOVO antes de inserir; se ja existir, PULE e diga.

> **Canal dos meta neste ciclo = CODE.** Esta WO e o registro.

---

## 1. Por que

Tres coisas caducaram ao mesmo tempo:

1. **Dois prints responderam perguntas antigas.** O de 2026-07-17 fecha o item aberto da DEC-030 (ha faixa de fundo, sim — medida por pixel). O de 2026-08-03 mostra um defeito cosmetico real que nunca foi registrado.
2. **Cinco ideias do usuario descrevem como pendente coisa que ja foi entregue** — algumas ha mais de um mes. IDEAS nao perde nada, mas status errado e pior que ideia ausente: le como trabalho aberto.
3. **O KCM respondeu ao feedback de 07-30** e a resposta muda coisas aqui (D-108, v1.95.0). O desfecho tem de ficar registrado do nosso lado.

## 2. Contexto factual (medido, nao lembrado)

- **Print de 2026-07-17, medicao de pixel no fundo das linhas do diff:** linha de contexto = `(255,255,255)`; linha removida = `(255,238,240)`; linha adicionada = `(230,255,237)`. **A faixa de fundo existe** e sao as cores classicas de diff (`#ffeef0` / `#e6ffed`), com as cores do TEXTO variando por token (sintaxe do Pygments ativa num `.md`). O desenho da DEC-030 esta integralmente realizado.
- **Print de 2026-08-03:** previa com falha, `Arquivo não encontrado`. Na coluna «Arquivo / Modificação» o rotulo aparece como `{'id': 'f_decisions', 'path_mode': 'relativ…` — **um `dict` cru do Python vazando para a interface**.
- **Causa, lida na fonte** (`src/core/patch_engine.py`, bloco «1) Resolver e checar pré-condições»): o `except FileLocatorError` monta `FileResult(file_id, str(file_entry), "failed", …)`. Em todos os outros caminhos o segundo argumento e `str(path)`. Atinge tambem o CLI, que imprime o mesmo campo.
- **Ambiguidade de ancora ja e ERRO, nao aviso** (`_resolve_occurrence`, DEC-011): casar mais de uma vez sem `occurrence` levanta `StrategyError` com mensagem explicita. Isso muda o significado do item «indicador de confianca» do ROADMAP, escrito em 2026-06-03 — antes da DEC-011.
- **Entregues, mas registradas como pendentes:** backup na pasta-pai (0.9.0, DEC-024c/DEC-032), nome por projeto quando externo (DEC-024b, ja no `patch_engine`), verificacao pos-aplicacao (item 9 do `PROMPT_IA.md` + §8 do guia), `PROMPT_IA.md` referenciado (GUIA §7, e agora com o cabecalho da wo0016), copia/desfazer em massa (spec0004 0.8.5 + «Desfazer última aplicação»).

---

## Edicao 1 — `meta/IDEAS.md` · fechar «Padrão do backup na pasta-PAI»

**Ancora:**

```
### 2026-06-28 — Padrão do backup na pasta-PAI da raiz — ACEITA, a implementar (DEC-024c)
```

**Substituir por:**

```
### 2026-06-28 — Padrão do backup na pasta-PAI da raiz — CONCLUÍDA (0.9.0, DEC-024c + DEC-032)
> **Fechada em 2026-08-01 (auditoria).** Entregue na 0.9.0 e refinada pela DEC-032: o padrão é `parent(raiz)/zz_backups/<timestamp>/`, **derivado da raiz** (trocar a raiz troca o destino), com o prefixo `zz_` empurrando a pasta para o fim da listagem — que era o pedido original do usuário ("ZZbackup"). O cuidado de design mapeado aqui foi respeitado: no caso padrão **não** se aninha por `<rootname>`, porque `parent(raiz)/<rootname>` é a própria raiz. Rollback de backups no layout `backups/` antigo continua funcionando.
```

## Edicao 2 — `meta/IDEAS.md` · fechar «Local do backup + nome com prefixo»

**Ancora:**

```
### 2026-06-15 — Local do backup junto da instrução + nome com prefixo da raiz — PARCIAL (DEC-018; a parte do NOME por projeto foi SPECADA em 2026-06-28)
```

**Substituir por:**

```
### 2026-06-15 — Local do backup junto da instrução + nome com prefixo da raiz — CONCLUÍDA (0.9.0; DEC-018 + DEC-024b + DEC-032)
> **Fechada em 2026-08-01 (auditoria).** As duas metades saíram: o LOCAL (`--backup-dir` desde a 0.6.0, campo Backup na GUI) e o NOME — quando o destino é externo à raiz, o `patch_engine` aninha por `<nome-do-projeto>` sanitizado (DEC-024b), e o padrão ganhou o prefixo `zz_` (DEC-032) que atende o "empurrar para o fundo da listagem". A 0.9.3 acrescentou o que faltava para usar isso de verdade: o `history.log` e o `manifest.txt` agora dizem **qual instrução** gerou cada leva.
```

## Edicao 3 — `meta/IDEAS.md` · fechar «Verificação pós-aplicação pela IA»

**Ancora:**

```
### 2026-06-13 — Verificação pós-aplicação pela IA (na sessão seguinte) — ACEITA, ver DEC-016
```

**Substituir por:**

```
### 2026-06-13 — Verificação pós-aplicação pela IA (na sessão seguinte) — CONCLUÍDA (DEC-016; entregue no kit de ensino)
> **Fechada em 2026-08-01 (auditoria).** A entrega desta ideia não é código: é instrução para a IA geradora, e ela está no lugar certo há tempos — **item 9 do `docs/PROMPT_IA.md`** ("confira no disco cada arquivo que a instrução tocou… não confie em 'deu certo': olhe o arquivo") e **§8 do `docs/INSTRUCTION_GUIDE.md`**. Ficou como "ACEITA" por inércia de registro, não por estar aberta. A DEC-016 já explicava o porquê (agentes emitem linguagem de conclusão independentemente do estado real).
```

## Edicao 4 — `meta/IDEAS.md` · reclassificar «EM MASSA e SELEÇÃO de blocos»

**Ancora:**

```
### 2026-06-15 — Aplicar/desfazer/copiar EM MASSA e SELEÇÃO de blocos na GUI — EM AVALIAÇÃO (possível conflito com o objetivo)
```

**Substituir por:**

```
### 2026-06-15 — Aplicar/desfazer/copiar EM MASSA e SELEÇÃO de blocos na GUI — METADE CONCLUÍDA, metade DESCARTADA (2026-08-01)
> **Resolvida em 2026-08-01 (auditoria).** Estava "EM AVALIAÇÃO" há sete semanas, o que não informava nada — então foi partida nas duas perguntas que ela sempre foram:
> **(a) EM MASSA — CONCLUÍDA.** Já é o comportamento padrão e nunca foi outro: o dry-run avalia a instrução inteira, Aplicar aplica tudo de uma vez, "Desfazer última aplicação" reverte a sessão inteira por timestamp, e "Copiar saída" copia o relatório completo (spec0004, 0.8.5). Nada a fazer.
> **(b) SELEÇÃO de blocos — DESCARTADA**, pela ressalva que o próprio usuário levantou ao propor. Aplicar metade de uma instrução produz um estado que **nenhum dos lados descreve**: o backup e o `manifest.txt` são por sessão, o rollback é tudo-ou-nada, e a IA que gerou a instrução raciocinou sobre o conjunto. Seleção parcial é consagrada no `git add -p` porque ali o autor das mudanças é o próprio humano que seleciona; aqui o autor é a IA, e a unidade de raciocínio dela é a instrução. Quem quiser aplicar só uma parte tem o caminho certo e barato: **pedir à IA outra instrução, menor.** Se voltar à pauta, volta como decisão nova, com o custo do estado parcial resolvido primeiro.
```

## Edicao 5 — `meta/IDEAS.md` · precisar o status do PROMPT_IA

**Ancora:**

```
### 2026-06-15 — Subir o PROMPT_IA.md ao projeto e referenciá-lo no CLAUDE.md — ACEITA (a documentar)
```

**Substituir por:**

```
### 2026-06-15 — Subir o PROMPT_IA.md ao projeto e referenciá-lo no CLAUDE.md — CONCLUÍDA e depois REFINADA (wo0016, 2026-07-30)
> **Fechada em 2026-08-01 (auditoria).** Documentada no `docs/GUIA_PASSO_A_PASSO.md` (§7) e no `README.md`. **Mas o desfecho virou o oposto para uma classe de projeto:** a wo0016 acrescentou um cabeçalho no `docs/PROMPT_IA.md` mandando **NÃO** colar o bloco em projeto que já usa o Kit de Contexto — lá o `CEREBRO.md` já traz a diretriz do ASU, curada, e duas diretrizes concorrentes viram sorteio. A ideia continua válida para projeto **sem** kit; com kit, sobe só o `INSTRUCTION_GUIDE.md`.
```

## Edicao 6 — `meta/IDEAS.md` · registrar o defeito achado no print

**Ancora:**

```
## 🤖 Ideias Ativas — Assistente
```

**Inserir IMEDIATAMENTE APOS** a linha da ancora:

```

### 2026-08-03 — `dict` cru vaza para a interface quando o arquivo não é encontrado — DEFEITO CONFIRMADO, correção de uma linha
Achado num print de uso real (previsão com falha, 2026-08-03): a coluna «Arquivo / Modificação» mostrou `{'id': 'f_decisions', 'path_mode': 'relativ…` em vez do caminho do arquivo. **Causa lida na fonte:** em `src/core/patch_engine.py`, no `except FileLocatorError` do bloco «1) Resolver e checar pré-condições», o `FileResult` é montado com `str(file_entry)` — o dicionário inteiro — enquanto todos os outros caminhos usam `str(path)`. Atinge a GUI **e** o CLI, que imprimem o mesmo campo. O erro em si está correto e legível ("Arquivo não encontrado: …"); o que quebra é o rótulo, justamente no momento em que o usuário mais precisa reconhecer QUAL arquivo falhou. **Correção mínima:** usar o caminho declarado — `file_entry.get("relative_path") or file_entry.get("absolute_path") or file_id`. Não usar `path`: quando a exceção vem do próprio `resolve_path`, ele não chegou a existir. **Sem custo de decisão; parqueado só porque o projeto está em repouso de maturação.** Vale um teste que afirme que o rótulo do `FileResult` com falha não contém `{'`.
```

## Edicao 7 — `meta/DECISIONS.md` · fechar o item aberto da DEC-030

**Ancora:**

```
## DEC-030 — Syntax-highlight opcional no diff da GUI via Pygments (degradação graciosa)
```

> Conferido: e a unica linha `## DEC-030` do arquivo.

**Inserir IMEDIATAMENTE APOS** a linha da ancora:

```
> **ITEM ABERTO RESOLVIDO em 2026-08-03 — não há nada a fazer.** A dúvida registrada aqui era se as linhas `+`/`-` do diff ficavam marcadas por **faixa de fundo** (deixando a cor do texto para a sintaxe) ou apenas por cor de texto. Medido por pixel num print de uso real de 2026-07-17: linha de contexto tem fundo `#ffffff`, linha removida `#ffeef0`, linha adicionada `#e6ffed` — as cores clássicas de diff —, com as cores do texto variando por token dentro da linha. **A faixa existe e o desenho está integralmente realizado**; a marcação de estado e o realce de sintaxe convivem como a decisão previa.
```

## Edicao 8 — `meta/ROADMAP.md` · reclassificar o indicador de confiança

**Ancora:**

```
- [ ] Indicador de confiança por modificação (🟢 único / 🟡 ambíguo / 🔴 não encontrado).
```

**Substituir por:**

```
- [~] Indicador de confiança por modificação (🟢 único / 🟡 ambíguo / 🔴 não encontrado) — **superado em parte pela DEC-011 (2026-08-01).** O item foi escrito em 2026-06-03; depois disso a DEC-011 decidiu que **âncora ambígua é ERRO, não aviso**: casar mais de uma vez sem `location.occurrence` levanta `StrategyError` com mensagem explícita, e a prévia já mostra isso como ✗/🔴 antes de qualquer escrita. Ou seja, os estados 🟡 (ambíguo) e 🔴 (não encontrado) **já são visíveis** — como falha, que é mais seguro do que como alerta. O que resta do item original é só um verniz: pintar de verde o que passou. Não vale frente própria; se voltar, volta junto de outra mudança na árvore.
```

## Edicao 9 — `meta/IDEAS.md` · desfecho da mensagem do KCM de 2026-08-01

**Ancora:**

```
## 📮 Feedback para o Kit
```

**Inserir IMEDIATAMENTE APOS** a linha da ancora:

```

### 2026-08-01 — Resposta do KCM ao nosso feedback de 07-30: 3 aceitos em fila, 1 refutado, 1 virou D-108
**Recebida** em `260801-mensagem-do-KCM-para-o-ASU.md` (caixa de entrada, não instrução). Desfecho do nosso lado:
- **Item 5 (a ocorrência do gatilho que disparou onde não devia) virou `D-108` e a v1.95.0 do kit.** O KCM diagnosticou o que chamou de **assimetria de concretude**: o lado que ALARGA o gatilho vinha com cinco exemplos nomeados, o lado que ESTREITA era um adjetivo solto e vinha depois — e entre um critério reconhecível e uma abstração, o assistente segue o reconhecível. Três consertos: os dois testes baratos ("o QUÊ já está decidido? então é execução"; "cabe em meia página? então é conversa") subiram para o **primeiro** item da seção e um deles entrou na linha das Instruções do Projeto; o gatilho ganhou o limite do **formato já extensível** (acrescentar campo/linha/seção a formato extensível **não é** mudar o formato — que é exatamente o nosso `manifest.txt`); e **abandonar a análise no meio virou desfecho de primeira classe**. Virou check de harness (C30) nos 18 nichos, guardando a ORDEM, não só o texto.
- **Item 4 (promover o gatilho concreto para a primeira linha) foi REFUTADO — e a refutação está certa.** Os itens 4 e 5 da nossa própria entrada puxavam em direções opostas: o 4 queria o gatilho mais visível, o 5 relatava o dano de ele ter sido visível demais. Atender os dois ao pé da letra teria consertado o sintoma e agravado a causa. O que subiu foi o contrapeso. **Aceito sem contra-argumento.**
- **Itens 1, 2 e 3 aceitos, em fila, não implementados** — o KCM conferiu um a um no `index.template.html` da v1.95.0 e avisou antes do próximo update, em vez de nos deixar descobrir. Nada a fazer aqui.
- **Convenção que fica entre as frentes:** feedback de frente irmã não se aceita cego nem se recusa em silêncio. É o segundo caso.
**A pedir/medir quando a v1.95.0 chegar:** (1) se `permissions.additionalDirectories: ["../"]` funciona de fato no Claude Code em Windows — o KCM não testou contra um Code vivo e diz que essa é a informação mais útil que podemos mandar; (2) se o contrapeso pegou: na primeira mudança pequena depois de adotar, o assistente foi direto ao trabalho? E se abriu análise e a leitura derrubou a premissa, **abandonou?**
**Heads-up recebido, sem ação agora:** o KCM estuda pedir ao FlatDrop que o `_MANIFEST` inclua `git log -1` e resumo de `git status`. Se sair, a técnica registrada no nosso CEREBRO («o mount não tem `.git`: peça `git log -1` UMA vez») muda de forma — o dado chegaria pronto, com a ressalva de ser foto do momento da geração.
**Sobre a `260730-origem-do-backup.md`:** o KCM pediu para **não** mexer — documento escrito, feature entregue, e análise vencida não se apaga. Combina com a nossa regra de não corrigir texto datado. Mantida como está.
```

## Edicao 10 — `meta/STATUS.md` · registrar o defeito conhecido

**Ancora:**

```
## ❌ Quebrado / Com Problema
```

**Inserir IMEDIATAMENTE APOS** a linha da ancora:

```
- **Cosmético (0.9.3, achado em 2026-08-03):** quando o arquivo não é encontrado, o rótulo na árvore da GUI (e no resumo do CLI) mostra o `dict` cru da entrada — `{'id': …, 'path_mode': …}` — em vez do caminho. O erro em si está correto e legível; só o rótulo quebra. Causa e correção de uma linha registradas no `meta/IDEAS.md` (2026-08-03). Não bloqueia nada; parqueado pelo repouso de maturação.
```

---

## Fora de escopo

- **Nao** corrigir o defeito do `dict` nesta WO. E codigo, o projeto esta em repouso, e a decisao de retomar e do usuario. Esta WO **registra**; nao conserta.
- **Nao** mexer em `meta/specs/260730-origem-do-backup.md` — pedido explicito do KCM e coerente com a regra de texto datado.
- **Nao** adotar nada da v1.95.0 por antecipacao (nem o relatorio em arquivo, nem a politica de analises no mount). Chegam pelo proximo template-update.
- **Nao** bumpar versao nem criar entrada no CHANGELOG: registro nao e entrega.
- **Nao** mexer nas ideias `2026-06-15 — Opção de não gerar / excluir o backup` (parqueada com razao) nem `2026-06-13 — Refinamento por tipo/linguagem` (PARCIAL correto).

## Armadilhas desta WO

- **A Edicao 6 e a Edicao 9 inserem no `meta/IDEAS.md` em secoes diferentes** (`## 🤖 Ideias Ativas — Assistente` e `## 📮 Feedback para o Kit`). Confira que cada uma caiu na secao certa — sao os dois unicos titulos com `## ` no meio do arquivo.
- **A Edicao 7 ancora numa linha `## DEC-030` possivelmente truncada** neste texto. Use a linha inteira do arquivo; se houver ambiguidade, PARE.
- **A Edicao 8 troca `- [ ]` por `- [~]`** — o ROADMAP usa `[~]` para parcial/superado em outros pontos, entao a convencao ja existe.
- Nenhuma edicao aqui remove conteudo. Se algo sumir, algo saiu errado.

---

## Depois de aplicar — conferencia antes do commit

- [ ] `git diff` mostra exatamente `meta/IDEAS.md`, `meta/DECISIONS.md`, `meta/ROADMAP.md`, `meta/STATUS.md`. Nada alem.
- [ ] `grep -c "ACEITA, a implementar\|ACEITA, a especificar\|EM AVALIAÇÃO" meta/IDEAS.md` — o resultado deve ser **0**.
- [ ] Nenhuma ideia foi apagada: `grep -c "^### " meta/IDEAS.md` tem de ter aumentado em 2 (as duas entradas novas), nunca diminuido.
- [ ] **Nao precisa de build.** Ainda assim `python -m pytest` para provar que nada de codigo foi tocado.

## Relatorio de aplicacao *(quem aplica preenche)*

O que foi feito · o que fugiu do texto literal da WO · arquivos tocados · resultado da validacao · o commit.

## Commit — blocos separados, mensagem SEM acento

```
git add -A
```

```
git commit -m "docs: fecha ideias ja entregues e registra achados dos prints e a resposta do KCM" -m "Auditoria das ideias ativas: backup na pasta-pai, nome por projeto, verificacao pos-aplicacao e PROMPT_IA sao fechadas como entregues; aplicar em massa e concluida e selecao de blocos e descartada com o motivo. Prints de uso real fecham o item aberto da DEC-030 (a faixa de fundo existe, medida por pixel) e revelam um defeito cosmetico: dict cru no rotulo quando o arquivo nao e encontrado, registrado com causa e correcao. Indicador de confianca do ROADMAP reclassificado, superado em parte pela DEC-011. Registrado o desfecho da mensagem do KCM de 2026-08-01."
```

```
git push
```
