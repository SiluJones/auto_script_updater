# spec0013 — Higiene de fechamento (0.9.2): alinhar STATUS/ROADMAP à realidade antes do repouso

> **Tipo:** registros/curadoria (meta apenas — SEM código). **Autoria:** chat. **Execução:** Claude Code.
> **Âncoras são SEMÂNTICAS** — trecho literal único, **nunca número de linha**. Localize cada âncora EXATAMENTE; **se não achar uma, PARE e reporte**. Não toque em nada fora das edições nomeadas.
> **Versão-alvo:** nenhuma (sem código; **não** bumpar, **não** mexer no CHANGELOG).

---

## Contexto

O ASU vai voltar ao **repouso** na **0.9.2** (estável, 158 testes verdes, uso real validado). Auditoria de fechamento achou 4 divergências entre o que os `meta/` AFIRMAM e o que o repo É — todas de registro. Elas enganam quem retomar depois de meses:

1. **STATUS diz "README/GUIA parados na 0.8.2"** — mas o README do repo já está em **0.8.5** (traz "Copiar saída") e o GUIA também descreve o "Copiar saída". Ou seja, o refresh entregue em sessão anterior **foi aplicado**; a dívida real é só **0.8.6→0.9.2** (syntax-highlight, ressalva no CLI, `zz_backups`, `--start-dir`). Duas fontes divergindo — viola "uma fonte de verdade por dado".
2. **Marco de pausa desatualizado:** a seção "⏸️ Pausa de maturação" ainda fala em pausa "na 0.8.7" e trata a interrupção como evento isolado; agora houve um ciclo inteiro 0.9.0→0.9.2 e novo repouso na 0.9.2.
3. **ROADMAP F2 não reflete o entregue:** o item de backup ainda diz `parent(root)/backups/<ts>` (agora é `zz_backups`, DEC-032) e não há marca do syntax-highlight nem do `--start-dir`.
4. **O bullet "Documentação de usuário" do STATUS** descreve a dívida com a régua antiga (0.8.3–0.8.6, "captura já disponível") — precisa passar a régua para 0.8.6→0.9.2.

Nenhuma DEC nova (as decisões desta leva — DEC-030/031/032 — já estão registradas).

---

## Parte A — `meta/STATUS.md`: corrigir a dívida de documentação

**Âncora (bloco literal único):**

```markdown
- **Documentação de usuário — ATUALIZADA (2026-07-03):** `README.md` reescrito para 0.8.2 (backup padrão na pasta-pai, `--backup-dir`, `history.log`, GUI completa, 13 estratégias, encodings) e `GUIA_PASSO_A_PASSO.md` criado do zero atendendo os pedidos do usuário (ideia-260614: local do `instrucao.yaml`, subir o PROMPT_IA ao projeto, `--backup-dir`/`history.log`/sandbox, `--no-backup`). Entregues pelo chat como arquivos inteiros e **commitados** (`ff67a39`/`fb0d5b6`). RESTA: refrescar `README.md`/`GUIA_PASSO_A_PASSO.md` para **0.8.3–0.8.6** (canal 🟡, dica do validador na borda, rollback no `history.log`, botão Copiar saída, syntax-highlight opcional) — chat autora arquivo inteiro, Code commita. Captura de tela de PRODUÇÃO **já disponível** (run 2026-07-17 no Novelista: diff real de `.md` + botão Copiar saída) para embutir no refresh — não precisa mais esperar a GUI "estabilizar".
```

**Substituir por:**

```markdown
- **Documentação de usuário — PARCIALMENTE atualizada:** `README.md` e `GUIA_PASSO_A_PASSO.md` estão em **0.8.5** (backup na pasta-pai, `--backup-dir`, `history.log`, 13 estratégias, encodings, canal 🟡, dica do validador na borda, rollback no `history.log`, botão **Copiar saída**). **RESTA refrescar para 0.8.6→0.9.2** (chat autora arquivo inteiro, Code commita): **syntax-highlight** opcional no diff (0.8.6); **ressalva 🟡 no CLI** (0.8.7); pasta de backup **`zz_backups`** + o campo Backup que agora DERIVA da raiz e mostra o destino no placeholder (0.9.0, DEC-032); atalho **"abrir GUI"** que semeia a navegação e começa limpo (0.9.1/0.9.2). Captura de tela de PRODUÇÃO já disponível (run 2026-07-17, Novelista) para embutir. É a dívida nº 1 ao retomar — mas **não é bloqueador** e não urge durante o repouso.
```

## Parte B — `meta/STATUS.md`: atualizar o marco de pausa para o repouso 0.9.2

**Âncora (bloco literal único — o cabeçalho da seção e seu parágrafo):**

```markdown
## ⏸️ Pausa de maturação (desde 2026-07-19)
Decisão do usuário: o ASU entra em **pausa deliberada** na **0.8.7** para maturar em uso real, sem novas features. Nada está quebrado; nenhuma fase grande está em aberto (F0/F1 concluídas; F2 com só itens cosméticos; F3 parcial por escolha; F4 é futura). Os itens abaixo, em «Em Progresso», seguem válidos mas **não são bloqueadores** — o principal é a dívida de documentação de usuário (README/GUIA parados na 0.8.2 enquanto o produto está na 0.8.7). Ao retomar: ler o HANDOFF-BRIEF da sessão de 2026-07-19 e rodar o ritual normal. O uso real continua (projeto Novelista) e é a própria fonte de feedback da pausa — se aparecer atrito, ele vira ideia no IDEAS, não correção imediata. Pausa interrompida em 2026-07-20 por um bug de endereçamento de backup encontrado em uso real (DEC-032) — exatamente o tipo de retorno que a pausa existia para colher.
```

**Substituir por:**

```markdown
## ⏸️ Repouso de maturação (retomado em 2026-07-20, na 0.9.2)
Decisão do usuário: o ASU volta ao **repouso deliberado** na **0.9.2**, para maturar em uso real, sem novas features. Nada está quebrado; nenhuma fase grande está em aberto (F0/F1 concluídas; F2 com só itens cosméticos; F3 parcial por escolha; F4 é futura). Os itens em «Em Progresso» seguem válidos mas **não são bloqueadores**; a única dívida de fundo é a documentação de usuário (README/GUIA em 0.8.5, produto em 0.9.2 — ver acima).

**Histórico do repouso:** a primeira pausa foi declarada em 2026-07-19 na 0.8.7. Foi **interrompida no dia seguinte** (2026-07-20) porque o uso real devolveu retorno concreto — um bug de endereçamento de backup (o campo "grudava" e ignorava a troca de raiz; agravado por testes que gravavam no `QSettings` real do usuário) e dois ajustes de usabilidade do atalho "abrir GUI". Isso virou o ciclo **0.9.0→0.9.2** (DEC-032 + specs 0010/0011/0012), validado em produção pelo usuário. **É exatamente o que o repouso existe para colher:** ficar em uso, deixar o atrito real aparecer, corrigir em lote, voltar a repousar. Ao retomar: ler o HANDOFF-BRIEF de 2026-07-20 e rodar o ritual normal.
```

## Parte C — `meta/ROADMAP.md`: refletir o backup `zz_backups` e o que foi entregue na F2

### C1 — item de backup (DEC-032)

**Âncora (bloco literal único):**

```markdown
- [x] Backup configurável: `--backup-dir` + `history.log` (DEC-018); exposto na GUI + aninhado por projeto quando externo + `rollback_from_dir` (DEC-024 a/b, 0.8.0); **padrão `parent(root)/backups/<ts>` (DEC-024c, 0.8.1)**. PENDENTE: limpeza automática de backups antigos (manter últimos N/X dias).
```

**Substituir por:**

```markdown
- [x] Backup configurável: `--backup-dir` + `history.log` (DEC-018); exposto na GUI + aninhado por projeto quando externo + `rollback_from_dir` (DEC-024 a/b, 0.8.0). **Padrão `parent(root)/zz_backups/<ts>`, DERIVADO da raiz** (DEC-024c → DEC-032, 0.9.0): o campo da GUI não é mais persistido, mostra o destino no placeholder e acompanha a troca de raiz; rollback tem fallback de leitura para o layout antigo `backups/`. PENDENTE: limpeza automática de backups antigos (manter últimos N/X dias) — parqueado (maior risco, interage com rollback).
```

### C2 — syntax-highlight entregue

**Âncora (linha única):**

```markdown
- [ ] Indicador de confiança por modificação (🟢 único / 🟡 ambíguo / 🔴 não encontrado).
```

**Substituir por:**

```markdown
- [x] Syntax-highlight opcional no diff da GUI via Pygments, com degradação graciosa (0.8.6, DEC-030).
- [x] Atalho "abrir GUI" semeia a navegação na própria pasta e começa limpo (`--start-dir`, 0.9.1/0.9.2, specs 0011/0012).
- [ ] Indicador de confiança por modificação (🟢 único / 🟡 ambíguo / 🔴 não encontrado).
```

---

## Validação (Code)

- Nenhum código muda. `python -m src self-test` (sanidade) e `git diff` restrito a **`meta/STATUS.md`** e **`meta/ROADMAP.md`**. Conferir que nenhuma outra linha do STATUS/ROADMAP foi deslocada e que nada sumiu.

## Commit + push

```
git add meta\STATUS.md meta\ROADMAP.md && git commit -m "docs: alinha STATUS e ROADMAP a realidade 0.9.2 antes do repouso"
```

```
git log origin/main..HEAD --oneline && git push
```
