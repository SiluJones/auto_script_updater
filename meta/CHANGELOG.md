# CHANGELOG

> Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/) e versionamento [SemVer](https://semver.org/lang/pt-BR/).
> **Cresce**: entradas novas no topo. Registra só o que foi de fato concluído/entregue.

## [Não lançado]
### Adicionado
- *(nada ainda — código não iniciado)*

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
