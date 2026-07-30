---
name: wrap
description: Encerra a tarefa no repo do ASU — validação, append em STATUS/DECISIONS/ROADMAP, git diff e comando de commit. Use quando o usuário pedir /wrap ou para fechar a sessão de trabalho.
disable-model-invocation: true
---
Encerre a tarefa:

- Se a tarefa tocou CÓDIGO, rode a validação (`python -m pytest`, e `python -m src self-test` quando fizer sentido; `ruff check .` e `black --check .`) e só siga se passar.
- Atualize `meta/STATUS.md` (append, não reescreva).
- Acrescente `DEC-`/`FIX-` em `meta/DECISIONS.md` se houve decisão de arquitetura ou bug grave.
- Marque estado de fase em `meta/ROADMAP.md` se uma fase mudou.
- Se o ciclo tinha uma WO com **Canal dos meta = CHAT**, NÃO faça esses appends: diga que o registro vem do chat.

Depois, me mostre o `git diff` e o comando de commit (uma linha por comando, mensagem SEM acento).

Feche com o RELATÓRIO de execução: o que foi feito, achados e desvios do que a tarefa pedia, arquivos tocados, resultado da validação e o commit.
