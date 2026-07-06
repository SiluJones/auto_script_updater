# HISTORY.md — Conhecimento Consolidado

> **Opcional.** Arquivo-baú para conhecimento denso que já foi aprendido e não muda mais — guias técnicos, análises de viabilidade, notas de migração — que tornariam o CONTEXT pesado demais.
> Não é lido no início da sessão; o assistente consulta sob demanda quando o assunto aparece.

---

## 1. Pesquisa: Por que número de linha falha em patches encadeados

**Contexto:** Sessão 2026-06-03. Motivação para DEC-001.

### O problema
Ao aplicar a modificação M1 que insere 3 linhas na linha 10, todas as modificações seguintes que referenciem linhas > 10 estão com números errados. Em instruções com 5+ modificações no mesmo arquivo, a taxa de falha é proporcional ao número de inserções precedentes.

### Confirmação da indústria
O OpenAI Codex e o GPT-5.1 `apply_patch` usam explicitamente **linhas de contexto** (código ao redor) para localizar hunks, não número de linha absoluto:

```
*** Begin Patch
*** Update File: src/app.py
@@ def greet():
-print("Hi")
+print("Hello, world!")
*** End Patch
```

O `@@` marca o contexto semântico (nome de função/classe); o ` ` (espaço) antes da linha é contexto de localização; `-` é linha a remover, `+` é linha a adicionar. Se o código ao redor for suficientemente único, o patch localiza corretamente mesmo sem linha.

A biblioteca Python `apply-patch-py` (port do Codex em Rust para Python) implementa progressive fallback: tenta matching estrito, depois relaxa normalização de espaços e por fim usa "anchor line fallback". Isso mostra que até o contexto pode ser impreciso — o sistema precisa ser robusto a pequenas variações.

### Nossa estratégia hierárquica (DEC-001)
1. **Semântico primeiro:** nome de função/classe (libcst), heading de seção, caminho JSON — imunes a mudanças de linha.
2. **Janela de contexto:** N linhas únicas antes + N depois — robusto para código que não tem estrutura semântica nomeada.
3. **Pattern regex único:** para inserções pontuais (ex: após `import os`) — frágil se o pattern não for único, então validamos unicidade.
4. **Número de linha:** nunca como localizador primário; aceito apenas como referência humana no `description` de uma modification.

---

## 2. Pesquisa: libcst vs ast para modificação Python

**Contexto:** Sessão 2026-06-03. Motivação para DEC-003.

### ast stdlib
- Parseia Python em AST (Abstract Syntax Tree).
- `ast.unparse()` (Python 3.9+) converte AST de volta para código.
- **Problema crítico:** `ast.unparse()` normaliza: remove todos os comentários, altera espaçamento, pode trocar aspas. O arquivo resultante parece reformatado por outra ferramenta.
- Adequado para análise, não para escrita.

### libcst (Meta/Instagram)
- **Versão atual:** 1.8.6 (novembro 2025, ativa).
- **Suporte:** Python 3.0–3.14.
- **Licença:** MIT.
- Concrete Syntax Tree: preserva TODOS os tokens (comentários, espaços, parênteses, aspas, vírgulas).
- Ao substituir um nó, apenas aquele nó muda; o resto do arquivo é preservado bit a bit.
- Padrão `CSTTransformer` para modificações; `Matcher` para buscas.
- Usado em produção na Meta, Instawork, SeatGeek, Carta (1.8M+ linhas de código).
- 409 pacotes dependentes no PyPI.
- Parser nativo em Rust (rápido o suficiente para uso interativo).

### Conclusão (DEC-003)
- libcst para toda modificação estrutural Python.
- text_strategy (regex) para operações textuais simples em .py que não exigem parsear AST (ex: inserir import específico).

---

## 3. Pesquisa: Stack GUI Python para Windows em 2025/2026

**Contexto:** Sessão 2026-06-03. Motivação para DEC-005.

| Framework | Aparência Windows | Widgets ricos | Licença | Exe aprox. | Maturidade |
|---|---|---|---|---|---|
| Tkinter | Datada | Fraco | MIT (stdlib) | ~15 MB | Alta |
| PySide6 | Nativa Qt | Excelente | LGPL | ~80–100 MB | Alta |
| PyQt6 | Nativa Qt | Excelente | GPL | ~80–100 MB | Alta |
| Flet | Flutter | Bom | Apache 2 | ~40 MB | Média |
| Dear PyGui | Dev/moderna | Bom | MIT | ~25 MB | Média |
| wxPython | Nativa OS | Bom | LGPL | ~30 MB | Alta |

### Por que PySide6 (DEC-005)
- `QSyntaxHighlighter`: essencial para diff colorido.
- `QTreeWidget`: árvore de arquivos com ícones de status.
- `QFileDialog`: seletor de pasta nativo do Windows.
- `QProgressBar`: progresso de aplicação.
- LGPL: sem restrição de distribuição (PyQt6 é GPL).
- Binding oficial Qt Company: mais futuro-seguro que PyQt6.
- Documentação Qt6 excelente; tutoriais abundantes em 2025.
- Artigo de referência (fevereiro 2026): "Which Python GUI library should you use in 2026?" — PySide6 é a recomendação primária para desktop profissional.

---

## 4. Pesquisa: YAML vs JSON vs TOML para arquivo de instrução

**Contexto:** Sessão 2026-06-03. Motivação para DEC-004.

### Requisitos críticos
1. Blocos de código Python/Markdown multiline legíveis (o `new_content` pode ter 50+ linhas).
2. Comentários (a IA pode explicar cada modificação no próprio arquivo).
3. Fácil de gerar corretamente por IA sem formatação errada.
4. Validável contra JSON Schema (após parse).

### Análise
- **YAML:** Bloco literal `|` mantém código intacto preservando indentação. Suporta comentários `#`. IA gera bem quando instruída. Após `yaml.safe_load()`, vira dict Python validável. **Escolhido.**
- **JSON:** Strings multiline exigem `\n` escapados — 50 linhas de Python ficam ilegíveis. Sem comentários nativos. Descartado como canônico (aceito como alternativa).
- **TOML:** Arrays de tabelas `[[files.modifications]]` ficam verbosos para hierarquia profunda. Sem ganho sobre YAML. Descartado.

### Armadilha YAML+Windows
Caminhos Windows (`C:\projetos\app`) em YAML precisam usar `\\` ou `/`:
```yaml
relative_path: "src\\auth\\login.py"   # correto
relative_path: "src\auth\login.py"      # ERRADO: \a e \l são escapes YAML
```
Isso deve estar no prompt padrão da IA.

---

## 5. Schema completo do arquivo de instrução YAML v1.0

**Contexto:** Sessão 2026-06-03. Referência para implementação do `instruction_v1.schema.json`.

```yaml
# Exemplo de instrução v1.0 com todos os campos documentados
format_version: "1.0"           # obrigatório — versão do schema
generated_by: "claude"          # opcional — qual IA gerou
generated_at: "2026-06-03T14:30:00"  # opcional — timestamp ISO 8601
description: "Adiciona logging ao módulo de autenticação"  # obrigatório
session_reference: "sess_20260603_auth"  # opcional — referência à sessão

settings:
  backup: true          # default: true  — criar backup antes de executar
  dry_run: false        # default: false — simular sem escrever
  stop_on_error: true   # default: true  — parar e reverter se houver erro
  encoding: "utf-8"     # default: utf-8 — encoding padrão para todos os arquivos

files:
  # ── Exemplo: arquivo Python com modificações estruturais ──────────────────
  - id: "f1"                         # obrigatório — identificador único
    path_mode: "relative"            # "relative" | "absolute"
    relative_path: "src\\auth\\login.py"  # usado quando path_mode = relative
    absolute_path: null              # usado quando path_mode = absolute
    type: "python"                   # "python" | "markdown" | "json" | "text"
    encoding: "utf-8"                # opcional — override do encoding global
    modifications:
      - id: "m1"
        description: "Adiciona import de logging após os imports existentes"
        strategy: "insert_after_pattern"
        location:
          type: "pattern"
          pattern: "^import os$"     # regex que casa a linha alvo
          occurrence: 1              # qual ocorrência usar (1-indexed)
        content: |
          import logging

          logger = logging.getLogger(__name__)

      - id: "m2"
        description: "Substitui função validate_token com versão que loga"
        strategy: "replace_function"
        location:
          type: "function_name"
          name: "validate_token"
          class_name: null           # preencher se o método estiver dentro de classe
        new_content: |
          def validate_token(token: str) -> bool:
              """Valida o token JWT e registra tentativas."""
              if not token:
                  logger.warning("Tentativa de validação com token vazio")
                  return False
              logger.debug("Validando token: %s...", token[:8])
              return True

      - id: "m3"
        description: "Substitui bloco por janela de contexto"
        strategy: "replace_context_block"
        location:
          type: "context"
          before: "def old_helper():"   # linhas únicas antes do bloco alvo
          after: "    return result"     # linhas únicas depois do bloco alvo
          occurrence: 1
        new_content: |
          def old_helper() -> str:
              """Helper atualizado."""
              return result

  # ── Exemplo: arquivo Markdown com substituição de seção ───────────────────
  - id: "f2"
    path_mode: "relative"
    relative_path: "README.md"
    type: "markdown"
    modifications:
      - id: "m1"
        description: "Atualiza seção de Configuração"
        strategy: "replace_section"
        location:
          type: "heading"
          heading: "## Configuração"   # texto exato do heading
          include_heading: true        # true = substitui heading + conteúdo
        new_content: |
          ## Configuração

          Configure as variáveis no `.env`:
          - `LOG_LEVEL`: nível de log (DEBUG, INFO, WARNING). Padrão: INFO.
          - `SECRET_KEY`: chave secreta da aplicação. Obrigatório.

  # ── Exemplo: arquivo JSON com operações por caminho ───────────────────────
  - id: "f3"
    path_mode: "absolute"
    absolute_path: "C:\\projetos\\meu_app\\config\\settings.json"
    type: "json"
    modifications:
      - id: "m1"
        description: "Atualiza versão da API"
        strategy: "set_json_path"
        location:
          path: "api.version"          # caminho jmespath
        value: "2.1.0"

      - id: "m2"
        description: "Adiciona feature flag de logging"
        strategy: "append_json_array"
        location:
          path: "features"             # caminho do array
        value:
          name: "enhanced_logging"
          enabled: false

      - id: "m3"
        description: "Remove chave obsoleta"
        strategy: "delete_json_path"
        location:
          path: "legacy.old_config"
```

---

## 6. Referências técnicas

- **libcst:** https://libcst.readthedocs.io/ | https://github.com/Instagram/LibCST
- **PySide6:** https://doc.qt.io/qtforpython-6/
- **jsonschema (Python):** https://python-jsonschema.readthedocs.io/
- **jmespath:** https://jmespath.org/ | `pip install jmespath`
- **PyYAML:** https://pyyaml.org/ | `pip install pyyaml`
- **PyInstaller:** https://pyinstaller.org/
- **apply-patch-py** (contexto/inspiração): https://pypi.org/project/apply-patch-py/
- **OpenAI apply_patch format** (referência para context patching): https://developers.openai.com/cookbook/examples/gpt4-1_prompting_guide
- **Keep a Changelog:** https://keepachangelog.com/pt-BR/
- **Unified diff format:** https://www.gnu.org/software/diffutils/manual/html_node/Unified-Format.html
