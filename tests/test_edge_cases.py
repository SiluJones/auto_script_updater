"""Bordas de encoding/newline (FIX-002) e guardas anti-silêncio (DEC-011, FIX-003)."""

from __future__ import annotations

import pytest

from src.core.patch_engine import apply_instruction
from src.strategies import StrategyError, get_strategy


def apply(strategy_name, source, **mod):
    mod["strategy"] = strategy_name
    return get_strategy(strategy_name).apply(source, mod)


def _instr_one(rel, strategy, location=None, **conteudo):
    mod = {"id": "m1", "description": "d", "strategy": strategy, **conteudo}
    if location is not None:
        mod["location"] = location
    return {
        "format_version": "1.0",
        "description": "borda",
        "files": [
            {
                "id": "f1",
                "path_mode": "relative",
                "relative_path": rel,
                "type": "text",
                "modifications": [mod],
            }
        ],
    }


# ─────────────── DEC-011: unicidade quando occurrence é implícito ───────────────


def test_pattern_ambiguous_without_occurrence_raises():
    src = "import a\nimport a\n"
    with pytest.raises(StrategyError, match="ambígua|ambigua"):
        apply("insert_after_pattern", src, location={"pattern": r"^import a$"}, content="x")


def test_pattern_explicit_occurrence_allows_multiple_matches():
    src = "import a\nimport a\n"
    out = apply(
        "insert_after_pattern",
        src,
        location={"pattern": r"^import a$", "occurrence": 2},
        content="x",
    )
    assert out == "import a\nimport a\nx\n"


def test_replace_line_ambiguous_without_occurrence_raises():
    src = "x = 1\nx = 1\n"
    with pytest.raises(StrategyError, match="ambígua|ambigua"):
        apply("replace_line_pattern", src, location={"pattern": r"^x = 1$"}, new_content="x = 2")


def test_context_block_ambiguous_before_raises():
    src = "def f():\n    a\n# fim\ndef f():\n    b\n# fim\n"
    with pytest.raises(StrategyError, match="ambígua|ambigua"):
        apply(
            "replace_context_block",
            src,
            location={"before": "def f():", "after": "# fim"},
            new_content="    z",
        )


def test_context_block_explicit_occurrence_picks_second():
    src = "def f():\n    a\n# fim\ndef f():\n    b\n# fim\n"
    out = apply(
        "replace_context_block",
        src,
        location={"before": "def f():", "after": "# fim", "occurrence": 2},
        new_content="    z",
    )
    assert "    a\n" in out  # primeiro bloco intacto
    assert "    b" not in out  # segundo substituído
    assert "    z" in out


def test_context_block_nested_braces_closes_at_first_after():
    """Fixa a semântica documentada: 'after' fecha no PRIMEIRO match.

    Com `after: "}"` curto e chaves aninhadas, o fechamento é o do bloco
    interno — por isso a docstring (e o futuro guia da IA) manda usar âncora
    distintiva (ex.: '\\n}' da coluna 0).
    """
    src = "function f() {\n  if (x) {\n    a();\n  }\n  b();\n}\n"
    out = apply(
        "replace_context_block",
        src,
        location={"before": "function f() {", "after": "}"},
        new_content="  novo();",
    )
    # fechou no '}' do if: 'b();' sobrevive depois do bloco substituído
    assert "novo();" in out and "b();" in out
    # a âncora distintiva resolve: '\n}' na coluna 0 é o fechamento da função
    out2 = apply(
        "replace_context_block",
        src,
        location={"before": "function f() {", "after": "\n}"},
        new_content="  novo();",
    )
    assert "b();" not in out2 and "if (x)" not in out2


# ─────────────── FIX-003: headings dentro de code fences ───────────────

MD_COM_FENCE = """# Doc

## Uso

Exemplo de markdown dentro de código:

```markdown
## Configuração
texto que NÃO é seção real
```

continuação da seção Uso.

## Configuração

conteúdo real de configuração.
"""


def test_replace_section_ignores_heading_inside_fence():
    out = apply(
        "replace_section",
        MD_COM_FENCE,
        location={"heading": "## Configuração"},
        new_content="## Configuração\n\nNOVO.",
    )
    # a seção REAL foi trocada…
    assert "conteúdo real de configuração" not in out
    assert "NOVO." in out
    # …e o heading dentro do fence ficou intacto (não é heading de verdade)
    assert "## Configuração\ntexto que NÃO é seção real" in out


def test_replace_section_end_not_cut_by_fenced_heading():
    md = "## A\n\ntexto\n\n```\n## B\n```\n\nmais texto da seção A\n\n## C\n\nfim\n"
    out = apply("replace_section", md, location={"heading": "## A"}, new_content="## A\n\nX")
    # 'mais texto da seção A' fazia parte da seção A (o ## B do fence não a corta)
    assert "mais texto" not in out
    assert "## C\n\nfim" in out


def test_replace_section_duplicate_heading_raises():
    md = "## X\n\na\n\n## X\n\nb\n"
    with pytest.raises(StrategyError, match="ambígua|ambigua|vezes"):
        apply("replace_section", md, location={"heading": "## X"}, new_content="## X\n\nz")


def test_replace_section_last_section_goes_to_eof():
    md = "# T\n\n## A\n\naaa\n\n## B\n\nbbb\nccc\n"
    out = apply("replace_section", md, location={"heading": "## B"}, new_content="## B\n\nNOVO")
    assert out.endswith("## B\n\nNOVO")
    assert "bbb" not in out and "aaa" in out


# ─────────────── FIX-002: encodings e newlines no engine ───────────────


def test_cp1252_roundtrip(tmp_path):
    """Arquivo cp1252 (ex.: 'ação' salvo no Notepad antigo) preserva o encoding."""
    alvo = tmp_path / "legado.txt"
    alvo.write_bytes("linha um: ação\nlinha dois\n".encode("cp1252"))

    instr = _instr_one(
        "legado.txt",
        "replace_line_pattern",
        location={"pattern": r"^linha dois$"},
        new_content="linha dois: coração",
    )
    report = apply_instruction(instr, root_path=tmp_path, color=False)
    assert report.ok, report.files[0].error
    raw = alvo.read_bytes()
    assert raw.decode("cp1252") == "linha um: ação\nlinha dois: coração\n"
    with pytest.raises(UnicodeDecodeError):
        raw.decode("utf-8")  # confirma que continua cp1252 de verdade


def test_crlf_preserved(tmp_path):
    alvo = tmp_path / "win.txt"
    alvo.write_bytes(b"a\r\nb\r\nc\r\n")
    instr = _instr_one(
        "win.txt", "replace_line_pattern", location={"pattern": r"^b$"}, new_content="B"
    )
    report = apply_instruction(instr, root_path=tmp_path, color=False)
    assert report.ok
    assert alvo.read_bytes() == b"a\r\nB\r\nc\r\n"


def test_no_trailing_newline_insert_after_last_line(tmp_path):
    alvo = tmp_path / "semfim.txt"
    alvo.write_bytes(b"primeira\nultima")
    instr = _instr_one(
        "semfim.txt", "insert_after_pattern", location={"pattern": r"^ultima$"}, content="extra"
    )
    report = apply_instruction(instr, root_path=tmp_path, color=False)
    assert report.ok
    assert alvo.read_text(encoding="utf-8") == "primeira\nultima\nextra\n"


def test_python_decorator_removed_if_not_repeated():
    """Fixa a semântica documentada: substituir função decorada sem repetir o
    decorador o REMOVE (o nó inclui decoradores). O guia da IA deve mandar
    incluí-los no new_content."""
    src = "@cache\ndef f():\n    return 1\n"
    out = apply(
        "replace_function", src, location={"name": "f"}, new_content="def f():\n    return 2\n"
    )
    assert "@cache" not in out and "return 2" in out
    # repetindo o decorador, ele permanece
    out2 = apply(
        "replace_function",
        src,
        location={"name": "f"},
        new_content="@cache\ndef f():\n    return 2\n",
    )
    assert out2.startswith("@cache\n")
