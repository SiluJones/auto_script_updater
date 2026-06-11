"""Estratégias JSON: set, append e delete por caminho.

Localização (leitura) usa **jmespath** para encontrar o valor atual e dar erros
claros; a mutação usa um navegador de caminho próprio (jmespath é só de
consulta, não escreve). Caminhos suportados: chaves com ponto e índices de
lista — ``a.b.c`` e ``a.b[0].c`` — que cobrem o uso documentado.

O arquivo é parseado como JSON, mutado em memória e reserializado com
``indent=2`` e ``ensure_ascii=False`` (preserva acentuação) + newline final.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Any

from .base_strategy import BaseStrategy, StrategyError, get_location

_TOKEN_RE = re.compile(r"\.?([^.\[\]]+)|\[(\d+)\]")


def _require_jmespath():
    try:
        import jmespath  # noqa: WPS433
    except ImportError as exc:  # pragma: no cover
        raise StrategyError(
            "Estratégias JSON exigem 'jmespath'. Instale com: pip install jmespath"
        ) from exc
    return jmespath


def _parse_json(source: str) -> Any:
    if source.strip() == "":
        return {}
    try:
        return json.loads(source)
    except json.JSONDecodeError as exc:
        raise StrategyError(f"O arquivo JSON é inválido: {exc}.") from exc


def _dump_json(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


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


def _check_exists(jmespath, data: Any, path: str) -> Any:
    """Usa jmespath para ler o valor atual (None se ausente)."""
    try:
        return jmespath.search(path, data)
    except Exception:  # pragma: no cover - jmespath é tolerante
        return None


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
        return _dump_json(data)


class AppendJsonArray(BaseStrategy):
    """Anexa ``value`` à lista existente em ``location.path``."""

    name = "append_json_array"

    def apply(self, source: str, modification: Mapping[str, Any]) -> str:
        jmespath = _require_jmespath()
        location = get_location(modification)
        path = location["path"]
        value = modification.get("value")
        data = _parse_json(source)

        target = _check_exists(jmespath, data, path)
        if target is None:
            raise StrategyError(f"Caminho {path!r} não existe; não há lista para anexar.")
        if not isinstance(target, list):
            raise StrategyError(
                f"Caminho {path!r} aponta para {type(target).__name__}, não uma lista."
            )
        target.append(value)
        return _dump_json(data)


class DeleteJsonPath(BaseStrategy):
    """Remove o nó em ``location.path`` (chave de objeto ou item de lista)."""

    name = "delete_json_path"

    def apply(self, source: str, modification: Mapping[str, Any]) -> str:
        jmespath = _require_jmespath()
        location = get_location(modification)
        path = location["path"]
        data = _parse_json(source)
        tokens = _tokenize(path)

        if _check_exists(jmespath, data, path) is None:
            raise StrategyError(f"Caminho {path!r} não existe; nada a remover.")

        cursor = data
        for tok in tokens[:-1]:
            cursor = cursor[tok] if isinstance(tok, str) else cursor[tok]

        last = tokens[-1]
        try:
            if isinstance(last, str):
                del cursor[last]
            else:
                del cursor[last]
        except (KeyError, IndexError, TypeError) as exc:  # pragma: no cover
            raise StrategyError(f"Falha ao remover {path!r}: {exc}.") from exc
        return _dump_json(data)
