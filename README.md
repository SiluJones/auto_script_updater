# Atualizador Automático de Scripts

Ferramenta que aplica modificações a arquivos de um projeto (`.py`, `.md`,
`.json`, `.txt` e **qualquer linguagem** via janela de contexto) a partir de um
**arquivo de instrução** gerado por IA. Elimina o copia-e-cola manual de trechos
de código entre sessões: a IA emite um YAML estruturado, você confere o diff e
aplica com um comando.

> Documentação de contexto completa (visão, arquitetura, decisões, armadilhas):
> ver `CONTEXT.md`, `DECISIONS.md` e `ROADMAP.md`.

## Estado atual — F1 (Core Engine + CLI)

A camada de execução está funcional e testada via linha de comando. A GUI
(PySide6) vem na F2 e reusará exatamente a mesma pilha (`parser → validator →
engine`).

Implementado:
- Parser (YAML/JSON) + validador contra JSON Schema (`format_version`).
- 13 estratégias de modificação (Python via libcst, texto/contexto universal,
  Markdown, JSON via jmespath, arquivo inteiro).
- Resolução de caminhos (relativo à raiz / absoluto) com guarda de contenção.
- Backup obrigatório timestampado + **rollback automático** em falha (atômico).
- Renderização de diff colorido.
- CLI com `validate`, `apply` (prévia + confirmação) e `rollback`.

## Instalação (Windows)

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Para desenvolvimento (testes + GUI futura + qualidade):

```
pip install -r requirements-dev.txt
```

## Uso

Validar uma instrução sem aplicar nada:

```
python -m src validate instrucao.yaml
```

Aplicar (mostra prévia em dry-run e pede confirmação antes de escrever):

```
python -m src apply instrucao.yaml --root C:\meu_projeto
```

Simular sem escrever / aplicar sem perguntar / desfazer:

```
python -m src apply instrucao.yaml --root C:\meu_projeto --dry-run
python -m src apply instrucao.yaml --root C:\meu_projeto --yes
python -m src rollback 20260607_231500 --root C:\meu_projeto
```

Um exemplo completo de arquivo de instrução está em
`examples/exemplo_instrucao.yaml`.

## Testes

```
pip install -r requirements-dev.txt
python -m pytest
```

## Formato da instrução (resumo)

```yaml
format_version: "1.0"
description: "O que esta instrução faz"
settings:
  backup: true          # cria backup antes de escrever (DEC-006)
  dry_run: false         # simula sem escrever
  stop_on_error: true    # para e reverte tudo em falha
files:
  - id: "f1"
    path_mode: "relative"          # ou "absolute"
    relative_path: "src/auth.py"   # caminhos Windows: use \\ ou /
    type: "python"                  # python | markdown | json | text
    modifications:
      - id: "m1"
        description: "Reescreve a função"
        strategy: "replace_function"
        location: { name: "validate_token" }
        new_content: |
          def validate_token(token):
              return bool(token)
```

A `strategy` é a fonte única de como interpretar `location` — **nunca** se usa
número de linha como localizador (ver DEC-001).
