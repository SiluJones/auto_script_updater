"""Prova de multilinguagem: o mecanismo universal (type="text") em 6 linguagens.

Estas estratégias operam sobre texto cru, então funcionam em QUALQUER
linguagem. Aqui cobrimos as que o usuário citou: C#, C++, Java, JSX, TSX e
GDScript — cada uma com replace_context_block e/ou patterns, mais um teste de
engine completo com C# + BOM UTF-8 (o caso real do Visual Studio, FIX-002).
"""

from __future__ import annotations

from src.core.patch_engine import apply_instruction
from src.strategies import get_strategy


def apply(strategy_name, source, **mod):
    mod["strategy"] = strategy_name
    return get_strategy(strategy_name).apply(source, mod)


# ───────────────────────── C# ─────────────────────────

CSHARP = """using System;

namespace Demo
{
    public class AuthService
    {
        public bool ValidateToken(string token)
        {
            // implementação antiga
            return token != null;
        }
    }
}
"""


def test_csharp_replace_method_body_by_context():
    out = apply(
        "replace_context_block",
        CSHARP,
        location={
            "before": "public bool ValidateToken(string token)\n        {",
            "after": "\n        }",
        },
        new_content=(
            "            if (string.IsNullOrEmpty(token)) return false;\n"
            "            return token.Length > 8;"
        ),
    )
    assert "IsNullOrEmpty" in out
    assert "implementação antiga" not in out
    # estrutura ao redor intacta
    assert "namespace Demo" in out and "public class AuthService" in out


def test_csharp_insert_using():
    out = apply(
        "insert_after_pattern",
        CSHARP,
        location={"pattern": r"^using System;$"},
        content="using System.Linq;",
    )
    assert out.splitlines()[1] == "using System.Linq;"


# ───────────────────────── C++ ─────────────────────────

CPP = """#include <iostream>

int soma(int a, int b) {
    // versao antiga
    return a + b;
}

int main() {
    std::cout << soma(2, 3);
    return 0;
}
"""


def test_cpp_replace_function_body_by_context():
    out = apply(
        "replace_context_block",
        CPP,
        location={"before": "int soma(int a, int b) {", "after": "\n}"},
        new_content="    // valida overflow antes de somar\n    return a + b;",
    )
    assert "valida overflow" in out
    assert "versao antiga" not in out
    assert "int main() {" in out  # função vizinha intacta


def test_cpp_insert_include():
    out = apply(
        "insert_after_pattern",
        CPP,
        location={"pattern": r"^#include <iostream>$"},
        content="#include <vector>",
    )
    assert "#include <vector>" in out.splitlines()[1]


# ───────────────────────── Java ─────────────────────────

JAVA = """package com.demo;

public class Calculator {
    public int divide(int a, int b) {
        return a / b;
    }
}
"""


def test_java_replace_method_by_context():
    out = apply(
        "replace_context_block",
        JAVA,
        location={
            "before": "public int divide(int a, int b) {",
            "after": "\n    }",
        },
        new_content=(
            '        if (b == 0) throw new ArithmeticException("div/0");\n' "        return a / b;"
        ),
    )
    assert "ArithmeticException" in out
    assert "public class Calculator" in out


# ───────────────────────── JSX ─────────────────────────

JSX = """import React from "react";

export function Header({ title }) {
  return (
    <header className="old">
      <h1>{title}</h1>
    </header>
  );
}
"""


def test_jsx_replace_render_block():
    out = apply(
        "replace_context_block",
        JSX,
        location={"before": "return (", "after": "\n  );"},
        new_content=(
            '    <header className="new">\n'
            "      <h1>{title}</h1>\n"
            "      <nav>menu</nav>\n"
            "    </header>"
        ),
    )
    assert 'className="new"' in out
    assert "<nav>menu</nav>" in out
    assert 'className="old"' not in out


# ───────────────────────── TSX ─────────────────────────

TSX = """type Props = { count: number };

export function Counter({ count }: Props) {
  const label = "old";
  return <span>{label}: {count}</span>;
}
"""


def test_tsx_replace_line_pattern_keeps_types():
    out = apply(
        "replace_line_pattern",
        TSX,
        location={"pattern": r'const label = "old";'},
        new_content='  const label = "contador";',
    )
    assert 'const label = "contador";' in out
    assert "type Props = { count: number };" in out  # tipagem intacta


# ───────────────────────── GDScript (Godot) ─────────────────────────
# GDScript é sensível a indentação (como Python): o splice por contexto preserva
# o texto cru, então a indentação fornecida no new_content é mantida fielmente.

GDSCRIPT = """extends Node2D

var speed := 100

func _process(delta):
\tposition.x += speed * delta

func reset():
\tposition = Vector2.ZERO
"""


def test_gdscript_replace_func_body_preserves_tabs():
    out = apply(
        "replace_context_block",
        GDSCRIPT,
        location={"before": "func _process(delta):", "after": "\nfunc reset():"},
        new_content="\tif speed > 0:\n\t\tposition.x += speed * delta",
    )
    assert "\tif speed > 0:\n\t\tposition.x += speed * delta" in out
    assert "func reset():" in out  # âncora 'after' (a função seguinte) intacta


def test_gdscript_replace_var_line():
    out = apply(
        "replace_line_pattern",
        GDSCRIPT,
        location={"pattern": r"^var speed := 100$"},
        new_content="var speed := 250",
    )
    assert "var speed := 250\n" in out


# ───────────────── Engine completo: C# com BOM UTF-8 (FIX-002) ─────────────────


def _instr_csharp(rel):
    return {
        "format_version": "1.0",
        "description": "patch em C# com BOM",
        "files": [
            {
                "id": "cs",
                "path_mode": "relative",
                "relative_path": rel,
                "type": "text",
                "language": "csharp",
                "modifications": [
                    {
                        "id": "m1",
                        "description": "d",
                        "strategy": "insert_after_pattern",
                        "location": {"pattern": r"^using System;$"},
                        "content": "using System.Linq;",
                    }
                ],
            }
        ],
    }


def test_engine_preserves_utf8_bom_in_csharp(tmp_path):
    """BOM do Visual Studio: localizador na 1ª linha deve casar e o BOM persistir."""
    alvo = tmp_path / "Service.cs"
    alvo.write_bytes(b"\xef\xbb\xbf" + CSHARP.encode("utf-8"))

    report = apply_instruction(_instr_csharp("Service.cs"), root_path=tmp_path, color=False)
    assert report.ok, report.files[0].error
    raw = alvo.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")  # BOM preservado (roundtrip fiel)
    texto = raw.decode("utf-8-sig")
    assert texto.splitlines()[1] == "using System.Linq;"


def test_engine_rejects_utf16_with_clear_error(tmp_path):
    """UTF-16 não pode virar lixo via cp1252: erro claro pedindo conversão."""
    alvo = tmp_path / "Service.cs"
    alvo.write_bytes(CSHARP.encode("utf-16"))  # inclui BOM FF FE

    report = apply_instruction(_instr_csharp("Service.cs"), root_path=tmp_path, color=False)
    assert not report.ok
    assert "UTF-16" in (report.files[0].error or "")
    # arquivo original intocado
    assert alvo.read_bytes().startswith((b"\xff\xfe", b"\xfe\xff"))
