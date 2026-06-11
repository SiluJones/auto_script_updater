"""Testes unitários das estratégias de modificação."""

from __future__ import annotations

import pytest

from src.strategies import StrategyError, get_strategy


def apply(strategy_name, source, **mod):
    mod["strategy"] = strategy_name
    return get_strategy(strategy_name).apply(source, mod)


# ───────────────────────── Python (libcst) ─────────────────────────

PY_SRC = """import os


class Auth:
    def login(self):
        return True

    def check(self, token):
        return bool(token)


def check():
    return "modulo"
"""


def test_replace_method_only_touches_class_scope():
    out = apply(
        "replace_method",
        PY_SRC,
        location={"class_name": "Auth", "name": "check"},
        new_content="def check(self, token):\n    return token is not None\n",
    )
    assert "return token is not None" in out
    # a função de módulo 'check' permanece intacta
    assert 'return "modulo"' in out


def test_replace_function_module_level_ignores_method():
    out = apply(
        "replace_function",
        PY_SRC,
        location={"name": "check"},
        new_content='def check():\n    return "NOVO"\n',
    )
    assert 'return "NOVO"' in out
    # o método da classe não foi tocado
    assert "return bool(token)" in out


def test_replace_class_whole():
    out = apply(
        "replace_class",
        PY_SRC,
        location={"name": "Auth"},
        new_content="class Auth:\n    pass\n",
    )
    assert "class Auth:\n    pass" in out
    assert "def login" not in out


def test_replace_function_not_found_raises():
    with pytest.raises(StrategyError, match="encontrei"):
        apply(
            "replace_function",
            PY_SRC,
            location={"name": "inexistente"},
            new_content="def inexistente():\n    return 1\n",
        )


def test_replace_method_requires_class_name():
    with pytest.raises(StrategyError):
        get_strategy("replace_method").apply(
            PY_SRC,
            {
                "strategy": "replace_method",
                "location": {"name": "check"},
                "new_content": "def check(self):\n    return 1\n",
            },
        )


# ───────────────────────── Texto universal ─────────────────────────


def test_insert_after_pattern():
    src = "import os\nimport sys\n"
    out = apply(
        "insert_after_pattern",
        src,
        location={"pattern": r"^import os$"},
        content="import logging\n",
    )
    assert out == "import os\nimport logging\nimport sys\n"


def test_insert_before_pattern():
    src = "a = 1\nb = 2\n"
    out = apply(
        "insert_before_pattern", src, location={"pattern": r"^b = 2$"}, content="# comentário\n"
    )
    assert out == "a = 1\n# comentário\nb = 2\n"


def test_pattern_occurrence_out_of_range():
    with pytest.raises(StrategyError, match="ocorrência|ocorrencia|casou"):
        apply(
            "insert_after_pattern", "x\n", location={"pattern": "x", "occurrence": 2}, content="y\n"
        )


def test_replace_line_pattern_preserves_newline():
    src = "VERSION = '1.0'\nother = 2\n"
    out = apply(
        "replace_line_pattern",
        src,
        location={"pattern": r"^VERSION"},
        new_content="VERSION = '2.0'",
    )
    assert out == "VERSION = '2.0'\nother = 2\n"


def test_replace_context_block():
    src = "def f():\n    OLD_A\n    OLD_B\n    return 1\n"
    out = apply(
        "replace_context_block",
        src,
        location={"before": "def f():", "after": "    return 1"},
        new_content="    NEW",
    )
    assert out == "def f():\n    NEW\n    return 1\n"


def test_context_block_after_anchor_missing():
    with pytest.raises(StrategyError, match="after"):
        apply(
            "replace_context_block",
            "def f():\n    x\n",
            location={"before": "def f():", "after": "NAO_EXISTE"},
            new_content="y",
        )


def test_context_block_rejects_anchors_in_new_content():
    # Erro comum: incluir as próprias âncoras no new_content duplicaria 'before'/'after'.
    # A guarda deve transformar essa corrupção silenciosa em erro claro.
    src = "function initApp() {\n  velho();\n}\n"
    with pytest.raises(StrategyError, match="âncoras|ancoras|miolo"):
        apply(
            "replace_context_block",
            src,
            location={"before": "function initApp() {", "after": "}"},
            new_content="function initApp() {\n  novo();\n}",
        )


# ───────────────────────── Markdown ─────────────────────────

MD = "# T\n\n## A\n\naaa\n\n## B\n\nbbb\n\n### B1\n\nb1\n\n## C\n\nccc\n"


def test_replace_section_stops_at_same_level():
    out = apply("replace_section", MD, location={"heading": "## B"}, new_content="## B\n\nNOVO")
    assert "NOVO" in out
    # não invadiu a seção C
    assert "## C\n\nccc" in out
    # subnível B1 foi substituído junto (faz parte da seção B)
    assert "b1" not in out


def test_replace_section_not_found_lists_headings():
    with pytest.raises(StrategyError, match="Headings encontrados|não encontrado|nao encontrado"):
        apply("replace_section", MD, location={"heading": "## Z"}, new_content="x")


# ───────────────────────── JSON ─────────────────────────

JSON_SRC = '{"api": {"version": "1.0"}, "list": [1, 2], "drop": {"k": 1}}'


def test_set_json_path_existing():
    out = apply("set_json_path", JSON_SRC, location={"path": "api.version"}, value="2.0")
    assert '"version": "2.0"' in out


def test_set_json_path_creates_intermediate():
    out = apply("set_json_path", "{}", location={"path": "a.b.c"}, value=1)
    import json

    assert json.loads(out) == {"a": {"b": {"c": 1}}}


def test_append_json_array():
    out = apply("append_json_array", JSON_SRC, location={"path": "list"}, value=3)
    import json

    assert json.loads(out)["list"] == [1, 2, 3]


def test_append_to_non_array_raises():
    with pytest.raises(StrategyError, match="lista|list"):
        apply("append_json_array", JSON_SRC, location={"path": "api"}, value=1)


def test_delete_json_path():
    out = apply("delete_json_path", JSON_SRC, location={"path": "drop.k"})
    import json

    assert json.loads(out)["drop"] == {}


def test_delete_missing_raises():
    with pytest.raises(StrategyError, match="não existe|nao existe"):
        apply("delete_json_path", JSON_SRC, location={"path": "ausente.x"})


# ───────────────────────── Arquivo inteiro ─────────────────────────


def test_create_file_returns_content():
    out = apply("create_file", "", content="linha\n")
    assert out == "linha\n"


def test_replace_file_ignores_source():
    out = apply("replace_file", "conteúdo antigo enorme", new_content="novo\n")
    assert out == "novo\n"


def test_unknown_strategy_raises():
    with pytest.raises(StrategyError, match="desconhecida"):
        get_strategy("nao_existe")
