# PROMPT_IA — Bloco pronto para colar no contexto de outros projetos

> **Como usar:** copie o bloco entre as linhas `─────` para as instruções do
> seu projeto (Claude Project, system prompt, CLAUDE.md…), junto com o arquivo
> `INSTRUCTION_GUIDE.md`. A partir daí, peça: *"emita uma instrução ASU para
> estas mudanças"*.

─────────────────────────────────────────────────────────────────────────────

## Saída de código via Atualizador Automático de Scripts (ASU)

Este projeto usa o **ASU**, uma ferramenta que aplica modificações de código a
partir de um arquivo de instrução YAML (`format_version: "1.0"`). Quando eu
pedir uma "instrução ASU" (ou quando entregar muitas mudanças pequenas em
arquivos existentes), em vez de colar trechos soltos:

1. **Emita UM arquivo YAML completo** seguindo o `INSTRUCTION_GUIDE.md` da base
   de conhecimento (esqueleto, tabela de estratégias e regras de ouro).
2. Prefira modificações **cirúrgicas** (função/método/seção/caminho JSON) a
   reescrever arquivos; use `create_file` para arquivos novos.
3. Para linguagens sem estratégia semântica (C#, C++, Java, JS/JSX/TSX,
   GDScript…), use `type: "text"` + `replace_context_block`, lembrando:
   - `new_content` é **só o miolo** — as âncoras `before`/`after` permanecem
     no arquivo e não podem aparecer no `new_content`;
   - escolha `after` **inequívoco** (ex.: `"\n}"` para fechamento na coluna 0,
     ou a assinatura do bloco seguinte) — nunca um `"}"` solto havendo
     aninhamento;
   - localizadores devem casar **uma única vez**; se a repetição for
     intencional, declare `occurrence: N`.
4. Reproduza **decoradores** no `new_content` ao substituir funções/métodos
   Python decorados.
5. Confira caminhos JSON letra a letra (`set_json_path` cria intermediários —
   um typo cria galho novo em vez de falhar).
6. Termine com 1 linha dizendo o comando de aplicação, ex.:
   `python -m src apply instrucao.yaml --root <RAIZ_DO_PROJETO> --dry-run`
7. Antes de emitir, rode o **checklist de autovalidação** da seção 6 do guia.

Se a mudança for grande/estrutural demais para caber bem numa instrução
(refactor amplo, renomeações em massa), diga isso e proponha dividir.

─────────────────────────────────────────────────────────────────────────────
