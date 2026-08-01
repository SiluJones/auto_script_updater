# Atualizador Automático de Scripts (ASU)

Ferramenta que aplica modificações a arquivos de um projeto (`.py`, `.md`,
`.json`, `.txt` e **qualquer linguagem** via janela de contexto) a partir de um
**arquivo de instrução** gerado por IA. Elimina o copia-e-cola manual de trechos
de código entre sessões: a IA emite um YAML estruturado, você confere o diff e
aplica com um comando — ou pela interface gráfica.

> Documentação de contexto completa (visão, arquitetura, decisões, armadilhas):
> ver `meta/CONTEXT.md`, `meta/DECISIONS.md` e `meta/ROADMAP.md`.

## Estado atual — 0.9.3

O núcleo (CLI) e a interface gráfica (PySide6) estão funcionais e testados
(**165 testes**). A GUI reusa exatamente a mesma pilha do CLI
(`parser → validator → engine`), sem lógica própria.

Implementado:
- Parser (YAML/JSON, com fallback de encoding) + validador contra JSON Schema
  (`format_version`), com intake estrito (chave YAML duplicada, IDs repetidos e
  arquivo binário são rejeitados com erro claro).
- **13 estratégias** de modificação: Python via libcst (`replace_function`,
  `replace_method`, `replace_class`); texto/contexto universal
  (`insert_after_pattern`, `insert_before_pattern`, `replace_line_pattern`,
  `replace_context_block`); Markdown (`replace_section`, fence-aware); JSON com
  navegador de caminho próprio (`set_json_path`, `append_json_array`,
  `delete_json_path`); arquivo inteiro (`create_file`, `replace_file`).
- Resolução de caminhos (relativo à raiz / absoluto) com guarda de contenção.
- **Backup obrigatório** timestampado + **rollback** atômico (automático em falha
  e manual por timestamp). Por padrão o backup vai para **fora do repositório**,
  num destino **derivado da raiz** (`parent(raiz)/zz_backups/<timestamp>/`) — o
  prefixo `zz_` mantém a pasta no fim da listagem, longe do projeto. Trocar a
  raiz troca o destino junto; configurável via `--backup-dir`. Backups antigos
  em `backups/` continuam restauráveis.
- Log consolidado `history.log`: uma linha por aplicação **e também por rollback
  manual** (Desfazer na GUI, `rollback` no CLI, `self-test`). Cada linha de
  aplicação traz **qual instrução a gerou** (o nome do arquivo), e o
  `manifest.txt` da sessão repete a origem no cabeçalho — com várias instruções
  circulando pelo mesmo projeto, é o que permite escolher o timestamp certo no
  Desfazer sem abrir cada pasta.
- **Canal de avisos não-fatais ("ressalva")** — um terceiro estado, *aplicado com
  ressalva*, entre sucesso e erro (ex.: `create_file` sobre um arquivo que já
  existe avisa da sobrescrita). O aviso **não aborta nem reverte** a aplicação; na
  GUI aparece como 🟡 na árvore e no CLI como `~` por arquivo, contado no resumo
  (`N com ressalva`), com uma linha de atenção quando houver (DEC-028).
- **Dica acionável do validador** quando a âncora de um `replace_context_block`
  fica vazia por tocar a borda do arquivo: a mensagem sugere alternativas
  (`replace_line_pattern`, `insert_before_pattern`, `replace_section`,
  `replace_function`).
- Renderização de diff colorido (unified diff). Na GUI, com **Pygments**
  instalado (dependência de GUI), o diff ganha **realce de sintaxe** por token,
  com o lexer escolhido pelo nome do arquivo; sem Pygments, ou em extensão
  desconhecida, cai no realce só-de-linha de sempre.
- CLI com `validate`, `apply` (prévia + confirmação), `rollback`, `self-test`,
  `--sandbox`.
- GUI: recentes/fixadas, atalhos `.bat` por projeto e "abrir GUI", campo de
  backup que mostra o destino calculado, colar instrução da área de
  transferência, copiar erro para a IA, **copiar a saída completa** da
  prévia/aplicação, e o indicador de ressalva 🟡.
- Encodings seguros: BOM UTF-8 preservado (roundtrip com Visual Studio); cp1252
  e CRLF preservados; UTF-16/32 rejeitados com erro claro.
- Multilinguagem comprovada por teste (C#, C++, Java, JSX, TSX, GDScript).

## Instalação (Windows)

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Para a GUI:

```
pip install -r requirements-gui.txt
```

Para desenvolvimento (testes + qualidade):

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

Por padrão o backup vai para `zz_backups/` na **pasta-pai** da raiz (fora do
projeto), então o repositório fica limpo. Para desfazer, o `rollback` procura no
mesmo lugar automaticamente — inclusive na pasta `backups/` de versões
anteriores; se você usou `--backup-dir`, repita a mesma flag no rollback.

> Nota: `examples\exemplo_instrucao.yaml` é apenas **ilustrativo** — aponta para
> caminhos fictícios e **não roda** como está. Para testar de fato, use
> `examples\demo.yaml` acima.

## Uso no seu projeto

Substitua `MINHA_INSTRUCAO.yaml` pelo caminho real da instrução que a IA gerou e
`C:\meu_projeto` pela raiz do seu projeto:

```
python -m src validate MINHA_INSTRUCAO.yaml
python -m src apply MINHA_INSTRUCAO.yaml --root C:\meu_projeto --dry-run
python -m src apply MINHA_INSTRUCAO.yaml --root C:\meu_projeto
python -m src rollback <TIMESTAMP> --root C:\meu_projeto
```

Flags úteis do `apply`: `--dry-run` (simula sem escrever), `--yes`/`-y` (aplica
sem perguntar), `--no-color` (saída sem cores), `--no-backup` (não recomendado),
`--sandbox` (aplica numa cópia irmã), `--backup-dir PASTA` (onde criar a pasta
de backups, em vez do `zz_backups/` derivado da raiz). O `rollback` aceita
`--root` e `--backup-dir`.

## Interface gráfica

Com as dependências de GUI instaladas:

```
python -m src.gui
```

Escolha a raiz e a instrução, clique **Pré-visualizar (dry-run)** para ver a
árvore de arquivos e o diff colorido, depois **Aplicar** (cria backup) ou
**Desfazer última aplicação**. A árvore usa 🟢 (ok) / 🔴 (falha) / ⚪ (inalterado)
por arquivo, com cada modificação marcada ✓/✗; quando uma aplicação passa **com
ressalva** (ver o canal de avisos abaixo), o arquivo aparece como 🟡 e a
modificação como ⚠, com o texto do aviso no tooltip (precedência 🔴 > 🟡 > 🟢 > ⚪).
Com **Pygments** instalado, o diff sai com realce de sintaxe; nesse modo as
linhas adicionadas/removidas são marcadas pelo **fundo** (verde/vermelho claros)
e as cores do texto ficam por conta da sintaxe.
Recursos de conveniência:
- **Recentes ▾** (até 8) e botão **📌** para fixar as raízes que você mais usa.
- Campo **Backup:** para escolher onde o backup é criado (expõe o
  `--backup-dir`). Deixe **vazio** para usar o padrão: o texto acinzentado
  mostra o destino calculado a partir da raiz atual e acompanha a troca de raiz.
- **Colar instrução** — lê o YAML direto da área de transferência, sem salvar arquivo.
- **Copiar erro para a IA** — em falha, copia um bloco pronto (erro + referência
  do guia) para colar na IA geradora e corrigir a instrução.
- **Copiar saída** — copia o relatório **completo** da última prévia/aplicação
  (todos os arquivos, status, avisos 🟡 e diffs), tanto em **sucesso** quanto em
  **falha**. Complementa o "Copiar erro para a IA" (que só surge em falha) — útil
  para colar num chat ou guardar registro da execução.
- **Aplicar em sandbox (cópia)** — paridade com o `--sandbox` do CLI.
- **Criar atalho .bat…** — gera um atalho **por projeto**, que reabre a GUI já
  apontada para aquela raiz e aquela pasta de instrução.
- **Criar atalho .bat (abrir GUI)…** — atalho **genérico**, sem console. Copie-o
  para a pasta onde você guarda seus projetos: ao abrir por ele, a GUI começa
  **limpa** (não traz a raiz do projeto anterior) e os diálogos de "Escolher..."
  abrem **na pasta do próprio `.bat`**. O menu **Recentes ▾** continua ali para
  retomar um projeto anterior. Abrindo a GUI na mão (`python -m src.gui`), o
  comportamento antigo se mantém: a última sessão é restaurada.

Passo a passo detalhado (com as decisões de fluxo e dicas): ver
`docs/GUIA_PASSO_A_PASSO.md`.

## Verificação rápida da instalação

```
python -m src self-test
```

Aplica a demo embutida num diretório temporário, confere os resultados e
reverte — um comando para confirmar que parser, estratégias, backup e rollback
estão sãos na sua máquina. Nada do seu disco é tocado.

## Modo seguro para os primeiros usos em projetos reais

Enquanto ganha confiança, rode numa cópia — e a ferramenta faz isso por você:

```
python -m src apply instrucao.yaml --root C:\meu_projeto --sandbox
```

O `--sandbox` duplica a raiz numa pasta irmã (`meu_projeto_sandbox_<timestamp>`,
ignorando `.git`, `node_modules`, venvs e afins), aplica **na cópia** e imprime
o caminho — o projeto original não é tocado. Revise, copie o que aprovar e
apague a pasta. (Instruções com `path_mode: absolute` são recusadas nesse modo,
pois escapariam da cópia.)

Com Git fica ainda melhor — a working tree é a "duplicata" com diff e desfazer
nativos:

```
git add -A & git commit -m "antes do ASU"
python -m src apply instrucao.yaml --root . --dry-run
python -m src apply instrucao.yaml --root .
git diff
git restore .
```

As camadas de proteção do ASU (dry-run, backup automático, rollback atômico e
por timestamp) continuam ativas em qualquer um dos fluxos.

## Gerando instruções com IA (kit de ensino)

Para que uma IA gere instruções corretas de primeira em **qualquer projeto seu**:

1. copie `docs/INSTRUCTION_GUIDE.md` para a base de conhecimento do projeto (ou
   suba o arquivo e referencie-o nas instruções — assim uma atualização é só
   trocar o arquivo);
2. cole o bloco de `docs/PROMPT_IA.md` nas instruções do projeto;
3. peça: *"emita uma instrução ASU para estas mudanças"*.

O guia codifica as regras que evitam os erros clássicos (âncoras no miolo,
`after` ambíguo, decoradores, `occurrence`, caminhos JSON, âncoras em ASCII) e
termina com um checklist de autovalidação e uma seção de verificação
pós-aplicação.

> Quando usar o ASU: ele brilha ao **editar arquivos existentes** (a instrução
> carrega só localizadores + linhas mudadas). Para **criar arquivo novo**, em
> geral é mais simples entregar o arquivo pronto para baixar — a não ser que ele
> faça parte de uma instrução que também altera arquivos existentes (aí o
> `create_file` na mesma instrução dá atomicidade). Ver DEC-025.

## Testes

```
pip install -r requirements-dev.txt
python -m pytest
```

Qualidade: `ruff check .` e `black --check .`.

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
número de linha como localizador (ver DEC-001, em `meta/DECISIONS-archive.md`).
