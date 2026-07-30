# SPEC — Origem do backup: qual instrução gerou esta sessão

> Primeira **spec de feature** do repo (modelo em `meta/SPEC.md`, DEC-033).
> Origem: nota do usuário de 2026-07-23, capturada no `meta/IDEAS.md` em 07-30.
> **Status:** proposta — aguarda o aval do usuário no ponto de decisão da §Decisões.
> Alvo: `src/core/backup_manager.py` + `src/core/patch_engine.py` + os dois chamadores (CLI e GUI).

## Problema

O backup identifica **quando** aconteceu (`timestamp`) e **o que** tocou (`manifest.txt`), mas não **de onde veio**. Com vários `.yaml` circulando pelo mesmo projeto — que é o modo de uso real: uma instrução por leva, guardada fora da raiz —, escolher o timestamp certo para desfazer vira adivinhação por horário.

Hoje o `history.log` grava `<timestamp>\t<n modificados, n criados>  <description>`, onde `description` é o campo da instrução. Isso ajuda, mas o campo é livre e frequentemente genérico ("Ajustes no módulo de auth"); duas levas do mesmo dia podem ter a mesma descrição. **O que falta é o nome do arquivo de instrução**, que é o identificador que o usuário reconhece — é o arquivo que ele tem aberto ao lado.

Sem isso, o custo aparece no pior momento: na hora de reverter, sob pressão, escolhendo entre timestamps parecidos.

## Critérios de aceite (verificáveis)

- [ ] Após um `apply` a partir do arquivo `260730-asu0001.yaml`, o `manifest.txt` da sessão contém uma linha de cabeçalho `# Instrução: 260730-asu0001.yaml`, **antes** da linha em branco que separa o cabeçalho das entradas.
- [ ] A linha correspondente no `history.log` contém o mesmo nome de arquivo, em posição fixa, **sem perder** o resumo (`N modificado(s), N criado(s)`) nem a `description` que já aparecia.
- [ ] `rollback_from_dir` e `rollback_session` continuam funcionando sobre um manifesto **novo** (com o cabeçalho) — nenhuma mudança no parser é necessária, porque ele já ignora linhas iniciadas por `#`. Há teste que prova isso.
- [ ] `rollback_from_dir` continua funcionando sobre um manifesto **antigo** (sem o cabeçalho), tanto no formato tab quanto no formato legado `[modificado] caminho`. Regressão coberta por teste.
- [ ] Aplicação vinda de **"Colar instrução"** (GUI, sem arquivo em disco) grava `# Instrução: (colado da área de transferência)` — nunca um campo vazio, nunca um caminho inventado.
- [ ] O nome gravado é o **nome do arquivo** (basename), não o caminho completo: o caminho absoluto vaza estrutura de pastas do usuário para um arquivo que ele pode compartilhar ao pedir ajuda.
- [ ] `python -m src apply ... --no-backup` continua sem criar nada — a feature não introduz escrita quando o backup está desligado.
- [ ] `python -m src self-test` verde; `python -m pytest` verde; `ruff check .` e `black --check .` limpos.
- [ ] **Conferência manual (a suíte não cobre):** aplicar duas instruções diferentes no mesmo projeto e confirmar, abrindo o `history.log`, que dá para dizer qual timestamp veio de qual arquivo sem abrir as pastas.

## Decisões de design

**1. Cabeçalho, não coluna.** A origem é um dado **da sessão**, não de cada arquivo. Colocá-la como 4ª coluna no `manifest.txt` repetiria o mesmo valor em toda linha e mexeria no formato tab que o rollback consome. Como cabeçalho `#`, o parser existente já a ignora — **compatibilidade sai de graça, sem fallback**. (Foi o que a leitura da fonte mostrou: `write_manifest` já emite `# Backup de <ts>` e o laço de `rollback_from_dir` já faz `if line.startswith("#"): continue`.)

**2. Nome do arquivo, e não só a `description`.** A `description` continua onde está; a origem é informação diferente e complementar. Quem escolhe um timestamp reconhece o nome do arquivo que gerou a leva mais depressa do que uma frase.

**3. Plumbing mínimo.** `BackupManager` ganha um campo opcional `instruction_label: str | None = None`; `write_manifest` emite o cabeçalho quando ele existe e `append_history` o inclui na linha. Quem sabe o nome do arquivo é o chamador, não o engine — então o rótulo desce pela mesma chamada que hoje monta o `BackupManager` em `patch_engine.py` (linha ~275) e é preenchido pelo CLI (`Path(instruction_path).name`) e pela GUI (nome do arquivo escolhido, ou o marcador de colagem).

**4. Ausência é um valor, não um branco.** Sem rótulo (chamada programática, teste antigo), o cabeçalho simplesmente **não é escrito** — nada de `# Instrução: ` vazio, que confundiria mais do que ajudaria.

> **Ponto de decisão (uma pergunta):** no `history.log`, a linha passa a ser
> `<timestamp>\t<resumo>\t<arquivo>  <description>` — o nome do arquivo entra num **terceiro campo tab**, antes da descrição. A alternativa era colar o nome dentro da descrição (`<resumo>  [arquivo] descrição`), que não muda o número de campos mas mistura dois dados num só. Recomendo o terceiro campo: o `history.log` é lido por humano, mas um dia pode virar entrada de uma tela de "seleção de timestamps antigos no Desfazer" (item aberto da F2), e aí campo separado se paga.

## Fora de escopo

- **Não** registrar o conteúdo nem o hash da instrução — só o nome. Guardar o YAML inteiro é outra feature (e outra decisão sobre tamanho de backup).
- **Não** mexer no formato das linhas de arquivo do `manifest.txt`. O parser fica intocado.
- **Não** criar tela nem comando para consultar a origem. A leitura é abrir o arquivo, como hoje.
- **Não** retroagir: sessões de backup já existentes seguem sem a informação, e isso não é erro.
- **Não** tocar no `_append_rollback_history` (a linha de rollback manual, spec0003) — a origem é da aplicação, não da reversão.

## Passos

1. `BackupManager`: campo `instruction_label`, emissão no `write_manifest`, inclusão no `append_history`. Docstrings explicando **por que** é cabeçalho e não coluna.
2. Testes do núcleo: cabeçalho presente/ausente; rollback sobre manifesto novo; regressão de rollback sobre manifesto antigo (tab e legado).
3. `patch_engine`: repassar o rótulo recebido até o `BackupManager`.
4. CLI (`src/__main__.py`): passar `Path(instruction_path).name`.
5. GUI (`main_window.py`): passar o nome do arquivo escolhido; no fluxo "Colar instrução", o marcador de colagem. Teste de smoke para os dois caminhos.
6. Bump `0.9.2 → 0.9.3`, entrada no CHANGELOG, linha no STATUS. Sem DEC nova — é aplicação de decisão existente (DEC-018 consolidou o `history.log`; esta spec só acrescenta um campo).
