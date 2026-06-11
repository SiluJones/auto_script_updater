"""Estratégias de modificação por tipo de arquivo (padrão Strategy — DEC-002).

Este módulo é o **registro**: mapeia o valor do campo ``strategy`` (do schema)
para a instância singleton da estratégia correspondente. O ``patch_engine`` usa
:func:`get_strategy` para resolver a estratégia de cada modificação.

As 13 estratégias da F1 cobrem três níveis de localização (semântico → contexto
→ regex) mais arquivo inteiro:

* Python (libcst): replace_function, replace_method, replace_class
* Texto universal (re): insert_after_pattern, insert_before_pattern,
  replace_line_pattern, replace_context_block
* Markdown: replace_section
* JSON (jmespath): set_json_path, append_json_array, delete_json_path
* Arquivo inteiro: replace_file, create_file
"""

from __future__ import annotations

from .base_strategy import BaseStrategy, StrategyError
from .file_strategy import CreateFile, ReplaceFile
from .json_strategy import AppendJsonArray, DeleteJsonPath, SetJsonPath
from .python_strategy import ReplaceClass, ReplaceFunction, ReplaceMethod
from .text_strategy import (
    InsertAfterPattern,
    InsertBeforePattern,
    ReplaceContextBlock,
    ReplaceLinePattern,
    ReplaceSection,
)

_STRATEGY_CLASSES: tuple[type[BaseStrategy], ...] = (
    ReplaceFunction,
    ReplaceMethod,
    ReplaceClass,
    InsertAfterPattern,
    InsertBeforePattern,
    ReplaceContextBlock,
    ReplaceLinePattern,
    ReplaceSection,
    SetJsonPath,
    AppendJsonArray,
    DeleteJsonPath,
    ReplaceFile,
    CreateFile,
)

#: Registro nome -> instância (estratégias são stateless, singletons bastam).
REGISTRY: dict[str, BaseStrategy] = {cls.name: cls() for cls in _STRATEGY_CLASSES}


def get_strategy(name: str) -> BaseStrategy:
    """Resolve a estratégia pelo nome do campo ``strategy``.

    Raises:
        StrategyError: se o nome não estiver registrado (não deveria ocorrer
            após a validação de schema, mas protege chamadas diretas).
    """
    try:
        return REGISTRY[name]
    except KeyError as exc:
        disponiveis = ", ".join(sorted(REGISTRY))
        raise StrategyError(
            f"Estratégia desconhecida: {name!r}. Disponíveis: {disponiveis}."
        ) from exc


__all__ = ["REGISTRY", "BaseStrategy", "StrategyError", "get_strategy"]
