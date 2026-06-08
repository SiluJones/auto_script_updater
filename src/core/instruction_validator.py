"""Valida a instrução parseada contra o JSON Schema v1 e a versão de formato.

Fluxo (ver DEC-007):
1. Confere ``format_version`` e rejeita famílias de *major* incompatíveis com
   mensagem clara, ANTES de qualquer outra checagem.
2. Valida a estrutura inteira contra ``schemas/instruction_v1.schema.json``,
   acumulando TODOS os erros encontrados, cada um com o caminho do campo, em
   mensagens PT-BR legíveis.

Ver GLOSSARY.md ("instruction_validator").
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator
from jsonschema.exceptions import ValidationError

# Major do schema suportado por esta versão da ferramenta (DEC-007).
SUPPORTED_SCHEMA_MAJOR = 1

# Caminho do schema, relativo a este módulo (src/core/ -> src/schemas/).
_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "instruction_v1.schema.json"


class InstructionValidationError(Exception):
    """Instrução não conforme. Carrega a lista de problemas encontrados."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__(self._render())

    def _render(self) -> str:
        cabecalho = "Instrução inválida — problemas encontrados:"
        linhas = "\n".join(f"  - {e}" for e in self.errors)
        return f"{cabecalho}\n{linhas}"


@lru_cache(maxsize=1)
def _load_schema() -> dict[str, Any]:
    """Carrega (e memoiza) o JSON Schema da instrução."""
    try:
        return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:  # pragma: no cover - erro de instalação
        raise InstructionValidationError(
            [f"Schema não encontrado em {_SCHEMA_PATH}. Instalação corrompida?"]
        ) from exc


def validate(instruction: dict[str, Any]) -> None:
    """Valida a instrução. Não retorna nada em caso de sucesso.

    Args:
        instruction: Instrução já parseada (dict) vinda do ``instruction_parser``.

    Raises:
        InstructionValidationError: se a versão de formato for incompatível ou a
            estrutura violar o schema. A exceção lista todos os problemas de uma vez.
    """
    # Passo 1 — versão de formato primeiro (DEC-007).
    version_errors = _check_format_version(instruction)
    if version_errors:
        raise InstructionValidationError(version_errors)

    # Passo 2 — validação estrutural completa contra o JSON Schema.
    validator = Draft7Validator(_load_schema())
    errors = sorted(validator.iter_errors(instruction), key=lambda e: list(e.absolute_path))
    if errors:
        raise InstructionValidationError([_format_error(e) for e in errors])


def _check_format_version(instruction: dict[str, Any]) -> list[str]:
    """Confere presença e compatibilidade de ``format_version``."""
    raw = instruction.get("format_version")
    if raw is None:
        return ['Campo obrigatório ausente: "format_version" (ex.: "1.0").']
    if not isinstance(raw, str):
        return [f'"format_version" deve ser string (ex.: "1.0"); recebido: {type(raw).__name__}.']
    try:
        major = int(raw.split(".", 1)[0])
    except (ValueError, IndexError):
        return [f'"format_version" malformado: {raw!r}. Use o formato "MAJOR.MINOR" (ex.: "1.0").']
    if major != SUPPORTED_SCHEMA_MAJOR:
        return [
            f"Instrução em formato {raw!r} (major {major}); esta ferramenta suporta "
            f"a família {SUPPORTED_SCHEMA_MAJOR}.x. Regenere a instrução no formato suportado."
        ]
    return []


def _format_error(error: ValidationError) -> str:
    """Converte um erro do jsonschema em mensagem PT-BR com o caminho do campo."""
    caminho = error.json_path  # ex.: "$.files[0].modifications[1].strategy"
    return f"{caminho}: {error.message}"
