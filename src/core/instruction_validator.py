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

    # Passo 3 — unicidade de IDs (FIX-006): o JSON Schema não expressa isso.
    # IDs repetidos não corrompem a aplicação, mas tornam o relatório/diff
    # ambíguo e quebram qualquer referência futura por id (GUI, histórico).
    id_errors = _check_unique_ids(instruction)
    if id_errors:
        raise InstructionValidationError(id_errors)


def _check_unique_ids(instruction: dict[str, Any]) -> list[str]:
    """Acusa ids duplicados em ``files[]`` e em ``modifications[]`` de cada arquivo."""
    erros: list[str] = []
    vistos_files: dict[str, int] = {}
    for idx, file_entry in enumerate(instruction.get("files", [])):
        fid = file_entry.get("id")
        if fid in vistos_files:
            erros.append(
                f'files[{idx}].id: "{fid}" repetido (já usado em files[{vistos_files[fid]}]). '
                "Cada arquivo precisa de um id único."
            )
        else:
            vistos_files[fid] = idx
        vistos_mods: dict[str, int] = {}
        for midx, mod in enumerate(file_entry.get("modifications", [])):
            mid = mod.get("id")
            if mid in vistos_mods:
                erros.append(
                    f'files[{idx}].modifications[{midx}].id: "{mid}" repetido dentro do '
                    f'arquivo "{fid}" (já usado em modifications[{vistos_mods[mid]}]).'
                )
            else:
                vistos_mods[mid] = midx
    return erros


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


def _schema_error_hint(error: ValidationError) -> str | None:
    """Dica acionável (porquê + conserto) para erros de schema comuns, ou ``None``.

    Segue a filosofia de "erro acionável" (DEC-014/DEC-026): a mensagem crua do
    jsonschema diz O QUE violou, mas não COMO consertar. Hoje cobre o caso mais
    comum em instruções geradas por IA — âncora vazia (``minLength``) em
    ``location.before``/``after`` do ``replace_context_block``, que quase sempre
    significa que o bloco-alvo toca a borda do arquivo, onde essa estratégia não
    serve. Chaveia pelo VALIDADOR (``minLength``), não pelo texto da mensagem,
    para resistir a mudanças de wording entre versões do jsonschema.
    """
    campo = error.absolute_path[-1] if error.absolute_path else None
    if error.validator == "minLength" and campo in ("before", "after"):
        vizinha = "acima" if campo == "before" else "abaixo"
        return (
            f"a âncora '{campo}' está vazia. Use uma linha ASCII estável {vizinha} "
            "do bloco. Se o bloco vai até a borda do arquivo (topo/fim), "
            "'replace_context_block' não serve: prefira 'replace_line_pattern' ou "
            "'insert_before_pattern' ancorando numa linha existente, ou a "
            "estratégia própria do tipo ('replace_section' p/ Markdown, "
            "'replace_function' p/ Python)."
        )
    return None


def _format_error(error: ValidationError) -> str:
    """Converte um erro do jsonschema em mensagem PT-BR com o caminho do campo.

    Quando há dica acionável para o erro (ver :func:`_schema_error_hint`),
    acrescenta uma segunda linha indentada com o porquê + o conserto.
    """
    caminho = error.json_path  # ex.: "$.files[0].modifications[1].location.after"
    base = f"{caminho}: {error.message}"
    dica = _schema_error_hint(error)
    return f"{base}\n      Dica: {dica}" if dica else base
