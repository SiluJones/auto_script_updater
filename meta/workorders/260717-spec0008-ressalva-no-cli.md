# spec0008 — CLI: exibir a ressalva (🟡) no relatório, fechando a paridade com a GUI

> **Tipo:** feat pequeno (CLI). **Autoria:** chat. **Execução:** Claude Code.
> **Âncoras são SEMÂNTICAS** — símbolo/atributo ou trecho literal único, **nunca número de linha**. Localize cada âncora EXATAMENTE; **se não achar uma, PARE e reporte**. Não toque em nada fora das edições nomeadas. Rode `git diff` antes de commitar.
> **Versão-alvo:** 0.8.7 (patch — inclui o `/wrap` no fim desta spec).

---

## Contexto e objetivo

O canal de avisos não-fatais (DEC-028, 0.8.3) criou um terceiro estado — *aplicado com ressalva*. Ele aparece na **GUI** (🟡 na árvore + ⚠ na modificação + tooltip) e no **texto do "Copiar saída"** (`_report_to_text` já serializa `mr.warnings`), mas **não aparece no CLI**: o `_print_report` (`src/__main__.py`) imprime só `criado/modificado/inalterado/falha`. Resultado: quem usa `python -m src apply` **não vê** o aviso — ex.: um `create_file` sobrescrevendo um arquivo existente passa como sucesso silencioso.

Esta spec fecha a paridade. Desenho:
- **Por arquivo:** logo após o cabeçalho `=== [status] caminho ===`, imprimir cada aviso como `  ~ <texto>` (marcador ASCII `~`, o mesmo que `_report_to_text` já usa para ressalva — coerência entre as duas saídas de texto).
- **No resumo:** acrescentar `, N com ressalva` à linha de contagem, **só quando houver** ressalva (não poluir a saída no caso comum). Mais uma linha de atenção quando houver.
- **Sem cor nova e sem quebrar contrato:** o `_print_report` continua imprimindo texto puro; nada muda quando não há avisos (saída idêntica byte a byte).

Arquivos tocados: `src/__main__.py`, `tests/test_patch_engine.py`. Mais o `/wrap` (bump + meta) no fim.

---

## Edição 1 — imprimir os avisos por arquivo

**Âncora (bloco literal único, dentro de `_print_report`):**

```python
        print(f"\n=== [{rotulo}] {fr.path} ===")
        if fr.error:
            print(f"  ! {fr.error}")
```

**Substituir por:**

```python
        print(f"\n=== [{rotulo}] {fr.path} ===")
        if fr.error:
            print(f"  ! {fr.error}")
        # Ressalva (DEC-028): avisos não-fatais — a aplicação deu certo, mas há
        # algo a conferir. Marcador `~` igual ao de `_report_to_text` (GUI).
        for mr in fr.modifications:
            for aviso in mr.warnings:
                print(f"  ~ {aviso}")
```

## Edição 2 — contar as ressalvas no resumo

**Âncora (bloco literal único):**

```python
    criados = sum(1 for f in report.files if f.status == "created")
    modificados = sum(1 for f in report.files if f.status == "modified")
    inalterados = sum(1 for f in report.files if f.status == "unchanged")
    falhas = sum(1 for f in report.files if f.status == "failed")
```

**Substituir por:**

```python
    criados = sum(1 for f in report.files if f.status == "created")
    modificados = sum(1 for f in report.files if f.status == "modified")
    inalterados = sum(1 for f in report.files if f.status == "unchanged")
    falhas = sum(1 for f in report.files if f.status == "failed")
    com_ressalva = sum(1 for f in report.files if f.has_warnings)
```

## Edição 3 — acrescentar a ressalva à linha de resumo (só quando houver)

**Âncora (bloco literal único):**

```python
    print("\n" + "-" * 60)
    modo = "SIMULAÇÃO (dry-run)" if report.dry_run else "APLICAÇÃO"
    print(
        f"{modo}: {criados} criado(s), {modificados} modificado(s), "
        f"{inalterados} inalterado(s), {falhas} falha(s)."
    )
```

**Substituir por:**

```python
    print("\n" + "-" * 60)
    modo = "SIMULAÇÃO (dry-run)" if report.dry_run else "APLICAÇÃO"
    # Sufixo da ressalva só aparece quando há alguma — sem avisos, a linha de
    # resumo fica IDÊNTICA à de antes (nada muda no caso comum).
    ressalva = f", {com_ressalva} com ressalva" if com_ressalva else ""
    print(
        f"{modo}: {criados} criado(s), {modificados} modificado(s), "
        f"{inalterados} inalterado(s), {falhas} falha(s){ressalva}."
    )
    if com_ressalva:
        print("Atenção: há aviso(s) não-fatal(is) marcados com `~` acima — confira.")
```

> Nota: o `.` final da frase saiu de dentro da f-string do `falhas` e passou a
> vir depois do `{ressalva}` — confira no `git diff` que a pontuação não ficou
> duplicada.

---

## Edição 4 — teste (`tests/test_patch_engine.py`)

**Âncora (linha única — início do teste de sandbox do CLI; a edição INSERE antes, sem alterá-lo):**

```python
def test_cli_sandbox_rejects_absolute_paths(tmp_path, capsys):
```

**Substituir por:**

```python
def test_cli_print_report_mostra_ressalva(capsys):
    """DEC-028/paridade: aviso não-fatal aparece por arquivo (`~`) e no resumo."""
    from src.__main__ import _print_report
    from src.core.patch_engine import ApplyReport, FileResult, ModificationResult

    mr = ModificationResult(mod_id="m1", strategy="create_file", ok=True)
    mr.warnings.append("arquivo já existia — sobrescrito")
    fr = FileResult(file_id="f1", path="x.py", status="created", modifications=[mr])
    _print_report(ApplyReport(ok=True, dry_run=False, files=[fr]))

    out = capsys.readouterr().out
    assert "~ arquivo já existia — sobrescrito" in out  # aviso por arquivo
    assert "1 com ressalva" in out  # contagem no resumo


def test_cli_print_report_sem_ressalva_nao_polui(capsys):
    """Sem avisos, a linha de resumo NÃO ganha o sufixo de ressalva."""
    from src.__main__ import _print_report
    from src.core.patch_engine import ApplyReport, FileResult

    fr = FileResult(file_id="f1", path="x.py", status="modified")
    _print_report(ApplyReport(ok=True, dry_run=False, files=[fr]))

    out = capsys.readouterr().out
    assert "com ressalva" not in out
    assert "1 modificado(s)" in out


def test_cli_sandbox_rejects_absolute_paths(tmp_path, capsys):
```

> **Se as assinaturas não baterem:** `ModificationResult`/`FileResult` são dataclasses do `patch_engine`. **Confira os campos reais antes de rodar** (o `test_gui_smoke.py` já constrói esses objetos — use-o como referência) e ajuste os kwargs do teste; se `warnings` aceitar `warnings=[...]` no construtor, prefira passar direto em vez do `.append`. Isto é ajuste de forma dentro da edição nomeada, não conteúdo novo.

---

## /wrap 0.8.7 (executar após validar — Parte final)

### W1 — bump

`src/__init__.py`: âncora `__version__ = "0.8.6"` → `__version__ = "0.8.7"`.

### W2 — `meta/CHANGELOG.md`

Inserir nova seção IMEDIATAMENTE ACIMA de `## [0.8.6]` (e o `---` correspondente):

```markdown
## [0.8.7] — 2026-07-17
### Adicionado
- **Ressalva (🟡) visível no CLI (spec0008):** `_print_report` passa a imprimir cada aviso não-fatal por arquivo (marcador `~`, o mesmo de `_report_to_text`) e a contá-los no resumo (`N com ressalva`), com uma linha de atenção quando houver. Fecha a paridade CLI↔GUI do canal de warnings (DEC-028): antes, um `create_file` que sobrescrevia arquivo existente passava como sucesso silencioso na linha de comando. Sem avisos, a saída é idêntica à anterior.
### Testes / Qualidade
- 2 testes novos em `test_patch_engine.py` (com ressalva; sem ressalva não polui o resumo); `ruff`/`black`/`self-test` limpos. `__version__` 0.8.6 → **0.8.7**.
```

### W3 — `meta/STATUS.md` (append/edições pontuais)

- **Versão Atual** → `[0.8.7] — 2026-07-17 — Ressalva (🟡) visível também no CLI (spec0008, paridade com a GUI).`; empurrar `[0.8.6]` para a lista "Anterior".
- Atualizar a contagem de testes (**150 → 152**, ou o que o `pytest` reportar) no bullet de testes.
- No bullet do CLI (seção "✅ Funcionando"), acrescentar ao fim: `A saída do \`apply\` mostra os avisos não-fatais por arquivo (\`~\`) e conta-os no resumo (0.8.7, spec0008).`

### W4 — `meta/IDEAS.md`

Marcar a ideia capturada nesta leva como concluída — âncora (título literal único):

```markdown
### 2026-07-17 — Exibir a ressalva 🟡 também no resumo do CLI — EM ABERTO (achado nesta sessão)
```

**Substituir por:**

```markdown
### 2026-07-17 — Exibir a ressalva 🟡 também no resumo do CLI — CONCLUÍDA (spec0008, 0.8.7)
```

> Se a spec0007 ainda NÃO tiver sido aplicada, esta âncora não existirá: nesse caso **PULE o W4 e reporte** — o item será marcado quando a spec0007 entrar. Não crie a seção só para marcá-la concluída.

### W5 — `meta/DECISIONS.md`

Nenhuma DEC nova: esta spec **estende a DEC-028** (canal de warnings), não decide nada novo. Não editar.

---

## Validação (antes de commitar)

- `python -m pytest` (suíte verde; 2 testes novos).
- `ruff check .` e `black --check .` limpos.
- `python -m src self-test` OK.
- **Conferência manual da saída real** (é o ponto da spec): rodar a demo DUAS vezes seguidas na mesma raiz — a segunda faz o `create_file` sobrescrever e deve exibir o `~` e o `N com ressalva`:
  ```
  python -m src apply examples\demo.yaml --root examples\demo_project -y
  python -m src apply examples\demo.yaml --root examples\demo_project -y
  ```
  Depois reverta com o `rollback` do timestamp impresso e confirme que `examples\demo_project\src\health.py` não ficou sujo (FIX-009 — o arquivo é gerado pela demo e está no `.gitignore`).
- `git diff`: só `src/__main__.py`, `tests/test_patch_engine.py`, `src/__init__.py` e os meta-docs (CHANGELOG/STATUS/IDEAS).

## Commit + push (Claude Code)

```
git add src\__main__.py tests\test_patch_engine.py src\__init__.py && git commit -m "feat: exibe ressalva nao-fatal no relatorio do CLI" -m "Avisos por arquivo com marcador ~ e contagem no resumo; paridade com a GUI (DEC-028). Sem avisos, saida inalterada. 2 testes novos. Bump 0.8.7."
```

```
git add meta\CHANGELOG.md meta\STATUS.md meta\IDEAS.md && git commit -m "docs: wrap 0.8.7 (ressalva no CLI)"
```

```
git log origin/main..HEAD --oneline && git push
```
