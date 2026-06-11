"""Estratégias de texto universais (re + difflib).

Operam sobre texto cru e, por isso, funcionam em **qualquer linguagem** (type =
"text"): JavaScript, Rust, Go, etc. São o mecanismo de fallback quando não há
parser semântico — equivalentes em espírito ao *apply_patch* por contexto.

Convenção de newline: preservamos o conteúdo como veio; o ``patch_engine`` é
quem decide o estilo de quebra de linha ao gravar em disco.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

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


def _resolve_occurrence(location: Mapping[str, Any], n_matches: int, descricao: str) -> int:
    """Resolve qual ocorrência usar, exigindo unicidade quando ela é implícita.

    Regra (Armadilha #5 / DEC-011): se ``location.occurrence`` NÃO foi
    especificado, o localizador precisa ser único — casar mais de uma vez é
    ambiguidade e vira erro (antes, aplicava na primeira silenciosamente, o que
    podia modificar o lugar errado). Se ``occurrence`` foi especificado, a
    escolha é posicional e explícita: validamos apenas o intervalo.

    Returns:
        Índice 1-based da ocorrência a usar.
    """
    explicit = "occurrence" in location
    occurrence = int(location.get("occurrence", 1))
    if occurrence < 1:
        raise StrategyError(f"location.occurrence deve ser >= 1 (recebido: {occurrence}).")
    if n_matches == 0 or occurrence > n_matches:
        raise StrategyError(
            f"{descricao} casou {n_matches} vez(es); a instrução pediu a ocorrência {occurrence}."
        )
    if not explicit and n_matches > 1:
        raise StrategyError(
            f"{descricao} casou {n_matches} vezes e 'location.occurrence' não foi "
            "especificado — localização ambígua. Especifique occurrence (1.."
            f"{n_matches}) para escolher qual, ou torne o localizador mais específico."
        )
    return occurrence


class _InsertPattern(BaseStrategy):
    """Insere ``content`` antes/depois da N-ésima linha que casa o regex."""

    after = True  # subclasses definem

    def apply(self, source: str, modification: Mapping[str, Any]) -> str:
        location = get_location(modification)
        regex = _compile(location["pattern"])
        content = modification.get("content", "")

        lines = _split_lines(source)
        matches = _matching_line_indices(lines, regex)
        occurrence = _resolve_occurrence(location, len(matches), f"Padrão {location['pattern']!r}")
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
        new_content = modification.get("new_content", "")

        lines = _split_lines(source)
        matches = _matching_line_indices(lines, regex)
        occurrence = _resolve_occurrence(location, len(matches), f"Padrão {location['pattern']!r}")
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

    Semântica do ``after`` (importante): é a PRIMEIRA ocorrência de ``after``
    DEPOIS de ``before``. Para código com delimitadores repetidos (ex.: ``}``
    em C/JS/Java com blocos aninhados), um ``after`` curto fecha no delimitador
    interno — use uma âncora distintiva (a linha completa de fechamento no
    nível certo, p.ex. ``"\\n}"`` no início de linha, ou um trecho do código
    que vem depois do bloco).
    """

    name = "replace_context_block"

    @staticmethod
    def _count(haystack: str, needle: str) -> int:
        return haystack.count(needle)

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
        new_content = modification.get("new_content", "")

        occurrence = _resolve_occurrence(
            location, self._count(source, before), f"Âncora 'before' {before!r}"
        )
        start = self._nth_index(source, before, occurrence)
        inner_start = start + len(before)
        after_pos = source.find(after, inner_start)
        if after_pos == -1:
            raise StrategyError(f"Âncora 'after' não encontrada depois de 'before': {after!r}.")
        # Guarda contra o erro mais comum: incluir as próprias âncoras no
        # new_content. Como 'before'/'after' PERMANECEM no arquivo, repeti-las
        # no miolo as duplicaria — uma corrupção que, sem esta checagem, passaria
        # silenciosamente (o apply "funcionaria"). Detectamos a assinatura
        # inequívoca: primeira linha == 'before' E última == 'after'.
        nc_lines = new_content.strip("\n").splitlines()
        if (
            nc_lines
            and nc_lines[0].strip() == before.strip()
            and nc_lines[-1].strip() == after.strip()
        ):
            raise StrategyError(
                "replace_context_block: o new_content inclui as âncoras 'before' e "
                "'after', que permanecem no arquivo e seriam duplicadas. Forneça "
                "apenas o conteúdo ENTRE as âncoras (o miolo), sem repetir "
                f"{before!r} nem {after!r}."
            )
        # Reconstrói com o novo bloco em suas próprias linhas, entre as âncoras intactas.
        replacement = "\n" + new_content.strip("\n") + "\n"
        return source[:inner_start] + replacement + source[after_pos:]


class ReplaceSection(BaseStrategy):
    """Substitui uma seção Markdown identificada pelo texto do heading.

    A seção vai do heading até (exclusive) o próximo heading de nível igual ou
    superior (mesmo nº de ``#`` ou menos), ou o fim do arquivo.
    ``include_heading`` controla se o próprio heading é substituído.

    Linhas dentro de *code fences* (blocos ``` ou ~~~) são ignoradas tanto na
    busca do heading quanto na detecção do fim da seção — um ``## Exemplo``
    dentro de um bloco de código não é um heading (FIX-003).
    """

    name = "replace_section"
    _HEADING_RE = re.compile(r"^(#{1,6})\s")
    _FENCE_RE = re.compile(r"^\s{0,3}(```|~~~)")

    @classmethod
    def _heading_indices(cls, lines: list[str], heading: str) -> list[int]:
        """Índices das linhas que são o heading procurado, fora de code fences."""
        found: list[int] = []
        in_fence = False
        for i, ln in enumerate(lines):
            if cls._FENCE_RE.match(ln):
                in_fence = not in_fence
                continue
            if not in_fence and ln.strip() == heading:
                found.append(i)
        return found

    def apply(self, source: str, modification: Mapping[str, Any]) -> str:
        location = get_location(modification)
        heading = location["heading"].strip()
        include_heading = bool(location.get("include_heading", True))
        new_content = modification.get("new_content", "")

        level = len(heading) - len(heading.lstrip("#"))
        if level == 0:
            raise StrategyError(f"location.heading deve começar com '#': {heading!r}.")

        lines = source.split("\n")
        candidatos = self._heading_indices(lines, heading)
        if not candidatos:
            existentes = []
            in_fence = False
            for ln in lines:
                if self._FENCE_RE.match(ln):
                    in_fence = not in_fence
                    continue
                if not in_fence and self._HEADING_RE.match(ln):
                    existentes.append(ln)
            dica = ""
            if existentes:
                amostra = ", ".join(repr(h) for h in existentes[:8])
                dica = f" Headings encontrados: {amostra}."
            raise StrategyError(f"Heading {heading!r} não encontrado.{dica}")
        if len(candidatos) > 1:
            raise StrategyError(
                f"Heading {heading!r} aparece {len(candidatos)} vezes no documento — "
                "localização ambígua. Torne os headings únicos (ou ajuste o documento) "
                "antes de usar replace_section."
            )
        start = candidatos[0]

        end = len(lines)
        in_fence = False
        for j in range(start + 1, len(lines)):
            if self._FENCE_RE.match(lines[j]):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
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
