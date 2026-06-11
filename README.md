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

## Quickstart — primeiro teste (copie e cole)

O repositório traz uma **demo executável** em `examples/demo_project/` (arquivos
reais) com a instrução `examples/demo.yaml`. Rode na raiz do projeto, com o
ambiente já ativado:

```
python -m src validate examples\demo.yaml
python -m src apply examples\demo.yaml --root examples\demo_project --dry-run
python -m src apply examples\demo.yaml --root examples\demo_project
python -m src rollback <TIMESTAMP> --root examples\demo_project
```

- O 1º comando valida a instrução.
- O 2º (`--dry-run`) mostra o diff colorido **sem escrever nada** — é o teste seguro e repetível.
- O 3º aplica de verdade (cria backup e pede confirmação); ao final imprime o `Backup: ...\<TIMESTAMP>`.
- O 4º desfaz tudo: copie o `<TIMESTAMP>` impresso pelo passo anterior (ex.: `20260610_041628`).

Depois de testar, a demo volta ao estado original (via rollback acima ou
`git checkout examples\demo_project`), então você pode repetir à vontade.

> Nota: `examples\exemplo_instrucao.yaml` é apenas **ilustrativo** — aponta para
> caminhos fictícios (`src/auth/login.py`, `C:\projetos\...`) e **não roda** como
> está. Para testar de fato, use `examples\demo.yaml` acima.

## Uso no seu projeto

Substitua `MINHA_INSTRUCAO.yaml` pelo caminho real da instrução que a IA gerou e
`C:\meu_projeto` pela raiz do seu projeto:

```
python -m src validate MINHA_INSTRUCAO.yaml
python -m src apply MINHA_INSTRUCAO.yaml --root C:\meu_projeto --dry-run
python -m src apply MINHA_INSTRUCAO.yaml --root C:\meu_projeto
python -m src rollback <TIMESTAMP> --root C:\meu_projeto
```

Flags úteis: `--dry-run` (simula sem escrever), `--yes` (aplica sem perguntar),
`--no-color` (saída sem cores), `--no-backup` (não recomendado).

## Gerando instruções com IA (kit de ensino)

Para que uma IA gere instruções corretas de primeira em **qualquer projeto seu**:

1. copie `docs/INSTRUCTION_GUIDE.md` para a base de conhecimento do projeto;
2. cole o bloco de `docs/PROMPT_IA.md` nas instruções do projeto;
3. peça: *"emita uma instrução ASU para estas mudanças"*.

O guia codifica as regras que evitam os erros clássicos (âncoras no miolo,
`after` ambíguo, decoradores, `occurrence`, caminhos JSON) e termina com um
checklist de autovalidação.

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
