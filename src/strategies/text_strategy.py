"""Estratégias de texto universais (re + difflib).

Operam sobre texto cru e, por isso, funcionam em **qualquer linguagem** (type =
"text"): JavaScript, Rust, Go, etc. São o mecanismo de fallback quando não há
parser semântico — equivalentes em espírito ao *apply_patch* por contexto.

Convenção de newline: preservamos o conteúdo como veio; o ``patch_engine`` é
quem decide o estilo de quebra de linha ao gravar em disco.
"""
from __future__ import annotations

import re
from typing import Any, Mapping

from .base_strategy import BaseStrategy, StrategyError, get_location


def _compile(pattern: str) -> re.Pattern[str]:
    try:
        return re.compile(pattern)
    except re.error as exc:
        raise StrategyError(f"Regex inválido em location.pattern: {pattern!r} ({exc}).") from exc


def _split_lines(source: str) -> list[str]:
    """Divide preservando os terminadores de linha (keepends)."""
    return source.splitlines(keepends=True)


def _matching_line_indices(lines: list[str], regex: re.Pattern[str]) -> list[int]:
    return [i for i, line in enumerate(lines) if regex.search(line)]


def _ensure_trailing_newline(text: str) -> str:
    return text if text.endswith("\n") else text + "\n"


class _InsertPattern(BaseStrategy):
    """Insere ``content`` antes/depois da N-ésima linha que casa o regex."""

    after = True  # subclasses definem

    def apply(self, source: str, modification: Mapping[str, Any]) -> str:
        location = get_location(modification)
        regex = _compile(location["pattern"])
        occurrence = int(location.get("occurrence", 1))
        content = modification.get("content", "")

        lines = _split_lines(source)
        matches = _matching_line_indices(lines, regex)
        if len(matches) < occurrence:
            raise StrategyError(
                f"Padrão {location['pattern']!r} casou {len(matches)} vez(es); "
                f"a instrução pediu a ocorrência {occurrence}."
            )
        target = matches[occurrence - 1]
        block = _ensure_trailing_newline(content)

        if self.after:
            # Garante que a linha-âncora termine em newline antes de inserir após ela.
            if not lines[target].endswith("\n"):
                lines[target] = lines[target] + "\n"
            lines.insert(target + 1, block)
        else:
            lines.insert(target, block)
        return "".join(lines)


class InsertAfterPattern(_InsertPattern):
    name = "insert_after_pattern"
    after = True


class InsertBeforePattern(_InsertPattern):
    name = "insert_before_pattern"
    after = False


class ReplaceLinePattern(BaseStrategy):
    """Substitui a linha inteira que casa o regex por ``new_content``."""

    name = "replace_line_pattern"

    def apply(self, source: str, modification: Mapping[str, Any]) -> str:
        location = get_location(modification)
        regex = _compile(location["pattern"])
        occurrence = int(location.get("occurrence", 1))
        new_content = modification.get("new_content", "")

        lines = _split_lines(source)
        matches = _matching_line_indices(lines, regex)
        if len(matches) < occurrence:
            raise StrategyError(
                f"Padrão {location['pattern']!r} casou {len(matches)} vez(es); "
                f"a instrução pediu a ocorrência {occurrence}."
            )
        target = matches[occurrence - 1]
        # Preserva o terminador de linha original (\n, \r\n ou ausente no fim do arquivo).
        original = lines[target]
        ending = ""
        if original.endswith("\r\n"):
            ending = "\r\n"
        elif original.endswith("\n"):
            ending = "\n"
        lines[target] = new_content.rstrip("\r\n") + ending
        return "".join(lines)


class ReplaceContextBlock(BaseStrategy):
    """Substitui o bloco entre as âncoras ``before`` e ``after`` (universal).

    ``before`` e ``after`` são trechos literais (não regex) que delimitam o
    bloco e **permanecem** no arquivo; tudo entre eles é trocado por
    ``new_content``. Como o mesmo modelo que gera o código escolhe as âncoras,
    é trivial torná-las únicas (ver DECISIONS.md).
    """

    name = "replace_context_block"

    @staticmethod
    def _nth_index(haystack: str, needle: str, n: int) -> int:
        idx = -1
        for _ in range(n):
            idx = haystack.find(needle, idx + 1)
            if idx == -1:
                return -1
        return idx

    def apply(self, source: str, modification: Mapping[str, Any]) -> str:
        location = get_location(modification)
        before = location["before"]
        after = location["after"]
        occurrence = int(location.get("occurrence", 1))
        new_content = modification.get("new_content", "")

        start = self._nth_index(source, before, occurrence)
        if start == -1:
            raise StrategyError(
                f"Âncora 'before' não encontrada (ocorrência {occurrence}): {before!r}."
            )
        inner_start = start + len(before)
        after_pos = source.find(after, inner_start)
        if after_pos == -1:
            raise StrategyError(
                f"Âncora 'after' não encontrada depois de 'before': {after!r}."
            )
        # Reconstrói com o novo bloco em suas próprias linhas, entre as âncoras intactas.
        replacement = "\n" + new_content.strip("\n") + "\n"
        return source[:inner_start] + replacement + source[after_pos:]


class ReplaceSection(BaseStrategy):
    """Substitui uma seção Markdown identificada pelo texto do heading.

    A seção vai do heading até (exclusive) o próximo heading de nível igual ou
    superior (mesmo nº de ``#`` ou menos), ou o fim do arquivo.
    ``include_heading`` controla se o próprio heading é substituído.
    """

    name = "replace_section"
    _HEADING_RE = re.compile(r"^(#{1,6})\s")

    def apply(self, source: str, modification: Mapping[str, Any]) -> str:
        location = get_location(modification)
        heading = location["heading"].strip()
        include_heading = bool(location.get("include_heading", True))
        new_content = modification.get("new_content", "")

        level = len(heading) - len(heading.lstrip("#"))
        if level == 0:
            raise StrategyError(
                f"location.heading deve começar com '#': {heading!r}."
            )

        lines = source.split("\n")
        start = next(
            (i for i, ln in enumerate(lines) if ln.strip() == heading), None
        )
        if start is None:
            existentes = [ln for ln in lines if self._HEADING_RE.match(ln)]
            dica = ""
            if existentes:
                amostra = ", ".join(repr(h) for h in existentes[:8])
                dica = f" Headings encontrados: {amostra}."
            raise StrategyError(f"Heading {heading!r} não encontrado.{dica}")

        end = len(lines)
        for j in range(start + 1, len(lines)):
            m = self._HEADING_RE.match(lines[j])
            if m and len(m.group(1)) <= level:
                end = j
                break

        new_lines = new_content.split("\n")
        if include_heading:
            replaced = lines[:start] + new_lines + lines[end:]
        else:
            replaced = lines[: start + 1] + new_lines + lines[end:]
        return "\n".join(replaced)
