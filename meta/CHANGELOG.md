# CHANGELOG

> Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/) e versionamento [SemVer](https://semver.org/lang/pt-BR/).
> **Cresce**: entradas novas no topo. Registra só o que foi de fato concluído/entregue.

## [Não lançado]
### Adicionado
- *(nada ainda — próximo ciclo: guia de geração para a IA + F2/GUI)*

---

## [0.2.0] — 2026-06-10
### Modificado (comportamento)
- **DEC-011 — unicidade implícita de localizadores:** com `occurrence` ausente, padrões/âncoras que casam mais de uma vez agora são **rejeitados como ambíguos** antes de qualquer escrita (antes aplicavam na 1ª ocorrência silenciosamente). `occurrence` explícito segue sendo escolha posicional. Vale para `insert_after_pattern`, `insert_before_pattern`, `replace_line_pattern` e a âncora `before` do `replace_context_block`; `replace_section` rejeita heading duplicado.

### Corrigido
- **FIX-002 — encodings:** BOM UTF-8 detectado e **preservado** (roundtrip com `utf-8-sig`; arquivos `.cs` do Visual Studio agora localizam padrões na 1ª linha). UTF-16/32 rejeitados com erro claro (antes, cp1252 os "decodificava" como lixo, e `replace_file` converteria o encoding silenciosamente). Detecção de newline movida para o texto decodificado. Erros de leitura/decodificação agora entram no fluxo normal de falha por arquivo (status `failed` + stop/rollback) em vez de derrubar o processo.
- **FIX-003 — `replace_section` fence-aware:** headings dentro de blocos ``` / ~~~ deixam de ser tratados como seções (não são mais encontrados nem encerram a seção real no lugar errado).

### Adicionado
- **Suíte multilinguagem** (`tests/test_multilang.py`): prova do mecanismo universal em **C#, C++, Java, JSX, TSX e GDScript**, incluindo engine completo com C# + BOM e rejeição de UTF-16.
- **Suíte de bordas** (`tests/test_edge_cases.py`): unicidade implícita/explícita, fences, heading duplicado, última seção até EOF, chaves aninhadas no context block (semântica fixada), decorador removido se não repetido (semântica fixada), cp1252 roundtrip, CRLF preservado, arquivo sem newline final.
- Total de testes: 43 → **68**.

### Qualidade
- `ruff check` limpo (auto-fix + correções manuais de B904) e `black` aplicado em todo o código.
- Versão unificada em `0.2.0` (`src/__init__.py` e `pyproject.toml` estavam dessincronizados em 0.0.1).

---

## [0.1.1] — 2026-06-10
### Adicionado
- **Demo executável** (`examples/demo_project/` + `examples/demo.yaml`) — projeto-alvo real com arquivos `.py`, `.md`, `.json` e `.js` e uma instrução que aplica de verdade (cobre os 4 tipos + `create_file`). Permite testar `validate → apply --dry-run → apply → rollback` de ponta a ponta sem ter um projeto próprio.
- README com seção **Quickstart** (comandos copiáveis usando a demo) e seção "Uso no seu projeto" com placeholder explícito.

### Corrigido
- **FIX-001:** `replace_context_block` agora rejeita com erro claro quando o `new_content` inclui as próprias âncoras `before`/`after` (antes, isso duplicava as âncoras silenciosamente, corrompendo o arquivo sem sinalizar). Acrescentado teste de regressão.
- `examples/exemplo_instrucao.yaml` — corrigido o bloco JavaScript que continha as âncoras no `new_content` (agora só o miolo entre elas).

### Documentação
- README deixou de usar o nome genérico `instrucao.yaml` nos comandos (causava confusão de "arquivo não encontrado" no primeiro uso).

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
