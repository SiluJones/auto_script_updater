# spec0010 — Backup volta a seguir a RAIZ: `zz_backups` na pasta-pai, campo não-persistente e QSettings isolado nos testes

> **Tipo:** fix (bug de endereçamento) + mudança de comportamento. **Autoria:** chat. **Execução:** Claude Code.
> **Âncoras são SEMÂNTICAS** — símbolo/atributo ou trecho literal único, **nunca número de linha**. Localize cada âncora EXATAMENTE; **se não achar uma, PARE e reporte**. Não toque em nada fora das edições nomeadas. Rode `git diff` antes de commitar.
> **Versão-alvo:** 0.9.0 (muda o nome da pasta padrão de backup — comportamento observável; inclui o `/wrap` no fim).

---

## Diagnóstico — DUAS causas somadas (não uma)

O usuário relatou que o backup "sai em lugar aleatório e fica nele para sempre, sem acompanhar a raiz". A investigação no código confirmou **duas causas independentes que se somam**:

**Causa 1 — o campo Backup da GUI é persistido e nunca re-derivado.**
`_save_last_paths` grava `last_backup_dir` no `QSettings` e `_restore_last_paths` o restaura na abertura. Como o engine só aplica o padrão (`parent(root)/backups/<ts>`) quando `backup_location is None` — e a GUI faz `backup_location = self.backup_edit.text().strip() or None` —, **qualquer valor salvo uma vez vence para sempre**, inclusive depois de trocar a raiz. Daí o "fica nele sempre sem mudar quando defino a raiz".

**Causa 2 — a suíte de testes escreve no `QSettings` REAL do usuário.**
`MainWindow` cria `QSettings("auto-script-updater", "gui")` (no Windows: registro do usuário) e o teste `test_save_and_restore_backup_dir` faz `win.backup_edit.setText(str(tmp_path / "meu_backup"))` seguido de `win._save_last_paths()`. **Isso grava um caminho temporário do pytest no perfil real.** É a explicação exata do print enviado pelo usuário, onde o campo Backup exibia:
`C:\Users\alexk\AppData\Local\Temp\pytest-of-alexk\pytest-22\test_save_and_restore_backup_d0\meu_backup`
— uma pasta de teste que já nem existe mais. Esse é o "aleatoriamente".

**Não havia bug no engine.** O padrão `parent(root)` (DEC-024c) está correto e funciona quando a GUI passa `None`. O defeito é de camada GUI + isolamento de teste.

## O que muda (comportamento desejado pelo usuário)

1. **Escolheu a raiz → o backup é derivado dela**, sempre: `parent(root)/zz_backups/<timestamp>/`.
2. **Nome da pasta:** `zz_backups`. O usuário sugeriu "zz backup" para ficar no fim da listagem; adoto o prefixo `zz` (mesma intenção) **sem espaço**, porque caminho com espaço é fonte recorrente de erro de aspas em CMD/`.bat` quando colado à mão. Trocar o nome depois é editar uma constante.
3. **O campo Backup deixa de ser persistido.** Vazio = derivado da raiz. Preenchido = override **daquela sessão**. O placeholder passa a MOSTRAR o destino calculado e a acompanhar a troca de raiz — o usuário vê onde vai cair antes de aplicar.
4. **Rollback continua achando backups antigos** em `backups/` (fallback), para não quebrar o que já existe em disco.
5. **Testes deixam de tocar o `QSettings` real** — a poluição morre na origem.

> **Sobre o valor podre que já está no registro do usuário:** não é preciso limpar nada à mão. Como o `_restore_last_paths` deixa de ler `last_backup_dir`, a chave velha simplesmente para de ser usada.

---

## Parte A — `src/core/backup_manager.py`

### A1 — constantes do nome da pasta

**Âncora (bloco literal único — imports + início do dataclass):**

```python
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class _Entry:
```

**Substituir por:**

```python
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# Nome da pasta que agrupa as sessões de backup (DEC-032). O prefixo "zz" é
# deliberado: mantém a pasta no FIM da listagem alfabética da pasta-pai, longe
# do projeto. Sem espaço no nome — caminho com espaço vira erro de aspas quando
# colado à mão em CMD/.bat.
BACKUP_DIRNAME = "zz_backups"
# Nome anterior (<= 0.8.7). Só é consultado na LEITURA (rollback), para que
# backups já existentes em disco continuem restauráveis.
LEGACY_BACKUP_DIRNAME = "backups"


@dataclass
class _Entry:
```

### A2 — `session_dir` passa a usar a constante

**Âncora (linha única):**

```python
        return Path(self.backup_root) / "backups" / self.timestamp
```

**Substituir por:**

```python
        return Path(self.backup_root) / BACKUP_DIRNAME / self.timestamp
```

### A3 — `history.log` acompanha o novo nome

**Âncora (linha única):**

```python
            backups_dir = Path(self.backup_root) / "backups"
```

**Substituir por:**

```python
            backups_dir = Path(self.backup_root) / BACKUP_DIRNAME
```

### A4 — `restore_backup` com fallback para o layout antigo

**Âncora (linha única):**

```python
    session_dir = Path(backup_root) / "backups" / timestamp
```

**Substituir por:**

```python
    session_dir = Path(backup_root) / BACKUP_DIRNAME / timestamp
    if not session_dir.exists():
        # Compatibilidade: backups criados até a 0.8.7 ficam em `backups/`.
        legado = Path(backup_root) / LEGACY_BACKUP_DIRNAME / timestamp
        if legado.exists():
            session_dir = legado
```

---

## Parte B — `src/core/patch_engine.py`: sandbox ignora as duas pastas

**Âncora (linha única, dentro de `SANDBOX_IGNORES`):**

```python
    "backups",
```

**Substituir por:**

```python
    "backups",  # layout <= 0.8.7 (mantido: projetos antigos ainda têm essa pasta)
    "zz_backups",
```

---

## Parte C — `src/gui/main_window.py`

### C1 — parar de persistir o backup-dir

**Âncora (bloco literal único):**

```python
    def _restore_last_paths(self) -> None:
        raiz = self._settings.value("last_root", "")
        instr = self._settings.value("last_instruction", "")
        bkp = self._settings.value("last_backup_dir", "")
        if raiz:
            self.root_edit.setText(str(raiz))
        if instr and instr != self.PASTED_MARK:
            self.instr_edit.setText(str(instr))
        if bkp:
            self.backup_edit.setText(str(bkp))

    def _save_last_paths(self) -> None:
        self._settings.setValue("last_root", self.root_edit.text().strip())
        if self.instr_edit.text() != self.PASTED_MARK:
            self._settings.setValue("last_instruction", self.instr_edit.text().strip())
        self._settings.setValue("last_backup_dir", self.backup_edit.text().strip())
```

**Substituir por:**

```python
    def _restore_last_paths(self) -> None:
        raiz = self._settings.value("last_root", "")
        instr = self._settings.value("last_instruction", "")
        if raiz:
            self.root_edit.setText(str(raiz))
        if instr and instr != self.PASTED_MARK:
            self.instr_edit.setText(str(instr))
        # O backup-dir NÃO é restaurado (DEC-032): ele é DERIVADO da raiz a cada
        # sessão. Persistir um caminho absoluto fazia o destino "grudar" e ignorar
        # a troca de raiz — era o bug relatado. Campo vazio = padrão da raiz.

    def _save_last_paths(self) -> None:
        self._settings.setValue("last_root", self.root_edit.text().strip())
        if self.instr_edit.text() != self.PASTED_MARK:
            self._settings.setValue("last_instruction", self.instr_edit.text().strip())
        # `last_backup_dir` deixou de ser salvo (DEC-032). A chave antiga que
        # eventualmente exista no perfil do usuário simplesmente não é mais lida.
```

### C2 — placeholder mostra o destino derivado; diálogo abre na pasta-pai

**Âncora (bloco literal único):**

```python
    def _pick_backup_dir(self) -> None:
        pasta = QFileDialog.getExistingDirectory(self, "Pasta de backup (opcional)")
        if pasta:
            self.backup_edit.setText(pasta)
```

**Substituir por:**

```python
    def _pick_backup_dir(self) -> None:
        # Abre já na pasta-pai da raiz — que é o destino padrão (DEC-032).
        inicio = ""
        raiz = self.root_edit.text().strip()
        if raiz:
            try:
                inicio = str(Path(raiz).resolve().parent)
            except OSError:  # caminho inválido/inacessível — abre onde o Qt decidir
                inicio = ""
        pasta = QFileDialog.getExistingDirectory(self, "Pasta de backup (opcional)", inicio)
        if pasta:
            self.backup_edit.setText(pasta)

    def _default_backup_hint(self) -> str:
        """Texto do destino padrão do backup para a raiz atual (só exibição)."""
        raiz = self.root_edit.text().strip()
        if not raiz:
            return "padrão: <pasta-pai da raiz>/" + BACKUP_DIRNAME
        try:
            destino = Path(raiz).resolve().parent / BACKUP_DIRNAME
        except OSError:
            return "padrão: <pasta-pai da raiz>/" + BACKUP_DIRNAME
        return f"padrão: {destino}"

    def _update_backup_placeholder(self) -> None:
        """Mantém o placeholder do campo Backup sincronizado com a raiz atual."""
        self.backup_edit.setPlaceholderText(self._default_backup_hint())
```

### C3 — ligar o placeholder à raiz (escolhida, digitada ou vinda de args)

**Âncora (bloco literal único, no `__init__`):**

```python
        self._restore_last_paths()

        # Sobrepõe com argumentos de lançamento (WI-2) — depois de _restore_last_paths.
```

**Substituir por:**

```python
        self._restore_last_paths()

        # O destino do backup segue a RAIZ (DEC-032): o placeholder exibe o
        # caminho calculado e acompanha qualquer mudança — escolhida, digitada
        # ou vinda dos argumentos de lançamento tratados logo abaixo.
        self.root_edit.textChanged.connect(self._update_backup_placeholder)
        self._update_backup_placeholder()

        # Sobrepõe com argumentos de lançamento (WI-2) — depois de _restore_last_paths.
```

### C4 — import da constante

O módulo precisa de `BACKUP_DIRNAME` e de `Path`. **Confira antes de editar:** `Path` já é importado no `main_window.py` (é usado em `_apply`/`Path(report.backup_dir)`); se estiver, **não** duplique. Para a constante, acrescente ao bloco de imports do core do módulo:

```python
from ..core.backup_manager import BACKUP_DIRNAME
```

Use a MESMA forma relativa dos imports de core já presentes no arquivo (ex.: se o arquivo usa `from ..core.patch_engine import ...`, siga esse padrão). **Se a forma não bater, PARE e reporte** em vez de inventar caminho de import.

---

## Parte D — testes

### D1 — isolar o `QSettings` (mata a poluição na origem)

**Âncora (bloco literal único em `tests/test_gui_smoke.py`):**

```python
@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])
```

**Substituir por:**

```python
@pytest.fixture(scope="module", autouse=True)
def _isolate_qsettings(tmp_path_factory):
    """Redireciona o QSettings da GUI para um .ini temporário.

    Sem isto, `MainWindow` grava em `QSettings("auto-script-updater", "gui")` —
    no Windows, o REGISTRO do usuário — e a suíte contamina a GUI real (foi o
    que injetou um caminho `pytest-of-*/.../meu_backup` no campo Backup de um
    usuário real). Ver DEC-032.
    """
    from PySide6.QtCore import QSettings

    destino = str(tmp_path_factory.mktemp("qsettings"))
    formato = QSettings.Format.IniFormat
    QSettings.setPath(formato, QSettings.Scope.UserScope, destino)
    QSettings.setDefaultFormat(formato)
    yield


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])
```

> Se a API de enum não bater nesta versão do PySide6 (`QSettings.Format.IniFormat` / `QSettings.Scope.UserScope`), use a forma equivalente aceita pelo binding instalado — o objetivo é redirecionar o armazenamento para `destino`. **Confirme que funcionou** rodando a suíte e checando que nenhum arquivo/chave real foi tocado.

### D2 — substituir o teste que persistia o backup-dir

**Âncora (bloco literal único):**

```python
def test_save_and_restore_backup_dir(app, tmp_path):
    """_save_last_paths / _restore_last_paths incluem o backup-dir."""
    pasta = str(tmp_path / "meu_backup")
    win = MainWindow()
    win.backup_edit.setText(pasta)
    win._save_last_paths()

    win2 = MainWindow()
    win2._settings = win._settings  # compartilha o mesmo QSettings
    win2._restore_last_paths()
    assert win2.backup_edit.text() == pasta
```

**Substituir por:**

```python
def test_backup_dir_nao_e_persistido(app, tmp_path):
    """DEC-032: o backup-dir NÃO sobrevive à sessão — ele é derivado da raiz.

    Regressão do bug em que um caminho salvo (inclusive um tmp de teste vazado
    para o perfil real) 'grudava' e ignorava a troca de raiz.
    """
    pasta = str(tmp_path / "meu_backup")
    win = MainWindow()
    win.backup_edit.setText(pasta)
    win._save_last_paths()

    win2 = MainWindow()
    win2._settings = win._settings  # compartilha o mesmo QSettings
    win2._restore_last_paths()
    assert win2.backup_edit.text() == ""  # não restaurou nada


def test_placeholder_do_backup_segue_a_raiz(app, tmp_path):
    """O destino padrão exibido acompanha a raiz escolhida (pasta-pai/zz_backups)."""
    from src.core.backup_manager import BACKUP_DIRNAME

    projeto = tmp_path / "meu_projeto"
    projeto.mkdir()
    win = MainWindow()
    win.root_edit.setText(str(projeto))

    dica = win.backup_edit.placeholderText()
    assert BACKUP_DIRNAME in dica
    assert str(tmp_path.resolve()) in dica  # a pasta-PAI, não a raiz
```

### D3 — testes do novo layout e do fallback (em `tests/test_patch_engine.py`)

**Âncora (linha única — o teste do CLI criado na spec0008; a edição INSERE antes):**

```python
def test_cli_print_report_mostra_ressalva(capsys):
```

**Substituir por:**

```python
def test_backup_usa_pasta_zz_backups(tmp_path):
    """DEC-032: a sessão de backup nasce em <backup_root>/zz_backups/<ts>."""
    from src.core.backup_manager import BACKUP_DIRNAME, BackupSession

    sess = BackupSession(backup_root=tmp_path)
    assert sess.session_dir.parent.name == BACKUP_DIRNAME


def test_rollback_encontra_layout_legado(tmp_path):
    """Backups criados até a 0.8.7 (pasta `backups/`) continuam restauráveis."""
    from src.core.backup_manager import LEGACY_BACKUP_DIRNAME, restore_backup

    ts = "20250101_000000"
    alvo = tmp_path / "arquivo.txt"
    alvo.write_text("novo", encoding="utf-8")

    sessao = tmp_path / LEGACY_BACKUP_DIRNAME / ts
    espelho = sessao / "arquivo.txt"
    espelho.parent.mkdir(parents=True, exist_ok=True)
    espelho.write_text("antigo", encoding="utf-8")
    (sessao / "manifest.txt").write_text(
        f"modificado\t{alvo}\t{espelho}\n", encoding="utf-8"
    )

    restore_backup(tmp_path, ts)
    assert alvo.read_text(encoding="utf-8") == "antigo"


def test_cli_print_report_mostra_ressalva(capsys):
```

> **Ajuste de forma permitido:** os kwargs de `BackupSession` e o formato exato da linha do `manifest.txt` (`estado<TAB>original<TAB>espelho`) devem ser conferidos no `backup_manager.py` antes de rodar — se a assinatura divergir, adapte a construção do objeto mantendo a INTENÇÃO do teste. Se o manifesto legado exigir cabeçalho ou outra convenção, siga a real. **Não invente API.**

### D4 — varredura de testes que assumem `backups/`

Procure na suíte referências ao layout antigo (`"backups"`, `/ "backups"`, `backups/`) e ajuste as que descrevem o PADRÃO para `BACKUP_DIRNAME` — **exceto** o teste do fallback legado acima, que deve continuar usando o nome antigo de propósito:

```
findstr /S /N "backups" tests\*.py
```

---

## Parte E — textos de ajuda e `.gitignore`

- **`src/__main__.py`:** há três textos de `--help` citando `backups/` (nas descrições de `--backup-dir` do `apply` e de `--root`/`--backup-dir` do `rollback`). Atualize para `zz_backups/`. São textos de ajuda, sem efeito funcional — se alguma âncora não bater exatamente, ajuste o texto equivalente e **reporte o que mudou**.
- **`.gitignore`:** a linha `backups/` existe. Acrescente `zz_backups/` logo abaixo (mantenha a antiga: projetos e checkouts antigos ainda têm a pasta).

---

## /wrap 0.9.0 (executar após validar)

### W1 — bump
`src/__init__.py`: `__version__ = "0.8.7"` → `__version__ = "0.9.0"`.

### W2 — `meta/CHANGELOG.md`
Inserir acima de `## [0.8.7]`:

```markdown
## [0.9.0] — 2026-07-20
### Corrigido
- **Endereçamento do backup voltou a seguir a RAIZ (spec0010, DEC-032).** Duas causas somadas: (1) a GUI persistia `last_backup_dir` no `QSettings` e nunca re-derivava o destino, então um caminho escolhido uma vez "grudava" e ignorava a troca de raiz; (2) a suíte de testes gravava no `QSettings` REAL (no Windows, o registro do usuário) — `test_save_and_restore_backup_dir` chegou a injetar um caminho `pytest-of-*/.../meu_backup` na GUI de um usuário real. O engine estava correto o tempo todo. Agora: campo vazio = destino derivado da raiz; o placeholder exibe o caminho calculado e acompanha a troca de raiz; o campo não é mais persistido; os testes rodam com `QSettings` isolado em `.ini` temporário.
### Alterado
- **Pasta padrão de backup renomeada de `backups/` para `zz_backups/`** (constante `BACKUP_DIRNAME`): o prefixo mantém a pasta no fim da listagem da pasta-pai, longe do projeto. **Rollback de backups antigos continua funcionando** (fallback para `backups/` na leitura). `SANDBOX_IGNORES` e `.gitignore` cobrem os dois nomes.
### Testes / Qualidade
- Testes novos: layout `zz_backups`, fallback de rollback legado, placeholder que segue a raiz, e regressão de "backup-dir não é persistido". Fixture `autouse` isolando o `QSettings` da GUI. `ruff`/`black`/`self-test` limpos. `__version__` 0.8.7 → **0.9.0**.
```

### W3 — `meta/DECISIONS.md` (append ao fim)

```markdown

## DEC-032 — Backup é DERIVADO da raiz; pasta `zz_backups`; QSettings da GUI isolado nos testes
**Contexto.** Bug relatado em uso real: o backup "saía em lugar aleatório e ficava nele", ignorando a troca de raiz. Investigação achou DUAS causas somadas — (1) a GUI persistia `last_backup_dir` e o engine só aplica o padrão `parent(root)` quando recebe `None`, então o valor salvo vencia para sempre; (2) `test_save_and_restore_backup_dir` gravava um `tmp_path` do pytest no `QSettings("auto-script-updater","gui")` REAL (registro do Windows), contaminando a GUI do usuário — comprovado por print onde o campo exibia `...pytest-of-alexk\pytest-22\...\meu_backup`. O engine (DEC-024c) estava correto.
**Decisão.** (a) O campo Backup da GUI **não é mais persistido**: vazio = derivado (`parent(root)/zz_backups/<ts>`), preenchido = override da sessão; o placeholder mostra o destino calculado e é religado a cada mudança de raiz (`textChanged`). (b) A pasta padrão passa de `backups/` para **`zz_backups/`** via constante `BACKUP_DIRNAME` — prefixo "zz" para ficar no fim da listagem da pasta-pai (pedido do usuário, que sugeriu "zz backup"); **sem espaço** no nome, para não criar armadilha de aspas em CMD/`.bat`. (c) A LEITURA do rollback tem fallback para `LEGACY_BACKUP_DIRNAME = "backups"`, preservando backups já existentes. (d) Os testes de GUI passam a redirecionar o `QSettings` para um `.ini` temporário via fixture `autouse`.
**Consequências.** Backups novos vão para `zz_backups/`; os antigos continuam restauráveis. A chave `last_backup_dir` eventualmente presente no perfil do usuário deixa de ser lida — não é preciso limpar nada à mão. Quem queria um diretório central fixo perde a persistência automática e deve usar `--backup-dir` (CLI) ou preencher o campo na sessão — trade-off aceito porque o comportamento pedido é "seguir a raiz". Supersede a parte de PERSISTÊNCIA da DEC-024 (o aninhamento por projeto em backup externo, DEC-024b, continua valendo).
```

### W4 — `meta/STATUS.md`
- **Versão Atual** → `[0.9.0] — 2026-07-20 — Backup segue a raiz; pasta zz_backups; QSettings isolado (spec0010, DEC-032).`; empurrar `[0.8.7]` para "Anterior".
- Atualizar a contagem de testes (152 → o que o `pytest` reportar).
- Na seção **⏸️ Pausa de maturação**, acrescentar ao fim: `Pausa interrompida em 2026-07-20 por um bug de endereçamento de backup encontrado em uso real (DEC-032) — exatamente o tipo de retorno que a pausa existia para colher.`
- No bullet de backup da seção "✅ Funcionando", trocar a menção ao padrão `parent(root)/backups/<ts>` por `parent(root)/zz_backups/<ts>` e citar o fallback de leitura.

### W5 — `meta/IDEAS.md`
Nenhuma ideia nova nesta spec (o bug virou DEC/FIX, não ideia). Não editar.

---

## Validação (antes de commitar)

- `python -m pytest` — suíte verde. **Preste atenção especial** a testes que assumiam `backups/`.
- `ruff check .` e `black --check .` limpos.
- `python -m src self-test` OK.
- **Conferência manual no Windows (é o ponto da spec):** abrir a GUI, escolher uma raiz **A** → o placeholder do campo Backup deve mostrar `padrão: <pai de A>\zz_backups`; trocar para uma raiz **B** em outra árvore → o placeholder deve **mudar sozinho** para `<pai de B>\zz_backups`. Aplicar algo em B e conferir que a pasta nasceu em `<pai de B>\zz_backups\<timestamp>`. Depois, **Desfazer** e confirmar que reverteu.
- `git diff`: só `src/core/backup_manager.py`, `src/core/patch_engine.py`, `src/gui/main_window.py`, `src/__main__.py`, `.gitignore`, os dois arquivos de teste, `src/__init__.py` e os meta-docs.

## Commit + push

```
git add src\core\backup_manager.py src\core\patch_engine.py src\gui\main_window.py src\__main__.py .gitignore tests\test_gui_smoke.py tests\test_patch_engine.py src\__init__.py && git commit -m "fix: backup volta a seguir a raiz e vai para zz_backups" -m "Campo de backup deixa de ser persistido (grudava e ignorava a troca de raiz); placeholder mostra o destino derivado. Pasta padrao renomeada com fallback de leitura para o layout antigo. Testes de GUI passam a isolar o QSettings, que antes contaminava o perfil real do usuario. DEC-032. Bump 0.9.0."
```

```
git add meta\CHANGELOG.md meta\DECISIONS.md meta\STATUS.md && git commit -m "docs: wrap 0.9.0 (DEC-032, backup segue a raiz)"
```

```
git log origin/main..HEAD --oneline && git push
```
