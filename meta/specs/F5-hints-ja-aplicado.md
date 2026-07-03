# SPEC — F5 · Dicas "já aplicado?" no erro de âncora (substring + presença do new_content)

> **Tipo:** spec de FEATURE (código + doc), para o Claude Code implementar.
> **Autoria:** chat (planejamento). **Execução:** Claude Code (`src/strategies/text_strategy.py`, `tests/test_edge_cases.py`, `docs/INSTRUCTION_GUIDE.md`), rodando `python -m pytest`, `ruff check .`, `black --check .` ao final.
> **Âncoras** são SÍMBOLOS do código (função/método); antes de editar, `grep`-os no arquivo. Se um não existir como descrito, **PARE e reporte** — o código pode ter mudado desde esta spec.
> **Origem:** feedback do VectorForge (260630), sugestões nº 1 e nº 2.
> **Filosofia preservada (DEC-014):** isto melhora só a MENSAGEM de erro — continua sendo erro acionável, NUNCA aplica no lugar "parecido"/"já aplicado". O ASU segue *stateless* no projeto-alvo: **não cria ledger nem arquivo de estado** (a proposta original do `.asu-applied.json` foi REJEITADA — ver IDEAS/Descartadas). A detecção de "já aplicado" é feita em memória, no caminho de erro, comparando com o `new_content`/`content` da própria modificação — espelhando o que o `patch(1)` do Unix faz ("reversed/already applied" por inspeção do conteúdo, sem diário).

## Objetivo

Hoje, quando uma âncora casa **0 vezes**, o usuário/gerador recebe `casou 0 vez(es)` (pattern) ou `Âncora 'before' não encontrada` (context_block), com — quando aplicável — a dica de **whitespace** (`_whitespace_hint`). Faltam dois diagnósticos comuns:

1. **Substring (nº 1):** a âncora é parte de um identificador maior no arquivo
   (`doGen(` ⊂ `doGenRandom()`). Provável erro de digitação/escopo.
   → "não encontrei `doGen(`, mas encontrei `doGenRandom()` na linha N."
2. **Já aplicado (nº 2, opção sem-ledger):** a âncora não casa, mas o
   `new_content`/`content` que a modificação QUER escrever **já está presente**
   no arquivo. Forte sinal de que esta modificação já foi aplicada antes.
   → "isto provavelmente já foi aplicado (o conteúdo-alvo já está no arquivo)."

Ambos são DICAS anexadas à mensagem de erro existente; o erro continua sendo um erro (a modificação não casou). O nº 2 transforma um vermelho assustador num diagnóstico informativo dentro da própria mensagem.

---

## Desenho (mínimo que resolve)

Três funções de leitura novas em `text_strategy.py`, todas puras (sem efeito colateral, sem I/O), todas chamadas SÓ no caminho de erro:

- `_substring_hint(source, needle) -> str` — se `needle` (após `strip`) for
  substring de uma linha do `source` **sem casar a linha inteira**, devolve a
  dica com a linha e o nº; senão `""`. **Guarda anti-ruído:** só dispara se
  `needle.strip()` tiver **≥ 4 caracteres** (evita `id`, `(`, `=` casando em
  tudo). Para âncora multilinha, considera só a 1ª linha não-vazia do needle.
- `_already_applied_hint(source, payload) -> str` — se `payload` (o
  `new_content`/`content` da modificação, após `strip`) for **não-vazio** e
  **já estiver presente** em `source` (comparação tolerante a whitespace,
  reusando `_normalize_ws` por linha), devolve a dica "já aplicado?"; senão `""`.
- `_anchor_hints(source, needle, payload="") -> str` — **agregador**: concatena,
  na ordem, `_whitespace_hint` → `_substring_hint` → `_already_applied_hint`,
  retornando a primeira dica não-vazia de cada tipo (pode somar mais de uma).
  É o ÚNICO ponto que as estratégias chamam, para manter os call-sites enxutos.

> Por que um agregador: hoje `_whitespace_hint` é chamado solto. Centralizar em
> `_anchor_hints` evita repetir a sequência de `if`/concatenação em cada
> estratégia e dá um lugar único para evoluir a ordem das dicas.

### Detalhe crítico dos pattern-based (onde o erro nasce hoje)

Em `InsertAfterPattern`/`InsertBeforePattern` (`_InsertPattern.apply`) e
`ReplaceLinePattern.apply`, o "casou 0 vezes" é levantado DENTRO de
`_resolve_occurrence`, que **não tem `source` nem `new_content` em escopo** —
por isso esses caminhos não dão dica de whitespace hoje. A correção mínima é, no
`apply()` (que tem tudo em escopo), **detectar `len(matches) == 0` ANTES** de
chamar `_resolve_occurrence` e lançar `StrategyError` com as dicas; quando
`matches` não é vazio, segue chamando `_resolve_occurrence` como hoje (o caminho
de ambiguidade `>1 sem occurrence` permanece intacto).

`replace_context_block` (`_ReplaceContextBlock.apply`) já chama o hint
diretamente nos dois pontos (`before` não encontrado; `after` não encontrado) —
basta trocar `_whitespace_hint(...)` por `_anchor_hints(...)`, passando o
`new_content` como `payload` no ponto do `before` (no ponto do `after`, passar
`payload=""` — o conteúdo-alvo do "já aplicado" se refere ao bloco inteiro, que
o `before` já cobre; evita dica dupla).

---

## Edição 1 — novas funções em `text_strategy.py`

**Arquivo:** `src/strategies/text_strategy.py`
**Âncora:** logo APÓS a função `_whitespace_hint` (que termina com `return ""`,
antes da linha `class _InsertPattern(BaseStrategy):`).
**Ação:** INSERIR as três funções abaixo entre `_whitespace_hint` e
`class _InsertPattern`. (Docstrings em PT-BR; comentário explica o PORQUÊ.)

```python
def _substring_hint(source: str, needle: str) -> str:
    """Dica quando a âncora é SUBSTRING de um identificador maior no arquivo.

    Caso típico: a instrução pede ``doGen(`` mas o arquivo tem ``doGenRandom()``
    — provável erro de escopo/digitacao, OU a modificacao ja foi aplicada e o
    nome mudou. Damos a linha real para o gerador decidir. Nao aplica nada.

    Guarda anti-ruido: so dispara para needles com >= 4 caracteres uteis, senao
    um trecho curto (``id``, ``(``) casaria em qualquer lugar.
    """
    alvo = needle.strip().splitlines()[0].strip() if needle.strip() else ""
    if len(alvo) < 4:
        return ""
    for i, ln in enumerate(source.split("\n")):
        # substring presente, mas a linha inteira (normalizada) nao e a propria ancora
        if alvo in ln and _normalize_ws(ln) != _normalize_ws(alvo):
            return (
                f" Nao encontrei {alvo!r}, mas e SUBSTRING de algo na linha "
                f"{i + 1}: {ln.strip()!r}. Era esse o alvo (nome maior), ou a "
                f"modificacao ja foi aplicada?"
            )
    return ""


def _already_applied_hint(source: str, payload: str) -> str:
    """Dica quando o conteudo que a modificacao QUER escrever ja esta no arquivo.

    Sem ledger: espelha o ``patch(1)`` ("reversed/already applied" por inspecao
    do conteudo). Comparacao tolerante a whitespace (reusa ``_normalize_ws`` por
    linha) para nao falhar por reindentacao. So um aviso — nao altera o arquivo.
    """
    corpo = [_normalize_ws(ln) for ln in payload.strip().splitlines() if ln.strip()]
    if not corpo:
        return ""
    fonte = [_normalize_ws(ln) for ln in source.split("\n")]
    # procura a sequencia 'corpo' como subsequencia contigua (ignorando linhas vazias)
    n = len(corpo)
    janela = [ln for ln in fonte if ln != ""]
    for i in range(0, len(janela) - n + 1):
        if janela[i : i + n] == corpo:
            return (
                " Aviso: o conteudo-alvo desta modificacao ja parece presente no "
                "arquivo — ela provavelmente JA FOI APLICADA. Se for o caso, "
                "remova-a da instrucao."
            )
    return ""


def _anchor_hints(source: str, needle: str, payload: str = "") -> str:
    """Agrega as dicas de ancora na ordem: whitespace -> substring -> ja aplicado.

    Ponto unico que as estrategias chamam ao falhar uma ancora, para nao repetir
    a sequencia em cada call-site e centralizar a evolucao das dicas.
    """
    return (
        _whitespace_hint(source, needle)
        + _substring_hint(source, needle)
        + _already_applied_hint(source, payload)
    )
```

## Edição 2 — `_InsertPattern.apply`: erro com dicas quando 0 matches

**Arquivo:** `src/strategies/text_strategy.py`
**Âncora:** método `apply` da classe `_InsertPattern`, na linha
`occurrence = _resolve_occurrence(location, len(matches), f"Padrão {location['pattern']!r}")`.
**Ação:** INSERIR, IMEDIATAMENTE ANTES dessa linha, o bloco:

```python
        if not matches:
            raise StrategyError(
                f"Padrão {location['pattern']!r} casou 0 vez(es)."
                + _anchor_hints(source, location["pattern"], content)
            )
```

> `content` é o nome da variável já definida acima neste método (linha
> `content = modification.get("content", "")`). NÃO renomear.

## Edição 3 — `ReplaceLinePattern.apply`: idem

**Arquivo:** `src/strategies/text_strategy.py`
**Âncora:** método `apply` da classe `ReplaceLinePattern`, na linha
`occurrence = _resolve_occurrence(location, len(matches), f"Padrão {location['pattern']!r}")`.
**Ação:** INSERIR, IMEDIATAMENTE ANTES dessa linha, o bloco:

```python
        if not matches:
            raise StrategyError(
                f"Padrão {location['pattern']!r} casou 0 vez(es)."
                + _anchor_hints(source, location["pattern"], new_content)
            )
```

> `new_content` já está definido acima neste método. NÃO renomear.

## Edição 4 — `_ReplaceContextBlock.apply`: trocar hint solto pelo agregador

**Arquivo:** `src/strategies/text_strategy.py`
**Âncora A:** no `apply` de `_ReplaceContextBlock`, a linha que monta o erro de
`before`: `f"Âncora 'before' não encontrada: {before!r}.{_whitespace_hint(source, before)}"`.
**Ação A:** trocar `_whitespace_hint(source, before)` por
`_anchor_hints(source, before, new_content)`.

**Âncora B:** poucas linhas abaixo, a linha do erro de `after` que contém
`{_whitespace_hint(source[inner_start:], after)}`.
**Ação B:** trocar `_whitespace_hint(source[inner_start:], after)` por
`_anchor_hints(source[inner_start:], after)` (sem `payload` — evita dica dupla
de "já aplicado", já coberta pelo ramo do `before`).

> Não tocar na guarda existente "o new_content inclui as âncoras" nem em
> nenhuma outra linha do método.

## Edição 5 — testes

**Arquivo:** `tests/test_edge_cases.py`
**Ação:** acrescentar testes (nomes sugeridos; ajuste ao estilo do arquivo):

- `test_substring_hint_em_insert_after` — `pattern` = `def doGen\(` num source
  que só tem `def doGenRandom(`; espera `StrategyError` cuja mensagem contém
  `SUBSTRING` e `doGenRandom`.
- `test_already_applied_hint_replace_line` — `replace_line_pattern` cujo
  `pattern` não casa, mas o `new_content` já está como linha do source; espera
  mensagem contendo `JA FOI APLICADA` (sem acento, como no código).
- `test_already_applied_hint_context_block` — `replace_context_block` com
  `before` ausente e o `new_content` já presente no arquivo; espera a dica de
  já-aplicado.
- `test_substring_hint_ignora_ancora_curta` — needle de 1–3 chars (`id`) NÃO
  dispara a dica de substring (mensagem não contém `SUBSTRING`).
- `test_whitespace_hint_ainda_funciona` — regressão: um caso que hoje dá a dica
  de whitespace continua dando (garante que o agregador não a engoliu).

> Cobertura honesta: a dica de "já aplicado" cobre bem `text`/`pattern`/
> `context_block`. NÃO cobre `set_json_path`/`append_json_array` (estruturais)
> nem garante 100% dos casos de `replace_function` (libcst, outra estratégia) —
> ver IDEAS, item deixado EM ABERTO para refino futuro. Não tentar forçar aqui.

## Edição 6 — guia: ajustar a linha da tabela §6

**Arquivo:** `docs/INSTRUCTION_GUIDE.md`
**Âncora:** na tabela sob `## 6. Se o usuário colar um ERRO da ferramenta...`, a
linha cujo "Erro contém…" é
`` `casou N vezes e 'location.occurrence' não foi especificado` ``.
**Ação:** INSERIR, IMEDIATAMENTE ANTES dela, duas linhas novas:

```markdown
| `casou 0 vez(es)` + `é SUBSTRING de algo na linha N` | Âncora é parte de um nome maior, OU já aplicada | Use o nome COMPLETO indicado, ou remova a modificação se já aplicada |
| `provavelmente JA FOI APLICADA` | O conteúdo-alvo já está no arquivo | Remova esta modificação da instrução (não repita o que já foi aplicado) |
```

> Se a spec `F5-guia-ancora-ascii.md` (nota Unicode) já tiver sido aplicada,
> esta tabela terá ganho outra linha antes — as âncoras acima continuam válidas
> (referem-se a linhas DIFERENTES). Aplique na ordem que preferir; se a âncora
> exata não bater por uma inserção anterior, reposicione pela coluna "Erro
> contém…" indicada, não por número de linha.

---

## O que testar (resumo p/ o Code)

- **Caso feliz intacto:** âncora que casa 1 vez aplica normalmente (nenhuma dica,
  nenhum erro novo) — rode a suíte inteira, não deve haver regressão nas 128.
- **Ambiguidade intacta:** `>1 match sem occurrence` ainda dá o erro de
  ambiguidade (não foi tocado).
- **Bordas das dicas:** âncora curta não rui­dosa; whitespace ainda dispara;
  já-aplicado tolerante a reindentação.

## Ao concluir (Claude Code)

1. `python -m pytest` (espera 128 + ~5 novos = ~133 verdes), `ruff check .`, `black --check .`.
2. `git diff` — confira que mudaram só `src/strategies/text_strategy.py`, `tests/test_edge_cases.py` e `docs/INSTRUCTION_GUIDE.md`.
3. Commit (mensagem sem acento), sugerido:

```
feat(text): dicas 'ja aplicado' no erro de ancora (substring + presenca do new_content)
```

> Fecha um incremento de PRODUTO → bumpe `__version__` e abra entrada de CHANGELOG **somente** via `/wrap` (ou conforme o protocolo da sessão). O chat atualiza STATUS/DECISIONS/IDEAS na leva desta sessão; sugiro uma DEC nova ("dicas de âncora 'já aplicado' sem ledger — stateless preservado") referenciando DEC-014.
