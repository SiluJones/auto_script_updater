# GLOSSARY.md — Termos do Projeto

> Termos próprios do projeto que o assistente reexplicaria a cada sessão sem este arquivo.

---

## Conceitos do projeto

- **Arquivo de instrução** — Arquivo `.yaml` (ou `.json`) gerado por IA que descreve quais arquivos modificar e como. Entrada principal da ferramenta. Segue o schema `instruction_v1.schema.json`.

- **Modification / modificação** — Uma operação atômica de modificação em um arquivo específico: localiza o ponto correto e aplica o novo conteúdo. Cada arquivo da instrução pode ter N modificações.

- **Strategy / estratégia de modificação** — Algoritmo que sabe como localizar e aplicar uma modificação em um tipo específico de arquivo. Implementada como subclasse de `BaseStrategy`. Ex: `replace_function`, `set_json_path`.

- **Localizador** — Identificador usado pela strategy para encontrar o ponto exato de modificação no arquivo (ex: nome de função, texto do heading, regex, janela de contexto). Nunca é número de linha absoluto.

- **Janela de contexto** — Técnica de localização que usa N linhas únicas antes e depois do ponto alvo para encontrá-lo sem depender de número de linha. Inspirada no formato unified diff (usado pelo git, OpenAI Codex).

- **Dry run** — Execução simulada: toda a lógica de localização e patch roda, mas nenhum arquivo é escrito em disco. Retorna o mesmo resultado que a execução real mostraria.

- **Rollback** — Restauração de todos os arquivos afetados ao estado anterior à aplicação, a partir do backup criado pelo `backup_manager` antes da execução.

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

- **file_locator** — Módulo que resolve o caminho final de cada arquivo (combinando `root_path` com `relative_path` ou usando `absolute_path` diretamente) e verifica existência e permissões.

- **backup_manager** — Módulo que cria cópia timestampada (`backups/<YYYYMMDD_HHMMSS>/`) de todos os arquivos listados na instrução antes de qualquer escrita. Restaura sob demanda.

- **diff_renderer** — Módulo que gera unified diff legível entre conteúdo original e conteúdo resultante de cada arquivo. Usado para prévia na GUI e output no CLI.

- **BaseStrategy** — Classe abstrata (ABC) que define a interface comum a toda strategy: `find_location()` e `apply()`. Importada pelo `patch_engine` para seleção dinâmica.

- **python_strategy** — Strategy para arquivos `.py` usando `libcst`. Suporta: `replace_function`, `replace_method`, `replace_class`.

- **text_strategy** — Strategy para `.txt`, `.md` e `.py` (operações textuais genéricas). Suporta: `insert_after_pattern`, `insert_before_pattern`, `replace_context_block`, `replace_line_pattern`, `replace_section`.

- **json_strategy** — Strategy para `.json` usando `jmespath` para navegação. Suporta: `set_json_path`, `append_json_array`, `delete_json_path`.

---

## Comandos / artefatos

- **`instruction_v1.schema.json`** — JSON Schema (rascunho 7) que define a estrutura obrigatória e opcional do arquivo de instrução v1.x. Fonte de verdade do contrato entre a IA geradora e a ferramenta.

- **`backups/<YYYYMMDD_HHMMSS>/`** — Diretório criado pelo `backup_manager` antes de cada aplicação. Contém cópia dos arquivos afetados com estrutura de pastas preservada.

- **`applied_instructions.json`** — (F3) Log de auditoria de instruções aplicadas: caminho, data/hora, arquivos afetados, resultado.

---

## Identificadores

- **DEC-N** — Decisão de arquitetura documentada em DECISIONS.md (ex: DEC-001).
- **FIX-N** — Bug grave documentado em DECISIONS.md (ex: FIX-001).
- **F0, F1, F2…** — Fases do roadmap em ROADMAP.md.
- **strategy** — Campo na modification que identifica qual algoritmo usar (ex: `"replace_function"`, `"set_json_path"`).
- **ASU** — Abreviação informal do projeto: **A**utualizador de **S**cripts **U**niversal (pode virar nome de pacote: `asu` ou `auto-script-updater`).
