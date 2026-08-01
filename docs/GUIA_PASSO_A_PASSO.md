# Guia passo a passo — ASU (Atualizador Automático de Scripts)

> Guia de USO para o dia a dia, em linguagem simples. Para a referência técnica
> do formato de instrução (voltada à IA que gera o YAML), veja
> `docs/INSTRUCTION_GUIDE.md`. Para visão/arquitetura, `meta/CONTEXT.md`.

## O que o ASU faz (em uma frase)

A IA gera um **arquivo de instrução** (YAML) descrevendo as mudanças; você abre
esse arquivo no ASU, **confere o diff** e **aplica** — com backup e desfazer
automáticos. Sem copiar e colar trechos à mão.

---

## 1. Preparar o ambiente (uma vez)

Na pasta do ASU, com o Prompt de Comando (CMD):

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-gui.txt
```

Confirme que está tudo são:

```
python -m src self-test
```

Se aparecer "self-test OK", a instalação está funcionando (esse comando aplica
uma demo num diretório temporário e reverte — não toca no seu disco).

---

## 2. Onde deixar o arquivo de instrução (evite esta confusão)

A dúvida mais comum: **onde salvar o `instrucao.yaml`?** A resposta que evita
dor de cabeça:

- **O nome e o local do arquivo de instrução NÃO precisam ser fixos.** O que
  importa é o `--root` (a raiz do projeto que será modificado). O arquivo de
  instrução pode ficar em qualquer pasta.
- **Vários arquivos com o mesmo nome, em pastas diferentes, NÃO dão problema** —
  cada um é aberto individualmente. O que os diferencia é para qual `--root`
  você aponta na hora de aplicar.
- Recomendação prática: deixe cada instrução numa pasta **ao lado** (fora) da
  raiz do projeto — assim ela não polui o repositório. A GUI e o atalho `.bat`
  sabem procurar a instrução na pasta que você indicar.

> Regra de ouro: a instrução diz **o que mudar**; o `--root` diz **em qual
> projeto**. Mantê-los separados é o que dá flexibilidade.

---

## 3. Usando pela interface gráfica (recomendado)

Abra a GUI:

```
python -m src.gui
```

Fluxo:
1. **Raiz:** aponte para a pasta do projeto que será modificado. Use o menu
   **Recentes ▾** para reabrir projetos usados antes, ou o **📌** para fixar os
   favoritos.
2. **Instrução:** aponte para o `.yaml` que a IA gerou — ou clique **Colar
   instrução** para colar o YAML direto do chat, sem salvar arquivo.
3. **Pré-visualizar (dry-run):** mostra a árvore de arquivos com 🟢 (ok) / 🔴
   (falha) / ⚪ (inalterado), cada modificação com ✓/✗, e o **diff colorido**.
   Nada é escrito ainda. **Sempre revise aqui antes de aplicar.**
   - Se você instalou as dependências de GUI, o diff vem com **realce de
     sintaxe** (a linguagem é deduzida do nome do arquivo): as linhas
     adicionadas e removidas ganham **fundo** verde/vermelho claro, e as cores do
     texto passam a ser as da sintaxe. Em arquivo de extensão desconhecida, cai
     no realce simples de antes — nada quebra.
   - Um arquivo pode aparecer como 🟡 (**aplicado com ressalva**) — deu certo,
     mas com um aviso a conferir (ex.: um `create_file` que vai **sobrescrever**
     um arquivo já existente). Passe o mouse sobre o item para ler o aviso no
     tooltip. A ressalva **não bloqueia** o Aplicar.
4. **Aplicar:** cria o backup e escreve as mudanças. Se algo falhar no meio,
   tudo é revertido automaticamente (atômico).
5. **Desfazer última aplicação:** reverte a última aplicação pelo backup.

Se a prévia mostrar erro, clique **Copiar erro para a IA** e cole o bloco no
chat — a IA corrige a instrução e você tenta de novo.

Para guardar ou compartilhar o resultado inteiro, use **Copiar saída**: ela copia
o relatório **completo** da última prévia/aplicação (todos os arquivos, status,
avisos 🟡 e diffs), tanto quando deu certo quanto quando falhou. Diferente do
"Copiar erro para a IA" (que só aparece em falha), o "Copiar saída" funciona nos
dois casos — bom para colar num chat, anexar num relato ou manter registro.

### Atalhos .bat — dois tipos, para dois usos

**Criar atalho .bat…** gera um atalho **por projeto**: reabre a GUI já apontada
para aquela raiz e aquela pasta de instrução. Guarde-o ao lado do projeto.

**Criar atalho .bat (abrir GUI)…** gera o atalho **genérico**, sem console. A
ideia é copiá-lo para a pasta onde você guarda seus projetos (ou para a Área de
Trabalho). Duas coisas que ele faz por você:

- **Começa limpo.** Aberto por esse atalho, a GUI **não** restaura a raiz do
  projeto anterior — se você copiou o `.bat` para uma pasta nova, ela não chega
  trazendo o projeto de ontem. O menu **Recentes ▾** continua disponível para
  retomar o que quiser.
- **Abre no lugar certo.** O "Escolher..." abre **na pasta onde o `.bat` está**,
  que normalmente é onde os projetos moram — não no último caminho usado.

Abrindo a GUI na mão (`python -m src.gui`), o comportamento é o de sempre: a
última raiz e a última instrução são restauradas.

---

## 4. Usando pela linha de comando

```
python -m src validate MINHA_INSTRUCAO.yaml
python -m src apply MINHA_INSTRUCAO.yaml --root C:\meu_projeto --dry-run
python -m src apply MINHA_INSTRUCAO.yaml --root C:\meu_projeto
python -m src rollback <TIMESTAMP> --root C:\meu_projeto
```

O `--dry-run` é o teste seguro (não escreve). O `apply` sem `--dry-run` aplica
de verdade, pedindo confirmação, e imprime o caminho do backup ao final — copie
o `<TIMESTAMP>` de lá para um eventual `rollback`.

A saída marca com `~` cada arquivo aplicado **com ressalva** e conta esses casos
no resumo (`N com ressalva`), com uma linha de atenção no fim — a mesma
informação que a GUI mostra como 🟡, para você não perder o aviso na linha de
comando.

---

## 5. Backup: onde fica, como configurar, como desligar

- **Padrão:** o backup vai para a **pasta-pai** da raiz
  (`parent(raiz)\zz_backups\<timestamp>\`) — fora do projeto, para não sujar o
  repositório; o prefixo `zz_` empurra a pasta para o fim da listagem, longe do
  que você usa. O destino é **derivado da raiz**: trocou a raiz, trocou o
  destino. O `rollback` procura nesse mesmo lugar automaticamente — e também na
  pasta `backups\` das versões anteriores, então backups antigos continuam
  restauráveis.
- **Escolher outro lugar:** use `--backup-dir PASTA` (no CLI) ou o campo
  **Backup:** (na GUI). Bom para mandar todos os backups para uma pasta central.
  Na GUI, deixe o campo **vazio** para usar o padrão: o texto acinzentado mostra
  exatamente para onde o backup vai, e muda sozinho quando você troca a raiz.
  O que você digitar ali vale só para aquela sessão — o campo não é memorizado
  entre aberturas, justamente para não "grudar" num caminho antigo.
  Quando o backup é externo e você tem vários projetos, o ASU aninha por nome do
  projeto (`PASTA\<nome-do-projeto>\<timestamp>\`) para não misturar. Nesse caso,
  repita o mesmo `--backup-dir` no `rollback`.
- **Histórico rápido:** dentro da pasta de backups há um `history.log` — uma
  linha por aplicação (data, nº de arquivos, **qual instrução gerou aquela
  leva**, descrição) **e também uma linha quando você faz o Desfazer/rollback
  manual**, para acompanhar o histórico sem abrir cada pasta de timestamp. O
  nome da instrução é o que resolve a dúvida real na hora de desfazer: com dois
  ou três `.yaml` aplicados no mesmo dia, é ele que diz qual timestamp é o que
  você quer. Dentro de cada pasta de sessão, o `manifest.txt` repete a origem na
  primeira linha. Instrução colada da área de transferência aparece como
  `(colado da área de transferência)`.
- **Não gerar backup:** existe `--no-backup`, mas **não é recomendado** — sem
  backup, o desfazer automático não tem de onde restaurar. Prefira deixar o
  backup ligado e, se quiser, limpar as pastas antigas manualmente.

---

## 6. Modo seguro para os primeiros usos

Enquanto ganha confiança, aplique numa **cópia**:

```
python -m src apply instrucao.yaml --root C:\meu_projeto --sandbox
```

O ASU duplica a raiz numa pasta irmã, aplica **na cópia** e imprime o caminho —
o original não é tocado. Revise a cópia, aproveite o que aprovar e apague a
pasta. (Na GUI, marque **Aplicar em sandbox (cópia)**.)

Se você usa Git, um fluxo equivalente e ainda mais prático:

```
git add -A & git commit -m "antes do ASU"
python -m src apply instrucao.yaml --root .
git diff
git restore .
```

---

## 7. Ensinando a IA a gerar instruções corretas

Para que a IA acerte a instrução de primeira, em qualquer projeto seu:

1. suba o `docs/INSTRUCTION_GUIDE.md` ao conhecimento do projeto (ou cole na base
   de conhecimento) — em vez de colar o conteúdo em toda conversa, você
   referencia o arquivo; atualizar é só trocar o arquivo;
2. cole o bloco de `docs/PROMPT_IA.md` nas instruções do projeto;
3. peça: *"emita uma instrução ASU para estas mudanças"*.

O guia já traz as regras que evitam os erros clássicos e um checklist de
autovalidação. Se a aplicação falhar, o bloco de "Copiar erro para a IA" fecha o
ciclo: a IA lê o erro, corrige a instrução, você reaplica.

> Dica do validador: se a IA gerar um `replace_context_block` com uma âncora
> **vazia** (por o trecho tocar o começo ou o fim do arquivo), o ASU já avisa e
> sugere estratégias melhores para aquele caso (`replace_line_pattern`,
> `insert_before_pattern`, `replace_section` ou `replace_function`).

---

## 8. Perguntas rápidas

- **"O que é o 🟡 (ressalva)?"** É o meio-termo entre 🟢 (ok) e 🔴 (falha): a
  mudança foi aplicada, mas com um aviso a conferir — hoje o caso típico é um
  `create_file` que sobrescreve um arquivo que já existia. A ressalva não bloqueia
  nem reverte nada; é só um alerta para você olhar o tooltip.
- **"Posso repetir a mesma instrução?"** Sim — `create_file` sobre arquivo
  existente vira sobrescrita com backup (e sinaliza 🟡); e se a mudança já foi
  aplicada, a âncora não casa e o ASU avisa (inclusive com a dica "provavelmente
  já foi aplicada"). Nada é aplicado no lugar errado em silêncio.
- **"E se eu mudar a pasta raiz entre aplicar e desfazer?"** O desfazer usa a
  raiz **capturada no momento da aplicação**, não a do campo — então não quebra.
- **"Dá para criar um arquivo novo com o ASU?"** Dá (`create_file`), mas para um
  arquivo novo isolado costuma ser mais simples pedir o arquivo pronto para
  baixar. O ASU compensa mesmo é **editando** arquivos existentes.
- **"Abri pelo atalho e a raiz veio vazia — perdi meus projetos?"** Não. O
  atalho "abrir GUI" começa limpo de propósito, para não trazer o projeto
  anterior quando você o copia para uma pasta nova. Clique em **Recentes ▾**:
  seus projetos estão todos lá.
- **"Meus backups antigos ficaram em `backups\`. Ainda dá para desfazer?"** Dá.
  A pasta padrão passou a ser `zz_backups\`, mas o rollback continua lendo o
  layout antigo. Nada do que já existe precisa ser movido.
