# CHANGELOG

> Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/) e versionamento [SemVer](https://semver.org/lang/pt-BR/).
> **Cresce**: entradas novas no topo. Registra só o que foi de fato concluído/entregue.

## [Não lançado]
### Adicionado
- *(nada ainda — próximo ciclo é a F2/GUI)*

---

## [0.1.0] — 2026-06-08
### Adicionado
- **Motor de execução (F1) funcional via CLI** — fluxo completo instrução → validação → localização → aplicação → backup → diff → resultado, com rollback.
- `instruction_v1.schema.json` — JSON Schema Draft 7 completo (contrato do arquivo de instrução), com `$comment` idiomático.
- `instruction_parser.py` — carrega YAML/JSON com fallback de encoding utf-8→cp1252.
- `instruction_validator.py` — valida contra o schema e o `format_version`, acumulando todos os erros com o caminho do campo.
- Treze estratégias de modificação (padrão Strategy): `replace_function`, `replace_method`, `replace_class` (Python/libcst); `insert_after_pattern`, `insert_before_pattern`, `replace_line_pattern`, `replace_context_block` (texto universal); `replace_section` (markdown); `set_json_path`, `append_json_array`, `delete_json_path` (JSON/jmespath); `replace_file`, `create_file` (arquivo inteiro).
- `file_locator.py` — resolve caminhos relative/absolute com guarda de contenção (caminho relativo não escapa da raiz).
- `backup_manager.py` — backup timestampado espelhando a estrutura de pastas; rollback atômico e rollback por timestamp.
- `diff_renderer.py` — unified diff colorido (colorama, com degradação graciosa).
- `patch_engine.py` — orquestração com transação e rollback automático em falha, dry-run e precedência de configuração (padrões < settings < flags).
- CLI (`python -m src`): subcomandos `validate`, `apply` (prévia + confirmação) e `rollback`.
- Arquivos de projeto: `pyproject.toml`, `requirements.txt` (núcleo sem Qt), `requirements-gui.txt`, `requirements-dev.txt`, `.gitignore`, `README.md`, `examples/exemplo_instrucao.yaml`.
- 42 testes (parser/validator, estratégias, integração do engine), todos verdes.

### Decisões
- DEC-008 (estratégias `create_file`/`replace_file`), DEC-009 (`location.type` removido; papéis Python explícitos; interface da estratégia com `apply()` único), DEC-010 (independência de linguagem via contexto; `requirements` dividido).

---

## [0.0.1] — 2026-06-03
### Adicionado
- Concepção do projeto: visão, escopo e objetivos definidos.
- Stack tecnológica selecionada e justificada (Python 3.11+, PySide6, libcst, PyYAML, jsonschema, jmespath, PyInstaller).
- Arquitetura modular definida: `core/` (parser, validator, locator, engine, backup, diff), `strategies/` (python, text, json), `gui/`, `schemas/`.
- Onze estratégias de modificação especificadas para 4 tipos de arquivo (Python, Markdown, JSON, texto genérico).
- Schema conceitual do arquivo de instrução YAML v1.0 com hierarquia: cabeçalho, settings, files[], modifications[].
- Sete decisões arquiteturais documentadas em DECISIONS.md (DEC-001 a DEC-007).
- Roadmap em 5 fases documentado (F0 concluída, F1–F4 futuras).
- Documentação completa de contexto gerada: CONTEXT.md, STATUS.md, DECISIONS.md, ROADMAP.md, GLOSSARY.md, HISTORICO.md, IDEAS.md, LOG-TEMPLATE.md, logs/2026-06-03.md.
