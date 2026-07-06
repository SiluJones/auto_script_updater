# SPEC — 260703-spec0001 · Canal de warnings no engine (avisos não-fatais)

> **Tipo:** FEATURE (código + testes). **Autoria:** chat. **Execução:** Claude Code.
> **Arquivos:** `src/strategies/base_strategy.py`, `src/core/patch_engine.py`, `src/strategies/text_strategy.py` (emissão inicial), `tests/`. NÃO altera a GUI (isso é a spec `260703-spec0002`).
> **Âncoras** são SÍMBOLOS/trechos do código; `grep`-os antes de editar. Se algum não existir como descrito, **PARE e reporte** — o código pode ter mudado.
> **Pré-requisito de:** `260703-spec0002` (indicador 🟡 na GUI). Esta spec entrega o CANO; a 0002 entrega a TORNEIRA. Aplicar esta primeiro.
> **Filosofia:** um warning é um **aviso não-fatal** — a modificação foi aplicada, mas com uma ressalva que o usuário deve ver. NÃO é erro (não aborta, não reverte) nem silêncio. Coexiste com a filosofia DEC-014 (erro = dica acionável): o warning é o degrau ANTES do erro, para casos onde aplicar é aceitável mas o usuário merece saber.

## Problema

Hoje o engine é binário por modificação: `strategy.apply()` devolve a string nova (sucesso) ou levanta `StrategyError` (falha → aborta/reverte). Não há um terceiro estado para "**aplicou, porém…**". Casos reais que hoje ou viram erro (drástico) ou passam calados (informação perdida):

- âncora casada por **fuzzy de whitespace** (indentação diferente da informada) — aplicou, mas convém avisar;
- `create_file` **sobrescreveu** um arquivo que já existia;
- `occurrence` ausente e havia exatamente 1 match — ok, mas dependeu de unicidade implícita (DEC-011);
- âncora casada adjacente a um trecho Unicode frágil (§4.7 do guia).

Este canal cria a terceira via: a estratégia **pode** emitir avisos que sobem pelo engine junto com o resultado, são coletados por modificação, e ficam disponíveis no relatório (para CLI e, na spec 0002, para a GUI).

## Desenho — menor toque possível nas 13 estratégias

**Princípio:** NÃO mudar a assinatura `apply(source, modification) -> str` de forma que quebre as 13 implementações e seus testes. Em vez disso, tornar o retorno **retrocompatível**: `apply` pode devolver `str` (como hoje) **ou** uma tupla `(str, list[str])` quando quiser emitir avisos. O engine normaliza os dois casos. Estratégias que não emitem warning **não mudam em nada**.

### Passo 1 — contrato opcional em `base_strategy.py`

**Arquivo:** `src/strategies/base_strategy.py`
**Âncora:** o docstring/assinatura do método `apply` em `BaseStrategy`.
**Ação:** atualizar o docstring de `apply` para documentar o retorno opcional em tupla, e adicionar um helper de normalização no módulo. NÃO tornar `apply` non-abstract; só documentar o novo contrato.

Adicionar ao final de `base_strategy.py` (após `get_location`):

```python
# Tipo do retorno de apply(): ou só o texto novo, ou (texto novo, avisos).
# Retrocompatível — estratégias que não avisam continuam retornando str puro.
ApplyResult = "str | tuple[str, list[str]]"


def split_apply_result(result: "str | tuple[str, list[str]]") -> tuple[str, list[str]]:
    """Normaliza o retorno de ``apply()``: sempre devolve ``(texto, avisos)``.

    Aceita tanto ``str`` (sem avisos) quanto ``(str, list[str])`` (com avisos),
    para que estratégias antigas — que retornam só o texto — sigam funcionando
    sem mudança. Avisos são mensagens curtas, PT-BR, não-fatais.
    """
    if isinstance(result, tuple):
        texto, avisos = result
        return texto, list(avisos)
    return result, []
```

E no docstring de `apply`, acrescentar após a descrição de `Returns`:

```
        Pode retornar, em vez de só a string, uma tupla ``(novo_conteudo, avisos)``
        onde ``avisos`` é uma lista de mensagens não-fatais (ressalvas que o
        usuário deve ver — ex.: âncora casada por fuzzy de whitespace, arquivo
        sobrescrito). Use ``split_apply_result`` no consumidor para normalizar.
```

### Passo 2 — `ModificationResult` carrega avisos

**Arquivo:** `src/core/patch_engine.py`
**Âncora:** a dataclass `ModificationResult`.
**Ação:** adicionar o campo `warnings`:

```python
@dataclass
class ModificationResult:
    """Resultado de uma única modificação."""

    mod_id: str
    strategy: str
    ok: bool
    error: str | None = None
    warnings: list[str] = field(default_factory=list)
```

> `field` já está importado no topo do arquivo (`from dataclasses import dataclass, field`). NÃO reimportar.

### Passo 3 — `FileResult` e `ApplyReport` propagam presença de avisos

**Arquivo:** `src/core/patch_engine.py`
**Âncora A:** dataclass `FileResult`. **Ação:** adicionar propriedade derivada (não campo novo — evita dessincronização) que diz se o arquivo tem avisos:

```python
    @property
    def has_warnings(self) -> bool:
        """True se qualquer modificação deste arquivo emitiu aviso não-fatal."""
        return any(m.warnings for m in self.modifications)
```

Inserir DENTRO da classe `FileResult`, após o campo `modifications`.

**Âncora B:** dataclass `ApplyReport`. **Ação:** adicionar propriedade análoga:

```python
    @property
    def has_warnings(self) -> bool:
        """True se qualquer arquivo do relatório tem avisos não-fatais."""
        return any(f.has_warnings for f in self.files)
```

### Passo 4 — o laço do engine coleta os avisos

**Arquivo:** `src/core/patch_engine.py`
**Âncora:** no laço `for mod in file_entry.get("modifications", [])`, a linha
`current = get_strategy(strat_name).apply(current, mod)` seguida de
`mod_results.append(ModificationResult(mod_id, strat_name, ok=True))`.
**Ação:** normalizar o retorno e anexar os avisos ao resultado:

```python
                resultado = get_strategy(strat_name).apply(current, mod)
                current, avisos = split_apply_result(resultado)
                mod_results.append(
                    ModificationResult(mod_id, strat_name, ok=True, warnings=avisos)
                )
```

> Requer importar `split_apply_result`. **Âncora do import:** a linha
> `from ..strategies import StrategyError, get_strategy`. **Ação:** trocar por
> `from ..strategies import StrategyError, get_strategy` + garantir que
> `split_apply_result` seja importável de `..strategies` (reexportar em
> `src/strategies/__init__.py` se necessário — ver Passo 5). Se preferir, importe
> direto: `from ..strategies.base_strategy import split_apply_result`.

### Passo 5 — reexport (se o Passo 4 importar de `..strategies`)

**Arquivo:** `src/strategies/__init__.py`
**Ação:** se `split_apply_result` for importado de `..strategies`, adicioná-lo ao
reexport ao lado de `StrategyError`/`get_strategy` (mesma linha de `from .base_strategy import ...`). Se o Passo 4 importou direto de `base_strategy`, **pular este passo**.

### Passo 6 — primeira estratégia a EMITIR um warning (piloto)

Para o canal não nascer vazio (e ser testável de ponta a ponta), fazer **uma** emissão real, de baixo risco:

**Arquivo:** `src/strategies/text_strategy.py`
**Alvo:** `_ReplaceContextBlock.apply` — quando a âncora `before`/`after` casa via
**fuzzy de whitespace** (o mesmo caminho que hoje já detecta e usa
`_normalize_ws`/`_whitespace_hint`), emitir um aviso em vez de aplicar em silêncio.
**Ação:** onde a estratégia decide usar um match tolerante a whitespace (após o
match exato falhar mas o normalizado casar), acumular:

```python
            avisos.append(
                f"Âncora casada ignorando espaços/indentação (o texto exato diferia): {ancora!r}."
            )
```

e retornar `(resultado, avisos)` em vez de só `resultado`. Se `_ReplaceContextBlock`
hoje só casa exato (sem fuzzy no caminho de sucesso), então o piloto vai para a
estratégia que tiver fuzzy no sucesso; se NENHUMA tem fuzzy no caminho de sucesso
(só no de erro/dica), o piloto passa a ser o **`create_file` sobrescrevendo**:

**Alvo alternativo (mais garantido):** a estratégia `create_file`
(`src/strategies/file_strategy.py` ou onde estiver). Quando `source != ""` (o
arquivo já existia e será sobrescrito), emitir:

```python
        if source:
            return novo_conteudo, [
                "create_file sobre arquivo existente: o conteúdo anterior foi substituído."
            ]
        return novo_conteudo
```

> O Code escolhe o alvo do piloto conforme o código real: preferir `create_file`
> sobrescrevendo (condição objetiva e fácil de testar). O importante é haver
> **pelo menos uma** emissão real para exercitar o canal.

## Testes

**Arquivo:** `tests/test_patch_engine.py` (+ `tests/test_strategies.py` se o piloto for numa estratégia).

- `test_split_apply_result_str` — `split_apply_result("x")` → `("x", [])`.
- `test_split_apply_result_tupla` — `split_apply_result(("x", ["a"]))` → `("x", ["a"])`.
- `test_modification_result_carrega_warnings` — `ModificationResult` aceita `warnings`.
- `test_engine_coleta_warning_do_piloto` — instrução que dispara o piloto (ex.: `create_file` sobre arquivo existente) → `report.ok is True`, a modificação aplicou, `report.has_warnings is True`, e a mensagem certa está em `mod.warnings`.
- `test_engine_sem_warning_fica_limpo` — instrução comum (estratégia que não avisa) → `report.has_warnings is False` e as 13 estratégias antigas seguem retornando `str` sem erro (regressão).
- `test_warning_nao_aborta_nem_reverte` — o warning NÃO muda `report.ok`, NÃO dispara rollback, NÃO marca o arquivo como `failed`.

## O que NÃO fazer

- NÃO mudar a assinatura de `apply` para forçar tupla — quebraria as 13 estratégias. O retorno é **opcional**.
- NÃO transformar warning em erro nem em bloqueio de aplicação.
- NÃO tocar na GUI (é a spec 0002).
- NÃO inventar warnings em massa nas 13 estratégias agora — só o piloto. Emissões adicionais entram sob demanda, cada uma com seu teste (registrar como follow-up no IDEAS).

## Ao concluir (Claude Code)

1. `python -m pytest` (133 + ~6 novos), `ruff check .`, `black --check .`.
2. `git diff` — confira que mudaram só os arquivos previstos (base_strategy, patch_engine, o do piloto, __init__ se aplicável, e os testes).
3. Commit (mensagem sem acento):

```
feat(engine): canal de warnings nao-fatais (retorno opcional em tupla) + piloto
```

> Fecha incremento de PRODUTO → bump de `__version__` e entrada de CHANGELOG via `/wrap`. Sugerir **DEC** nova ("canal de warnings: terceiro estado entre sucesso e erro; retorno opcional em tupla p/ não quebrar as 13 estratégias") referenciando DEC-002 (Strategy) e DEC-014 (erro acionável). O chat cuida de STATUS/IDEAS/ROADMAP.
