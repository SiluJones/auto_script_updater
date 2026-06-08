"""Testes da camada de intake: parser, validator e validade do schema."""
from __future__ import annotations

from pathlib import Path

import pytest
from jsonschema import Draft7Validator

from src.core.instruction_parser import (
    InstructionParseError,
    load_instruction,
    load_instruction_from_string,
)
from src.core.instruction_validator import (
    InstructionValidationError,
    _load_schema,
    validate,
)

EXEMPLO = Path(__file__).resolve().parent.parent / "examples" / "exemplo_instrucao.yaml"


# ── Schema ─────────────────────────────────────────────────────────────────
def test_schema_eh_draft7_valido() -> None:
    """O próprio JSON Schema deve ser um Draft 7 bem-formado."""
    Draft7Validator.check_schema(_load_schema())


# ── Parser ─────────────────────────────────────────────────────────────────
def test_parser_arquivo_inexistente() -> None:
    with pytest.raises(InstructionParseError):
        load_instruction("nao_existe_123.yaml")


def test_parser_yaml_invalido() -> None:
    with pytest.raises(InstructionParseError):
        load_instruction_from_string("a: [1, 2\n  b: nope")


def test_parser_rejeita_string_vazia() -> None:
    with pytest.raises(InstructionParseError):
        load_instruction_from_string("   ")


def test_parser_rejeita_nao_objeto() -> None:
    with pytest.raises(InstructionParseError):
        load_instruction_from_string("- apenas\n- uma\n- lista")


# ── Validator ──────────────────────────────────────────────────────────────
def test_exemplo_oficial_eh_valido() -> None:
    """O exemplo distribuído deve passar parser + validator sem erros."""
    instrucao = load_instruction(EXEMPLO)
    validate(instrucao)  # não deve levantar


def test_validator_rejeita_versao_incompativel() -> None:
    instrucao = {"format_version": "2.0", "description": "x", "files": []}
    with pytest.raises(InstructionValidationError) as info:
        validate(instrucao)
    assert "1.x" in str(info.value)  # cita a família suportada


def test_validator_exige_format_version() -> None:
    instrucao = {"description": "x", "files": []}
    with pytest.raises(InstructionValidationError) as info:
        validate(instrucao)
    assert "format_version" in str(info.value)


def test_validator_acumula_erro_com_caminho_de_campo() -> None:
    """Modificação sem 'strategy' → erro citando o campo."""
    instrucao = {
        "format_version": "1.0",
        "description": "teste",
        "files": [
            {
                "id": "f1",
                "path_mode": "relative",
                "relative_path": "x.py",
                "type": "python",
                "modifications": [{"id": "m1", "description": "sem strategy"}],
            }
        ],
    }
    with pytest.raises(InstructionValidationError) as info:
        validate(instrucao)
    assert "strategy" in str(info.value)


def test_validator_path_relative_exige_relative_path() -> None:
    instrucao = {
        "format_version": "1.0",
        "description": "teste",
        "files": [
            {
                "id": "f1",
                "path_mode": "relative",
                "type": "text",
                "modifications": [
                    {
                        "id": "m1",
                        "description": "cria arquivo",
                        "strategy": "create_file",
                        "content": "olá",
                    }
                ],
            }
        ],
    }
    with pytest.raises(InstructionValidationError) as info:
        validate(instrucao)
    assert "relative_path" in str(info.value)


def test_validator_replace_function_exige_name_no_location() -> None:
    instrucao = {
        "format_version": "1.0",
        "description": "teste",
        "files": [
            {
                "id": "f1",
                "path_mode": "relative",
                "relative_path": "x.py",
                "type": "python",
                "modifications": [
                    {
                        "id": "m1",
                        "description": "troca função sem dizer o nome",
                        "strategy": "replace_function",
                        "location": {},
                        "new_content": "def f(): ...",
                    }
                ],
            }
        ],
    }
    with pytest.raises(InstructionValidationError) as info:
        validate(instrucao)
    assert "name" in str(info.value)
