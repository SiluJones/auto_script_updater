# CONTEXT.md — Atualizador Automático de Scripts

> Arquivo **estável**. Descreve o que o projeto É, não o que está acontecendo agora (isso é o STATUS).
> Muda só em alteração estrutural (stack, arquitetura, escopo, nova armadilha descoberta).

---

## Visão Geral
Ferramenta desktop em Python que aplica automaticamente modificações a arquivos de projeto (`.py`, `.md`, `.json`, `.txt`) a partir de arquivos de instrução gerados por IA (Claude ou similar). Elimina o trabalho manual de copiar e colar trechos de código entre sessões: ao final de uma sessão de trabalho com IA, o assistente gera um YAML de instrução estruturado; o usuário abre na ferramenta, confere o diff colorido e aplica com um clique. Objetivo: tempo entre "IA gerou a instrução" e "modificações aplicadas no projeto" < 30 segundos, com zero edição manual.

## Stack Tecnológica
- **Linguagem:** Python 3.11+
- **GUI:** PySide6 6.x (binding oficial do Qt 6 — licença LGPL)
- **Parsing de instrução:** PyYAML + jsonschema
- **Manipulação Python:** libcst 1.x (Concrete Syntax Tree — preserva comentários e espaçamento)
- **Manipulação texto/MD/TXT:** `re` + `difflib` (stdlib)
- **Manipulação JSON:** `json` (stdlib) + jmespath (navegação por caminho)
- **Testes:** pytest + pytest-qt
- **Packaging:** PyInstaller (executável `.exe` standalone Windows)
- **Formato de instrução:** YAML 1.2

## Estrutura do Projeto
```
auto_script_updater/
├── src/
│   ├── core/
│   │   ├── instruction_parser.py      # Carrega e deserializa YAML/JSON de instrução
│   │   ├── instruction_validator.py   # Valida estrutura contra JSON Schema
│   │   ├── file_locator.py            # Resolve root_path + relative_path; verifica existência
│   │   ├── patch_engine.py            # Orquestra modificações; transação; rollback
│   │   ├── backup_manager.py          # Cria backup timestampado; restaura sob demanda
│   │   └── diff_renderer.py           # Gera unified diff legível (prévia GUI + output CLI)
│   ├── strategies/
│   │   ├── base_strategy.py           # ABC: interface find_location() + apply()
│   │   ├── python_strategy.py         # Estratégias Python via libcst (CST)
│   │   ├── text_strategy.py           # Estratégias texto genérico: regex + janela de contexto
│   │   └── json_strategy.py           # Estratégias JSON: jmespath set/append/delete
│   ├── gui/
│   │   ├── main_window.py             # Janela principal + orquestração de UI
│   │   ├── file_tree_panel.py         # Árvore de arquivos afetados (QTreeWidget + status)
│   │   ├── diff_viewer.py             # Diff colorido (QTextEdit + QSyntaxHighlighter)
│   │   └── root_picker.py             # Seletor de pasta raiz com histórico
│   ├── schemas/
│   │   └── instruction_v1.schema.json # JSON Schema — contrato do arquivo de instrução v1.x
│   └── __main__.py                    # Entry point: `python -m src [instrucao.yaml] [--root ...]`
├── tests/
│   ├── fixtures/                      # Arquivos de referência para testes
│   ├── test_strategies.py             # Testes unitários por strategy
│   ├── test_patch_engine.py           # Testes de integração do engine
│   └── test_instruction_parser.py     # Testes do parser + validator
├── backups/                           # Backups automáticos por timestamp (gitignored)
├── requirements.txt
└── requirements-dev.txt               # pytest, pytest-qt, ruff, black
```

## Como o Arquivo de Instrução Funciona (CRÍTICO)
O arquivo de instrução (`.yaml`) é gerado pela IA e consumido pela ferramenta. Hierarquia:

```
instrução
├── cabeçalho: format_version, generated_by, generated_at, description
├── settings: backup, dry_run, stop_on_error, encoding
└── files[]
    ├── id, path_mode ("relative" | "absolute"), caminho
    ├── type ("python" | "markdown" | "json" | "text")
    └── modifications[]
        ├── id, description, strategy (nome do algoritmo)
        ├── location (tipo + identificador único, sem número de linha)
        └── new_content / content / value (o conteúdo a aplicar)
```

**Resolução de caminho:**
- `path_mode: relative` → usuário define pasta raiz na GUI; ferramenta concatena `root_path + relative_path`.
- `path_mode: absolute` → a IA preencheu o caminho completo; ferramenta usa diretamente.

**Localização sem número de linha** (ver DEC-001): modificações são localizadas por identificadores semânticos ou janela de contexto — nunca por número de linha absoluto — para resistir a edições anteriores no mesmo arquivo.

## Estratégias de Modificação
| Estratégia | Arquivo-alvo | Como localiza |
|---|---|---|
| `replace_function` | Python | Nome da função (libcst — nó FunctionDef) |
| `replace_method` | Python | Nome da classe + nome do método |
| `replace_class` | Python | Nome da classe (libcst — nó ClassDef) |
| `insert_after_pattern` | Qualquer | Regex único + nº de ocorrência |
| `insert_before_pattern` | Qualquer | Regex único + nº de ocorrência |
| `replace_context_block` | Qualquer | Janela de contexto: N linhas antes + N depois |
| `replace_line_pattern` | Qualquer | Regex que casa exatamente a linha alvo |
| `replace_section` | Markdown | Texto do heading (ex: `## Configuração`) |
| `set_json_path` | JSON | Caminho jmespath (ex: `config.database.host`) |
| `append_json_array` | JSON | Caminho jmespath do array + valor a inserir |
| `delete_json_path` | JSON | Caminho jmespath do nó a remover |

## Convenções de Código
- **Nomes:** snake_case, inglês (arquivos, funções, variáveis, classes)
- **Comentários:** PT-BR; toda função pública tem docstring PT-BR (estilo Google)
- **Commits:** PT-BR, imperativo curto, Conventional Commits (`feat`, `fix`, `docs`, `refactor`, `chore`)
- **Estilo:** ruff (lint) + black (format); linha máxima 100 caracteres
- **Tipos:** type hints em toda assinatura de função pública
- **Testes:** pytest; cobertura mínima do core: 80%

## Arquitetura — Pontos-chave
- Estratégias são intercambiáveis via padrão Strategy (ABC) — ver DEC-002.
- libcst, não ast stdlib, para toda modificação Python — ver DEC-003.
- YAML como formato canônico de instrução — ver DEC-004.
- PySide6 como framework GUI — ver DEC-005.
- Backup obrigatório antes de qualquer escrita em disco — ver DEC-006.
- Schema versionado com campo `format_version` — ver DEC-007.

## Armadilhas Conhecidas
1. **Localizar por número de linha absoluto** — linhas se deslocam após qualquer inserção/deleção anterior no mesmo arquivo; em instruções com várias modificações, a taxa de falha é alta → usar estratégias semânticas (nome de função, heading, jmespath) ou janela de contexto; se inevitável usar posição textual, aplicar modificações do fim para o início do arquivo.

2. **ast stdlib para reescrita Python** — `ast.unparse()` normaliza o código: remove comentários, altera espaçamento, pode trocar aspas simples por duplas → nunca usar ast para escrever de volta em disco; sempre libcst.

3. **Encoding ambíguo no Windows** — arquivos sem BOM podem ser CP-1252 ou UTF-8 → abrir sempre com `encoding="utf-8"` explícito; capturar `UnicodeDecodeError` e tentar `"cp1252"` como fallback; informar o usuário qual encoding foi detectado.

4. **Modificações interdependentes no mesmo arquivo** — uma modificação pode depender de linha inserida pela anterior; aplicar via texto sem reparse pode errar o contexto → o `patch_engine` reparseia (recarrega o conteúdo atual do arquivo ou do CST em memória) após cada modificação do mesmo arquivo antes de aplicar a próxima.

5. **Pattern regex não-único** — se o padrão casa mais de uma vez no arquivo, a modificação pode ocorrer no lugar errado → validar unicidade (para `occurrence: 1`) antes de qualquer escrita; alertar e bloquear se o regex casar ≠ 1 vez quando unicidade é esperada.

6. **Caminhos Windows com barras invertidas no YAML** — `\` em YAML é caractere de escape; caminhos Windows devem usar `\\` ou `/` no arquivo de instrução → documentar isso no prompt padrão que a IA usa para gerar instruções.

## Contexto de Produto
- **Usuário-alvo:** Desenvolvedor que usa IA de forma intensiva; trabalha em Windows; cansa de copiar manualmente sugestões da IA para o projeto entre sessões.
- **Dor que resolve:** Risco de erro ao copiar manualmente + tempo perdido com copiar/colar trechos longos em múltiplos arquivos.
- **O que é sucesso:** IA gera instrução → ferramenta aplica → zero edição manual; < 30 s do início ao fim.
- **O que o projeto deliberadamente NÃO é:** editor de código completo, plugin de IDE, ferramenta de merge/conflito, sistema de controle de versão, agente com acesso direto à IA.
