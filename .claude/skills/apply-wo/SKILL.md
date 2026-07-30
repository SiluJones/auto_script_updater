---
name: apply-wo
description: Aplica uma WO de meta/workorders/ ao repo do ASU — localiza cada âncora exatamente, substitui, e para se não achar. Use quando o usuário pedir /apply-wo ou para aplicar uma WO nomeada.
disable-model-invocation: true
---
Leia o arquivo de WO indicado em `meta/workorders/` e execute-o.

Localize cada âncora EXATAMENTE (seção/título/símbolo de código, nunca nº de linha); se não achar uma, **PARE e reporte** — não chute um lugar próximo. Antes de cada inserção, procure a frase-chave do texto NOVO: se já existir, PULE o item e diga no relatório (idempotência) — não duplique.

Respeite o campo **Canal dos meta neste ciclo** do cabeçalho da WO: se for CHAT, não faça append nos `meta/` (o chat entrega os documentos depois); se for CODE, a WO é o registro.

Não toque em nada fora das edições nomeadas.

Antes de commitar:
- `git diff` mostra exatamente os arquivos previstos, e nada além.
- WO que toca CÓDIGO: `python -m pytest`, `python -m src self-test`, `ruff check .` e `black --check .` limpos. Se acusar erro, PARE e reporte antes de commitar.
- WO só de doc: não precisa de build — a rede é o `git diff`.

Ao terminar, RELATE: o que foi feito, o que fugiu do texto literal da WO, arquivos tocados, resultado da validação e o commit. Não substitua este relatório pelo bloco de fecho do chat.

WO: $ARGUMENTS
