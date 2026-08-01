# WO NNNN — [titulo curto e concreto, no que a WO ENTREGA]

> **Numeracao continua a serie das specs deste repo:** a ultima instrucao de aplicacao foi a
> `spec0013`, entao a primeira WO e a `wo0014`. Nao reinicie a contagem.

> **Este arquivo e o MODELO — nao o preencha aqui.** Copie para `meta/workorders/AAMMDD-woNNNN-desc.md`
> e preencha a copia. Ele sobe sempre ao Projeto (o `.flatdropignore` ignora `meta/workorders/*` mas
> reinclui `!meta/workorders/_TEMPLATE.md`), para que a primeira sessao depois de uma transferencia
> tenha o formato a mao sem precisar das WOs antigas.
>
> **O que e uma WO:** instrucao de APLICACAO — ancora + texto exato — que o chat autora e o Code posiciona.
> **O que NAO e:** a spec de feature diz **o que** construir e quando esta pronto; a WO diz **como aplicar**.
> Se voce ainda nao sabe o que construir, nao e hora de escrever WO — e hora de analise ou spec.

---

## Cabecalho — preencha as linhas que se aplicam e apague as que nao

> **Tipo:** WO de CODIGO · WO de DOC (registro) · mista.
> **Config sugerida:** modelo e esforco para quem for aplicar (WO mecanica = Sonnet/baixo; WO que toca patch_engine ou backup_manager = Opus/alto).
> **Pre-requisito:** versao/commit em que esta WO foi escrita, e o estado esperado (testes verdes, arvore limpa). Leia a versao no `src/__init__.py` e a contagem de testes no `meta/STATUS.md` na hora de escrever — nao copie do modelo, que envelhece.
> **Base:** a decisao, a analise ou a conversa que originou.
> **Depende de:** WOs que precisam estar aplicadas antes — ou apague a linha.
> **Ancora semantica:** se um trecho-ancora nao bater EXATAMENTE, **PARE e reporte** — nunca chute um
> lugar proximo. Os arquivos podem ter mudado entre a escrita desta WO e a aplicacao.
> **Idempotencia:** antes de cada insercao, procure a frase-chave do texto NOVO. Se ja existir, **PULE**
> o item e diga no relatorio — nao duplique.

> **Canal dos meta neste ciclo = CHAT** *(ou **CODE** — escolha um e apague o outro)*.
> Se **CHAT**: esta WO toca so codigo/config — nao faca append nos `meta/`; o chat entrega os
> documentos depois da validacao. Se **CODE**: esta WO E o registro — aplique os appends previstos
> e nao espere doc do chat. *Uma fonte por doc por ciclo; escolher errado aqui duplica conteudo.*

---

## 1. Por que

[Uma a tres frases: a dor concreta, ou a causa raiz se for correcao. Quem aplica precisa saber o que
esta consertando para reconhecer quando o resultado sai errado. Se for correcao de defeito introduzido
por WO anterior, diga qual e assuma — historico honesto e o que impede repetir.]

## 2. Contexto factual *(so em WO de registro — apague em WO de codigo)*

[Os fatos que os textos das edicoes afirmam, na ordem em que aconteceram. Esta secao e a FONTE dos
blocos abaixo: fato que nao esta aqui nao deveria aparecer la. Marque o que foi **medido** e o que e
**deduzido** — inferencia sem rotulo vira fato na leitura seguinte.]

---

## Edicao 1 — `caminho/real/do/arquivo.ext` · [o que muda, em cinco palavras]

**Ancora** *(diga ONDE fica: secao, funcao, item — nunca numero de linha)*:

```
[trecho literal e unico do arquivo vivo, copiado sem reformatar]
```

**Substituir por:**

```
[texto exato que entra]
```

> Variantes — use a que couber, sempre com a ancora acima: **Inserir IMEDIATAMENTE APOS** ·
> **Inserir IMEDIATAMENTE ANTES** · **Remover o bloco inteiro** · **Criar arquivo novo** (sem ancora;
> diga o que fazer se ele ja existir).

## Edicao 2 — `caminho/real/do/arquivo.ext` · [...]

[Repita. Uma edicao por bloco. Se um arquivo recebe mudancas distantes entre si, numere 2a/2b/2c em
vez de empilhar num bloco so — cada uma com a propria ancora.]

---

## Fora de escopo

[O que esta WO deliberadamente NAO faz, para que quem aplica nao "aproveite a viagem". Melhoria que
voce enxergou no caminho vira ideia no IDEAS ou outra WO — nao entra aqui.]

## Armadilhas desta WO

[So quando houver. O que ja deu errado antes neste mesmo lugar e o que quem aplica pode quebrar sem
perceber: ancora que aparece duas vezes, arquivo com fim de linha CRLF (ancora multi-linha colada com
\\n nao casa), bloco gerado que sera reescrito, numero de check ja usado.]

---

## Depois de aplicar — conferencia antes do commit

- [ ] `git diff` mostra **exatamente** os arquivos previstos, e nada alem.
- [ ] [Conferencia de forma especifica desta WO — ex.: "a entrada nova ficou dentro da secao certa".]
- [ ] **WO de codigo:** `python -m pytest`, `python -m src self-test`, `ruff check .` e `black --check .` passam com **0 erros**. Se acusar erro,
      **PARE e reporte antes de commitar**.
- [ ] **WO so de doc:** nao precisa de build — a rede e o `git diff`.
- [ ] **Teste manual que a validacao NAO cobre** (obrigatorio quando a WO toca dado carregado ou UI):
      [caso feliz · caso de borda · regressao possivel].

## Relatorio de aplicacao *(quem aplica preenche ao terminar)*

O que foi feito · o que fugiu do texto literal da WO · arquivos tocados · resultado da validacao · o commit.
**Nao** substitua este relatorio pelo bloco de fecho do chat: aquele e da raia de planejamento, e trocar
relatorio por formulario perde justamente o que so quem aplicou viu.

## Commit — blocos separados, mensagem SEM acento

```
git add [caminhos]
```

```
git commit -m "tipo(escopo): descricao no imperativo curto" -m "Corpo explicando o porque, sem acento."
```

```
git push
```