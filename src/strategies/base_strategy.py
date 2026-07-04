"""Contrato comum a todas as estratégias de modificação (DEC-002, Strategy pattern).

Cada estratégia recebe o **texto atual** de um arquivo e devolve o **texto novo**
completo. Estratégias que operam sobre estruturas (JSON) parseiam o texto,
mutam e reserializam — mas a interface externa é sempre ``str -> str``. Isso
mantém o ``patch_engine`` uniforme: ler texto, aplicar, escrever texto.

Localização é responsabilidade de cada estratégia, guiada exclusivamente pelo
campo ``location`` da modificação (a ``strategy`` é a fonte única de como
interpretá-lo — ver schema/DECISIONS.md).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any


class StrategyError(Exception):
    """Falha ao localizar o alvo ou ao aplicar a modificação.

    Mensagem deve ser acionável (dizer o que não casou e, quando útil, o que
    existe no arquivo) para o usuário corrigir a instrução rapidamente.
    """


class BaseStrategy(ABC):
    """Algoritmo de localização+aplicação de uma única modificação.

    Subclasses declaram ``name`` (a chave usada no campo ``strategy`` do schema)
    e implementam :meth:`apply`. São *stateless* — uma instância única por
    estratégia é registrada em ``strategies/__init__.py``.
    """

    #: Chave da estratégia no schema (ex.: "replace_function").
    name: str = ""

    @abstractmethod
    def apply(self, source: str, modification: Mapping[str, Any]) -> str:
        """Aplica a modificação a ``source`` e retorna o conteúdo novo completo.

        Args:
            source: Texto atual do arquivo. ``""`` quando o arquivo não existe
                (caso de ``create_file``).
            modification: Bloco de modificação já validado contra o schema.

        Returns:
            O novo conteúdo completo do arquivo.

            Pode retornar, em vez de só a string, uma tupla ``(novo_conteudo, avisos)``
            onde ``avisos`` é uma lista de mensagens não-fatais (ressalvas que o
            usuário deve ver — ex.: âncora casada por fuzzy de whitespace, arquivo
            sobrescrito). Use ``split_apply_result`` no consumidor para normalizar.

        Raises:
            StrategyError: se o alvo não for encontrado, for ambíguo, ou a
                aplicação falhar.
        """
        raise NotImplementedError


def get_location(modification: Mapping[str, Any]) -> dict[str, Any]:
    """Atalho: devolve o dict ``location`` (ou ``{}`` se ausente)."""
    loc = modification.get("location") or {}
    if not isinstance(loc, dict):  # pragma: no cover - schema já garante
        raise StrategyError("Campo 'location' deveria ser um objeto.")
    return loc


# Tipo do retorno de apply(): ou só o texto novo, ou (texto novo, avisos).
# Retrocompatível — estratégias que não avisam continuam retornando str puro.
ApplyResult = "str | tuple[str, list[str]]"


def split_apply_result(result: str | tuple[str, list[str]]) -> tuple[str, list[str]]:
    """Normaliza o retorno de ``apply()``: sempre devolve ``(texto, avisos)``.

    Aceita tanto ``str`` (sem avisos) quanto ``(str, list[str])`` (com avisos),
    para que estratégias antigas — que retornam só o texto — sigam funcionando
    sem mudança. Avisos são mensagens curtas, PT-BR, não-fatais.
    """
    if isinstance(result, tuple):
        texto, avisos = result
        return texto, list(avisos)
    return result, []
