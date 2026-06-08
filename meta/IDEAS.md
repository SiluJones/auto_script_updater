# IDEAS.md — Brainstorm e Visão

> **Segundo cérebro** do projeto. Captura TUDO que for mencionado, mesmo solto ou no meio de outro assunto.
> Nunca perde: ideia implementada → «Concluídas»; recusada → «Descartadas» com motivo.

---

## 💡 Ideias Ativas — Usuário

### 2026-06 — Ferramenta desktop de aplicação de instruções de IA
Ferramenta que lê arquivo de instrução gerado pela IA e aplica modificações a scripts e documentos do projeto automaticamente, com prévia e rollback. Núcleo do projeto.

### 2026-06 — Interface gráfica (não só CLI)
A ferramenta deve ter GUI para não exigir terminal. Usuário seleciona o arquivo de instrução e a pasta raiz visualmente, confere o diff, e aplica com um clique.

### 2026-06 — Suporte a múltiplos tipos de arquivo
Além de `.py`: `.md`, `.json`, `.txt` — e possivelmente mais no futuro.

### 2026-06 — Pasta raiz selecionável na GUI
Para caminhos relativos na instrução: usuário define a pasta raiz do projeto na interface; a ferramenta resolve `root + relative_path`.

### 2026-06 — Prévia de diff antes de aplicar
Mostrar o que vai mudar (antes/depois colorido) antes de qualquer escrita em disco. Usuário vê exatamente o que será modificado.

### 2026-06 — Schema / molde de instrução para a IA seguir
A ferramenta deve ter um formato de instrução bem definido que a IA aprende a gerar corretamente. O prompt padrão faz parte do produto.

---

## 🤖 Ideias Ativas — Assistente

### 2026-06-03 — Modo dry run / simulação
Executar toda a lógica de localização e patch sem escrever nada em disco. Mostrar o resultado completo como se tivesse aplicado. Útil para validar instruções antes de usar em produção. Já planejado no schema (`dry_run: true`) e na GUI (checkbox).

### 2026-06-03 — Validação de unicidade do localizador pré-execução
Antes de qualquer escrita, verificar que cada localizador (regex, nome de função, heading) casa exatamente uma vez no arquivo alvo. Se casar zero ou mais de uma, bloquear e reportar com detalhes (qual arquivo, qual modification id, quantas ocorrências encontradas).

### 2026-06-03 — Indicador de confiança por modificação na GUI
Durante a fase de validação, exibir um ícone de status para cada modificação: 🟢 localizador único e arquivo encontrado; 🟡 aviso (ex: arquivo encontrado mas regex é ambíguo); 🔴 erro (arquivo não encontrado, localizador inválido). Usuário não aplica sem ver todos os itens verdes.

### 2026-06-03 — Modo transação com rollback automático em falha
Se `stop_on_error: true` e qualquer modificação falhar, reverter AUTOMATICAMENTE todas as modificações já aplicadas na sessão usando o backup. Garante que o projeto nunca fica em estado parcialmente modificado. Crítico para instruções com 10+ modificações.

### 2026-06-03 — Leitura de instrução direto da área de transferência
Botão "Colar instrução" que lê YAML diretamente da clipboard. Útil quando a IA gerou a instrução no chat e o usuário não quer salvar em arquivo separado — reduz fricção do fluxo principal.

### 2026-06-03 — Gerador de prompt de instrução embutido
Painel dentro da GUI com o prompt padrão que o usuário deve dar para a IA gerar um arquivo de instrução válido. Botão "Copiar prompt" para colar no chat. Elimina a necessidade de o usuário lembrar o formato.

### 2026-06-03 — Histórico de instruções aplicadas
Arquivo `applied_instructions.json` que registra: caminho do arquivo de instrução, data/hora, lista de arquivos afetados, resultado (sucesso/erro parcial). Permite auditoria futura sem precisar abrir logs individuais.

### 2026-06-03 — Checksum SHA-256 dos arquivos antes/depois
Calcular e registrar hash SHA-256 de cada arquivo afetado antes e depois da aplicação. Serve para: (1) detectar modificações externas concorrentes (arquivo mudou desde que a instrução foi gerada); (2) auditoria de integridade no log.

### 2026-06-03 — Suporte a `.env` como tipo de arquivo futuro
Modificar variáveis em arquivos `.env` por nome de variável (ex: `DATABASE_URL=nova_url`). Mais seguro do que regex genérico em arquivos de configuração. Entra como nova strategy em F4.

### 2026-06-03 — Suporte a `.sql` como tipo de arquivo futuro
Inserção de instruções SQL por marcador de comentário (ex: `-- PATCH_ANCHOR: migration_001`). Viável com a text_strategy + padrão de anchor comment. F4 ou além.

### 2026-06-03 — Extensão VS Code usando o core Python sem GUI
Empacotar o `src/core/` + `src/strategies/` como biblioteca Python pura (sem dependência de PySide6) e disponibilizar como extensão VS Code. O editor lê a instrução e aplica diretamente no workspace aberto. Reutiliza toda a lógica de modificação. Viável em F4.

### 2026-06-03 — Templates de prompt para diferentes IAs
Fornecer templates de prompt para Claude, GPT-4o, Gemini com as nuances de como cada modelo melhor gera o YAML de instrução (ex: Claude precisa de `<format>` tags; GPT prefere JSON Schema embutido no prompt). Documentação do produto, não código.

### 2026-06-03 — Modo comparação acumulada pós-aplicação
Após aplicar todas as modificações, mostrar numa única tela um diff acumulado de TODOS os arquivos modificados. Permite revisão rápida do resultado antes de fechar a ferramenta.

### 2026-06-03 — Suporte ao formato apply_patch do OpenAI/Codex como entrada alternativa
O formato `*** Begin Patch / *** End Patch` (usado por Codex, GPT-5.1, opencode) usa context-based patching similar ao nosso. Poderia ser aceito como formato alternativo de instrução (além do YAML estruturado). Útil se o usuário já usa ferramentas que emitem esse formato. Existe biblioteca Python `apply-patch-py` que já implementa o parser. Baixa prioridade (F3/F4), mas vale registrar.

### 2026-06-03 — Anchor comments opcionais no código-alvo
Modo opcional onde o usuário insere comentários especiais no código (`# ASU_ANCHOR: feature_login`) que servem como marcadores de localização ultra-estáveis. A IA referencia o anchor pelo nome; a ferramenta localiza por busca de string exata. Complementa as estratégias existentes para casos onde o código é muito dinâmico.

### 2026-06-03 — CLI funcional sem GUI (F1)
`python -m src instrucao.yaml --root C:\meu_projeto [--dry-run]` — aplicar modificações via linha de comando sem abrir a GUI. Útil para integração em scripts e automação. Planejado em F1 antes de construir a GUI em F2.

---

## ✅ Concluídas
*(nenhuma ainda — projeto em fase inicial)*

---

## 🚫 Descartadas
- **Localização por número de linha absoluto** — frágil após modificações anteriores no mesmo arquivo; taxa de falha alta em instruções com múltiplas modificações → descartada em DEC-001.
- **ast stdlib para reescrita Python** — não preserva comentários e formatação ao serializar via `ast.unparse()` → descartada em DEC-003.
- **Tkinter como GUI** — aparência datada no Windows; widgets insuficientes para diff colorido → descartada em DEC-005.
- **PyQt6 como GUI** — API idêntica ao PySide6, mas licença GPL mais restritiva → descartada em DEC-005 em favor do PySide6 (LGPL).
- **Integração direta com API da IA** — criaria acoplamento a fornecedor específico e mudaria o escopo da ferramenta (ela consome instruções pré-geradas, não gera) → fora de escopo; pode ser reavaliada em F4+ como feature opcional.
