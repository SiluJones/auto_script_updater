# ASU — Atualizador Automático de Scripts — guia para o Claude Code

> Arquivo-raiz lido pelo Claude Code em toda sessão. Mantenha CURTO (custa token em todo turno).
> O comportamento detalhado do assistente está em `meta/CEREBRO.md`. Não duplique regra aqui.

## Ritual de início
Leia `meta/CEREBRO.md` → `meta/CONTEXT.md` → `meta/STATUS.md` → `meta/HUB.md` antes de agir. Confirme em uma frase o que entendeu. Se houver ambiguidade real, pergunte antes.

## Build / validação
- Testes: `python -m pytest` — devem ficar todos verdes antes de commitar mudança de código.
- Self-test ponta a ponta: `python -m src self-test` (aplica a demo embutida em tempdir; nada do disco é tocado).
- Lint/format: `ruff check .` e `black --check .` — limpos antes do commit.
- Mudança só de doc (`meta/`) NÃO precisa de build; a rede é o `git diff`.

## Convenções
- Mensagens de commit em PT-BR, imperativo curto, **sem acento** (Conventional Commits: `tipo(escopo): descricao`).
- Edições nos `meta/` são **append-only** pelo Code (linha no STATUS, `DEC-`/`FIX-` no DECISIONS, marcar estado de fase no ROADMAP); curadoria que reescreve vem do chat (arquivo inteiro OU spec em `meta/specs/`).
- Ao aplicar uma spec de `meta/specs/`: ache cada âncora EXATAMENTE (seção/título, nunca nº de linha); se não achar, **PARE e reporte**. Não mexa fora das edições nomeadas. `git diff` antes do commit.
- Código: docstring em função pública; comentário explica o PORQUÊ; mudança mínima que resolve; vai à causa raiz.
- Arquivos críticos (ler antes de tocar): `src/core/patch_engine.py`, `src/core/backup_manager.py`, `src/schemas/instruction_v1.schema.json`, `docs/INSTRUCTION_GUIDE.md`.
