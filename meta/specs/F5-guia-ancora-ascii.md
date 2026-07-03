# SPEC — F5 · Nota anti-Unicode nas âncoras (INSTRUCTION_GUIDE)

> **Tipo:** spec de DOC, para o Claude Code aplicar. NÃO toca o produto (`src/`/`tests/`) → não precisa de build; a rede é o `git diff`.
> **Autoria:** chat (planejamento). **Execução:** Claude Code posiciona o texto exato nas âncoras semânticas indicadas (seção/título, nunca nº de linha).
> **Âncoras** são TÍTULOS/linhas literais do `docs/INSTRUCTION_GUIDE.md`. Localize cada uma EXATAMENTE; se não achar, **PARE e reporte** — o guia pode ter mudado desde esta spec.
> **Origem:** feedback do VectorForge (260630), sugestão nº 3. Causa-raiz de um round-trip de debug: âncora com literal Unicode não-ASCII (setas `→`, box-drawing `│├└─`) frágil a encoding/cópia. A correção é de PREVENÇÃO (orienta o gerador), independente de a causa real ter sido corrupção de encoding ou outra coisa.

## Objetivo

Acrescentar ao kit de ensino da IA uma regra explícita: **evitar caracteres não-ASCII como literais em `pattern`/`before`/`after`**; preferir `.*` (em `pattern`) ou recortar a âncora (`before`/`after`) para cair em texto **ASCII estável** ao redor do trecho Unicode, em vez de tentar casar a seta/box-drawing exata.

Isso NÃO muda o comportamento da ferramenta (o ASU continua aceitando qualquer caractere); muda só a ORIENTAÇÃO de quem gera a instrução, reduzindo a classe de erro "âncora não casa por causa de um glifo Unicode".

---

## Edição 1 — nova regra de ouro §4.7

**Arquivo:** `docs/INSTRUCTION_GUIDE.md`
**Âncora (fim da seção 4):** a regra §4.6 termina com o parágrafo que começa em
`Confira o caminho letra a letra contra o arquivo real.` e fecha com
`...(valor `null` existe e é removível).`
**Ação:** INSERIR, imediatamente APÓS esse parágrafo e ANTES do título `## 5. Detalhes que evitam fricção`, o bloco abaixo (com a linha em branco antes e depois):

```markdown
### 4.7 Âncoras em ASCII: não ancore em setas/box-drawing
Caracteres não-ASCII usados como literal na âncora (setas `→ ← ⟶`, traços
longos `— –`, box-drawing `│ ├ └ ─ ┌`, marcadores `• ◦`, aspas curvas `" " ' '`)
são uma fonte recorrente de "casou 0 vezes": variam por encoding, por cópia
entre editores e por normalização. Quando o trecho-alvo CONTÉM esses glifos:

- Em `pattern` (regex): use `.*` para saltar sobre o glifo e ancore em texto
  ASCII estável ao redor — ex.: em vez de `^├── src/` use `^.*src/`.
- Em `before`/`after` (âncora literal): recorte a âncora para começar/terminar
  num ponto ASCII — escolha a linha vizinha (ou o pedaço da linha) que não
  tenha o glifo. A âncora não precisa ser a linha inteira, só ser ÚNICA (§4.4).

Não é proibido casar um caractere Unicode (a ferramenta aceita), mas ancorar em
ASCII estável evita um round-trip de debug por um detalhe invisível.
```

## Edição 2 — linha nova na tabela erro→correção §6

**Arquivo:** `docs/INSTRUCTION_GUIDE.md`
**Âncora:** na tabela sob `## 6. Se o usuário colar um ERRO da ferramenta, corrija assim`,
a linha existente cujo "Erro contém…" é
`` `Encontrei um trecho parecido na linha X… indentação/os espaços diferem` ``.
**Ação:** INSERIR uma linha nova IMEDIATAMENTE APÓS essa linha (mantendo o
alinhamento de colunas do markdown):

```markdown
| `casou 0 vez(es)` numa âncora que tem seta/box-drawing/aspas curvas | Glifo não-ASCII na âncora não casou (encoding/cópia) | Reescreva a âncora em ASCII: `.*` no `pattern`, ou recorte `before`/`after` p/ texto ASCII vizinho (§4.7) |
```

> Nota de posição: esta linha é uma DICA de diagnóstico para o gerador. Ela NÃO
> corresponde a uma mensagem literal nova da ferramenta (o erro continua sendo
> `casou 0 vez(es)`); por isso o "Erro contém…" cita o sintoma observável
> (`casou 0 vez(es)` + presença do glifo), não uma string inédita.

---

## Ao concluir (Claude Code)

1. `git diff` — confira que SÓ `docs/INSTRUCTION_GUIDE.md` mudou, com as duas inserções acima e nada mais.
2. Sem build/teste (spec só de doc).
3. Commit (mensagem sem acento), sugerido:

```
docs(guide): regra 4.7 ancoras em ASCII (evitar setas/box-drawing) + linha na tabela erro->correcao
```

> Não fecha versão (é doc). O STATUS/IDEAS são atualizados pelo chat na mesma leva desta sessão.
