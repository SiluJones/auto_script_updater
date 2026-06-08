"""Estratégias de arquivo inteiro: substituir tudo ou criar do zero (DEC-008).

Unificam os dois modos do fluxo de transferência de contexto: a IA pode emitir
uma instrução que **cria o projeto inteiro** (vários ``create_file``) ou que faz
um **patch cirúrgico** (estratégias semânticas/contexto). Ambas no mesmo schema.
"""
from __future__ import annotations

from typing import Any, Mapping

from .base_strategy import BaseStrategy


class ReplaceFile(BaseStrategy):
    """Substitui todo o conteúdo do arquivo por ``new_content``."""

    name = "replace_file"

    def apply(self, source: str, modification: Mapping[str, Any]) -> str:
        return modification.get("new_content", "")


class CreateFile(BaseStrategy):
    """Cria o arquivo com ``content`` (o engine cuida de diretórios pais)."""

    name = "create_file"

    def apply(self, source: str, modification: Mapping[str, Any]) -> str:
        return modification.get("content", "")
