Encerre a tarefa:
- Se a tarefa tocou CÓDIGO, rode a validação (`python -m pytest`, e `python -m src self-test` quando fizer sentido; `ruff check .` e `black --check .`) e só siga se passar.
- Atualize `meta/STATUS.md` (append, não reescreva).
- Acrescente `DEC-`/`FIX-` em `meta/DECISIONS.md` se houve decisão de arquitetura ou bug grave.
- Marque estado de fase em `meta/ROADMAP.md` se uma fase mudou.
Depois, me mostre o `git diff` e o comando de commit (uma linha por comando, mensagem SEM acento).
