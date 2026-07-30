# WO 0015 — gravar a origem do backup (qual instrucao gerou a sessao)

> **Tipo:** CODIGO (+ fecho da spec e registro).
> **Config sugerida:** Opus, `/effort` alto. Toca `backup_manager.py`, que e peca critica, e o criterio de aceite inclui regressao de rollback sobre manifesto antigo.
> **Pre-requisito:** 0.9.2, commit `6b815c9` ou posterior (README/GUIA/spec ja commitados), 158 testes verdes, arvore limpa.
> **Base:** `meta/specs/260730-origem-do-backup.md` (spec de feature) + decisao do usuario em 2026-07-30 (terceiro campo tab). Origem: nota do usuario de 2026-07-23.
> **Ancora semantica:** se um trecho-ancora nao bater EXATAMENTE, **PARE e reporte**.
> **Idempotencia:** antes de cada insercao, procure a frase-chave do texto NOVO (ex.: `instruction_label`). Se ja existir, **PULE** e diga no relatorio.

> **Canal dos meta neste ciclo = CODE.** Faca os appends previstos nas Edicoes 9-11. O chat nao entrega STATUS/CHANGELOG nesta rodada.

> **Sobre o texto das EDICOES 1-8:** o codigo vem literal porque os diffs sao pequenos e as linhas vizinhas foram lidas na fonte. Os TESTES (Edicao 9) vem descritos por comportamento, nao por texto exato — escrever teste e sua raia, e voce enxerga as fixtures.

---

## 1. Por que

O backup diz **quando** (timestamp) e **o que** (manifesto), mas nao **de onde veio**. Com varias instrucoes circulando pelo mesmo projeto — que e o uso real —, escolher o timestamp certo para desfazer vira adivinhacao por horario, justamente sob pressao.

O `history.log` ja grava a `description` da instrucao, mas ela e livre e costuma se repetir entre levas do mesmo dia. O identificador que o usuario reconhece e **o nome do arquivo** que ele tem aberto ao lado.

## 2. Contexto factual (lido na fonte, nao de memoria)

- `BackupManager.write_manifest` ja emite `# Backup de <ts>` como primeira linha, seguida de uma linha em branco.
- `rollback_from_dir` ja faz `if not line.strip() or line.startswith("#"): continue`. **Portanto o cabecalho novo e ignorado pelo parser sem nenhuma mudanca** — nao ha fallback a escrever.
- `append_history` monta `f"{self.timestamp}\t{resumo}{desc}\n"`, com `desc = f"  {description}"`.
- Quem constroi o `BackupManager` e `patch_engine.apply_instruction`; quem conhece o nome do arquivo e o chamador (CLI e GUI). Logo, o rotulo desce por parametro.
- A GUI ja distingue colagem de arquivo por `self._pasted_text is not None and self.instr_edit.text() == self.PASTED_MARK`.

---

## Edicao 1 — `src/core/backup_manager.py` · campo novo no dataclass

**Ancora:**

```
    backup_root: Path
    root: Path | None = None
    project_name: str | None = None
```

**Substituir por:**

```
    backup_root: Path
    root: Path | None = None
    project_name: str | None = None
    instruction_label: str | None = None
```

## Edicao 2 — `src/core/backup_manager.py` · documentar o campo

**Ancora** (dentro do docstring da classe):

```
        project_name: quando fornecido (backup externo), substitui ``backups/``
            como agrupador: sessão fica em ``<backup_root>/<project_name>/<ts>``
            e ``history.log`` em ``<backup_root>/<project_name>/``.
    """
```

**Substituir por:**

```
        project_name: quando fornecido (backup externo), substitui ``backups/``
            como agrupador: sessão fica em ``<backup_root>/<project_name>/<ts>``
            e ``history.log`` em ``<backup_root>/<project_name>/``.
        instruction_label: nome do arquivo de instrução que originou a sessão
            (ou marcador de colagem). Só rótulo para leitura humana — quem o
            conhece é o chamador (CLI/GUI), não o engine. ``None`` = origem
            desconhecida (chamada programática, teste), e nesse caso o cabeçalho
            do manifesto simplesmente não é escrito.
    """
```

## Edicao 3 — `src/core/backup_manager.py` · cabecalho no manifesto

**Ancora:**

```
        Formato por linha: ``[estado]<TAB>caminho_original<TAB>caminho_espelho``
        (o espelho fica vazio para arquivos criados). Gravar o espelho explícito
        torna o rollback independente de qualquer heurística de caminho.
        """
        self.session_dir.mkdir(parents=True, exist_ok=True)
        manifest = self.session_dir / "manifest.txt"
        linhas = [f"# Backup de {self.timestamp}", ""]
```

**Substituir por:**

```
        Formato por linha: ``[estado]<TAB>caminho_original<TAB>caminho_espelho``
        (o espelho fica vazio para arquivos criados). Gravar o espelho explícito
        torna o rollback independente de qualquer heurística de caminho.

        A origem (qual instrução gerou a sessão) entra como linha de CABEÇALHO,
        não como quarta coluna: é um dado da SESSÃO, não de cada arquivo — como
        coluna se repetiria em toda linha e mexeria no formato que o rollback
        consome. Como comentário, o parser existente já a ignora, então a
        compatibilidade sai de graça (ver ``rollback_from_dir``).
        """
        self.session_dir.mkdir(parents=True, exist_ok=True)
        manifest = self.session_dir / "manifest.txt"
        linhas = [f"# Backup de {self.timestamp}"]
        if self.instruction_label:
            linhas.append(f"# Instrução: {self.instruction_label}")
        linhas.append("")
```

## Edicao 4 — `src/core/backup_manager.py` · terceiro campo no history.log

**Ancora:**

```
        complementar ao manifesto por sessão (que continua sendo a fonte para o
        rollback) — aqui é só leitura humana cronológica.
        """
```

**Substituir por:**

```
        complementar ao manifesto por sessão (que continua sendo a fonte para o
        rollback) — aqui é só leitura humana cronológica.

        A origem entra como TERCEIRO campo tab, antes da descrição, e é escrita
        SEMPRE (vazia quando desconhecida) para que a posição da coluna seja
        estável: o log é lido por humano hoje, mas é o candidato natural a
        alimentar a futura tela de "seleção de timestamps antigos no Desfazer",
        e aí campo em posição fixa se paga.
        """
```

## Edicao 5 — `src/core/backup_manager.py` · montagem da linha

**Ancora:**

```
        desc = f"  {description}" if description else ""
        linha = f"{self.timestamp}\t{resumo}{desc}\n"
```

**Substituir por:**

```
        desc = f"  {description}" if description else ""
        origem = self.instruction_label or ""
        linha = f"{self.timestamp}\t{resumo}\t{origem}{desc}\n"
```

## Edicao 6 — `src/core/patch_engine.py` · parametro novo em apply_instruction

**Ancora:**

```
    stop_on_error: bool | None = None,
    color: bool = True,
) -> ApplyReport:
```

**Substituir por:**

```
    stop_on_error: bool | None = None,
    color: bool = True,
    instruction_label: str | None = None,
) -> ApplyReport:
```

> Acrescente tambem, no docstring de `apply_instruction`, junto dos demais parametros: `instruction_label: nome do arquivo de instrução (ou marcador de colagem), gravado no backup para identificar a origem da sessão. Só rótulo.`

## Edicao 7 — `src/core/patch_engine.py` · repassar ao BackupManager

**Ancora:**

```
        BackupManager(backup_root, root=project_root, project_name=project_name)
```

**Substituir por:**

```
        BackupManager(
            backup_root,
            root=project_root,
            project_name=project_name,
            instruction_label=instruction_label,
        )
```

## Edicao 8a — `src/__main__.py` · CLI passa o nome do arquivo

**Ancora** (a chamada REAL de aplicacao; **nao** a da previa, que e dry-run e nao escreve manifesto):

```
    report = apply_instruction(
        instruction,
        root_path=args.root,
        dry_run=args.dry_run,
        backup=False if args.no_backup else None,
        backup_location=getattr(args, "backup_dir", None),
        color=color,
    )
```

**Substituir por:**

```
    report = apply_instruction(
        instruction,
        root_path=args.root,
        dry_run=args.dry_run,
        backup=False if args.no_backup else None,
        backup_location=getattr(args, "backup_dir", None),
        color=color,
        instruction_label=Path(args.instruction).name,
    )
```

> Confira que `Path` ja esta importado em `src/__main__.py` (esta — `_make_sandbox` usa). Se nao estiver, PARE e reporte.

## Edicao 8b — `src/gui/main_window.py` · helper de rotulo

**Ancora:**

```
    def _run(self, *, dry: bool, backup_location: str | Path | None = None) -> ApplyReport | None:
```

**Inserir IMEDIATAMENTE ANTES** da linha da ancora:

```
    def _instruction_label(self) -> str:
        """Origem da instrução, para o backup registrar de onde a sessão veio.

        Nome do ARQUIVO (basename), não o caminho: o manifesto pode ser
        compartilhado ao pedir ajuda, e o caminho absoluto vazaria a estrutura
        de pastas do usuário. Colagem não tem arquivo — vira marcador explícito,
        nunca campo vazio.
        """
        if self._pasted_text is not None and self.instr_edit.text() == self.PASTED_MARK:
            return "(colado da área de transferência)"
        return Path(self.instr_edit.text().strip()).name

```

## Edicao 8c — `src/gui/main_window.py` · passar o rotulo no fluxo normal

**Ancora:**

```
        return apply_instruction(
            instruction,
            root_path=root,
            dry_run=dry,
            backup_location=backup_location,
            color=False,
        )
```

**Substituir por:**

```
        return apply_instruction(
            instruction,
            root_path=root,
            dry_run=dry,
            backup_location=backup_location,
            color=False,
            instruction_label=self._instruction_label(),
        )
```

## Edicao 8d — `src/gui/main_window.py` · passar o rotulo no fluxo de sandbox

**Ancora:**

```
            report = apply_instruction(
                instruction, root_path=root_usada, dry_run=False, color=False
            )
```

**Substituir por:**

```
            report = apply_instruction(
                instruction,
                root_path=root_usada,
                dry_run=False,
                color=False,
                instruction_label=self._instruction_label(),
            )
```

## Edicao 9 — testes (descritos por comportamento; o texto e seu)

Em `tests/test_patch_engine.py` (ou onde os testes de backup ja vivem — siga o vizinho):

1. **Cabecalho presente:** aplicar com `instruction_label="260730-asu0001.yaml"` e afirmar que o `manifest.txt` contem a linha `# Instrução: 260730-asu0001.yaml` **antes** da primeira linha de entrada.
2. **Cabecalho ausente:** aplicar sem rotulo e afirmar que **nenhuma** linha comeca por `# Instrução:` — nada de cabecalho vazio.
3. **Rollback sobre manifesto NOVO:** aplicar com rotulo, rodar `rollback_from_dir` na sessao e afirmar que os arquivos voltaram. Este e o teste que prova que o cabecalho novo nao confunde o parser.
4. **Regressao — manifesto ANTIGO:** montar a mao um `manifest.txt` sem cabecalho de instrucao (formato tab) e outro no formato legado `[modificado] caminho`, e afirmar que `rollback_from_dir` continua restaurando os dois. Se ja houver teste equivalente, **nao duplique** — diga no relatorio qual cobre.
5. **`history.log` com tres campos:** afirmar que a linha tem `timestamp`, resumo, o rotulo no **terceiro** campo tab, e a `description` depois; e que, sem rotulo, o terceiro campo existe **vazio** (a linha tem o mesmo numero de tabs).

Em `tests/test_gui_smoke.py`:

6. **Rotulo por arquivo:** com um caminho de instrucao no campo, `_instruction_label()` devolve so o basename.
7. **Rotulo por colagem:** apos o fluxo de colar, devolve `(colado da área de transferência)`.

## Edicao 10 — `src/__init__.py` · bump

**Ancora:**

```
__version__ = "0.9.2"
```

**Substituir por:**

```
__version__ = "0.9.3"
```

## Edicao 11a — `meta/CHANGELOG.md` · nova versao

> **ATENCAO: arquivo em CRLF.** Preserve o fim de linha.

**Ancora:**

```
## [Não lançado]
```

**Inserir IMEDIATAMENTE APOS** a linha da ancora (a entrada de [Não lançado] que ja existe continua abaixo):

```

## [0.9.3] — 2026-07-30
### Adicionado
- **O backup agora registra de ONDE veio.** O `manifest.txt` da sessão ganha uma linha de cabeçalho `# Instrução: <arquivo>` e o `history.log` passa a trazer o nome do arquivo de instrução num terceiro campo, antes da descrição. Com várias instruções circulando pelo mesmo projeto, dá para escolher o timestamp certo no Desfazer sem abrir cada pasta. Aplicação vinda de **Colar instrução** grava `(colado da área de transferência)` — nunca campo vazio. Só o nome do arquivo é gravado (nunca o caminho completo, que vazaria a estrutura de pastas ao compartilhar o manifesto). **Nenhuma mudança de formato:** a origem é cabeçalho, não coluna, e o parser do rollback já ignorava linhas `#` — manifestos antigos (tab e legado `[modificado]`) continuam restauráveis, com teste de regressão. Spec: `meta/specs/260730-origem-do-backup.md` (wo0015).
```

## Edicao 11b — `meta/STATUS.md` · versao atual

**Ancora** (a linha da secao «Versão Atual» que cita a 0.9.2 — se o texto exato divergir, PARE e reporte em vez de adivinhar):

```
## Versão Atual
```

**Inserir IMEDIATAMENTE APOS** a linha da ancora:

```
> **0.9.3 (2026-07-30)** — o backup registra a instrução de origem (`# Instrução:` no `manifest.txt`, terceiro campo no `history.log`). Sem mudança de formato; rollback de manifestos antigos coberto por regressão. Primeira feature entregue a partir de uma **spec de feature** (`meta/specs/260730-origem-do-backup.md`).
```

## Edicao 12 — `meta/specs/260730-origem-do-backup.md` · fechar a spec

**Ancora:**

```
> **Status:** proposta — aguarda o aval do usuário no ponto de decisão da §Decisões.
```

**Substituir por:**

```
> **Status:** aceita e implementada em 2026-07-30 (wo0015, versão 0.9.3). Ponto de decisão resolvido pelo usuário: terceiro campo tab no `history.log`.
```

**Ancora 2** (o bloco de decisao aberta, inteiro):

```
> **Ponto de decisão (uma pergunta):** no `history.log`, a linha passa a ser
> `<timestamp>\t<resumo>\t<arquivo>  <description>` — o nome do arquivo entra num **terceiro campo tab**, antes da descrição. A alternativa era colar o nome dentro da descrição (`<resumo>  [arquivo] descrição`), que não muda o número de campos mas mistura dois dados num só. Recomendo o terceiro campo: o `history.log` é lido por humano, mas um dia pode virar entrada de uma tela de "seleção de timestamps antigos no Desfazer" (item aberto da F2), e aí campo separado se paga.
```

**Substituir por:**

```
> **Decidido (usuário, 2026-07-30):** terceiro campo tab. A linha passa a ser
> `<timestamp>\t<resumo>\t<arquivo>  <description>`. O campo é escrito **sempre**, vazio quando a origem é desconhecida, para que a posição da coluna seja estável — o `history.log` é lido por humano hoje, mas é o candidato natural a alimentar a tela de "seleção de timestamps antigos no Desfazer" (item aberto da F2). A alternativa descartada era colar o nome dentro da descrição, que não muda o número de campos mas mistura dois dados num só.
```

---

## Fora de escopo

- **Nao** registrar conteudo nem hash da instrucao — so o nome.
- **Nao** mexer no formato das linhas de arquivo do `manifest.txt`. O parser fica intocado.
- **Nao** criar tela nem comando para consultar a origem.
- **Nao** retroagir: sessoes antigas seguem sem a informacao, e isso nao e erro.
- **Nao** tocar em `_append_rollback_history` — a origem e da aplicacao, nao da reversao.
- **Nao** passar rotulo na chamada de previa (dry-run) nem no `self-test`: dry-run nao escreve manifesto, e o self-test nao tem arquivo de origem do usuario.
- **Nao** commitar o `INSTRUCOES-DO-PROJETO.md` da raiz junto — decisao separada (ver relatorio da wo0014).

## Armadilhas desta WO

- **A ancora da Edicao 8a e a chamada REAL**, nao a da previa. As duas sao parecidas: a da previa tem `dry_run=True` e nao tem `backup_location`. Se casar na errada, o rotulo nunca chega ao manifesto.
- **`meta/CHANGELOG.md` esta em CRLF**; os demais `meta/` em LF.
- **A Edicao 12 mexe num arquivo dentro de `meta/specs/`**, que **nao** esta no `.flatdropignore` (so `meta/workorders/*` esta). O arquivo existe e sobe ao mount — confira que voce esta editando o do repo.
- **Ordem:** faca as Edicoes 1-8 e rode a suite ANTES das 9-12. Se um teste de backup ja existente quebrar, o motivo mais provavel e o terceiro campo tab — e ai a pergunta e se o teste afirmava o numero de campos. Reporte antes de "consertar" o teste.

---

## Depois de aplicar — conferencia antes do commit

- [ ] `python -m pytest` verde (158 + os novos), `python -m src self-test` OK, `ruff check .` e `black --check .` limpos.
- [ ] `git diff` mostra exatamente: `backup_manager.py`, `patch_engine.py`, `__main__.py`, `main_window.py`, os arquivos de teste, `src/__init__.py`, `meta/CHANGELOG.md`, `meta/STATUS.md`, `meta/specs/260730-origem-do-backup.md`. Nada alem.
- [ ] **Conferencia manual (a suite nao cobre):** aplicar duas instrucoes diferentes no mesmo projeto e abrir o `history.log` — tem de dar para dizer qual timestamp veio de qual arquivo sem abrir as pastas. Depois abrir um `manifest.txt` gerado e conferir o cabecalho.
- [ ] **Vale print para o README:** a linha do `history.log` com duas levas de instrucoes diferentes. Nao gere a imagem; so aponte o momento de capturar.

## Relatorio de aplicacao *(quem aplica preenche)*

O que foi feito · o que fugiu do texto literal da WO · arquivos tocados · resultado da validacao · o commit.

## Commit — blocos separados, mensagem SEM acento

```
git add -A
```

```
git commit -m "feat(backup): registra a instrucao de origem no manifesto e no history" -m "O manifest.txt ganha a linha de cabecalho '# Instrucao: <arquivo>' e o history.log passa a trazer o nome do arquivo num terceiro campo tab, antes da descricao. Origem e dado da sessao, entao entra como cabecalho e nao como coluna: o parser do rollback ja ignorava linhas '#', logo nao ha mudanca de formato nem fallback. Colagem grava marcador explicito. Regressao de rollback sobre manifesto antigo coberta por teste. Versao 0.9.3. Spec: meta/specs/260730-origem-do-backup.md."
```

```
git push
```
