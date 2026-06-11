# INSTRUCTION_GUIDE — Como gerar instruções para o Atualizador Automático de Scripts

> **Para quem é este documento:** a IA (ou pessoa) que vai GERAR arquivos de
> instrução. Ele é autocontido: pode ser copiado para a base de conhecimento de
> qualquer projeto. Versão do formato: **1.0** · Guia revisado em 2026-06-10
> (ferramenta v0.3.0).

## 1. O que é uma instrução

Um arquivo **YAML** (JSON também é aceito) que descreve modificações a aplicar
em arquivos de um projeto. A ferramenta valida contra um schema, mostra o diff,
cria backup e aplica com rollback automático em falha. O fluxo do usuário:

```
python -m src validate INSTRUCAO.yaml
python -m src apply INSTRUCAO.yaml --root C:\projeto --dry-run   (revisão)
python -m src apply INSTRUCAO.yaml --root C:\projeto             (aplicação)
```

## 2. Esqueleto mínimo

```yaml
format_version: "1.0"            # obrigatório, exatamente assim
generated_by: "claude"           # opcional
generated_at: "2026-06-10T12:00:00"  # opcional
description: "Resumo do que esta instrução faz"   # obrigatório

settings:                        # opcional (estes são os padrões)
  backup: true
  dry_run: false
  stop_on_error: true
  encoding: "utf-8"

files:
  - id: "f1"                     # único entre os arquivos
    path_mode: "relative"        # "relative" (recomendado) ou "absolute"
    relative_path: "src/app.py"  # use / ou \\ ; relativo à --root do usuário
    type: "python"               # python | markdown | json | text
    modifications:
      - id: "m1"                 # único dentro do arquivo
        description: "O que esta modificação faz"
        strategy: "replace_function"
        location: { name: "minha_funcao" }
        new_content: |
          def minha_funcao():
              return 42
```

Regras gerais de campos:
- `new_content` = conteúdo que **substitui** algo; `content` = conteúdo
  **inserido/criado**; `value` = valor JSON (qualquer tipo).
- **Não existe `location.type`** — a `strategy` define sozinha como ler o
  `location`.
- **Nunca use número de linha** como localizador.
- IDs (`files[].id`, `modifications[].id`) **não podem se repetir** — a
  validação rejeita.
- Não repita chaves YAML no mesmo nível (ex.: dois `files:`) — o parser rejeita.

## 3. Escolhendo a estratégia certa

| Alvo | Estratégia | `location` | Conteúdo |
|---|---|---|---|
| Função Python (nível de módulo) | `replace_function` | `{name}` (+`class_name` p/ função aninhada em classe) | `new_content` |
| Método Python | `replace_method` | `{class_name, name}` — class_name **obrigatório** | `new_content` |
| Classe Python inteira | `replace_class` | `{name}` | `new_content` |
| Inserir linha(s) após um ponto | `insert_after_pattern` | `{pattern, occurrence?}` (regex de linha) | `content` |
| Inserir linha(s) antes de um ponto | `insert_before_pattern` | `{pattern, occurrence?}` | `content` |
| Trocar UMA linha | `replace_line_pattern` | `{pattern, occurrence?}` | `new_content` |
| Trocar um BLOCO em **qualquer linguagem** | `replace_context_block` | `{before, after, occurrence?}` (literais) | `new_content` (só o miolo!) |
| Seção Markdown | `replace_section` | `{heading, include_heading?}` | `new_content` |
| Valor em JSON | `set_json_path` | `{path}` (ex.: `api.version`, `a.b[0].c`) | `value` |
| Acrescentar a array JSON | `append_json_array` | `{path}` | `value` |
| Remover nó JSON | `delete_json_path` | `{path}` | — |
| Substituir arquivo INTEIRO | `replace_file` | — | `new_content` |
| Criar arquivo NOVO | `create_file` | — | `content` |

Preferências: para `.py` use as estratégias Python (precisão semântica); para
`.json` use as de JSON; para **qualquer outra linguagem** (C#, C++, Java, JS,
JSX, TSX, GDScript, Rust, Go…) use `type: "text"` + `replace_context_block` ou
patterns, e preencha `language: "csharp"` etc. (informativo). Para entregar um
arquivo completo novo, `create_file`; para reescrever um inteiro, `replace_file`
(prefira modificações cirúrgicas quando possível).

## 4. ⚠️ As cinco regras de ouro (erros que a ferramenta REJEITA ou que corrompem)

### 4.1 `replace_context_block`: o `new_content` é SÓ O MIOLO
As âncoras `before` e `after` **permanecem no arquivo**. Repeti-las no
`new_content` é rejeitado (duplicaria as linhas).

```yaml
# ❌ ERRADO — repete as âncoras
location: { before: "function initApp() {", after: "}" }
new_content: |
  function initApp() {
    console.log("novo");
  }

# ✅ CERTO — só o que vai ENTRE as âncoras
location: { before: "function initApp() {", after: "}" }
new_content: |2
    console.log("novo");
```

### 4.2 `after` fecha no PRIMEIRO match — use âncora distintiva
Em linguagens com `}` (C#, C++, Java, JS…), um `after: "}"` curto fecha no
delimitador **interno** se o bloco tem `if`/`for` aninhado. Escolha um `after`
inequívoco: a linha de fechamento no nível certo (`"\n}"` = `}` na coluna 0,
`"\n    }"` = fechamento indentado de método) ou um trecho do código que vem
DEPOIS do bloco (ex.: a assinatura da próxima função).

```yaml
# Para substituir o corpo inteiro de uma função C# (4 espaços de indentação):
location:
  before: "public bool ValidateToken(string token)\n        {"
  after: "\n        }"
```

### 4.3 Localizador ambíguo sem `occurrence` é REJEITADO
Se o `pattern`/`before` casa mais de uma vez e você não declarou `occurrence`,
a ferramenta bloqueia (evita modificar o lugar errado). Duas saídas: torne o
localizador mais específico (preferível) ou declare `occurrence: N`
conscientemente. O mesmo vale para headings Markdown repetidos
(`replace_section` exige heading único no documento).

### 4.4 Decoradores fazem parte da função
`replace_function`/`replace_method` substituem o nó COMPLETO. Se a função
original tem `@decorator` e o `new_content` não o repete, **o decorador some**.
Sempre reproduza os decoradores que devem permanecer.

### 4.5 JSON: o caminho `set_json_path` cria intermediários
`set_json_path` com `path: "aip.version"` (typo) **cria** o galho `aip` em vez
de falhar. Confira o caminho letra a letra contra o arquivo real. Para
`append_json_array` e `delete_json_path` o caminho precisa existir (um valor
`null` existe e é removível).

## 5. Detalhes que evitam fricção

- **Indentação no YAML:** o bloco `|` remove a indentação comum. Quando o
  conteúdo precisa começar indentado (miolo de função), use o indicador
  numérico: `|2` preserva 2 espaços, `|4` preserva 4. Em GDScript, use TAB real
  dentro do bloco.
- **Encoding:** arquivos-alvo devem ser UTF-8 (BOM ok — é preservado) ou
  CP-1252. UTF-16 e binários são rejeitados. A instrução em si: UTF-8.
- **Caminhos Windows:** em YAML com aspas duplas, escape a barra (`"C:\\proj"`)
  ou use barra normal (`C:/proj`). Prefira `path_mode: relative` — o usuário
  passa a raiz com `--root`.
- **Regex em `pattern`:** é regex Python aplicada **linha a linha**; `^` e `$`
  ancoram a linha. Escape metacaracteres (`\.`, `\(`, `\[`).
- **Ordem das modificações:** dentro de um arquivo elas são aplicadas em
  sequência, cada uma vendo o resultado da anterior. Se a mod 2 procura algo
  que a mod 1 inseriu, isso funciona — mas prefira independência.
- **Markdown:** headings dentro de blocos de código (``` ``` ```) são ignorados
  corretamente pela ferramenta; não conte com eles como âncora de seção.
- **Arquivo grande novo:** prefira UM `create_file` com o conteúdo completo a
  dezenas de inserções.

## 6. Checklist de autovalidação (rode mentalmente antes de emitir)

1. `format_version: "1.0"` e `description` presentes?
2. Todos os `id` únicos (arquivos entre si; modificações dentro do arquivo)?
3. Cada `strategy` recebe o campo de conteúdo certo (`new_content` × `content`
   × `value`) e o `location` no formato da tabela?
4. Algum `replace_context_block` com âncoras dentro do `new_content`? (proibido)
5. Algum `after` genérico (`"}"` solto) num bloco com aninhamento? (use âncora
   distintiva)
6. Algum localizador que provavelmente casa mais de uma vez sem `occurrence`?
7. Funções decoradas: decoradores reproduzidos no `new_content`?
8. Caminhos JSON conferidos contra o arquivo real (sem typo)?
9. Indentação do conteúdo correta (indicador `|N` quando necessário)?
10. Caminhos de arquivo relativos à raiz que o usuário vai passar?

## 7. Exemplo completo de referência

O repositório da ferramenta traz `examples/demo.yaml` (executável contra
`examples/demo_project/`) cobrindo Python, Markdown, JSON, JavaScript via
contexto e criação de arquivo — use-o como gabarito de estilo.
