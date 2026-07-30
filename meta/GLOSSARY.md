# GLOSSARY.md — Termos do Projeto

> **Opcional.** Use quando o projeto tem vocabulário próprio (nomes de módulos, conceitos, identificadores) que o assistente reexplicaria a cada sessão sem isto.
> Mantenha curto: só o que não é óbvio para alguém de fora.

---

## Conceitos do projeto

- **Arquivo de instrução** — Arquivo `.yaml` (ou `.json`) gerado por IA que descreve quais arquivos modificar e como. Entrada principal da ferramenta. Segue o schema `instruction_v1.schema.json`.

- **Modification / modificação** — Uma operação atômica de modificação em um arquivo específico: localiza o ponto correto e aplica o novo conteúdo. Cada arquivo da instrução pode ter N modificações.

- **Strategy / estratégia de modificação** — Algoritmo que sabe como localizar e aplicar uma modificação em um tipo específico de arquivo. Implementada como subclasse de `BaseStrategy`. Ex: `replace_function`, `set_json_path`.

- **Localizador** — Identificador usado pela strategy para encontrar o ponto exato de modificação no arquivo (ex: nome de função, texto do heading, regex, janela de contexto). Nunca é número de linha absoluto.

- **Janela de contexto** — Técnica de localização que usa N linhas únicas antes e depois do ponto alvo para encontrá-lo sem depender de número de linha. Inspirada no formato unified diff (usado pelo git, OpenAI Codex).

- **Dry run** — Execução simulada: toda a lógica de localização e patch roda, mas nenhum arquivo é escrito em disco. Retorna o mesmo resultado que a execução real mostraria.

- **Rollback** — Restauração de todos os arquivos afetados ao estado anterior à aplicação, a partir do backup criado pelo `backup_manager` antes da execução. Pode ser **automático** (disparado pelo `patch_engine` quando uma modificação falha com `stop_on_error`) ou **manual** (via `python -m src rollback <timestamp>`, que lê o `manifest.txt` da sessão de backup).

- **Rollback atômico** — Garantia de que uma instrução é "tudo ou nada": se qualquer arquivo falhar no meio da execução, os arquivos já escritos são revertidos e os criados são removidos, deixando o projeto exatamente como estava. Implementado em F1 no `patch_engine` + `backup_manager`.

- **Guarda de contenção** — Verificação do `file_locator`, no modo `relative`, de que o caminho resolvido não escapa da pasta raiz (`..` ou caminhos que sairiam do projeto são rejeitados). Impede que uma instrução gerada por IA escreva fora do projeto sem o usuário ter escolhido explicitamente o modo `absolute`.

- **Root path / pasta raiz** — Pasta base do projeto do usuário. Definida na GUI ou via `--root` no CLI. Usada para resolver caminhos relativos da instrução (`root_path + relative_path`).

- **path_mode** — Campo da instrução que define como o caminho do arquivo é especificado: `"relative"` (relativo ao root_path) ou `"absolute"` (caminho completo já embutido na instrução pela IA).

- **format_version** — Campo de cabeçalho da instrução que identifica a versão do schema (ex: `"1.0"`). Permite detectar incompatibilidades entre instruções antigas e versões novas da ferramenta.

- **Confidence / confiança** — Indicador calculado pré-aplicação que informa se o localizador de uma modificação é válido: único (🟢), ambíguo/aviso (🟡), inválido/não encontrado (🔴).

- **Anchor comment** — Comentário especial inserido no código-alvo (`# ASU_ANCHOR: nome`) que serve como marcador de localização ultra-estável para a ferramenta. Uso opcional e futuro.

---

## Arquiteturas / módulos

- **patch_engine** — Módulo orquestrador. Recebe a instrução parseada, seleciona strategies, aplica modificações em sequência, gerencia transação (com rollback em falha) e reporta resultado.

- **instruction_parser** — Módulo que lê o arquivo YAML/JSON e retorna um dicionário Python com a instrução deserializada. Não valida — apenas parseia.

- **instruction_validator** — Módulo que valida o dicionário Python contra o JSON Schema. Lança `ValidationError` com caminho do campo inválido se a instrução não for conformante.

- **file_locator** — Módulo que resolve o caminho final de cada arquivo (combinando `root_path` com `relative_path` ou usando `absolute_path` diretamente) e verifica existência. Aplica a **guarda de contenção** no modo relativo (o caminho resolvido não pode escapar da pasta raiz) e aceita a inexistência do arquivo quando todas as suas modificações são de criação.

- **backup_manager** — Módulo que cria cópia timestampada (`backups/<YYYYMMDD_HHMMSS>/`) de todos os arquivos listados na instrução antes de qualquer escrita. Restaura sob demanda.

- **diff_renderer** — Módulo que gera unified diff legível entre conteúdo original e conteúdo resultante de cada arquivo. Usado para prévia na GUI e output no CLI.

- **BaseStrategy** — Classe abstrata (ABC) que define a interface comum a toda strategy: um único método `apply(source, modification) -> str` que **localiza e aplica** a modificação num passo (DEC-009). Pode, opcionalmente, retornar `(str, list[str])` para emitir avisos não-fatais (DEC-028; normalizado por `split_apply_result`). Importada pelo `patch_engine` via registry para seleção dinâmica. *(Nota: a separação conceitual `find_location()`/`apply()` da F0 foi unificada em `apply()`; a pré-checagem de confiança da GUI virá do dry-run por modificação.)*

- **python_strategy** — Strategy para arquivos `.py` usando `libcst`. Suporta: `replace_function`, `replace_method`, `replace_class`.

- **text_strategy** — Strategy para `.txt`, `.md` e `.py` (operações textuais genéricas). Suporta: `insert_after_pattern`, `insert_before_pattern`, `replace_context_block`, `replace_line_pattern`, `replace_section`.

- **json_strategy** — Strategy para `.json` com navegador de caminho próprio (caminhos pontilhados `a.b[0].c`; distingue `null` de chave ausente — FIX-005; preserva o estilo de serialização do original — FIX-004). Suporta: `set_json_path`, `append_json_array`, `delete_json_path`.

- **file_strategy** — Strategy de arquivo inteiro (DEC-008), independente de tipo. Suporta: `create_file` (cria arquivo novo a partir de `content`) e `replace_file` (substitui todo o conteúdo por `new_content`). Não usa `location`.

---

## Comandos / artefatos

- **`instruction_v1.schema.json`** — JSON Schema (rascunho 7) que define a estrutura obrigatória e opcional do arquivo de instrução v1.x. Fonte de verdade do contrato entre a IA geradora e a ferramenta.

- **`backups/<YYYYMMDD_HHMMSS>/`** — Diretório criado pelo `backup_manager` antes de cada aplicação. Contém cópia dos arquivos afetados com estrutura de pastas preservada **relativa à raiz** (FIX-008) + um `manifest.txt`.

- **`manifest.txt`** — Arquivo dentro de cada pasta de backup, formato `estado<TAB>caminho_original<TAB>caminho_espelho` (espelho vazio para arquivos criados). É a FONTE para o `rollback` (lido por `rollback_session`). Aceita também o formato antigo `[estado] caminho` por retrocompatibilidade.

- **`backups/history.log`** — (DEC-018) Arquivo append-only, um por pasta de backups, com uma linha por aplicação: `timestamp<TAB>N modificado(s), N criado(s)  descrição`. Leitura humana cronológica; complementar ao manifesto (não substitui, não é fonte de rollback).

- **`--backup-dir PASTA`** — (DEC-018) Flag do `apply`/`rollback` que define ONDE criar a pasta `backups/`. Exposto na GUI no campo "Backup:" (DEC-024). Quando aponta para fora da raiz, o backup é aninhado por projeto: `<dir>/<nome-da-raiz>/<timestamp>/` (DEC-024b). **Padrão (sem flag): a pasta-PAI da raiz — `parent(root)/backups/<ts>/` — DEC-024c, implementado em 0.8.1; mantém o repositório limpo. O `rollback` sem flag procura no mesmo lugar.**

- **`launcher.py` (gui)** — Módulo PURO (sem Qt), testável isoladamente, com as funções dos atalhos `.bat`: `resolve_instruction_in_dir` (escaneia só o TOPO de uma pasta atrás de YAMLs → `one`/`none`/`many`, ignorando subpastas), `build_launcher_bat` (gera o `.bat` por projeto: python do venv direto, `--root` relativo/absoluto, `--instruction-dir "%~dp0."`, `chcp 65001`+UTF-8 quando algum caminho tem acento) e `build_open_gui_bat` (gera o `.bat` clássico "abrir GUI": `pythonw`+`start "" /d`, sem console). DEC-022/023.

- **`rollback_from_dir(session_dir)`** — (DEC-024) Função do `backup_manager` que reverte a partir do CAMINHO COMPLETO de uma pasta de sessão de backup (lê o `manifest.txt` dela). `rollback_session(timestamp)` delega a ela. Faz o desfazer funcionar igual para backup interno (`root/backups/<ts>`) e externo (`<dir>/<projeto>/<ts>`); a GUI guarda `(pai_do_session_dir, ts)` em `_last_backup`.

- **`_sanitize_name`** — (DEC-024) Helper do `patch_engine` que transforma o basename da raiz num nome de pasta Windows válido, usado como `<project_name>` no aninhamento do backup externo.

- **Sandbox / `*_sandbox_<timestamp>/`** — (DEC-015/019) Cópia irmã do projeto criada por `apply --sandbox` (CLI) ou pelo checkbox da GUI, via `patch_engine.make_sandbox`. A instrução é aplicada na cópia; o original não é tocado. Ignora `.git`, `node_modules`, venvs, `backups/`, caches (`SANDBOX_IGNORES`).

- **`self-test`** — Subcomando do CLI (`python -m src self-test`) que aplica a demo embutida num tempdir, confere resultados-chave e reverte. Verificação de instalação que não toca o disco do usuário.

- **`applied_instructions.json`** — (F3, NÃO implementado) Log de auditoria mais rico de instruções aplicadas. Hoje o papel de histórico é parcialmente coberto pelo `history.log`.

---

- **WO (work order)** — Instrução de APLICAÇÃO que o chat autora e o Code posiciona: âncora semântica + texto exato. Vive em `meta/workorders/AAMMDD-woNNNN-desc.md`; aplica-se com `/apply-wo`. Diz **como aplicar**. Até 2026-07-30 chamava-se «spec» neste repo (DEC-033).

- **Spec de feature** — Documento do Spec-Driven Development que diz **o que** construir e **quando está pronto**: problema, critérios de aceite verificáveis, decisões de design, fora de escopo. Modelo em `meta/SPEC.md`, uma por feature em `meta/specs/`. Não é a WO.

- **Análise** — Documento que precede o compromisso numa mudança não-trivial: problema, restrições medidas, opções (inclusive as descartadas), recomendação, riscos, ponto de decisão. Vive em `meta/analises/AAMMDD-ANALISE-<tema>.md`; a pasta nasce no primeiro uso. Gatilho concreto: mudar o formato de um artefato que outra pessoa vai ler ou editar, mesmo com diff pequeno.

## Identificadores

- **DEC-N** — Decisão de arquitetura documentada em DECISIONS.md (ex: DEC-001).
- **FIX-N** — Bug grave documentado em DECISIONS.md (ex: FIX-001).
- **F0, F1, F2…** — Fases do roadmap em ROADMAP.md.
- **strategy** — Campo na modification que identifica qual algoritmo usar (ex: `"replace_function"`, `"set_json_path"`).
- **ASU** — Abreviação informal do projeto (Atualizador Automático de Scripts; pacote: `asu` ou `auto-script-updater`).
- **`backup_location` × `root_path`** — Parâmetros distintos de `apply_instruction`: `root_path` é a base dos caminhos relativos (e encurta o espelho — FIX-008); `backup_location` é só onde a pasta `backups/` mora (DEC-018). Por padrão são iguais.
- **`_MISSING`** — Sentinela do `json_strategy._walk` que distingue "chave ausente" de "valor `null`" (FIX-005), permitindo deletar chaves nulas.
- **`SandboxError`** — Exceção do core levantada por `make_sandbox` quando a instrução tem `path_mode=absolute` (que escaparia da cópia). O CLI a traduz em stderr + exit 2; a GUI mostra um diálogo.

- **Warning / aviso não-fatal** — (DEC-028) Terceiro estado de uma modificação, entre sucesso e erro: **aplicou, mas com uma ressalva** que o usuário deve ver (ex.: `create_file` sobrescrevendo um arquivo existente). Não aborta, não reverte, não altera `report.ok`. Carregado por `ModificationResult.warnings`; a presença agregada é derivada por `FileResult.has_warnings`/`ApplyReport.has_warnings`. Na GUI aparece como 🟡 (arquivo) / ⚠ (modificação) com o texto no tooltip.

- **`split_apply_result`** — (DEC-028) Helper de `base_strategy` que normaliza o retorno de `apply()`: aceita `str` (sem avisos, como antes) OU `(str, list[str])` (com avisos) e sempre devolve `(texto, avisos)`. Torna o canal de warnings retrocompatível — as 13 estratégias que não avisam seguem retornando `str` puro.
