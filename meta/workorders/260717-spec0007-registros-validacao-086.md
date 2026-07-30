# spec0007 — Registros: validação 0.8.6 em produção + captura de ideias

> **Tipo:** registros/curadoria (meta apenas — SEM código). **Autoria:** chat. **Execução:** Claude Code.
> **Âncoras são SEMÂNTICAS** — trecho literal único, **nunca número de linha**. Localize cada âncora EXATAMENTE; **se não achar uma, PARE e reporte**. Não toque em nada fora das edições nomeadas.
> **Versão-alvo:** nenhuma (não há mudança de código; não bumpar, não mexer no CHANGELOG).

---

## Contexto

O 0.8.6 (syntax-highlight, spec0006) foi exercitado em **uso real de produção** (projeto Novelista "Rascunho de um Despertar", run 2026-07-17): a GUI aplicou uma instrução com 7 arquivos `.md`, o botão **Copiar saída** produziu o relatório completo num caso de SUCESSO, e o diff renderizou com o pipeline novo. Isto valida na prática os itens que estavam pendentes de "validação visual". Falta só confirmar um detalhe específico da DEC-030 (o fundo das linhas +/-).

Esta spec **não muda código** — só atualiza registros: o STATUS (validação + dívida de docs) e o IDEAS (captura de 3 ideias novas desta leva). Nenhuma DEC nova (a política do FlatDrop fica em IDEAS até ser adotada — ver Parte B3).

---

## Parte A — `meta/STATUS.md`

### A1 — validação visual em bom estado

**Âncora (bullet literal único, seção "🔧 Em Progresso"):**

```markdown
- **F2 (GUI) — itens estruturais restantes:** validação VISUAL no Windows segue pendente (o usuário rodou a GUI e confirmou que os botões/atalhos e o campo Backup aparecem — ver screenshot 06-28 — mas falta uso prolongado); barra de progresso; tema claro/escuro; seleção de timestamps antigos no Desfazer.
```

**Substituir por:**

```markdown
- **F2 (GUI) — itens estruturais restantes:** validação VISUAL no Windows em bom estado — uso real em PRODUÇÃO 2026-07-17 (projeto Novelista): prévia/aplicação, árvore, botão **Copiar saída** (caso de SUCESSO conferido) e **syntax-highlight** rendendo um diff real de `.md`. Resta confirmar só o item específico da DEC-030: se as linhas +/- exibem o **fundo** verde/vermelho (não apenas texto colorido) no `QTextEdit` desta versão do Qt — se não exibirem, aplicar o fallback `<div>` já anotado na DEC-030. Restantes: barra de progresso; tema claro/escuro; seleção de timestamps antigos no Desfazer.
```

### A2 — dívida de documentação de usuário (README/GUIA)

**Âncora (frase literal única, mesma seção):**

```markdown
RESTA: refrescar o conteúdo para 0.8.3/0.8.4 (canal 🟡, dica do validador na borda, rollback registrado no `history.log`, botão Copiar saída da spec0004) e capturas quando a GUI estabilizar visualmente.
```

**Substituir por:**

```markdown
RESTA: refrescar `README.md`/`GUIA_PASSO_A_PASSO.md` para **0.8.3–0.8.6** (canal 🟡, dica do validador na borda, rollback no `history.log`, botão Copiar saída, syntax-highlight opcional) — chat autora arquivo inteiro, Code commita. Captura de tela de PRODUÇÃO **já disponível** (run 2026-07-17 no Novelista: diff real de `.md` + botão Copiar saída) para embutir no refresh — não precisa mais esperar a GUI "estabilizar".
```

---

## Parte B — `meta/IDEAS.md` (captura de 3 ideias novas)

**Âncora (linha única — cabeçalho da subseção do assistente):**

```markdown
## 🤖 Ideias Ativas — Assistente
```

**Substituir por:**

```markdown
## 🤖 Ideias Ativas — Assistente

### 2026-07-17 — Exibir a ressalva 🟡 também no resumo do CLI — EM ABERTO (achado nesta sessão)
O canal de warnings (DEC-028, 0.8.3) faz o 🟡 aparecer na GUI (árvore + tooltip), mas o `_print_report` do CLI (`src/__main__.py`) só imprime criado/modificado/inalterado/falha — a RESSALVA fica **invisível na linha de comando**. Achado ao autorar a spec0006. Baixo risco: no resumo do `_print_report`, contar as ressalvas e, por arquivo com `has_warnings`, imprimir os avisos (a mesma informação que o `_report_to_text` já serializa). Fecha a paridade CLI↔GUI do 🟡. Candidato natural de próxima passada pequena.

### 2026-07-17 — Diff intra-linha (nível de palavra) na GUI — PROPOSTA (mecânica on-theme para prosa)
Hoje o diff realça a LINHA inteira quando ela muda. Para PROSA (o caso de maior medo — ver ideia 2026-06-19: erro em `.md`/`.txt` é invisível até alguém ler), o que mais ajuda é ver EXATAMENTE quais palavras mudaram dentro de uma linha longa quase idêntica. Mecânica: além do diff por linha, um realce intra-linha (nível de palavra) marcando só o trecho alterado entre a linha `-` e a `+` correspondente (via `difflib.SequenceMatcher` sobre tokens). Constrói sobre o painel de diff recém-melhorado (0.8.6, syntax-highlight) e serve direto o uso real (edição de meta/prosa no Novelista). Risco médio (parear linhas -/+ e destacar spans); GUI-only, degradação graciosa. Avaliar como próxima mecânica de review.

### 2026-07-17 — Política de ignore do FlatDrop (logs/specs/archive fora do mount) — ENTREGUE, adoção pendente
Entregue nesta sessão um `.flatdropignore` adaptado ao ASU: exclui do mount `logs/`, specs aplicadas (`meta/specs/*` + reinclusão pontual da spec em voo) e `meta/DECISIONS-archive.md` — economia ~54k tokens (~186k → ~132k). Continua tudo no git; só não é enviado ao Projeto. TRADE-OFF registrado no próprio arquivo: com specs fora do mount, a salvaguarda "checar `meta/specs/` antes de autorar spec" passa a depender de STATUS/CHANGELOG/DECISIONS (que citam cada spec por número). Estado atual: arquivo no repo como `.flatdropignore.txt`, **não versionado/ativo**. PENDENTE de decisão do usuário: (1) confirmar o NOME que o FlatDrop lê de fato; (2) versionar (o header do arquivo diz "versionado, tem a palavra final"); (3) então registrar **DEC-031** (adoção da política). Enquanto não ativado, o mount segue completo.
```

---

## Validação (Code)

- Nenhum teste/código muda; ainda assim rodar `python -m src self-test` e `git diff` para confirmar que SÓ `meta/STATUS.md` e `meta/IDEAS.md` mudaram, e que os appends do IDEAS não deslocaram nenhuma ideia existente (nada some — IDEAS é append-only).

## Commit (Claude Code)

Bloco isolado, CMD Windows numa linha, mensagem PT-BR imperativa sem acento:

```
git add meta\STATUS.md meta\IDEAS.md && git commit -m "docs: registra validacao 0.8.6 em producao e captura ideias (CLI ressalva, diff intra-linha, politica flatdrop)"
```

```
git log origin/main..HEAD --oneline && git push
```
