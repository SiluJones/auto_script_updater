"""Estratégias Python baseadas em libcst (DEC-003).

Substituem função, método ou classe **por nome**, preservando a indentação e o
espaçamento ao redor (libcst recalcula a indentação ao renderizar dentro do
bloco pai; copiamos ``leading_lines`` do nó original para manter as linhas em
branco que o separavam do vizinho).

libcst é importado preguiçosamente: assim o restante do pacote (texto, JSON,
arquivo) continua funcionando mesmo sem libcst instalado, e só estas três
estratégias exigem a dependência.
"""
from __future__ import annotations

from typing import Any, Mapping

from .base_strategy import BaseStrategy, StrategyError, get_location


def _require_libcst():
    try:
        import libcst as cst  # noqa: WPS433 (import local proposital)
    except ImportError as exc:  # pragma: no cover - ambiente sem libcst
        raise StrategyError(
            "Estratégias Python exigem 'libcst'. Instale com: pip install libcst"
        ) from exc
    return cst


def _extract_single_def(cst, new_content: str, want: str):
    """Extrai o único FunctionDef/ClassDef de ``new_content``.

    ``want`` é "function" ou "class". Garante que o conteúdo novo contém
    exatamente uma definição do tipo esperado (erro claro caso contrário).
    """
    node_type = cst.FunctionDef if want == "function" else cst.ClassDef
    try:
        module = cst.parse_module(new_content)
    except Exception as exc:  # libcst.ParserSyntaxError e afins
        raise StrategyError(f"new_content não é Python válido: {exc}") from exc

    defs = [s for s in module.body if isinstance(s, node_type)]
    rotulo = "função" if want == "function" else "classe"
    if not defs:
        raise StrategyError(
            f"new_content deveria conter uma definição de {rotulo} no nível do módulo."
        )
    if len(defs) > 1:
        raise StrategyError(
            f"new_content contém {len(defs)} definições de {rotulo}; forneça apenas uma."
        )
    return defs[0]


def _transform(cst, source: str, replacement, *, target: str, kind: str, class_name: str | None):
    """Percorre ``source`` e substitui o alvo, rastreando o escopo léxico.

    kind: "function" (função/método) ou "class".
    class_name: None = função de módulo; caso contrário, método cujo escopo
    imediato é a classe nomeada.
    """

    class _Replacer(cst.CSTTransformer):
        def __init__(self) -> None:
            self.scope: list[tuple[str, str]] = []
            self.count = 0

        def visit_FunctionDef(self, node):  # noqa: N802 (API libcst)
            self.scope.append(("func", node.name.value))

        def leave_FunctionDef(self, original, updated):  # noqa: N802
            self.scope.pop()
            if kind != "function" or original.name.value != target:
                return updated
            enclosing = self.scope
            if class_name is None:
                matched = len(enclosing) == 0
            else:
                matched = bool(enclosing) and enclosing[-1] == ("class", class_name)
            if matched:
                self.count += 1
                return replacement.with_changes(leading_lines=original.leading_lines)
            return updated

        def visit_ClassDef(self, node):  # noqa: N802
            self.scope.append(("class", node.name.value))

        def leave_ClassDef(self, original, updated):  # noqa: N802
            self.scope.pop()
            if kind == "class" and original.name.value == target and len(self.scope) == 0:
                self.count += 1
                return replacement.with_changes(leading_lines=original.leading_lines)
            return updated

    try:
        tree = cst.parse_module(source)
    except Exception as exc:
        raise StrategyError(f"O arquivo Python não pôde ser parseado: {exc}") from exc

    replacer = _Replacer()
    new_tree = tree.visit(replacer)
    return replacer.count, new_tree.code


class _PythonDefStrategy(BaseStrategy):
    """Base para as três estratégias Python (função, método, classe)."""

    kind = "function"  # ou "class"
    requires_class = False  # método exige class_name
    rotulo = "função"

    def apply(self, source: str, modification: Mapping[str, Any]) -> str:
        cst = _require_libcst()
        location = get_location(modification)
        name = location.get("name")
        class_name = location.get("class_name")
        if self.requires_class and not class_name:
            raise StrategyError(f"{self.name}: 'location.class_name' é obrigatório.")

        replacement = _extract_single_def(
            cst, modification.get("new_content", ""), want=self.kind
        )
        count, code = _transform(
            cst, source, replacement,
            target=name, kind=self.kind, class_name=class_name,
        )
        if count == 0:
            alvo = f"{self.rotulo} '{name}'"
            if class_name:
                alvo += f" na classe '{class_name}'"
            elif self.kind == "function":
                alvo += " no nível do módulo"
            raise StrategyError(f"Não encontrei {alvo} para substituir.")
        if count > 1:  # pragma: no cover - nomes duplicados no mesmo escopo
            raise StrategyError(
                f"{self.rotulo.capitalize()} '{name}' aparece {count} vezes no mesmo "
                "escopo; localização ambígua."
            )
        return code


class ReplaceFunction(_PythonDefStrategy):
    name = "replace_function"
    kind = "function"
    requires_class = False
    rotulo = "função"


class ReplaceMethod(_PythonDefStrategy):
    name = "replace_method"
    kind = "function"
    requires_class = True
    rotulo = "método"


class ReplaceClass(_PythonDefStrategy):
    name = "replace_class"
    kind = "class"
    requires_class = False
    rotulo = "classe"
