# SPEC — 260703-spec0002 · Indicador 🟡 "aplicado com ressalva" na GUI

> **Tipo:** FEATURE (código + testes). **Autoria:** chat. **Execução:** Claude Code.
> **Arquivos:** `src/gui/main_window.py`, `tests/test_gui_smoke.py`.
> **DEPENDE de `260703-spec0001`** (canal de warnings no engine) — precisa de `FileResult.has_warnings`, `ApplyReport.has_warnings` e `ModificationResult.warnings`. **NÃO aplicar antes da 0001.** Se esses símbolos não existirem no `patch_engine`, PARE e reporte.
> **Âncoras** são trechos/métodos do código; `grep`-os antes de editar.

## Objetivo

Hoje a árvore da GUI mostra, por arquivo, 🔴 (falha) / 🟢 (mudança aplicável) / ⚪ (sem alteração), e por modificação ✓ / ✗. Com o canal de warnings (spec 0001), existe um quarto estado: **aplicou, mas com ressalva não-fatal**. Esta spec faz esse estado aparecer como 🟡, no arquivo e na modificação, com o texto do aviso acessível (tooltip), **sem** bloquear o botão Aplicar (warning não é erro).

## Regras de exibição

- **Por arquivo:** o ícone vira 🟡 quando o arquivo aplicaria uma mudança (status `created`/`modified`) **e** `fr.has_warnings` é verdadeiro. Precedência: 🔴 (failed) > 🟡 (com ressalva) > 🟢 (aplicável limpo) > ⚪ (unchanged). Falha sempre vence ressalva.
- **Por modificação:** hoje é ✓ / ✗. Passa a ✓ / ⚠ / ✗ — ⚠ quando `mr.ok and mr.warnings`. (Erro continua ✗.)
- **Tooltip:** no arquivo com ressalva, o tooltip lista os avisos (além do `fr.error`, se houver). Na modificação com ressalva, o tooltip mostra os avisos daquela modificação.
- **Botão Aplicar:** permanece HABILITADO com warnings (só `report.ok` o governa, e warning não muda `report.ok`). NÃO desabilitar por causa de ressalva.
- **Barra de status:** o resumo pode indicar a presença de ressalvas (ex.: "… (com N ressalva(s))"), sem alarmar.

## Edição 1 — ícone do arquivo na árvore

**Arquivo:** `src/gui/main_window.py`
**Âncora:** em `_populate_tree`, a linha
`icone = "🔴" if fr.status == "failed" else ("⚪" if fr.status == "unchanged" else "🟢")`.
**Ação:** substituir por uma escolha com o 🟡 no meio da precedência:

```python
            # 🔴 falha > 🟡 aplicável com ressalva > 🟢 aplicável limpo > ⚪ sem alteração.
            if fr.status == "failed":
                icone = "🔴"
            elif fr.status == "unchanged":
                icone = "⚪"
            elif fr.has_warnings:
                icone = "🟡"
            else:
                icone = "🟢"
```

## Edição 2 — tooltip do arquivo inclui os avisos

**Arquivo:** `src/gui/main_window.py`
**Âncora:** logo após `item.setData(0, Qt.ItemDataRole.UserRole, fr)`, o bloco
`if fr.error: item.setToolTip(0, fr.error)`.
**Ação:** estender para agregar avisos:

```python
            tips = []
            if fr.error:
                tips.append(fr.error)
            for mr in fr.modifications:
                for w in mr.warnings:
                    tips.append(f"⚠ {mr.mod_id}: {w}")
            if tips:
                item.setToolTip(0, "\n".join(tips))
```

> Isto SUBSTITUI o `if fr.error: item.setToolTip(0, fr.error)` existente (não
> deixar os dois, para não sobrescrever o tooltip).

## Edição 3 — ícone e tooltip da modificação

**Arquivo:** `src/gui/main_window.py`
**Âncora:** no laço `for mr in fr.modifications:`, as linhas
`micone = "✓" if mr.ok else "✗"` e o `QTreeWidgetItem([... "" if mr.ok else "erro"])`
e `if mr.error: filho.setToolTip(0, mr.error)`.
**Ação:** introduzir o estado ⚠ e ajustar rótulo/tooltip:

```python
                if not mr.ok:
                    micone, rotulo = "✗", "erro"
                elif mr.warnings:
                    micone, rotulo = "⚠", "ressalva"
                else:
                    micone, rotulo = "✓", ""
                filho = QTreeWidgetItem(
                    [f"   {micone} {mr.mod_id} ({mr.strategy})", rotulo]
                )
                tip = mr.error or ("\n".join(mr.warnings) if mr.warnings else "")
                if tip:
                    filho.setToolTip(0, tip)
```

> Substitui o trio de linhas antigo (micone / QTreeWidgetItem / setToolTip) por
> este bloco. Confira que `filho.setData(...)` e `item.addChild(filho)` logo
> abaixo permanecem.

## Edição 4 — resumo da barra de status (opcional, recomendado)

**Arquivo:** `src/gui/main_window.py`
**Âncora:** o método `_resumo` (usado em `_preview`/`_apply` para compor a mensagem da barra). `grep "_resumo"`.
**Ação:** acrescentar, ao final do texto do resumo, um sufixo quando `report.has_warnings`:

```python
        if report.has_warnings:
            n = sum(len(m.warnings) for f in report.files for m in f.modifications)
            resumo = f"{resumo} (com {n} ressalva(s))"
```

> Adaptar ao formato real de `_resumo` (a variável pode ter outro nome). Se
> `_resumo` retorna string, concatenar antes do `return`. Não alarmar — é
> informativo.

## Edição 5 — comentário de topo do arquivo

**Arquivo:** `src/gui/main_window.py`
**Âncora:** o comentário do cabeçalho que hoje diz
`(🟢 ok / 🔴 falha — o 🟡 chegará com o canal de warnings, ver IDEAS)`.
**Ação:** atualizar para refletir que o 🟡 chegou:

```
(🟢 aplicável / 🟡 aplicável com ressalva / 🔴 falha / ⚪ sem alteração)
```

## Testes

**Arquivo:** `tests/test_gui_smoke.py` (seguir o estilo de smoke test já existente; se a suíte de GUI usa `pytest-qt`/`QApplication` headless, reusar o fixture).

- `test_tree_mostra_amarelo_com_ressalva` — montar um `ApplyReport` (ou rodar o engine com a instrução-piloto da spec 0001) em que um arquivo tem `status="modified"` e `has_warnings True`; após `_populate_tree`, o item de topo começa com "🟡".
- `test_tree_falha_vence_ressalva` — arquivo `failed` com warnings → ícone 🔴 (precedência).
- `test_modificacao_ressalva_mostra_warn` — modificação `ok=True` com `warnings` → filho começa com "⚠" e rótulo "ressalva".
- `test_aplicar_habilitado_com_ressalva` — `report.ok True` + `has_warnings True` → `btn_apply` habilitado (warning não bloqueia).

> Se o ambiente de teste não tem display, usar `QApplication` offscreen
> (`QT_QPA_PLATFORM=offscreen`) como o smoke test atual já deve fazer. Se a GUI
> não for testável no CI, marcar com o mesmo skip/condição dos testes de GUI
> existentes — não inventar um novo mecanismo.

## O que NÃO fazer

- NÃO desabilitar Aplicar por causa de warning.
- NÃO transformar ressalva em erro nem em bloqueio.
- NÃO reintroduzir o `if fr.error:` antigo junto do novo (evitar tooltip duplicado).
- NÃO mexer no engine (é a spec 0001).

## Ao concluir (Claude Code)

1. `python -m pytest`, `ruff check .`, `black --check .`.
2. `git diff` — só `src/gui/main_window.py` e `tests/test_gui_smoke.py`.
3. Commit (mensagem sem acento):

```
feat(gui): indicador amarelo para modificacao aplicada com ressalva
```

> Fecha incremento de PRODUTO → bump/CHANGELOG via `/wrap`. Pode entrar na mesma
> versão da spec 0001 se aplicadas juntas, ou numa subsequente. Sugerir nota na
> DEC do canal de warnings (0001) de que a GUI passou a exibir 🟡. **Vale um print
> do README** (a árvore com 🟡) quando a GUI estabilizar — sinalizar, sem gerar a imagem.
