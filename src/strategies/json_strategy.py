"""Estratégias JSON: set, append e delete por caminho.

Caminhos suportados: chaves com ponto e índices de lista — ``a.b.c`` e
``a.b[0].c``. A navegação (leitura e escrita) usa um navegador próprio que,
diferente de bibliotecas de consulta como jmespath, **distingue "chave
ausente" de "valor null"** (FIX-005) — sem isso, era impossível deletar uma
chave cujo valor é ``null``.

Estilo de serialização (FIX-004): o estilo do arquivo ORIGINAL é detectado e
preservado — indentação (2/4/tab), formato compacto de uma linha e presença
do newline final. Antes, tudo era reserializado com ``indent=2``, o que
reformatava o arquivo inteiro e explodia o diff. ``ensure_ascii=False``
preserva acentuação.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Any

from .base_strategy import BaseStrategy, StrategyError, get_location

_TOKEN_RE = re.compile(r"\.?([^.\[\]]+)|\[(\d+)\]")

# Primeira linha indentada de um JSON multilinha: captura a indentação base.
_INDENT_RE = re.compile(r'\n([ \t]+)["{\[\d]')

# Sentinela para distinguir "não achei" de "achei o valor None (null)".
_MISSING = object()


def _parse_json(source: str) -> Any:
    if source.strip() == "":
        return {}
    try:
        return json.loads(source)
    except json.JSONDecodeError as exc:
        raise StrategyError(f"O arquivo JSON é inválido: {exc}.") from exc


def _detect_style(source: str) -> tuple[int | str | None, str]:
    """Detecta (indent, trailing_newline) do JSON original.

    indent: nº de espaços, "\\t" para tab, ou None para formato compacto
    (uma linha). Para fonte vazia (arquivo novo), usa o padrão (2, "\\n").
    """
    if source.strip() == "":
        return 2, "\n"
    trailing = "\n" if source.endswith("\n") else ""
    m = _INDENT_RE.search(source)
    if not m:
        return None, trailing  # compacto: sem linha indentada
    ws = m.group(1)
    if ws.startswith("\t"):
        return "\t", trailing
    return len(ws), trailing


def _dump_json(data: Any, source: str) -> str:
    """Serializa preservando o estilo do original (FIX-004)."""
    indent, trailing = _detect_style(source)
    if indent is None:
        return json.dumps(data, ensure_ascii=False, separators=(", ", ": ")) + trailing
    return json.dumps(data, indent=indent, ensure_ascii=False) + trailing


def _tokenize(path: str) -> list[Any]:
    """Quebra um caminho em tokens (str para chave, int para índice de lista)."""
    tokens: list[Any] = []
    pos = 0
    for m in _TOKEN_RE.finditer(path):
        if m.start() != pos:
            raise StrategyError(f"Caminho JSON malformado perto de {path[pos:]!r} em {path!r}.")
        pos = m.end()
        key, index = m.group(1), m.group(2)
        tokens.append(int(index) if index is not None else key)
    if pos != len(path) or not tokens:
        raise StrategyError(f"Caminho JSON inválido: {path!r}.")
    return tokens


def _walk(data: Any, tokens: list[Any]) -> Any:
    """Caminha pelos tokens. Retorna o valor encontrado ou ``_MISSING``.

    Diferente do jmespath, devolve o valor REAL mesmo quando é ``None`` (null
    no JSON) — ausência é sinalizada pela sentinela, não por None (FIX-005).
    """
    cursor = data
    for tok in tokens:
        if isinstance(tok, str):
            if not isinstance(cursor, dict) or tok not in cursor:
                return _MISSING
            cursor = cursor[tok]
        else:
            if not isinstance(cursor, list) or tok >= len(cursor):
                return _MISSING
            cursor = cursor[tok]
    return cursor


class SetJsonPath(BaseStrategy):
    """Define (criando intermediários) o valor em ``location.path``."""

    name = "set_json_path"

    def apply(self, source: str, modification: Mapping[str, Any]) -> str:
        location = get_location(modification)
        path = location["path"]
        value = modification.get("value")
        data = _parse_json(source)
        tokens = _tokenize(path)

        cursor = data
        for i, tok in enumerate(tokens[:-1]):
            nxt = tokens[i + 1]
            if isinstance(tok, str):
                if not isinstance(cursor, dict):
                    raise StrategyError(f"Esperava objeto em '{tok}' no caminho {path!r}.")
                if tok not in cursor or cursor[tok] is None:
                    cursor[tok] = [] if isinstance(nxt, int) else {}
                cursor = cursor[tok]
            else:  # índice de lista
                if not isinstance(cursor, list):
                    raise StrategyError(f"Esperava lista no índice [{tok}] do caminho {path!r}.")
                if tok >= len(cursor):
                    raise StrategyError(f"Índice [{tok}] fora dos limites no caminho {path!r}.")
                cursor = cursor[tok]

        last = tokens[-1]
        if isinstance(last, str):
            if not isinstance(cursor, dict):
                raise StrategyError(f"Esperava objeto para a chave '{last}' em {path!r}.")
            cursor[last] = value
        else:
            if not isinstance(cursor, list) or last >= len(cursor):
                raise StrategyError(f"Índice [{last}] inválido para atribuição em {path!r}.")
            cursor[last] = value
        return _dump_json(data, source)


class AppendJsonArray(BaseStrategy):
    """Anexa ``value`` à lista existente em ``location.path``."""

    name = "append_json_array"

    def apply(self, source: str, modification: Mapping[str, Any]) -> str:
        location = get_location(modification)
        path = location["path"]
        value = modification.get("value")
        data = _parse_json(source)

        target = _walk(data, _tokenize(path))
        if target is _MISSING:
            raise StrategyError(f"Caminho {path!r} não existe; não há lista para anexar.")
        if target is None:
            raise StrategyError(
                f"Caminho {path!r} existe mas vale null, não uma lista. "
                "Use set_json_path para defini-lo como lista primeiro."
            )
        if not isinstance(target, list):
            raise StrategyError(
                f"Caminho {path!r} aponta para {type(target).__name__}, não uma lista."
            )
        target.append(value)
        return _dump_json(data, source)


class DeleteJsonPath(BaseStrategy):
    """Remove o nó em ``location.path`` (chave de objeto ou item de lista)."""

    name = "delete_json_path"

    def apply(self, source: str, modification: Mapping[str, Any]) -> str:
        location = get_location(modification)
        path = location["path"]
        data = _parse_json(source)
        tokens = _tokenize(path)

        # Existência via navegador próprio: um valor null EXISTE e é removível.
        if _walk(data, tokens) is _MISSING:
            raise StrategyError(f"Caminho {path!r} não existe; nada a remover.")

        cursor = _walk(data, tokens[:-1]) if len(tokens) > 1 else data
        last = tokens[-1]
        try:
            del cursor[last]
        except (KeyError, IndexError, TypeError) as exc:  # pragma: no cover
            raise StrategyError(f"Falha ao remover {path!r}: {exc}.") from exc
        return _dump_json(data, source)
