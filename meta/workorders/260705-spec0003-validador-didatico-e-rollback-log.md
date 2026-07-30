# spec0003 — Mensagem do validador mais didática + rollback no history.log

> **Tipo:** FIX + DOC (sem nova arquitetura; estende DEC-014/DEC-026 e DEC-018).
> **Autoria:** chat (planejamento). **Execução:** Claude Code.
> **Âncoras são SEMÂNTICAS** — símbolo de código (nome de função) ou trecho literal único / título de seção, **nunca número de linha**. Ao aplicar: localize cada âncora EXATAMENTE; **se não achar uma, PARE e reporte** — não chute um lugar próximo. Não toque em nada fora das edições nomeadas. Rode `git diff` e confira a forma antes de commitar.
> **Versão-alvo:** 0.8.4 (no `/wrap`, feito pelo chat). Pré-condição: finalizar antes o wrap 0.8.3 pendente (`__version__` 0.8.2→0.8.3 + commit da leva DEC-028 + push). Não pule 0.8.3 — ele já tem entrada no CHANGELOG.

---

## Contexto e objetivo

Dois itens leves do "trilho auditável", num ciclo só. Nenhum é arquitetura nova:

- **Parte A (FIX):** o validador devolve o texto CRU do jsonschema (inglês, sem porquê/conserto). Enriquecer os erros de schema mais comuns — piloto: âncora vazia (`minLength`) em `location.before`/`after` do `replace_context_block`, que quase sempre significa "o bloco toca a borda do arquivo". Origem: print do usuário 07-03 (`$.files[5].modifications[0].location.after: '' should be non-empty`). Filosofia DEC-014/DEC-026 (erro acionável).
- **Parte B (FIX/feat pequeno):** o `history.log` (DEC-018) registra só APLICAÇÕES; falta registrar o ROLLBACK. Como GUI (`main_window._on_undo` → `rollback_from_dir`), CLI (`_cmd_rollback`) e self-test passam todos por `rollback_from_dir`, registrar ali cobre os três de uma vez.
- **Parte C (DOC):** nota no `INSTRUCTION_GUIDE` (§4.1 + linha na tabela §6) sobre não usar `replace_context_block` na borda do arquivo.

Escopo consciente (o que NÃO entra): a Parte B registra rollbacks MANUAIS. O rollback automático em falha (`_maybe_rollback` → `backup_mgr.restore_all()`) NÃO é registrado — e não deve ser: aquela aplicação falhou e nem sequer escreveu linha de aplicação no history (o `append_history` só roda no passo 6, após sucesso). O log fica coerente: só aplicações bem-sucedidas e rollbacks manuais.

---

## Parte A — Validador com dica acionável

**Arquivo:** `src/core/instruction_validator.py`

### Edição A1 — substituir a função `_format_error` inteira pelo par (nova `_schema_error_hint` + `_format_error` enriquecida)

**Âncora (localize e substitua este bloco EXATO — é a função `_format_error` atual, ao fim do arquivo):**

```python
def _format_error(error: ValidationError) -> str:
    """Converte um erro do jsonschema em mensagem PT-BR com o caminho do campo."""
    caminho = error.json_path  # ex.: "$.files[0].modifications[1].strategy"
    return f"{caminho}: {error.message}"
```

**Substituir por:**

```python
def _schema_error_hint(error: ValidationError) -> str | None:
    """Dica acionável (porquê + conserto) para erros de schema comuns, ou ``None``.

    Segue a filosofia de "erro acionável" (DEC-014/DEC-026): a mensagem crua do
    jsonschema diz O QUE violou, mas não COMO consertar. Hoje cobre o caso mais
    comum em instruções geradas por IA — âncora vazia (``minLength``) em
    ``location.before``/``after`` do ``replace_context_block``, que quase sempre
    significa que o bloco-alvo toca a borda do arquivo, onde essa estratégia não
    serve. Chaveia pelo VALIDADOR (``minLength``), não pelo texto da mensagem,
    para resistir a mudanças de wording entre versões do jsonschema.
    """
    campo = error.absolute_path[-1] if error.absolute_path else None
    if error.validator == "minLength" and campo in ("before", "after"):
        vizinha = "acima" if campo == "before" else "abaixo"
        return (
            f"a âncora '{campo}' está vazia. Use uma linha ASCII estável {vizinha} "
            "do bloco. Se o bloco vai até a borda do arquivo (topo/fim), "
            "'replace_context_block' não serve: prefira 'replace_line_pattern' ou "
            "'insert_before_pattern' ancorando numa linha existente, ou a "
            "estratégia própria do tipo ('replace_section' p/ Markdown, "
            "'replace_function' p/ Python)."
        )
    return None


def _format_error(error: ValidationError) -> str:
    """Converte um erro do jsonschema em mensagem PT-BR com o caminho do campo.

    Quando há dica acionável para o erro (ver :func:`_schema_error_hint`),
    acrescenta uma segunda linha indentada com o porquê + o conserto.
    """
    caminho = error.json_path  # ex.: "$.files[0].modifications[1].location.after"
    base = f"{caminho}: {error.message}"
    dica = _schema_error_hint(error)
    return f"{base}\n      Dica: {dica}" if dica else base
```

> Nota: `error.absolute_path` é um deque; `[-1]` devolve o último segmento do caminho da instância (`"after"`/`"before"`). `error.validator` é a palavra-chave do schema (`"minLength"`) — estável entre versões, ao contrário de `error.message`.

### Edição A2 — teste novo

**Arquivo:** `tests/test_instruction_parser.py`
**Âncora:** acrescente ao FIM do arquivo, após a última função de teste (`test_validator_replace_function_exige_name_no_location`).

```python
def test_validator_dica_ancora_vazia_no_context_block() -> None:
    """`after` vazio no replace_context_block → erro traz dica acionável de borda."""
    instrucao = {
        "format_version": "1.0",
        "description": "teste",
        "files": [
            {
                "id": "f1",
                "path_mode": "relative",
                "relative_path": "x.md",
                "type": "text",
                "modifications": [
                    {
                        "id": "m1",
                        "description": "bloco que vai ate o fim do arquivo",
                        "strategy": "replace_context_block",
                        "location": {"before": "## Fim", "after": ""},
                        "new_content": "novo miolo",
                    }
                ],
            }
        ],
    }
    with pytest.raises(InstructionValidationError) as info:
        validate(instrucao)
    msg = str(info.value)
    assert "after" in msg
    assert "Dica:" in msg
    assert "replace_context_block" in msg
```

---

## Parte B — Registrar o rollback no history.log

**Arquivo:** `src/core/backup_manager.py`
> `datetime` já está importado no topo (`from datetime import datetime`) — não adicione import.

### Edição B1 — nova função `_append_rollback_history` imediatamente ANTES de `def rollback_from_dir`

**Âncora:** insira o bloco abaixo na linha imediatamente anterior a `def rollback_from_dir(session_dir: Path) -> list[str]:` (fica entre o fim do `class BackupManager` e essa função).

```python
def _append_rollback_history(session_dir: Path, n_reverted: int) -> None:
    """Registra um rollback no ``history.log`` (best-effort).

    O ``history.log`` fica no diretório-PAI da sessão — o que vale para os dois
    layouts: ``backups/<ts>`` (padrão, DEC-024c) e ``<project_name>/<ts>``
    (backup externo, DEC-024b). Assim o log cronológico deixa de conter só
    aplicações (``BackupManager.append_history``) e passa a registrar também os
    rollbacks manuais (Desfazer da GUI / ``rollback`` do CLI).

    É best-effort DE PROPÓSITO: se a linha de log não puder ser escrita, o
    rollback JÁ ocorreu e não deve ser abortado por causa do log — engolimos o
    ``OSError`` em vez de estourar uma operação já concluída.
    """
    history = Path(session_dir).parent / "history.log"
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    linha = f"{now}\trollback de {Path(session_dir).name} ({n_reverted} revertido(s))\n"
    try:
        history.parent.mkdir(parents=True, exist_ok=True)
        with history.open("a", encoding="utf-8") as fh:
            fh.write(linha)
    except OSError:
        pass  # log é secundário ao rollback já concluído
```

### Edição B2 — registrar ao fim de `rollback_from_dir`

**Âncora (localize esta linha ÚNICA — é o `return` final de `rollback_from_dir`):**

```python
    return revertidos
```

**Substituir por:**

```python
    if revertidos:
        # Log cronológico: antes só continha aplicações; agora também rollbacks.
        _append_rollback_history(session_dir, len(revertidos))
    return revertidos
```

> A assinatura de `rollback_from_dir` NÃO muda. `rollback_session` delega a `rollback_from_dir`, então também passa a registrar — sem edição. Só registra quando algo foi de fato revertido (`if revertidos`), evitando linha de rollback no-op.

### Edição B3 — teste novo

**Arquivo:** `tests/test_patch_engine.py`
**Âncora:** acrescente após `test_rollback_from_dir_backup_interno` (usa os helpers já existentes no arquivo: `_instr`, `_txt_file`, `_replace_file_mod`).

```python
def test_rollback_registra_no_history(tmp_path):
    """Um rollback manual acrescenta uma linha 'rollback de <ts>' ao history.log."""
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "f.txt").write_text("antigo\n", encoding="utf-8")
    instr = _instr([_txt_file("f.txt", _replace_file_mod("novo\n"))])
    instr["description"] = "aplicacao 1"

    report = apply_instruction(instr, root_path=proj, color=False)
    session_dir = Path(report.backup_dir)
    history = session_dir.parent / "history.log"
    # Após a aplicação: 1 linha (a aplicação).
    assert history.read_text(encoding="utf-8").count("\n") == 1

    rollback_from_dir(session_dir)
    conteudo = history.read_text(encoding="utf-8")
    # Agora 2 linhas: a aplicação + o rollback.
    assert conteudo.count("\n") == 2
    assert f"rollback de {session_dir.name}" in conteudo
    assert (proj / "f.txt").read_text(encoding="utf-8") == "antigo\n"
```

---

## Parte C — Nota no guia (DOC, sem build)

**Arquivo:** `docs/INSTRUCTION_GUIDE.md`

### Edição C1 — §4.1, após a frase de fechamento

**Âncora (trecho literal único, fim do parágrafo da §4.1):**

```
`new_content` é rejeitado pela ferramenta (duplicaria as linhas).
```

**Acrescentar logo a seguir (novo parágrafo):**

```
**Não use na borda do arquivo:** se o bloco-alvo começa na 1ª linha ou termina
na última, não há linha estável para `before`/`after`, e uma âncora vazia é
rejeitada pelo schema (`location.after: '' should be non-empty`). Nesse caso
ancore numa linha existente (`insert_before_pattern`/`replace_line_pattern`) ou
use a estratégia do tipo (`replace_section` p/ Markdown, `replace_function` p/
Python).
```

### Edição C2 — nova linha na tabela §6

**Âncora (linha ÚNICA da tabela — a outra linha específica do context_block):**

```
| `o new_content inclui as âncoras` | Miolo repetiu `before`/`after` | Remova as âncoras do `new_content` (deixe só o conteúdo entre elas) |
```

**Inserir a nova linha IMEDIATAMENTE APÓS ela:**

```
| `location.before`/`after` + `non-empty`/`is too short`/`minLength` | Âncora `before`/`after` vazia (bloco toca a borda do arquivo) | Ancore numa linha existente (`insert_before_pattern`/`replace_line_pattern`) ou use `replace_section`/`replace_function`; `replace_context_block` não serve na borda |
```

---

## Ao concluir (Code)

1. **Validação (código foi tocado):** `python -m pytest` (esperado: suíte anterior + 2 testes novos, todos verdes), `ruff check .`, `black --check .`, `python -m src self-test`.
   - Regressão a vigiar: `test_history_log_accumulates` NÃO faz rollback → deve seguir com 2 linhas (não é afetado). O self-test chama `rollback_from_dir` num tempdir → passa a escrever uma linha de rollback no history do tempdir (inócuo; nada assere contagem lá).
2. **Commit** do código + testes + doc (a Parte C é só-doc, mas entra no mesmo commit por ser o mesmo ciclo lógico). Bloco pronto na resposta do chat.
3. **Deixar para o `/wrap` (chat):** versão-alvo **0.8.4** (após finalizar o 0.8.3 pendente); entrada no CHANGELOG; marcar no STATUS/IDEAS as duas ideias como concluídas (IDEAS: "Registrar rollbacks no history" dentro da entrada 2026-06-15; "Mensagem de erro do validador mais didática" 2026-07-03). **Sem DEC nova** (estende DEC-014/026 e DEC-018).
