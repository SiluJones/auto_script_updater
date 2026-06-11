"""Carrega e deserializa arquivos de instrução YAML/JSON.

Responsabilidade única: ler o conteúdo (de disco ou de uma string) e devolver
um dicionário Python. NÃO valida o conteúdo — isso é tarefa do
``instruction_validator`` (ver GLOSSARY.md). JSON é aceito por ser subconjunto
de YAML (DEC-004).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class InstructionParseError(Exception):
    """Falha de I/O ou de sintaxe ao ler/parsear o arquivo de instrução."""


class _StrictLoader(yaml.SafeLoader):
    """SafeLoader que rejeita chaves duplicadas (FIX-006).

    O PyYAML padrão aceita ``{a: 1, a: 2}`` silenciosamente (a última vence) —
    num arquivo gerado por IA, uma chave repetida faria metade da instrução
    evaporar sem aviso. Aqui, duplicata vira erro de parse com linha/coluna.
    """


def _construct_mapping_no_dups(loader: _StrictLoader, node: yaml.MappingNode, deep: bool = False):
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                None,
                None,
                f"chave duplicada no YAML: {key!r} (a primeira ocorrência seria descartada)",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_StrictLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping_no_dups
)


# Ordem de tentativa de encoding ao abrir o arquivo.
# UTF-8 primeiro; CP-1252 como contingência para arquivos legados do Windows
# sem BOM (ver Armadilha #3 no CONTEXT.md).
_ENCODINGS_FALLBACK: tuple[str, ...] = ("utf-8", "cp1252")


def load_instruction(path: str | Path) -> dict[str, Any]:
    """Lê um arquivo de instrução do disco e retorna o dict parseado.

    Args:
        path: Caminho do arquivo ``.yaml``/``.yml``/``.json``.

    Returns:
        Instrução deserializada como dicionário (ainda NÃO validada).

    Raises:
        InstructionParseError: arquivo inexistente, ilegível em todos os
            encodings suportados, ou conteúdo YAML/JSON inválido/vazio.
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise InstructionParseError(f"Arquivo de instrução não encontrado: {file_path}")

    text = _read_text_with_fallback(file_path)
    return _parse(text, source=str(file_path))


def load_instruction_from_string(text: str, *, source: str = "<string>") -> dict[str, Any]:
    """Parseia uma instrução a partir de uma string (ex.: colada da área de transferência).

    Suporta o fluxo "Colar instrução" planejado para a GUI (ver IDEAS.md).

    Args:
        text: Conteúdo YAML/JSON da instrução.
        source: Rótulo de origem usado nas mensagens de erro.

    Returns:
        Instrução deserializada como dicionário (ainda NÃO validada).

    Raises:
        InstructionParseError: conteúdo YAML/JSON inválido/vazio.
    """
    return _parse(text, source=source)


def _read_text_with_fallback(file_path: Path) -> str:
    """Lê o arquivo tentando UTF-8 e, em falha, CP-1252.

    Registra um aviso quando precisa recorrer à contingência, para que o
    CLI/GUI possa informar o usuário qual encoding foi detectado.
    """
    last_error: UnicodeDecodeError | None = None
    for encoding in _ENCODINGS_FALLBACK:
        try:
            text = file_path.read_text(encoding=encoding)
        except UnicodeDecodeError as exc:
            last_error = exc
            continue
        if encoding != "utf-8":
            logger.warning(
                "Arquivo %s lido com encoding de contingência '%s' (não era UTF-8 válido).",
                file_path,
                encoding,
            )
        return text
    raise InstructionParseError(
        f"Não foi possível decodificar {file_path} como UTF-8 nem CP-1252."
    ) from last_error


def _parse(text: str, *, source: str) -> dict[str, Any]:
    """Parseia com o loader estrito e garante que o resultado é um mapeamento."""
    try:
        data = yaml.load(text, Loader=_StrictLoader)  # noqa: S506 (SafeLoader estendido)
    except yaml.YAMLError as exc:
        raise InstructionParseError(f"YAML/JSON inválido em {source}: {exc}") from exc

    if data is None:
        raise InstructionParseError(f"A instrução em {source} está vazia.")
    if not isinstance(data, dict):
        raise InstructionParseError(
            f"A instrução em {source} deve ser um objeto (mapeamento), "
            f"mas foi parseada como {type(data).__name__}."
        )
    return data
