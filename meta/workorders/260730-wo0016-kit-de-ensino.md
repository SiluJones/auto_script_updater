# WO 0016 — kit de ensino: resolver o conflito do PROMPT_IA e afrouxar o guia da CLI

> **Tipo:** DOC (tres arquivos de `docs/` e `examples/`).
> **Config sugerida:** Sonnet, `/effort` baixo. Texto exato, sem julgamento pendente.
> **Pre-requisito:** 0.9.2/0.9.3, arvore limpa. Independente da wo0015 — pode ir antes, depois ou no mesmo ciclo.
> **Base:** nota `260729-RECOMENDACOES-KCM-para-o-ASU.md`, capturada no `meta/IDEAS.md` em 2026-07-30; triagem do chat em 2026-07-30, aprovada pelo usuario.
> **Ancora semantica:** se um trecho-ancora nao bater EXATAMENTE, **PARE e reporte**.
> **Idempotencia:** procure a frase-chave do texto novo antes de inserir; se ja existir, PULE e diga.

> **Canal dos meta neste ciclo = CODE.** Faca o append da Edicao 4.

---

## 1. Por que

O KCM devolveu tres observacoes sobre o kit de ensino do ASU (`docs/`). A primeira corrige um problema **ativo**, nao hipotetico.

**O conflito:** num projeto que usa o Kit de Contexto (KCM), o `CEREBRO.md` daquele projeto ja traz a diretriz de saida do ASU, curada, e ela **diverge** do nosso `PROMPT_IA.md` em dois pontos — entrega como **arquivo `.yaml` para baixar** (em vez de bloco colado no chat) e **sem** a linha de comando de execucao. Se o usuario colar o nosso bloco por cima, ficam duas instrucoes concorrentes disputando o mesmo turno, e a que ganha e sorteio. A perdedora manda colar YAML no chat — que e exatamente o caminho que corrompe ancora acentuada, coisa que a §4.7 do nosso proprio guia adverte.

**A causa nao e nossa**, e vale registrar: o kit injeta uma diretriz de saida E recomenda subir um arquivo que traz outra. A correcao de fundo ja foi feita do lado deles (apontar so para o `INSTRUCTION_GUIDE.md`). O cabecalho que esta WO acrescenta e **cinto de seguranca para quem estiver numa versao antiga do kit** — nao redundancia. Por isso o proprio texto diz por que existe: senao, daqui a tres versoes alguem o remove por achar que sobra.

## 2. Contexto factual

- O `docs/PROMPT_IA.md` abre com um bloco `>` de "Como usar" antes da primeira linha `─────`.
- A §0 do `docs/INSTRUCTION_GUIDE.md` manda, no item 2, emitir a linha de comando **sempre** — o que assume que o usuario aplica pela CLI. Hoje ha tres caminhos (CLI, GUI por arquivo, GUI por colagem) e a diretriz curada do kit pede a entrega por arquivo.
- O `examples/demo.yaml` ja abre com um bloco de comentario explicando que e executavel; falta so dizer que **nao precisa subir ao Projeto**.

**Nao adotado da recomendacao do KCM:** a frase sugerida sobre "nao inventar pasta de destino" na §0. Ela resolve um sintoma do lado do kit, nao do guia — e o guia e autocontido de proposito. Se o problema reaparecer, entra com evidencia propria.

---

## Edicao 1 — `docs/PROMPT_IA.md` · cabecalho de convivencia

**Ancora:**

```
> **Como usar:** copie o bloco entre as linhas `─────` para as instruções do
> seu projeto (Claude Project, system prompt, CLAUDE.md…), e suba o arquivo
> `INSTRUCTION_GUIDE.md` na base de conhecimento. A partir daí, peça:
> *"emita uma instrução ASU para estas mudanças"*.
```

**Substituir por:**

```
> **Como usar:** copie o bloco entre as linhas `─────` para as instruções do
> seu projeto (Claude Project, system prompt, CLAUDE.md…), e suba o arquivo
> `INSTRUCTION_GUIDE.md` na base de conhecimento. A partir daí, peça:
> *"emita uma instrução ASU para estas mudanças"*.
>
> **ANTES de colar: o seu projeto usa o Kit de Contexto (KCM)?** Se o projeto
> já tem um `CEREBRO.md`/`meta/CEREBRO.md`, ele provavelmente **já traz a
> diretriz de saída do ASU**, curada e possivelmente diferente desta (entrega
> como arquivo `.yaml` para baixar, sem linha de comando). Nesse caso **NÃO
> cole o bloco abaixo**: suba apenas o `INSTRUCTION_GUIDE.md` e deixe o
> CEREBRO mandar. Duas diretrizes concorrentes no mesmo contexto viram sorteio
> — e a que perde costuma ser a que manda colar YAML no chat, que é como
> âncora acentuada se corrompe (§4.7 do guia).
>
> Este aviso não é redundância com o kit: ele existe para quem está numa
> versão antiga do KCM, que ainda recomenda colar este bloco. Não o remova
> por parecer repetido.
```

## Edicao 2 — `docs/INSTRUCTION_GUIDE.md` · §0 deixa de assumir a CLI

**Ancora:**

```
Quando pedirem uma "instrução ASU", responda com:
1. **UM único bloco de código `yaml`** contendo a instrução completa (nada de
   XML, nada de JSON, nada de vários blocos, nada de explicação no meio do YAML);
2. depois do bloco, **uma linha** com o comando de aplicação, ex.:
   `Salve como instrucao.yaml e rode: python -m src apply instrucao.yaml --root <RAIZ> --dry-run`
```

**Substituir por:**

```
Quando pedirem uma "instrução ASU", responda com:
1. **A instrução completa em YAML.** Se a sua interface permite entregar
   arquivo, entregue como **`.yaml` para baixar** — é o caminho preferido:
   colar YAML no chat é onde acento e indentação de âncora se corrompem
   (§4.2, §4.7). Se não permite, então **UM único bloco de código `yaml`**
   (nada de XML, nada de JSON, nada de vários blocos, nada de explicação no
   meio do YAML);
2. **só se a pessoa aplica pela linha de comando**, uma linha depois com o
   comando, ex.:
   `Salve como instrucao.yaml e rode: python -m src apply instrucao.yaml --root <RAIZ> --dry-run`
   Quem usa a interface gráfica não precisa dela — lá é apontar a raiz e a
   instrução (ou usar **Colar instrução**) e clicar em Pré-visualizar. Na
   dúvida sobre qual caminho a pessoa usa, ofereça o comando **e** diga que
   pela GUI basta abrir o arquivo.
```

## Edicao 3 — `examples/demo.yaml` · rotulo de "nao precisa subir"

**Ancora** (as tres primeiras linhas do arquivo):

```
# Instrução de DEMONSTRAÇÃO — executável de ponta a ponta.
#
# Diferente de exemplo_instrucao.yaml (ilustrativo, com caminhos fictícios),
```

**Substituir por:**

```
# Instrução de DEMONSTRAÇÃO — executável de ponta a ponta.
#
# Este arquivo é para RODAR e para LER na sua máquina. Ele NÃO precisa ser
# subido à base de conhecimento de nenhum projeto: quem ensina a IA a gerar
# instruções é o docs/INSTRUCTION_GUIDE.md, cuja §2 já traz um exemplo
# completo. Subir a demo junto só ocupa contexto a cada turno.
#
# Diferente de exemplo_instrucao.yaml (ilustrativo, com caminhos fictícios),
```

## Edicao 4 — `meta/IDEAS.md` · fechar o item

**Ancora:**

```
### 2026-07-30 — Três recomendações do KCM sobre o kit de ensino (`PROMPT_IA.md`, guia §0, `demo.yaml`) — ACEITAS em princípio, a implementar
```

**Substituir por:**

```
### 2026-07-30 — Três recomendações do KCM sobre o kit de ensino (`PROMPT_IA.md`, guia §0, `demo.yaml`) — IMPLEMENTADAS (wo0016)
> **Fechado em 2026-07-30.** (1) e (3) entraram como propostas. (2) entrou **sem** a frase sugerida sobre "não inventar pasta de destino" — ela resolve um sintoma do lado do kit, e o guia é autocontido de propósito. **Devolvido ao KCM:** a causa do conflito do item (1) é do lado deles (o kit injeta uma diretriz de saída E recomenda subir um arquivo que traz outra); nosso cabeçalho é cinto de segurança para quem está numa versão antiga do kit, e o próprio texto diz isso para não ser removido no futuro por parecer redundante.
```

---

## Fora de escopo

- **Nao** mexer no `README.md` nem no `GUIA_PASSO_A_PASSO.md` (o passo "cole o bloco do `PROMPT_IA.md`" segue valido — o cabecalho novo e que decide quando nao colar).
- **Nao** mexer no corpo do bloco colavel do `PROMPT_IA.md` (entre as linhas `─────`): o item 1 dele continua pedindo bloco YAML, porque quem cola esse bloco e justamente quem **nao** tem a diretriz curada do kit.
- **Nao** adotar a frase do KCM sobre pasta de destino na §0.
- **Nao** bumpar versao: `docs/` e `examples/` nao mudam o comportamento da ferramenta.

## Armadilhas desta WO

- O `PROMPT_IA.md` tem **duas** linhas `─────` iguais; a ancora da Edicao 1 e o bloco `>` **antes** da primeira. Nao case na linha divisoria.
- A §0 do guia e citada por numero em outros pontos do proprio guia e no `PROMPT_IA.md` ("§0", "checklist da §7"). A Edicao 2 nao muda a numeracao — confira que continua §0 depois de editar.
- `examples/demo.yaml` e consumido pelos testes e pelo `self-test`. Comentario no topo e inofensivo, **mas rode a suite** para provar: se o parser reclamar, PARE e reporte.

---

## Depois de aplicar — conferencia antes do commit

- [ ] `python -m pytest` verde e `python -m src self-test` OK — a Edicao 3 toca um arquivo que os testes consomem.
- [ ] `python -m src validate examples\demo.yaml` continua valido.
- [ ] `git diff` mostra exatamente `docs/PROMPT_IA.md`, `docs/INSTRUCTION_GUIDE.md`, `examples/demo.yaml` e `meta/IDEAS.md`. Nada alem.
- [ ] Ler a §0 do guia inteira depois da edicao, de cabo a rabo: ela e o primeiro texto que a IA geradora le, e uma frase truncada ali contamina toda instrucao gerada.

## Relatorio de aplicacao *(quem aplica preenche)*

O que foi feito · o que fugiu do texto literal da WO · arquivos tocados · resultado da validacao · o commit.

## Commit — blocos separados, mensagem SEM acento

```
git add -A
```

```
git commit -m "docs: evita diretriz concorrente com o kit e tira o vies de CLI do guia" -m "PROMPT_IA ganha cabecalho dizendo para NAO colar o bloco em projeto que ja tem CEREBRO com a diretriz do ASU: duas diretrizes concorrentes viram sorteio, e a perdedora manda colar YAML no chat, que corrompe ancora acentuada. A secao 0 do INSTRUCTION_GUIDE deixa de assumir linha de comando: entrega por arquivo passa a ser o caminho preferido e o comando vira condicional. demo.yaml ganha rotulo dizendo que nao precisa subir a base de conhecimento. Origem: recomendacoes do KCM de 2026-07-29."
```

```
git push
```
