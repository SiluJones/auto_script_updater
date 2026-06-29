# SPEC — F3 · Padrão do backup na pasta-PAI da raiz (DEC-024c)

> **Tipo:** spec de FEATURE (código), para o Claude Code. PEQUENA, mas mexe em comportamento PADRÃO de backup/rollback — teste com cuidado.
> **Base:** `src/core/backup_manager.py`, `src/core/patch_engine.py`, `src/__main__.py`, `src/gui/main_window.py`. O aninhamento por projeto quando externo já existe (DEC-024b).
> **Âncoras** = símbolos do código; `grep` antes de editar.

## Objetivo
Tornar o PADRÃO do backup `parent(root)/backups/<timestamp>/` (fora do repositório), em vez de `root/backups/<timestamp>/`. Pedido do usuário: o backup não deve sujar o repo por padrão.

## Decisão de design (DEC-024c — cuidados que NÃO podem ser ignorados)
1. **Não aninhar por `<rootname>` no caso padrão.** `parent(root)/<rootname>` É a própria `root` → colidiria (backup cairia dentro do projeto). No padrão, usar `parent(root)/backups/<ts>` DIRETO. (O aninhamento por projeto da DEC-024b continua valendo só quando o usuário aponta `--backup-dir` para uma pasta COMPARTILHADA externa.)
2. **Rollback default tem de acompanhar.** Hoje o `rollback` sem `--backup-dir` procura em `root` (ver `src/__main__.py`, `base = getattr(args,"backup_dir",None) or args.root or cwd`). Mudar para procurar em `parent(root)` por padrão — senão o desfazer de CLI não acha o backup novo. GUI idem (o `_last_backup` já guarda o caminho real da sessão, então o undo da sessão corrente funciona; o que muda é onde o backup nasce).
3. **Edge — raiz sem pai** (drive root, ex.: `C:\`): `parent` seria o próprio drive ou vazio. Detectar e cair para dentro do projeto (`root/backups`) com segurança.
4. **MAX_PATH:** `parent(root)` é mais curto que `root`, então o espelho relativo (FIX-008) continua seguro (igual ou melhor).

## Itens de trabalho
### WI-1 — Local padrão do backup (`patch_engine.py` / `backup_manager.py`)
- Quando `backup_location` é `None` (padrão), calcular a base como `parent(root)` (com o fallback do edge 3). Quando `backup_location` é dado, comportamento atual (incl. aninhamento por projeto da DEC-024b se for externo).
- A pasta segue `backups/<timestamp>/` sob a base. NÃO aninhar `<rootname>` no caso padrão.

### WI-2 — Rollback default (`src/__main__.py`)
- Ajustar a resolução da base do `rollback` sem `--backup-dir` para `parent(root)` (mesmo fallback do edge). Manter `--backup-dir` explícito como override.

### WI-3 — GUI (`main_window.py`)
- Atualizar o placeholder do campo "Backup:" para refletir o novo padrão (ex.: "Padrão: pasta-pai da raiz (fora do projeto). Opcional: outra pasta."). O comportamento do undo da sessão já usa o caminho real; conferir que continua ok.

### WI-4 — Testes (`tests/test_patch_engine.py`)
- Padrão (sem `backup_location`) → backup nasce em `parent(root)/backups/<ts>` e o rollback default o encontra. Edge raiz-sem-pai → cai para `root/backups`. Externo compartilhado → continua aninhando por projeto (DEC-024b, não regredir).

## Critério de conclusão
- `pytest` verde; `ruff`/`black` limpos. Aplicar pela GUI sem preencher Backup → backup aparece na pasta-PAI da raiz; Desfazer funciona.

## Ao concluir (via /wrap)
- Fechar a **DEC-024(c)** (de "a implementar" para implementada) no DECISIONS; entrada no CHANGELOG (0.8.1 ou próxima); atualizar STATUS (sai de "Em Progresso").
