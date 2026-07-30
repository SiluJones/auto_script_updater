# CHANGELOG

> Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/) e versionamento [SemVer](https://semver.org/lang/pt-BR/).
> **Cresce**: entradas novas no topo. Registra só o que foi de fato concluído/entregue.

## [Não lançado]
### Alterado
- **Vocabulário WO × spec e migração das skills (3ª atualização do KCM, template-update v1.94.0 — DEC-033, wo0014).** As instruções de aplicação saíram de `meta/specs/` para **`meta/workorders/`** (`git mv`; nomes preservados, numeração contínua — a próxima é `wo0014`), e o nome «spec» passou a designar a **spec de feature** do SDD (novo modelo `meta/SPEC.md`, uma por feature em `meta/specs/`). Os comandos `/` migraram do formato descontinuado `.claude/commands/*.md` para **`.claude/skills/<nome>/SKILL.md`** com front-matter: `/apply-spec` → **`/apply-wo`**, e `/wrap` atualizado. `meta/CEREBRO.md` foi mergeado com o template do kit (seções novas: «Técnicas específicas deste projeto», «Análise antes do compromisso», «Ao receber um template-update do KCM», «Bloco de fecho de turno», «Refino das Instruções», 3 regras de higiene), o `CLAUDE.md` da raiz ganhou vocabulário, teto de tamanho e seção de config, e o `.flatdropignore` passou ao formato de bloco do editor do FlatDrop. Novo `meta/workorders/_TEMPLATE.md`. **Sem mudança de código** — 0.9.2 e os 158 testes intactos.

---

## [0.9.2] — 2026-07-20
### Corrigido
- **Atalho "abrir GUI" começa limpo (spec0012, ajuste da spec0011).** Antes, a GUI restaurava a última raiz do `QSettings` mesmo quando aberta pelo atalho genérico — então clicar o `.bat` numa pasta nova ainda trazia o projeto anterior, e o "Escolher..." abria no lugar errado (relatado com print: atalho em `Artista`, raiz vinda de `Lunada`). Agora, quando a GUI é aberta com `--start-dir` (a marca do atalho "abrir GUI"), ela **não restaura** a última raiz/instrução e o "Escolher..." abre na pasta do próprio `.bat`. O botão **Recentes ▾** segue disponível para retomar um projeto anterior. Execução manual (`python -m src.gui`, sem `--start-dir`) continua restaurando a sessão como antes.
### Testes / Qualidade
- Teste novo: com `start_dir`, a janela não restaura `last_root`; sem ele, restaura. `ruff`/`black`/`self-test` limpos. `__version__` 0.9.1 → **0.9.2**.

---

## [0.9.1] — 2026-07-20
### Adicionado
- **`--start-dir` na GUI e no atalho "abrir GUI" (spec0011):** o `.bat` clássico passa a mandar `--start-dir "%~dp0."`, então os diálogos de "Escolher..." abrem **na pasta onde o `.bat` está** — que é para onde o usuário copia o atalho, junto dos projetos. O argumento apenas SEMEIA a navegação; **não define a raiz** (o atalho clássico continua genérico). O seletor de raiz usa, nesta ordem: a raiz já preenchida → a semente → o padrão do Qt. Sem o argumento, o comportamento é o de antes. Estende DEC-022/DEC-023 (incluindo o truque `"%~dp0."`, que evita a barra invertida escapando a aspa).
### Testes / Qualidade
- Testes novos: o `.bat` contém `--start-dir "%~dp0."` e não contém `--root`; `MainWindow(start_dir=...)` guarda a semente sem preencher a raiz. `ruff`/`black`/`self-test` limpos. `__version__` 0.9.0 → **0.9.1**.

---

## [0.9.0] — 2026-07-20
### Corrigido
- **Endereçamento do backup voltou a seguir a RAIZ (spec0010, DEC-032).** Duas causas somadas: (1) a GUI persistia `last_backup_dir` no `QSettings` e nunca re-derivava o destino, então um caminho escolhido uma vez "grudava" e ignorava a troca de raiz; (2) a suíte de testes gravava no `QSettings` REAL (no Windows, o registro do usuário) — `test_save_and_restore_backup_dir` chegou a injetar um caminho `pytest-of-*/.../meu_backup` na GUI de um usuário real. O engine estava correto o tempo todo. Agora: campo vazio = destino derivado da raiz; o placeholder exibe o caminho calculado e acompanha a troca de raiz; o campo não é mais persistido; os testes rodam com `QSettings` isolado em `.ini` temporário.
### Alterado
- **Pasta padrão de backup renomeada de `backups/` para `zz_backups/`** (constante `BACKUP_DIRNAME`): o prefixo mantém a pasta no fim da listagem da pasta-pai, longe do projeto. **Rollback de backups antigos continua funcionando** (fallback para `backups/` na leitura). `SANDBOX_IGNORES` e `.gitignore` cobrem os dois nomes.
### Testes / Qualidade
- Testes novos: layout `zz_backups`, fallback de rollback legado, placeholder que segue a raiz, e regressão de "backup-dir não é persistido". Fixture `autouse` isolando o `QSettings` da GUI. `ruff`/`black`/`self-test` limpos. `__version__` 0.8.7 → **0.9.0**.

---

## [0.8.7] — 2026-07-17
### Adicionado
- **Ressalva (🟡) visível no CLI (spec0008):** `_print_report` passa a imprimir cada aviso não-fatal por arquivo (marcador `~`, o mesmo de `_report_to_text`) e a contá-los no resumo (`N com ressalva`), com uma linha de atenção quando houver. Fecha a paridade CLI↔GUI do canal de warnings (DEC-028): antes, um `create_file` que sobrescrevia arquivo existente passava como sucesso silencioso na linha de comando. Sem avisos, a saída é idêntica à anterior.
### Testes / Qualidade
- 2 testes novos em `test_patch_engine.py` (com ressalva; sem ressalva não polui o resumo); `ruff`/`black`/`self-test` limpos. `__version__` 0.8.6 → **0.8.7**.

---

## [0.8.6] — 2026-07-16
### Adicionado
- **Syntax-highlight opcional no diff da GUI (spec0006, DEC-030):** com Pygments instalado (dependência de GUI), o diff da prévia/resultado ganha realce de sintaxe por token; o lexer é escolhido pelo nome do arquivo. Nesse modo, adição/remoção passam a marcar pelo FUNDO (verde/vermelho claros) e o foreground carrega as cores de sintaxe. Sem Pygments, sem caminho, ou extensão desconhecida → cai no realce só-de-linha antigo (degradação graciosa, como o colorama no core). Núcleo/CLI intactos. `_diff_to_html` ganhou parâmetro `path` opcional (default `None` = comportamento antigo).
### Testes / Qualidade
- 3 testes novos em `test_gui_smoke.py` (regressão sem `path`, fallback de extensão desconhecida, realce de Python sob `importorskip`); `ruff`/`black`/`self-test` limpos. `__version__` 0.8.5 → **0.8.6**.

---

## [0.8.5] — 2026-07-15
### Adicionado
- **Botão "Copiar saída" na GUI (spec0004):** copia o relatório COMPLETO da última prévia/aplicação — todos os arquivos, status, avisos (🟡) e diffs, tanto no sucesso quanto na falha — para a área de transferência. Serialização por função pura `_report_to_text` (sem Qt, testável); gancho em `_populate_tree`, cobrindo preview e apply. Complementa o "Copiar erro para a IA" (que só aparece em falha). Commit `31b8350`. Sem DEC nova.

---

## [0.8.4] — 2026-07-06
### Corrigido / Ajustado
- **Validador com dica acionável (spec0003):** `instruction_validator._format_error` ganhou `_schema_error_hint` — quando o erro de schema é `minLength` em `location.before`/`after` (âncora vazia do `replace_context_block`), a mensagem passa a incluir uma segunda linha "Dica:" explicando que o bloco provavelmente toca a borda do arquivo e sugerindo `replace_line_pattern`/`insert_before_pattern`/`replace_section`/`replace_function` como alternativa. Chaveia por `error.validator` (estável), não pelo texto da mensagem. Origem: print do usuário 07-03.
- **Rollback registrado no `history.log` (spec0003):** `backup_manager.rollback_from_dir` passa a chamar `_append_rollback_history` (best-effort) sempre que algo foi de fato revertido, gravando uma linha `rollback de <sessão> (N revertido(s))` no `history.log` do diretório-pai da sessão. Cobre os três caminhos que passam por `rollback_from_dir`: GUI (Desfazer), CLI (`rollback`) e `self-test`. Rollback automático em falha (`_maybe_rollback`) NÃO é registrado (nunca chegou a gravar linha de aplicação).
### Documentação / Processo
- **`docs/INSTRUCTION_GUIDE.md`:** nota na §4.1 sobre não usar `replace_context_block` na borda do arquivo + linha nova na tabela erro→correção (§6) para `minLength`/`non-empty` em `location.before`/`after`.
### Testes / Qualidade
- 2 testes novos (`test_validator_dica_ancora_vazia_no_context_block`, `test_rollback_registra_no_history`); suíte, `ruff`, `black` e `self-test` limpos. `__version__` 0.8.3 → **0.8.4**. Sem DEC nova (estende DEC-014/026 e DEC-018).

---

## [0.8.3] — 2026-07-03
### Adicionado
- **Canal de warnings não-fatais — DEC-028 (specs 0001+0002):** terceiro estado "aplicado com ressalva", entre sucesso e erro. No engine, `apply()` pode retornar `(str, list[str])` além de `str` (retrocompatível — não quebra as 13 estratégias); `split_apply_result` normaliza; `ModificationResult.warnings` + `FileResult.has_warnings`/`ApplyReport.has_warnings`. Piloto: `create_file` sobre arquivo existente avisa da sobrescrita. Na GUI, a árvore ganha 🟡 por arquivo (precedência 🔴 > 🟡 > 🟢 > ⚪) e ⚠ por modificação, com avisos no tooltip; Aplicar segue habilitado (ressalva não bloqueia); resumo mostra "(N ressalva(s))". Warning não altera `report.ok`, não aborta, não reverte.
### Documentação / Processo
- **README.md** reescrito para 0.8.x (backup padrão na pasta-pai, `--backup-dir`, `history.log`, GUI completa, 13 estratégias, encodings, quando-usar-ASU) e **GUIA_PASSO_A_PASSO.md** criado (ideia-260614).
- **DECISIONS arquivado** — DEC-001..012 + FIX-001..006 → `meta/DECISIONS-archive.md` (o principal passou de 715 linhas). Numeração preservada.
- **2ª atualização do KCM integrada — DEC-027:** config-no-Code no CEREBRO, convenção de spec do KCM (`AAMMDD-specNNNN-desc.md` / `AAMMDD-asuNNNN.yaml`), `HISTORICO.md`→`HISTORY.md` (via `git mv`, refs em README/CONTEXT ajustadas), painel (Instruções do Projeto) atualizado.
- **HUB.md** atualizado (status relâmpago do ASU → 0.8.x; 3 itens abertos na caixa do KCM).
- `black` reinstalado no ambiente do Claude Code (via `requirements-dev.txt`); `black --check .` limpo nos 27 arquivos.
### Testes / Qualidade
- Suíte em ~144 funções `test_` (133 + specs 0001/0002); `ruff`/`black`/`self-test` limpos. `__version__` 0.8.2 → **0.8.3**.

---

## [0.8.2] — 2026-06-30
### Adicionado
- **Dicas "já aplicado?" no erro de âncora — DEC-026:** quando uma âncora casa 0 vezes, a mensagem de erro agora pode incluir duas dicas novas, além da de whitespace (DEC-014): (1) **substring** — a âncora é parte de um identificador maior no arquivo (ex.: `doGen(` ⊂ `doGenRandom()`), provável erro de escopo/digitação; (2) **já aplicado** — o `new_content`/`content` que a modificação quer escrever já está presente no arquivo (comparação tolerante a whitespace), forte sinal de que a modificação já foi aplicada. Detecção **sem ledger**, feita em memória só no caminho de erro (ASU continua *stateless* no projeto-alvo).
- Funções novas e puras em `text_strategy.py`: `_substring_hint`, `_already_applied_hint`, agregadas por `_anchor_hints` (ponto único chamado pelas estratégias ao falhar uma âncora).

### Corrigido / Ajustado
- `insert_after_pattern`/`replace_line_pattern` agora dão dica também no caminho de "casou 0 vez(es)" (antes esse caminho não tinha `source`/`new_content` em escopo para dar dica nenhuma).
- `docs/INSTRUCTION_GUIDE.md` §6: duas linhas novas na tabela erro→correção.

### Qualidade
- Testes: 128 → **133** (5 novos em `test_edge_cases.py`); ruff limpo; `black --check` confirmado limpo nos arquivos tocados (validado na conferência do chat — o ambiente do Code não tinha `black` instalado).
- `__version__` bumpeado para `0.8.2`.

---

## [0.8.1] — 2026-06-28
### Adicionado
- **Backup padrão na pasta-pai da raiz — DEC-024(c):** sem `--backup-dir`, o backup vai para `parent(root)/backups/<timestamp>/` em vez de `root/backups/`. Projeto fica limpo por padrão. Edge: `root` sem pai utilizável (drive root) → fallback para `root/backups/` (seguro). NÃO aninha por `<rootname>` no padrão (colidiria com a própria raiz).

### Corrigido / Ajustado
- **Rollback default acompanha o padrão:** `rollback` sem `--backup-dir` procura em `parent(root)` (antes: `root`). CLI e GUI coerentes.
- **`self-test` usa `rollback_from_dir(path)`** em vez de `rollback_session(raiz, ts)` — agnóstico à localização do backup, independentemente de interno ou externo.

### Qualidade
- Testes: 126 → **128** (2 novos: `test_backup_padrao_rollback_via_cli`, `test_backup_externo_nao_regride_dec024b`); `test_backup_interno_estrutura_atual` → `test_backup_padrao_pasta_pai`; ruff/black limpos.
- `__version__` bumpeado para `0.8.1`.

---

## [0.8.0] — 2026-06-28
### Adicionado
- **Atalho "abrir GUI" (clássico) — DEC-023:** novo botão "Criar atalho .bat (abrir GUI)…" + função pura `build_open_gui_bat`. Gera um `.bat` que só abre a interface (sem `--root`/`--instruction`), via `pythonw.exe` + `start "" /d "<asu_home>"` — sem janela de console, destacado, diretório de trabalho correto. Independente de projeto (salvar onde quiser). Inspirado no `flatdrop-ui.bat`.
- **Local do backup na GUI — DEC-024(a):** linha "Backup:" com campo + "Escolher…" (`_pick_backup_dir`), persistida em `QSettings` (`last_backup_dir`). Expõe o `--backup-dir`/`backup_location` (DEC-018) que já existia no núcleo — permite manter o backup FORA do repositório sem `.gitignore`.
- **Backup nomeado por projeto quando externo — DEC-024(b):** quando o backup vai para fora da raiz, aninha `<backup-dir>/<nome-da-raiz>/<timestamp>/` (e o `history.log` por projeto), resolvendo a mistura de vários projetos numa pasta compartilhada. `_sanitize_name` higieniza o nome para pasta Windows válida. Dentro do projeto, mantém `backups/<ts>` (sem aninhar — evita alongar caminhos, MAX_PATH/FIX-008).

### Corrigido
- **`.bat` por projeto não abria apontado (BUG do `%~dp0`) — DEC-023:** `--instruction-dir "%~dp0"` terminava em `\` → `"...\"` → a sequência `\"` era lida como aspa escapada e corrompia o argumento. Corrigido para `--instruction-dir "%~dp0."`.
- **`chcp` agora considera a pasta do `.bat` — DEC-023:** como `%~dp0` resolve para `bat_dir` em runtime, o teste de não-ASCII passou a incluir `bat_dir` (um `.bat` em pasta acentuada nasce em UTF-8 + `chcp 65001`).

### Endurecido
- **Encoding do `.bat` gerado — DEC-023:** caminhos ASCII → `.bat` ASCII puro; caminho com acento → `chcp 65001 >nul` + arquivo UTF-8 **sem BOM**; removido o `errors="replace"` (que corromperia um caminho acentuado em silêncio). *(parte deste endurecimento foi escrita na linha 0.7.x e é lançada junto aqui.)*

### Refatorado
- **Rollback extraído para `rollback_from_dir(session_dir)` — DEC-024:** aceita o caminho completo da pasta de sessão; `rollback_session` delega a ela. Faz o desfazer funcionar igual para backup interno e externo (a GUI guarda `(pai_do_session_dir, ts)`).

### Qualidade
- Testes: 112 → **126** (endurecimento ASCII: +5 em `test_launcher.py`; bat-fix + launcher clássico: +5 em `test_launcher.py`; backup externo: +5 em `test_patch_engine.py`, +2 em `test_gui_smoke.py`); ruff/black limpos. *(A divergência 97/112/107 dos relatórios do Code foi sanada na conferência pós-merge: 126 é a contagem definitiva.)*

---

## [0.7.0] — 2026-06-23
### Adicionado
- **F2 increment "Acesso rápido a projetos"** — quatro itens implementados de uma vez:
  - **Recentes e fixadas (WI-1):** `btn_recentes` abre menu "Recentes ▾" com seções Fixadas (📌) e Recentes; botão 📌 fixa/desafixa a raiz atual. `_push_recent_root` (máx. 8, case-insensitive) é chamado após `preview()` e `apply_changes()` OK. Persistido em `QSettings` (`recent_roots`/`pinned_roots`).
  - **Args de lançamento (WI-2):** `python -m src.gui --root <pasta> --instruction-dir <pasta> --instruction <arquivo>` abre a GUI já apontada para o projeto. `MainWindow.__init__` aceita os kwargs; `run()` os repassa; `__main__.py` parseia via `argparse`.
  - **Resolução pasta→instrução (WI-2/D3):** `_apply_instruction_dir` escaneia só o topo da pasta — 1 yaml = pré-preenche o campo; 0 ou 2+ = aponta o seletor "Abrir…" para essa pasta + exibe dica no status. Assim instruções arquivadas em subpastas são ignoradas de propósito.
  - **Gerador de atalho .bat por projeto (WI-3+WI-4):** novo módulo puro `src/gui/launcher.py` (`resolve_instruction_in_dir` + `build_launcher_bat`); botão "Criar atalho .bat…" na GUI. O `.bat` gerado chama `.venv\Scripts\python.exe` direto (sem `activate` — DEC-022), com `--root` relativo a `%~dp0` quando o projeto é descendente da pasta do `.bat`, absoluto caso contrário.

### Qualidade
- Testes: 93 → **112** (+10 em `tests/test_launcher.py` para funções puras + 9 em `tests/test_gui_smoke.py` para WI-1/WI-2); ruff/black limpos; versão `0.7.0`.

---

## [0.6.0] — 2026-06-15
### Adicionado
- **`--backup-dir PASTA` (apply e rollback) — DEC-018:** permite criar a pasta `backups/` FORA do projeto (padrão segue sendo a raiz do projeto). Mantém a árvore do projeto 100% limpa. O `rollback` aceita o mesmo `--backup-dir` (com `--root` como fallback) para localizar a pasta quando ela está fora.
- **`backups/history.log` consolidado — DEC-018:** arquivo append-only com uma linha por aplicação (`timestamp` + nº de arquivos + descrição da instrução), para ver o histórico sem abrir cada pasta de timestamp. O CLI imprime o caminho do history após aplicar.
- **Checkbox "Aplicar em sandbox (cópia)" na GUI — DEC-019:** paridade com o `--sandbox` do CLI. Aplica numa cópia irmã; o original não é tocado; o status bar mostra o caminho da sandbox.

### Refatorado
- **Sandbox movido para o core (`patch_engine.make_sandbox` + `SandboxError`) — DEC-019:** a lógica saiu de `__main__.py` (que usava `print`/`SystemExit`) para o core, sinalizando erro por exceção. CLI e GUI agora compartilham uma única implementação (cumpre DEC-013, GUI fina).

### Qualidade
- Testes: 90 → **93** (2 de backup_location/history + 1 de sandbox na GUI); ruff/black limpos; versão `0.6.0`.

---


## [0.5.2] — 2026-06-14
### Corrigido
- **FIX-009 — artefato da demo (`health.py`) vazou para o repo e quebrava 4 testes + self-test no Windows.** A `demo.yaml` cria `examples/demo_project/src/health.py` via `create_file`; numa execução anterior (provavelmente antes do FIX-008, quando o rollback no Windows não removia o criado) o arquivo ficou como resíduo e foi versionado. Os testes/self-test copiam `demo_project` e encontravam o `health.py` já presente, quebrando o `assert "não escreveu nada"`. **Não foi erro de processo do usuário — os arquivos estavam nos lugares certos.** Correção em 3 camadas: `.gitignore` ignora o artefato e `*_sandbox_*/`; a fixture de teste e o self-test limpam o que a demo gera após copiar; resíduo removido do pacote.

### Documentação
- **DEC-017** registra a separação de dois canais de feedback: sobre o **Kit de Contexto** → IDEAS › «Feedback para o Kit»; sobre o **ASU** (a ferramenta) → DEC/FIX/IDEAS/STATUS normais (não precisa de canal paralelo).

---

## [0.5.1] — 2026-06-13
### Corrigido
- **FIX-008 (Windows) — backup estourava o MAX_PATH (260 chars):** o espelho de backup recriava o caminho ABSOLUTO inteiro do arquivo dentro de `backups/`, o que no Windows (com `AppData\Local\Temp` + pasta `_sandbox_`) ultrapassava o limite e quebrava com `WinError 3`. Atingia 5 testes e o `self-test` — invisível no Linux/CI (caminhos curtos). O espelho passou a ser **relativo à raiz** (`backups/<ts>/<caminho_relativo>`), o `manifest.txt` grava o espelho explícito, e o formato antigo segue legível. **Era o que derrubava o `python -m pytest` e o `self-test` na sua máquina.**

### Adicionado
- **Guia §8 "Verificação pós-aplicação" (DEC-016):** a IA, na sessão seguinte a uma instrução ASU, confere no disco cada arquivo tocado antes de seguir (em vez de confiar em "deu certo") — prática *outcome-based* validada por pesquisa. Item correspondente no `PROMPT_IA.md`.

### Kit de contexto
- CLAUDE.md alinhado à atualização do Kit (parágrafos: adaptar as Instruções do Projeto a este projeto; criar arquivo de doc ausente na primeira necessidade). Cabeçalhos dos templates atualizados ao formato novo, preservando o conteúdo do projeto.

---

## [0.5.0] — 2026-06-12
### Adicionado
- **`apply --sandbox` (DEC-015)** — o "modo seguro" virou comando: duplica a raiz numa pasta irmã `<nome>_sandbox_<ts>` (ignorando `.git`, `node_modules`, venvs, caches…), aplica NA CÓPIA e imprime o caminho; o projeto original não é tocado. Instruções com `path_mode: absolute` são recusadas nesse modo.
- **GUI: "Colar instrução"** — usa o YAML direto da área de transferência (sem salvar arquivo), via `load_instruction_from_string`.
- **GUI: "Copiar erro para a IA"** — em falha de validação/prévia/aplicação, copia um bloco pronto (erros + referência às §4/§6 do guia) para colar na IA geradora; fecha o loop de autocorreção na interface.
- **GUI: lembra os últimos caminhos** (raiz e instrução) entre sessões, via QSettings.

### Corrigido
- **FIX-007a (GUI):** o Desfazer usa a raiz CAPTURADA no momento da aplicação — trocar a pasta no campo depois de aplicar não quebra mais o rollback.
- **FIX-007b (GUI):** Aplicar exige que a instrução e a raiz sejam EXATAMENTE as da última prévia (impressão digital SHA-256); editar o YAML após revisar bloqueia com aviso e pede nova prévia.

### Qualidade
- Testes: 84 → **90** (4 da GUI nova + 2 do sandbox); ruff/black limpos; versão `0.5.0`.

---

## [0.4.0] — 2026-06-11
### Adicionado
- **GUI (F2 inicial, DEC-013)** — `python -m src.gui`: janela PySide6 fina sobre a mesma pilha do CLI. Pré-visualizar (dry-run) popula árvore de arquivos com indicador 🟢/🔴/⚪ e ✓/✗ por modificação (derivados do `ApplyReport`), diff colorido por arquivo, Aplicar com confirmação + backup, Desfazer última aplicação. Testes offscreen do circuito completo.
- **`python -m src self-test`** — valida a instalação ponta a ponta aplicando a demo embutida em diretório temporário (e revertendo). Nada do disco do usuário é tocado.
- **Dica acionável de whitespace nas âncoras (DEC-014)** — quando `before`/`after` não casa exato mas existe trecho equivalente módulo espaços/indentação, o erro aponta a linha e a forma exata do arquivo para copiar (estilo "did you mean" do Aider; estudo do apply_patch/V4A da OpenAI). Sem fuzzy matching silencioso.
- **Kit de ensino v2** — `INSTRUCTION_GUIDE.md` agora é 100% autocontido: exemplo completo embutido (a v1 apontava para um arquivo fora do contexto dos projetos consumidores — causa provável do desentendimento em campo), seção de formato de resposta + anti-padrões (YAML-only, nunca XML), regra de âncora exata/multilinha e **tabela erro→correção** que fecha o loop de autocorreção da IA geradora. `PROMPT_IA.md` v2 alinhado.
- README: seções "Interface gráfica", "Verificação rápida (self-test)" e "Modo seguro para os primeiros usos" (fluxo com duplicata e com Git).

### Qualidade
- Testes: 79 → **84** (dica de whitespace + 3 de GUI offscreen); ruff/black limpos; versão `0.4.0`.

---

## [0.3.0] — 2026-06-10
### Adicionado
- **Kit de ensino para a IA geradora (DEC-012)**: `docs/INSTRUCTION_GUIDE.md` (referência completa: estratégias, cinco regras de ouro, checklist de autovalidação) + `docs/PROMPT_IA.md` (bloco pronto para colar no contexto de outros projetos). Validado por dogfooding: instrução escrita só com o guia aplicou C# com BOM, Python decorado e TSX, com rollback íntegro. README ganhou a seção "Gerando instruções com IA".

### Corrigido
- **FIX-004:** modificações JSON preservam o estilo do arquivo original (indentação 2/4/tab, formato compacto e newline final) — antes tudo era reformatado com `indent=2`, explodindo o diff.
- **FIX-005:** `delete_json_path` agora remove chaves de valor `null` (o jmespath confundia `null` com "ausente"); `append_json_array` distingue os dois casos. Navegação 100% própria — **jmespath removido do núcleo** (requirements: PyYAML, jsonschema, libcst, colorama).
- **FIX-006:** intake endurecido — chave YAML duplicada vira erro de parse com linha/coluna (antes a primeira evaporava); IDs repetidos (`files[].id` / `modifications[].id`) rejeitados na validação; arquivo-alvo **binário** (byte NUL, incl. UTF-16 sem BOM) rejeitado com erro claro antes que um `replace_file` o sobrescrevesse.

### Qualidade
- Testes: 68 → **79**; ruff e black limpos; versão `0.3.0` em `__init__`/`pyproject`.

---

## [0.2.0] — 2026-06-10
### Modificado (comportamento)
- **DEC-011 — unicidade implícita de localizadores:** com `occurrence` ausente, padrões/âncoras que casam mais de uma vez agora são **rejeitados como ambíguos** antes de qualquer escrita (antes aplicavam na 1ª ocorrência silenciosamente). `occurrence` explícito segue sendo escolha posicional. Vale para `insert_after_pattern`, `insert_before_pattern`, `replace_line_pattern` e a âncora `before` do `replace_context_block`; `replace_section` rejeita heading duplicado.

### Corrigido
- **FIX-002 — encodings:** BOM UTF-8 detectado e **preservado** (roundtrip com `utf-8-sig`; arquivos `.cs` do Visual Studio agora localizam padrões na 1ª linha). UTF-16/32 rejeitados com erro claro (antes, cp1252 os "decodificava" como lixo, e `replace_file` converteria o encoding silenciosamente). Detecção de newline movida para o texto decodificado. Erros de leitura/decodificação agora entram no fluxo normal de falha por arquivo (status `failed` + stop/rollback) em vez de derrubar o processo.
- **FIX-003 — `replace_section` fence-aware:** headings dentro de blocos ``` / ~~~ deixam de ser tratados como seções (não são mais encontrados nem encerram a seção real no lugar errado).

### Adicionado
- **Suíte multilinguagem** (`tests/test_multilang.py`): prova do mecanismo universal em **C#, C++, Java, JSX, TSX e GDScript**, incluindo engine completo com C# + BOM e rejeição de UTF-16.
- **Suíte de bordas** (`tests/test_edge_cases.py`): unicidade implícita/explícita, fences, heading duplicado, última seção até EOF, chaves aninhadas no context block (semântica fixada), decorador removido se não repetido (semântica fixada), cp1252 roundtrip, CRLF preservado, arquivo sem newline final.
- Total de testes: 43 → **68**.

### Qualidade
- `ruff check` limpo (auto-fix + correções manuais de B904) e `black` aplicado em todo o código.
- Versão unificada em `0.2.0` (`src/__init__.py` e `pyproject.toml` estavam dessincronizados em 0.0.1).

---

## [0.1.1] — 2026-06-10
### Adicionado
- **Demo executável** (`examples/demo_project/` + `examples/demo.yaml`) — projeto-alvo real com arquivos `.py`, `.md`, `.json` e `.js` e uma instrução que aplica de verdade (cobre os 4 tipos + `create_file`). Permite testar `validate → apply --dry-run → apply → rollback` de ponta a ponta sem ter um projeto próprio.
- README com seção **Quickstart** (comandos copiáveis usando a demo) e seção "Uso no seu projeto" com placeholder explícito.

### Corrigido
- **FIX-001:** `replace_context_block` agora rejeita com erro claro quando o `new_content` inclui as próprias âncoras `before`/`after` (antes, isso duplicava as âncoras silenciosamente, corrompendo o arquivo sem sinalizar). Acrescentado teste de regressão.
- `examples/exemplo_instrucao.yaml` — corrigido o bloco JavaScript que continha as âncoras no `new_content` (agora só o miolo entre elas).

### Documentação
- README deixou de usar o nome genérico `instrucao.yaml` nos comandos (causava confusão de "arquivo não encontrado" no primeiro uso).

---

## [0.1.0] — 2026-06-08
### Adicionado
- **Motor de execução (F1) funcional via CLI** — fluxo completo instrução → validação → localização → aplicação → backup → diff → resultado, com rollback.
- `instruction_v1.schema.json` — JSON Schema Draft 7 completo (contrato do arquivo de instrução), com `$comment` idiomático.
- `instruction_parser.py` — carrega YAML/JSON com fallback de encoding utf-8→cp1252.
- `instruction_validator.py` — valida contra o schema e o `format_version`, acumulando todos os erros com o caminho do campo.
- Treze estratégias de modificação (padrão Strategy): `replace_function`, `replace_method`, `replace_class` (Python/libcst); `insert_after_pattern`, `insert_before_pattern`, `replace_line_pattern`, `replace_context_block` (texto universal); `replace_section` (markdown); `set_json_path`, `append_json_array`, `delete_json_path` (JSON/jmespath); `replace_file`, `create_file` (arquivo inteiro).
- `file_locator.py` — resolve caminhos relative/absolute com guarda de contenção (caminho relativo não escapa da raiz).
- `backup_manager.py` — backup timestampado espelhando a estrutura de pastas; rollback atômico e rollback por timestamp.
- `diff_renderer.py` — unified diff colorido (colorama, com degradação graciosa).
- `patch_engine.py` — orquestração com transação e rollback automático em falha, dry-run e precedência de configuração (padrões < settings < flags).
- CLI (`python -m src`): subcomandos `validate`, `apply` (prévia + confirmação) e `rollback`.
- Arquivos de projeto: `pyproject.toml`, `requirements.txt` (núcleo sem Qt), `requirements-gui.txt`, `requirements-dev.txt`, `.gitignore`, `README.md`, `examples/exemplo_instrucao.yaml`.
- 42 testes (parser/validator, estratégias, integração do engine), todos verdes.

### Decisões
- DEC-008 (estratégias `create_file`/`replace_file`), DEC-009 (`location.type` removido; papéis Python explícitos; interface da estratégia com `apply()` único), DEC-010 (independência de linguagem via contexto; `requirements` dividido).

---

## [0.0.1] — 2026-06-03
### Adicionado
- Concepção do projeto: visão, escopo e objetivos definidos.
- Stack tecnológica selecionada e justificada (Python 3.11+, PySide6, libcst, PyYAML, jsonschema, jmespath, PyInstaller).
- Arquitetura modular definida: `core/` (parser, validator, locator, engine, backup, diff), `strategies/` (python, text, json), `gui/`, `schemas/`.
- Onze estratégias de modificação especificadas para 4 tipos de arquivo (Python, Markdown, JSON, texto genérico).
- Schema conceitual do arquivo de instrução YAML v1.0 com hierarquia: cabeçalho, settings, files[], modifications[].
- Sete decisões arquiteturais documentadas em DECISIONS.md (DEC-001 a DEC-007).
- Roadmap em 5 fases documentado (F0 concluída, F1–F4 futuras).
- Documentação completa de contexto gerada: CONTEXT.md, STATUS.md, DECISIONS.md, ROADMAP.md, GLOSSARY.md, HISTORICO.md, IDEAS.md, LOG-TEMPLATE.md, logs/2026-06-03.md.
