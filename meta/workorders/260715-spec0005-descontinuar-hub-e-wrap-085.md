# spec0005 — Transferência: `/wrap` 0.8.5 + descontinuar o HUB (DEC-029) + correções

> **Tipo:** wrap + DEC + limpeza de docs. **Autoria:** chat. **Execução:** Claude Code.
> **Âncoras são SEMÂNTICAS** — trecho literal único / título de seção, **nunca número de linha** (os números aqui são só orientação). Localize cada âncora EXATAMENTE; **se não achar uma, PARE e reporte** — não chute. Não toque em nada fora das edições nomeadas. Rode `git diff` e confira antes de commitar.
> **Objetivo:** deixar o repo consolidado para transferência de conversa. Ao fim: versão 0.8.5, HUB descontinuado e registrado, tudo commitado e **empurrado**.
> **Contexto de estado:** código em 0.8.4; **spec0004 já aplicada** (`31b8350`, botão "Copiar saída"); falta o `/wrap` 0.8.5. O `CLAUDE.md` (ritual) e a seção "🔗 Grupo/Toolchain" do `STATUS.md` **já tiveram o HUB removido** por arquivos que o usuário aplicou pelo chat — **NÃO precisa mexer nesses dois** além do que esta spec pede em B.

---

## PARTE A — `/wrap` da 0.8.5 (fecha a spec0004)

Edições explícitas (NÃO rode o comando `/wrap` automático — ele tem um passo de HUB que estamos removendo; faça os passos abaixo à mão):

### A1 — bump de versão
**Arquivo:** `src/__init__.py` — **âncora:** `__version__ = "0.8.4"` → `__version__ = "0.8.5"`.

### A2 — CHANGELOG (nova entrada no topo, acima de `## [0.8.4]`)
**Arquivo:** `CHANGELOG.md` — **âncora:** a linha `## [0.8.4] — 2026-07-06`. **Inserir ANTES dela:**

```
## [0.8.5] — 2026-07-15
### Adicionado
- **Botão "Copiar saída" na GUI (spec0004):** copia o relatório COMPLETO da última prévia/aplicação — todos os arquivos, status, avisos (🟡) e diffs, tanto no sucesso quanto na falha — para a área de transferência. Serialização por função pura `_report_to_text` (sem Qt, testável); gancho em `_populate_tree`, cobrindo preview e apply. Complementa o "Copiar erro para a IA" (que só aparece em falha). Commit `31b8350`. Sem DEC nova.

```

### A3 — STATUS: promover a Versão Atual
**Arquivo:** `meta/STATUS.md`. **Âncora:** o bloco atual que começa em `## Versão Atual` e a linha `**[0.8.4]** — 2026-07-06 — **Validador com dica acionável...`. Substituir o parágrafo da versão atual (o que começa com `**[0.8.4]** — 2026-07-06 — **Validador...`) por:

```
**[0.8.5]** — 2026-07-15 — **Botão "Copiar saída" na GUI (spec0004).** Copia o relatório COMPLETO (todos os arquivos, status, avisos 🟡, diffs — sucesso E falha) via função pura `_report_to_text`; gancho em `_populate_tree` (cobre preview e apply). Complementa o "Copiar erro para a IA". `__version__` = 0.8.5. 1 teste novo; suíte/ruff/black/self-test limpos (commit `31b8350`). Sem DEC nova.
```

E na linha `> **Anterior:**`, inserir no início da lista: `[0.8.4] — 2026-07-06 — Validador com dica acionável + rollback no history.log (spec0003). ` (mantendo o resto da lista intacto).

### A4 — IDEAS: marcar a ideia concluída
**Arquivo:** `meta/IDEAS.md`. **Âncora:** `### 2026-06-15 — Copiar console/saída (não só erro) na GUI, e em massa — EM AVALIAÇÃO`. Trocar o sufixo do título para: `— CONCLUÍDA (spec0004, 0.8.5, commit 31b8350)`. Acrescentar ao fim do parágrafo dessa entrada: ` FEITO: botão "Copiar saída" com `_report_to_text` (relatório completo, sucesso e falha).`

### A5 — ROADMAP: marcar o item F3
**Arquivo:** `meta/ROADMAP.md`. **Âncora:** `- [ ] Botão/flag para copiar a SAÍDA completa (não só erro), inclusive em sucesso — ver IDEAS.` → trocar `- [ ]` por `- [x]` e acrescentar ao fim: ` (spec0004, 0.8.5)`.

---

## PARTE B — Corrigir a imprecisão do "push feito" no STATUS

**Arquivo:** `meta/STATUS.md`. A entrada da sessão 2026-07-06 afirma que os 3 commits foram empurrados e o `main` sincronizado — mas a spec0004 (`31b8350`) veio depois e provavelmente **não** foi empurrada.
**Âncora (trecho literal único):**

```
**Push feito:** os 3 commits (`e6b5aff`, `e5b318a`, `655c808`) empurrados; `main` sincronizado com `origin/main` em `655c808`. Sessões anteriores:
```

**Substituir por:**

```
**Push:** os commits da 0.8.4 (`e6b5aff`, `e5b318a`, `655c808`) foram empurrados; **depois** vieram a spec0004 (`31b8350`) e este wrap 0.8.5 — verificar `git log origin/main..HEAD` e empurrar (ver Parte E). Sessões anteriores:
```

---

## PARTE C — Descontinuar o HUB (caminho 1: parar de usar, MANTER a história, REGISTRAR o motivo)

### C1 — DECISIONS: nova DEC-029 (append ao fim do arquivo)
**Arquivo:** `meta/DECISIONS.md`. **Âncora:** fim do arquivo (após a última DEC, a `## DEC-028 — Canal de warnings...`). **Acrescentar:**

```

## DEC-029 — HUB descontinuado; coordenação entre frentes passa a ser direta (supersede DEC-020)
**Contexto.** O toolchain **KCM · ASU · FlatDrop** era coordenado por um `HUB.md` único (gerado pela conversa do KCM), que registrava contratos entre as frentes e "caixas de entrada" por frente (ver DEC-020, "modo só-HUB").
**Decisão.** Descontinuar o uso do HUB. A troca de informação entre frentes passa a ser **direta** — arquivo ou trecho colado — quando necessária. O **KCM segue sendo usado no ASU** (e projetos que usam o KCM são instruídos a usar o ASU); o **FlatDrop segue** organizando/movendo/subindo os arquivos. Sugestões para o KCM vão ao `IDEAS.md` e/ou são levadas pelo usuário.
**Motivo.** O HUB não vinha de fato sendo usado para coordenar — ficava defasado (chegou a citar a ferramenta em v0.4.0 estando ela em 0.8.x). Um documento de coordenação meio-mantido gera mais confusão do que a sua ausência, e a coordenação de 3 frentes pequenas se resolve bem na mão. Não se automatiza (nem se monitora) o que não está sendo usado.
**Consequências.** O assistente não lê mais o HUB no ritual, não monitora nem aponta "HUB defasado", e não instrui KCM/FlatDrop sobre o HUB. A história é preservada: DEC-020 (e a menção em DEC-021) permanecem como registro — esta DEC apenas as **supersede** na parte operacional. As referências operacionais ao HUB saem dos docs (ver C2–C5).
```

### C2 — DECISIONS: marcar a DEC-020 como superseded
**Arquivo:** `meta/DECISIONS.md`. **Âncora:** `## DEC-020 — ASU entra no toolchain via HUB compartilhado, em "modo só-HUB" (sem auto-aplicação do ASU sobre si)`. **Inserir uma linha logo abaixo do título:**

```
> **SUPERSEDIDA por DEC-029 (2026-07-15):** o HUB foi descontinuado; mantida aqui como registro histórico.
```

### C3 — CEREBRO: remover as referências operacionais ao HUB (4 pontos)
**Arquivo:** `meta/CEREBRO.md`.

**C3a — ritual.** Remover a linha inteira do passo do ritual que lê o HUB:
```
4. Lê `HUB.md` — sua caixa de entrada e o status relâmpago das outras frentes do grupo (ver «Projeto em grupo» abaixo). Este projeto faz parte do toolchain KCM · ASU · FlatDrop.
```
(Se os passos do ritual forem numerados, renumere os seguintes para não deixar buraco. Se o fato "faz parte do toolchain KCM·ASU·FlatDrop" for útil em outro ponto, ele já está no CONTEXT — não recriar aqui.)

**C3b — tabela de gatilhos.** Remover as duas linhas da tabela:
```
| Mudança sua que afeta outra frente do grupo (KCM/FlatDrop) | Abre um item na Caixa de entrada da frente dona, no `HUB.md`, assinado `[ASU AAAA-MM-DD]` — nunca edita os arquivos da outra frente (ver «Projeto em grupo»). |
| Contrato do HUB mudou (você subiu uma versão: schema, manifesto, diretriz) | Atualiza a tabela do Cânone do `HUB.md` e abre item nas caixas dos consumidores, no mesmo passo (D3). |
```
> Se quiser preservar o princípio "não edito arquivos de outra frente", ele está no novo texto do painel e no DEC-029; não é obrigatório manter uma linha na tabela.

**C3c — fim de sessão.** Remover o item 7 da lista "Ao final de cada sessão":
```
7. HUB.md — completo, se a sessão tocou o grupo (sua caixa processada + status relâmpago ≤3 linhas atualizado); há um só HUB (na raiz comum), então a versão nova substitui a anterior
```
(Renumere itens seguintes se houver.)

**C3d — seção dedicada.** Remover a seção INTEIRA, do título `## Projeto em grupo (HUB compartilhado)` até o fim do parágrafo que começa com `> **Particularidade deste HUB:**` (inclusive), parando antes do próximo `## `.

### C4 — CONTEXT: remover a cláusula do HUB
**Arquivo:** `meta/CONTEXT.md`. **Âncora (linha única):**
```
# Raiz do repo (modo Claude Code): CLAUDE.md (ponteiro curto p/ o Code) + .claude/ (settings.json + commands/). HUB.md do toolchain vive na pasta-raiz comum aos 3 projetos (não dentro deste repo).
```
**Substituir por (mesma linha sem a menção ao HUB):**
```
# Raiz do repo (modo Claude Code): CLAUDE.md (ponteiro curto p/ o Code) + .claude/ (settings.json + commands/).
```

### C5 — comando `/wrap`: remover o passo do HUB
**Arquivo:** `.claude/commands/wrap.md`. **Âncora (linha única):**
```
- Se a sessão tocou o grupo, atualize seu status relâmpago no `meta/HUB.md`.
```
**Remover essa linha inteira.**

> **Já feitos (não mexer):** `CLAUDE.md` (ritual sem HUB) e a seção "🔗 Grupo/Toolchain (HUB)" do `STATUS.md` já foram removidos. Se o Code encontrá-los ainda presentes, aí sim removê-los seguindo o mesmo critério; caso contrário, seguir.

---

## PARTE D — IDEAS: capturar a variante parqueada de backup

**Arquivo:** `meta/IDEAS.md`. **Âncora:** o fim do parágrafo da entrada `### 2026-06-15 — Opção de não gerar / excluir o backup depois — JÁ EXISTE (parcial) + a avaliar` (termina em `Avaliar como feature de manutenção.`). **Acrescentar ao fim desse parágrafo:**

```
 PARQUEADO (decisão 2026-07): não fazer agora. Além do `clean-backups` automático, registrou-se uma VARIANTE MANUAL: um painel/ação na GUI para LISTAR as sessões de backup por data e EXCLUIR manualmente com confirmação (mais seguro que política automática; a listagem — função pura `list_backup_sessions(backup_root)` — também destrava a "seleção de timestamps antigos no Desfazer"). Ao retomar, começar por essa metade manual antes de qualquer automação. Cuidado: excluir um backup remove a possibilidade de rollback para aquele ponto → exige confirmação.
```

---

## PARTE E — Commit e push

1. **Validação:** como esta spec toca só docs/comandos (nenhum `src/` além do bump de versão), rode ao menos `python -m pytest -q` e `python -m src self-test` para garantir que o bump não quebrou nada; `ruff`/`black --check` se quiser.
2. **Commit** (mensagem PT-BR, sem acento). Sugestão — commits separados por assunto, ou um só se preferir:
```
git add -A
git commit -m "chore: wrap 0.8.5 (botao Copiar saida, spec0004)" -m "Bump 0.8.4->0.8.5; CHANGELOG/STATUS/IDEAS/ROADMAP atualizados."
git commit -m "docs: descontinua o HUB (DEC-029, supersede DEC-020)" -m "Registra o motivo e remove as referencias operacionais em CEREBRO/CONTEXT/wrap; captura variante de backup no IDEAS."
```
   (Se `git add -A` já pegou tudo antes do 1º commit, faça os `git add` por caminho para separar os dois commits; ou entregue um commit único cobrindo ambos.)
3. **PUSH — passo crítico da transferência:** `git log origin/main..HEAD --oneline` para ver a fila (deve incluir `31b8350` da spec0004 + os commits acima) e então `git push`. O repo é o que a próxima conversa vai ler; só encerra a transferência com tudo empurrado.
4. Reportar de volta (txt) o resultado: hashes dos commits, saída do `push`, e confirmação de que `origin/main..HEAD` ficou vazio.
