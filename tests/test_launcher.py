"""Testes das funcoes puras do launcher (sem dependencia de Qt).

Cobre WI-3 da spec F2-acesso-rapido.md.
"""

from __future__ import annotations

from src.gui.launcher import build_launcher_bat, resolve_instruction_in_dir

# ── resolve_instruction_in_dir ──────────────────────────────────────────────


def test_resolve_none(tmp_path):
    kind, files = resolve_instruction_in_dir(tmp_path)
    assert kind == "none"
    assert files == []


def test_resolve_one_yaml(tmp_path):
    (tmp_path / "instrucao.yaml").write_text("x: 1")
    kind, files = resolve_instruction_in_dir(tmp_path)
    assert kind == "one"
    assert len(files) == 1
    assert files[0].name == "instrucao.yaml"


def test_resolve_one_yml(tmp_path):
    (tmp_path / "instrucao.yml").write_text("x: 1")
    kind, files = resolve_instruction_in_dir(tmp_path)
    assert kind == "one"
    assert len(files) == 1


def test_resolve_many(tmp_path):
    (tmp_path / "a.yaml").write_text("x: 1")
    (tmp_path / "b.yml").write_text("y: 2")
    kind, files = resolve_instruction_in_dir(tmp_path)
    assert kind == "many"
    assert len(files) == 2


def test_resolve_ignores_subdir(tmp_path):
    """Yaml em subpasta nao e contabilizado."""
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "deep.yaml").write_text("x: 1")
    kind, files = resolve_instruction_in_dir(tmp_path)
    assert kind == "none"


def test_resolve_topo_mais_subdir_conta_so_topo(tmp_path):
    """1 yaml no topo + 1 yaml em subpasta = 'one' (so conta o topo)."""
    (tmp_path / "ativo.yaml").write_text("x: 1")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "arquivado.yaml").write_text("y: 2")
    kind, files = resolve_instruction_in_dir(tmp_path)
    assert kind == "one"
    assert files[0].name == "ativo.yaml"


# ── build_launcher_bat ─────────────────────────────────────────────────────


def test_build_bat_root_descendant(tmp_path):
    """Raiz descendente de bat_dir: --root usa %~dp0<nome>."""
    bat_dir = tmp_path / "cinzeiro"
    bat_dir.mkdir()
    project_root = bat_dir / "Cinzeiro-Game"
    project_root.mkdir()
    asu_home = tmp_path / "asu"
    asu_home.mkdir()

    texto = build_launcher_bat(asu_home=asu_home, project_root=project_root, bat_dir=bat_dir)
    assert "python.exe" in texto
    assert "activate" not in texto
    assert "%~dp0" in texto
    assert "Cinzeiro-Game" in texto


def test_build_bat_root_outside(tmp_path):
    """Raiz fora de bat_dir: --root usa caminho absoluto."""
    bat_dir = tmp_path / "bat_dir"
    bat_dir.mkdir()
    project_root = tmp_path / "outro_projeto"
    project_root.mkdir()
    asu_home = tmp_path / "asu"
    asu_home.mkdir()

    texto = build_launcher_bat(asu_home=asu_home, project_root=project_root, bat_dir=bat_dir)
    assert "python.exe" in texto
    assert "activate" not in texto
    assert str(project_root.resolve()) in texto


def test_build_bat_no_activate(tmp_path):
    """O .bat nao usa 'call activate' — chama python.exe do venv diretamente (D1)."""
    bat_dir = tmp_path / "bat"
    bat_dir.mkdir()
    projeto = tmp_path / "proj"
    projeto.mkdir()
    asu = tmp_path / "asu"
    asu.mkdir()

    texto = build_launcher_bat(asu_home=asu, project_root=projeto, bat_dir=bat_dir)
    # 'call activate' e 'activate.bat' nao devem aparecer; 'python.exe' sim
    assert "call activate" not in texto.lower()
    assert "activate.bat" not in texto.lower()
    assert "python.exe" in texto


def test_build_bat_instruction_dir_uses_dp0(tmp_path):
    """--instruction-dir sempre usa %~dp0 (pasta do .bat)."""
    bat_dir = tmp_path / "bat"
    bat_dir.mkdir()
    proj = tmp_path / "proj"
    proj.mkdir()
    asu = tmp_path / "asu"
    asu.mkdir()

    texto = build_launcher_bat(asu_home=asu, project_root=proj, bat_dir=bat_dir)
    assert "--instruction-dir" in texto
    assert "%~dp0" in texto


# ── Testes de encoding ASCII (F2-bat-ascii.md) ─────────────────────────────


def test_build_bat_ascii_paths_is_ascii(tmp_path):
    """Caminhos ASCII: texto retornado eh 100% ASCII e nao contem 'chcp'."""
    bat_dir = tmp_path / "bat"
    bat_dir.mkdir()
    project_root = tmp_path / "projeto"
    project_root.mkdir()
    asu_home = tmp_path / "asu"
    asu_home.mkdir()

    texto = build_launcher_bat(asu_home=asu_home, project_root=project_root, bat_dir=bat_dir)
    assert texto.isascii(), "Texto deve ser ASCII puro quando todos os caminhos sao ASCII"
    assert "chcp" not in texto, "Nao deve conter 'chcp' para caminhos ASCII"


def test_build_bat_accented_path_has_chcp(tmp_path):
    """Caminho acentuado: texto contem 'chcp 65001' e o nome acentuado intacto (nao vira '?')."""
    bat_dir = tmp_path / "bat"
    bat_dir.mkdir()
    project_root = tmp_path / "Café"  # Café — 'é' eh nao-ASCII
    project_root.mkdir()
    asu_home = tmp_path / "asu"
    asu_home.mkdir()

    texto = build_launcher_bat(asu_home=asu_home, project_root=project_root, bat_dir=bat_dir)
    assert "chcp 65001" in texto, "Deve conter 'chcp 65001' para caminho acentuado"
    assert "Café" in texto, "Nome acentuado deve aparecer intacto (nao vira '?')"
