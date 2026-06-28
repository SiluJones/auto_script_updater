# SPEC — F3 · Local do backup na GUI + nome por projeto (quando externo)

> **Tipo:** spec de FEATURE (código), para o Claude Code implementar.
> **Base:** o núcleo JÁ suporta backup fora do projeto via `backup_location` (CLI `--backup-dir`, DEC-018) — ver `src/core/patch_engine.py` (`backup_dir` no `ApplyReport`) e `src/__main__.py` (`backup_location=getattr(args, "backup_dir", None)`). A GUI **não expõe** isso. Esta spec leva o recurso à GUI e melhora o nome do backup quando ele vai para fora.
> **Âncoras** são símbolos do código; `grep`-os antes de editar.

## Contexto / pedido do usuário (260628)
1. **Backup fora do repositório:** o usuário quer gerar o backup numa pasta FORA da raiz da modificação (algo como onde ficam o `.bat` e a instrução), para não sujar o repositório. — O recurso EXISTE no núcleo (`--backup-dir`); falta o campo na GUI.
2. **Nome genérico "backup":** hoje o backup nasce em `backups/<timestamp>/`. Quando vários projetos mandam o backup para a MESMA pasta externa, eles se misturam — o usuário quer saber de qual projeto é cada backup.

## Análise / decisão (livre p/ refutar — eis o veredito)
- **(1) Expor backup-dir na GUI: FAZER.** É só ligar um recurso que já existe e é testado no núcleo; risco baixo, valor direto (backup fora do repo sem depender de `.gitignore`).
- **(2) Nome por projeto: FAZER, mas SÓ quando o backup vai para fora.** Dentro do projeto (padrão), `backups/` já está no contexto do próprio projeto — nome do projeto seria redundante e alongaria caminhos (risco MAX_PATH, FIX-008). Quando `backup-dir` aponta para fora, aninhar por projeto resolve a mistura com **um único nível** de pasta (impacto mínimo no comprimento, melhor que prefixar cada arquivo). Estrutura: `<backup-dir>/<nome-da-raiz>/<timestamp>/...` (e o `history.log` passa a ser por projeto, em `<backup-dir>/<nome-da-raiz>/history.log`).
- Reuso do que já existe: a profundidade do espelho já é curta/relativa (FIX-008), então o nível extra do nome do projeto é seguro na prática. Se um nome de projeto for muito longo + arquivos muito profundos, há risco residual de MAX_PATH — aceitável e raro; não justifica complicar.

## Itens de trabalho

### WI-1 — `backup_manager` aceita um nome de projeto opcional (`src/core/backup_manager.py`)
- Onde hoje a pasta de sessão é montada como `<base>/backups/<timestamp>`, permitir um segmento de projeto opcional: quando o backup vai para um `backup_location` EXTERNO (≠ dentro da raiz), montar `<backup_location>/<project_name>/<timestamp>` (e o `history.log` no nível `<backup_location>/<project_name>/`).
- `project_name` = basename da raiz (sanitizado para nome de pasta válido no Windows). Passado pela camada de cima (engine/CLI/GUI). Quando ausente/backup interno, manter o comportamento atual (`backups/<timestamp>`), sem regressão.
- Manter `restore_all`/rollback funcionando com a nova estrutura (o `report.backup_dir` continua apontando para a pasta de sessão real).

### WI-2 — `patch_engine`/CLI repassam o nome do projeto (`src/core/patch_engine.py`, `src/__main__.py`)
- O engine deriva `project_name` da raiz quando `backup_location` é externo e repassa ao `backup_manager`. Não alterar a assinatura pública mais do que o necessário; manter `backup_location` opcional como hoje.
- O CLI continua funcionando igual (só ganha o aninhamento por projeto quando `--backup-dir` é externo).

### WI-3 — Campo de backup na GUI (`src/gui/main_window.py`)
- Adicionar uma linha: rótulo "Backup:" + `QLineEdit` (placeholder "Padrão: pasta do projeto. Opcional: pasta fora do projeto.") + botão "Escolher…" (`QFileDialog.getExistingDirectory`). Persistir o último valor no `QSettings` (chave `last_backup_dir`), como já se faz com raiz/instrução.
- Em `apply_changes`, passar esse valor como `backup_location` para `apply_instruction` (vazio = `None` = comportamento atual). Quando preenchido (externo), o núcleo aninha por projeto (WI-1/WI-2).
- Sandbox e dry-run inalterados. O `_save_last_paths` passa a salvar também o backup-dir.

### WI-4 — Testes
- `backup_manager`: backup interno (sem project_name) → estrutura atual `backups/<ts>`. Backup externo com project_name → `<ext>/<project>/<ts>` e `history.log` em `<ext>/<project>/`. Rollback funciona nos dois.
- (GUI) smoke: a janela instancia com o campo de backup; `_save_last_paths`/restauração incluem o backup-dir.

## Critério de conclusão
- `pytest` verde; `ruff`/`black` limpos.
- Na GUI, apontar o backup para uma pasta externa e aplicar → o backup aparece em `<externo>/<nome-do-projeto>/<timestamp>/`. Sem apontar → comportamento de hoje.

## Ao concluir (raia do Code — via `/wrap`)
- CHANGELOG (entrada na próxima versão menor) + STATUS atualizados; **DEC** nova (ou estender a DEC-018) registrando: backup externo aninha por `<nome-da-raiz>` (um nível, MAX_PATH ok porque o espelho já é raso — FIX-008); GUI expõe o backup-dir.
- Atualizar o IDEAS (mover a ideia "local do backup + nome com prefixo da raiz" de PARCIAL para concluída na parte que esta spec entrega). [Se o Code não mexer em IDEAS, deixar para o chat.]

## Fora do escopo
Limpeza automática de backups antigos (continua no Backlog/F3). Correção do `.bat` e atalho "abrir GUI" têm spec própria.
