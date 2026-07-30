# ASU — Atualizador Automático de Scripts — guia para o Claude Code

> Arquivo-raiz lido pelo Claude Code em toda sessão. Mantenha CURTO (< 200 linhas — custa token em todo turno).
> Regra prática: se remover uma linha e o Claude ainda acerta, ela não pertence aqui. Procedural detalhado → vira skill em `.claude/skills/`.
> O comportamento detalhado do assistente está em `meta/CEREBRO.md`. Não duplique regra aqui.

## Ritual de início
Leia `meta/CEREBRO.md` → `meta/CONTEXT.md` → `meta/STATUS.md` antes de agir. Confirme em uma frase o que entendeu. Se houver ambiguidade real, pergunte antes.

## Build / validação
- Testes: `python -m pytest` — devem ficar todos verdes antes de commitar mudança de código.
- Self-test ponta a ponta: `python -m src self-test` (aplica a demo embutida em tempdir; nada do disco é tocado).
- Lint/format: `ruff check .` e `black --check .` — limpos antes do commit.
- Mudança só de doc (`meta/`) NÃO precisa de build; a rede é o `git diff`.

## Vocabulário (DEC-033)
- **WO** = instrução de APLICAÇÃO (âncora + texto exato), em `meta/workorders/AAMMDD-woNNNN-desc.md`. Comando: `/apply-wo`.
- **spec** = spec de FEATURE (o QUE construir e quando está pronto), modelo em `meta/SPEC.md`, uma por feature em `meta/specs/`.
- As instruções antigas `AAMMDD-specNNNN-desc.md` e `F<n>-slug.md` **mudaram de pasta, não de nome**: estão em `meta/workorders/`. Citação antiga a `meta/specs/<arquivo>` em doc datado vale para `meta/workorders/<arquivo>` — não corrija texto datado.
- A numeração é contínua: a última foi `spec0013`, a primeira WO é `wo0014`.

## Convenções
- Mensagens de commit em PT-BR, imperativo curto, **sem acento** (Conventional Commits: `tipo(escopo): descricao`).
- Edições nos `meta/` são **append-only** pelo Code (linha no STATUS, `DEC-`/`FIX-` no DECISIONS, marcar estado de fase no ROADMAP); curadoria que reescreve vem do chat (arquivo inteiro OU WO em `meta/workorders/`).
- Respeite o campo **Canal dos meta neste ciclo** do cabeçalho da WO: CHAT = não faça append (o chat entrega os docs); CODE = a WO é o registro. Uma fonte por doc por ciclo.
- Ao aplicar uma WO: ache cada âncora EXATAMENTE (seção/título/símbolo, nunca nº de linha); se não achar, **PARE e reporte**. Idempotência: se a frase-chave do texto novo já existe, PULE e diga. Não mexa fora das edições nomeadas. `git diff` antes do commit.
- Código: docstring em função pública; comentário explica o PORQUÊ; mudança mínima que resolve; vai à causa raiz.
- Arquivos críticos (ler antes de tocar): `src/core/patch_engine.py`, `src/core/backup_manager.py`, `src/schemas/instruction_v1.schema.json`, `docs/INSTRUCTION_GUIDE.md`.
- **Ao fechar a tarefa, RELATE o trabalho** — o que fez, achados e desvios do que a tarefa pedia, arquivos tocados, resultado do build/validação e o commit. **Não** copie o bloco de fecho do `meta/CEREBRO.md`: aquele é da raia de planejamento, e trocar relatório por formulário perde o que só você viu.

## Config (modelo × esforço)
- WO com diff exato já validado → **Sonnet**, esforço proporcional (mecânico = baixo/médio).
- Tarefa com julgamento sem rede (mexer no `patch_engine`/`backup_manager`, refator multi-arquivo, WO que delega decisão) → **Opus**, esforço alto.
- Esforço proporcional à ambiguidade; `/effort low` para o trivial. No Code não existe toggle de pensamento — para um turno difícil pontual, `ultrathink` no prompt.
