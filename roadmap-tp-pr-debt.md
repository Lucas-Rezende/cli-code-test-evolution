# Roadmap Completo — PR Debt Scanner
### Dívida de Testes em Pull Requests · Trabalho Prático

> **Como usar este roadmap:** Cada checkbox = 1 commit (ou 2 se a tarefa for grande).
> Convenção de prefixos: `feat:` `fix:` `test:` `docs:` `chore:` `refactor:`

---

## FASE 1 — Setup e Fundação `(Dia 1)`

### 1.1 Repositório e Controle de Versão

- [ ] **[P1]** Como o repositório Lucas-Rezende/cli-code-test-evolution já existe, basta garantir que a branch main seja a padrão e esteja protegida (Settings → Branches).
- [ ] **[P1]** Clonar o repositório localmente: `git clone <url>`
- [ ] **[P1]** Criar a branch `main` como padrão e protegê-la (Settings → Branches)
- [V] **[P1]** Criar o arquivo `.gitignore` com entradas para Python (`__pycache__/`, `.env`, `*.pyc`, `.venv/`)
- [ ] **[P1]** Fazer o primeiro commit: `chore: init repo com .gitignore`
- [ ] **[P1]** Criar o arquivo `.env.example` com o conteúdo `GITHUB_TOKEN=seu_token_aqui`
- [ ] **[P1]** Commit: `chore: adiciona .env.example`

### 1.2 Ambiente Virtual e Dependências

- [ ] **[Todos]** Cada membro clona o repositório localmente
- [ ] **[Todos]** Criar o ambiente virtual: `python -m venv .venv`
- [ ] **[Todos]** Ativar o ambiente: `source .venv/bin/activate` (Linux/Mac) ou `.venv\Scripts\activate` (Windows)
- [ ] **[P1]** Criar o `pyproject.toml` com as dependências abaixo
- [ ] **[P1]** Commit: `chore: adiciona pyproject.toml com dependências`

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "pr-debt-scanner"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "typer>=0.12",
    "PyGithub>=2.3",
    "python-dotenv>=1.0",
    "rich>=13.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-mock>=3.12",
]

[project.scripts]
pr-debt = "pr_debt_scanner.main:app"
```

- [ ] **[Todos]** Instalar em modo editável: `pip install -e ".[dev]"`

### 1.3 Esqueleto de Pastas

- [ ] **[P1]** Criar a estrutura de pastas abaixo e fazer commit de todos os `__init__.py` vazios

```
pr-debt-scanner/
├── .github/
│   └── workflows/
│       └── ci.yml          ← deixar em branco por ora
├── pr_debt_scanner/
│   ├── __init__.py
│   ├── main.py             ← deixar em branco por ora
│   ├── github_client.py    ← deixar em branco por ora
│   ├── analyzer.py         ← deixar em branco por ora
│   ├── line_counter.py     ← deixar em branco por ora
│   └── reporter.py         ← deixar em branco por ora
├── tests/
│   ├── __init__.py
│   ├── test_line_counter.py
│   ├── test_analyzer.py
│   └── test_github_client.py
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md               ← criar com título apenas
```

- [ ] **[P1]** Commit: `chore: cria esqueleto de pastas e módulos vazios`

### 1.4 README Inicial

- [ ] **[P3]** Criar o `README.md` com as seções abaixo (conteúdo pode ser placeholder):
  - Título e badges (CI)
  - Nomes dos membros e RA
  - Objetivo do projeto
  - Tecnologias utilizadas
  - Como instalar
  - Como usar
  - Como rodar os testes
- [ ] **[P3]** Commit: `docs: cria README.md com estrutura base`

---

## FASE 2 — Desenvolvimento do Core `(Dias 2–4)`

> Esta é a parte mais importante. Cada função deve ser desenvolvida e commitada separadamente.

### 2.1 Módulo `line_counter.py` — Responsabilidade: P2

**Objetivo:** Receber o `patch` (diff) de um arquivo como string e retornar a contagem de linhas de código efetivas adicionadas (sem comentários, sem linhas em branco).

- [ ] **[P2]** Entender o formato do patch do GitHub:
  - Linhas que começam com `+` = código adicionado
  - Linhas que começam com `-` = código removido (ignorar)
  - Linhas que começam com `+++` = cabeçalho do diff (ignorar)
  - Linhas sem `+` ou `-` = contexto (ignorar)

- [V] **[P2]** Implementar a função `count_effective_lines(patch: str) -> int`:

```python
# pr_debt_scanner/line_counter.py
import re

# Padrões de linhas a ignorar (após remover o '+' inicial)
_IGNORE_PATTERNS = [
    re.compile(r'^\s*#'),    # comentário Python
    re.compile(r'^\s*$'),    # linha em branco ou só espaços
    re.compile(r'^\s*"""'),  # início/fim de docstring
    re.compile(r"^\s*'''"),  # início/fim de docstring (aspas simples)
]

def count_effective_lines(patch: str | None) -> int:
    """
    Conta linhas de código efetivas adicionadas em um diff (patch).
    Ignora comentários, linhas em branco e docstrings.
    Retorna 0 se o patch for None (ex: arquivos binários).
    """
    if not patch:
        return 0

    count = 0
    for line in patch.splitlines():
        # Só nos interessa linhas adicionadas
        if not line.startswith('+') or line.startswith('+++'):
            continue
        # Remove o '+' inicial para analisar o conteúdo
        code = line[1:]
        # Verifica se a linha deve ser ignorada
        if not any(pattern.match(code) for pattern in _IGNORE_PATTERNS):
            count += 1

    return count
```

- [ ] **[P2]** Commit: `feat: implementa count_effective_lines em line_counter.py`
- [ ] **[P2]** Adicionar filtro para comentários de bloco (`/* */` — útil se quiser estender para JS no futuro)
- [ ] **[P2]** Commit: `feat: adiciona filtro de docstrings em line_counter.py`

### 2.2 Módulo `analyzer.py` — Responsabilidade: P2

**Objetivo:** Dada uma lista de arquivos de um PR, decidir se há dívida de testes.

- [ ] **[P2]** Implementar a função auxiliar `is_test_file(filename: str) -> bool`:

```python
# pr_debt_scanner/analyzer.py
from pr_debt_scanner.line_counter import count_effective_lines

_TEST_DIRS = frozenset({"test", "tests", "spec", "specs"})

def is_test_file(filename: str) -> bool:
    """
    Detecta se um arquivo é de teste pela sua localização ou nome.
    Exemplos que retornam True:
      - tests/test_main.py
      - src/test_utils.py
      - utils_test.py
    """
    parts = filename.lower().split("/")
    basename = parts[-1]
    dirs = set(parts[:-1])

    return (
        bool(dirs & _TEST_DIRS)          # está em diretório de teste
        or basename.startswith("test_")  # nome começa com test_
        or basename.endswith("_test.py") # nome termina com _test.py
    )
```

- [ ] **[P2]** Commit: `feat: implementa is_test_file em analyzer.py`

- [ ] **[P2]** Implementar a função principal `analyze_pr(files, threshold: int) -> dict`:

```python
def analyze_pr(files: list, threshold: int = 50) -> dict:
    """
    Analisa os arquivos de um PR e detecta possível dívida de testes.

    Retorna um dicionário com:
      - total_code_lines: int  — linhas efetivas adicionadas (não-teste)
      - has_test_changes: bool — se algum arquivo de teste foi alterado
      - has_debt: bool         — True se há dívida detectada
      - analyzed_files: list   — lista de arquivos analisados com detalhes
    """
    total_code_lines = 0
    has_test_changes = False
    analyzed_files = []

    for f in files:
        file_is_test = is_test_file(f.filename)
        if file_is_test:
            has_test_changes = True
        else:
            lines = count_effective_lines(f.patch)
            total_code_lines += lines
            analyzed_files.append({
                "filename": f.filename,
                "effective_lines": lines,
            })

    has_debt = (total_code_lines >= threshold) and not has_test_changes

    return {
        "total_code_lines": total_code_lines,
        "has_test_changes": has_test_changes,
        "has_debt": has_debt,
        "threshold": threshold,
        "analyzed_files": analyzed_files,
    }
```

- [ ] **[P2]** Commit: `feat: implementa analyze_pr com lógica de detecção de dívida`
- [ ] **[P2]** Commit: `refactor: extrai constante _TEST_DIRS para facilitar configuração`

### 2.3 Módulo `github_client.py` — Responsabilidade: P1

**Objetivo:** Encapsular toda a comunicação com a API do GitHub via PyGithub.

- [ ] **[P1]** Gerar um token no GitHub: Settings → Developer Settings → Personal Access Tokens → Fine-grained → permissão `Pull Requests: Read`
- [ ] **[P1]** Salvar o token no arquivo `.env` local (nunca commitar este arquivo!)
- [ ] **[P1]** Implementar a função `get_pr_files`:

```python
# pr_debt_scanner/github_client.py
import os
from github import Github, GithubException
from dotenv import load_dotenv

load_dotenv()

def get_github_client() -> Github:
    """Cria e retorna um cliente autenticado do PyGithub."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise EnvironmentError(
            "Variável GITHUB_TOKEN não encontrada. "
            "Crie um arquivo .env com GITHUB_TOKEN=seu_token."
        )
    return Github(token)


def get_pr_files(repo_name: str, pr_number: int) -> list:
    """
    Busca a lista de arquivos modificados em um Pull Request.

    Args:
        repo_name: No formato "owner/repo" (ex: "torvalds/linux")
        pr_number: Número do PR (ex: 42)

    Returns:
        Lista de objetos PullRequestFile do PyGithub.

    Raises:
        SystemExit: Se o repo ou PR não existirem, ou o token for inválido.
    """
    try:
        client = get_github_client()
        repo = client.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        return list(pr.get_files())
    except GithubException as e:
        raise SystemExit(f"Erro ao acessar o GitHub: {e.data.get('message', str(e))}")
```

- [ ] **[P1]** Commit: `feat: implementa get_github_client com autenticação via .env`
- [ ] **[P1]** Commit: `feat: implementa get_pr_files em github_client.py`
- [ ] **[P1]** Commit: `feat: adiciona tratamento de erros em get_pr_files`

---

## FASE 3 — CLI e Integração `(Dias 4–5)`

### 3.1 Módulo `reporter.py` — Responsabilidade: P3

**Objetivo:** Formatar e exibir o resultado no terminal de forma clara.

- [ ] **[P3]** Implementar `print_report` usando a biblioteca `rich`:

```python
# pr_debt_scanner/reporter.py
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def print_report(repo: str, pr_number: int, result: dict, as_json: bool = False) -> None:
    """Exibe o relatório de análise no terminal."""
    if as_json:
        print(json.dumps(result, indent=2))
        return

    # Cabeçalho
    console.print(f"\n[bold]Analisando:[/bold] {repo} · PR #{pr_number}\n")

    # Tabela de arquivos
    table = Table(title="Arquivos Analisados (não-teste)", show_lines=True)
    table.add_column("Arquivo", style="cyan")
    table.add_column("Linhas Efetivas", justify="right")

    for f in result["analyzed_files"]:
        table.add_row(f["filename"], str(f["effective_lines"]))

    console.print(table)

    # Veredicto
    total = result["total_code_lines"]
    threshold = result["threshold"]
    has_tests = result["has_test_changes"]
    has_debt = result["has_debt"]

    console.print(f"\nLinhas de código efetivas adicionadas: [bold]{total}[/bold] (threshold: {threshold})")
    console.print(f"Arquivos de teste modificados: {'[green]Sim ✓[/green]' if has_tests else '[yellow]Não[/yellow]'}")

    if has_debt:
        console.print(Panel(
            "[bold red]⚠ DÍVIDA DE TESTES DETECTADA[/bold red]\n"
            f"Este PR adicionou [bold]{total}[/bold] linhas de código "
            "sem modificar nenhum arquivo de teste.",
            border_style="red"
        ))
    else:
        console.print(Panel(
            "[bold green]✓ Nenhuma dívida detectada[/bold green]",
            border_style="green"
        ))
```

- [V] **[P3]** Commit: `feat: implementa print_report com Rich em reporter.py`
- [ ] **[P3]** Commit: `feat: adiciona flag --json para output em JSON no reporter`

### 3.2 Módulo `main.py` — Responsabilidade: P1

**Objetivo:** Juntar tudo usando Typer e expor o comando `pr-debt scan`.

- [ ] **[P1]** Implementar o comando principal:

```python
# pr_debt_scanner/main.py
import typer
from pr_debt_scanner.github_client import get_pr_files
from pr_debt_scanner.analyzer import analyze_pr
from pr_debt_scanner.reporter import print_report

app = typer.Typer(
    name="pr-debt",
    help="Detecta dívida de testes em Pull Requests do GitHub.",
    add_completion=False,
)

@app.command()
def scan(
    repo: str = typer.Argument(
        ...,
        help="Repositório no formato owner/repo (ex: octocat/Hello-World)",
    ),
    pr_number: int = typer.Argument(
        ...,
        help="Número do Pull Request a ser analisado",
    ),
    threshold: int = typer.Option(
        50,
        "--threshold", "-t",
        help="Mínimo de linhas efetivas para emitir alerta de dívida",
    ),
    as_json: bool = typer.Option(
        False,
        "--json",
        help="Exibe o resultado em formato JSON",
    ),
):
    """Analisa um Pull Request e detecta possível dívida de testes."""
    files = get_pr_files(repo, pr_number)
    result = analyze_pr(files, threshold=threshold)
    print_report(repo, pr_number, result, as_json=as_json)
    if result["has_debt"]:
        raise typer.Exit(code=1)  # exit code 1 sinaliza problema (útil em CI)
```

- [ ] **[P1]** Commit: `feat: implementa comando scan em main.py com Typer`
- [ ] **[P1]** Commit: `feat: adiciona exit code 1 quando dívida é detectada`

### 3.3 Teste Manual de Integração

- [ ] **[Todos]** Rodar o comando e verificar se funciona end-to-end:
  ```bash
  pr-debt scan octocat/Hello-World 1
  pr-debt scan torvalds/linux 100 --threshold 30
  pr-debt scan microsoft/vscode 200000 --json
  ```
- [ ] **[Todos]** Testar o caso de erro (repo inexistente, PR inexistente)
- [ ] **[P1]** Commit: `fix: corrige mensagem de erro para PR não encontrado`

---

## FASE 4 — Cobertura de Testes e CI `(Dias 5–7)`

### 4.1 Como Fazer o Mock (Sem Bater na API do GitHub)

> O segredo é mockar o objeto `PullRequestFile` que o PyGithub retorna.
> Use a função abaixo como helper nos seus testes:

```python
# No topo de cada arquivo de teste
from unittest.mock import MagicMock

def make_mock_file(filename: str, patch: str | None) -> MagicMock:
    """Cria um mock de PullRequestFile do PyGithub."""
    f = MagicMock()
    f.filename = filename
    f.patch = patch
    return f
```

### 4.2 Testes de `line_counter.py` — `tests/test_line_counter.py`

- [V] **[P3]** **Teste 1:** Linha de código válida é contada

```python
def test_conta_linha_de_codigo():
    patch = "+x = 1\n"
    assert count_effective_lines(patch) == 1
```

- [V] **[P3]** Commit: `test: testa contagem de linha de código válida`

- [V] **[P3]** **Teste 2:** Comentário Python é ignorado

```python
def test_ignora_comentario():
    patch = "+# isso é um comentário\n"
    assert count_effective_lines(patch) == 0
```

- [V] **[P3]** **Teste 3:** Linha em branco é ignorada

```python
def test_ignora_linha_em_branco():
    patch = "+\n+   \n"
    assert count_effective_lines(patch) == 0
```

- [V] **[P3]** **Teste 4:** Cabeçalho do diff é ignorado

```python
def test_ignora_cabecalho_diff():
    patch = "+++ b/arquivo.py\n+x = 1\n"
    assert count_effective_lines(patch) == 1
```

- [V] **[P3]** **Teste 5:** Patch `None` retorna zero (arquivo binário)

```python
def test_patch_none_retorna_zero():
    assert count_effective_lines(None) == 0
```

- [V] **[P3]** **Teste 6:** Linhas removidas (`-`) não são contadas

```python
def test_nao_conta_linhas_removidas():
    patch = "-x = 1\n"
    assert count_effective_lines(patch) == 0
```

- [V] **[P3]** Commit: `test: adiciona testes 2-6 para line_counter.py`

### 4.3 Testes de `analyzer.py` — `tests/test_analyzer.py`

- [V] **[P3]** **Teste 7:** `is_test_file` detecta diretório `tests/`

```python
def test_is_test_file_por_diretorio():
    assert is_test_file("tests/test_main.py") is True
```

- [V] **[P3]** **Teste 8:** `is_test_file` detecta sufixo `_test.py`

```python
def test_is_test_file_por_sufixo():
    assert is_test_file("src/utils_test.py") is True
```

- [V] **[P3]** **Teste 9:** `is_test_file` retorna `False` para arquivo normal

```python
def test_is_test_file_arquivo_normal():
    assert is_test_file("pr_debt_scanner/analyzer.py") is False
```

- [V] **[P3]** Commit: `test: adiciona testes 7-9 para is_test_file`

- [ ] **[P3]** **Teste 10:** `analyze_pr` detecta dívida quando há código sem testes

```python
def test_analyze_pr_detecta_divida():
    files = [make_mock_file("src/main.py", "+x = 1\n" * 60)]
    result = analyze_pr(files, threshold=50)
    assert result["has_debt"] is True
    assert result["has_test_changes"] is False
    assert result["total_code_lines"] == 60
```

- [ ] **[P3]** **Teste 11:** `analyze_pr` não detecta dívida quando testes foram alterados

```python
def test_analyze_pr_sem_divida_com_testes():
    files = [
        make_mock_file("src/main.py", "+x = 1\n" * 60),
        make_mock_file("tests/test_main.py", "+assert x == 1\n"),
    ]
    result = analyze_pr(files, threshold=50)
    assert result["has_debt"] is False
    assert result["has_test_changes"] is True
```

- [V] **[P3]** Commit: `test: adiciona testes 10-11 para analyze_pr`

- [ ] **[P3]** **Teste 12 (bônus):** `analyze_pr` não detecta dívida quando código está abaixo do threshold

```python
def test_analyze_pr_sem_divida_abaixo_threshold():
    files = [make_mock_file("src/utils.py", "+x = 1\n" * 10)]
    result = analyze_pr(files, threshold=50)
    assert result["has_debt"] is False
```

- [V] **[P3]** Commit: `test: adiciona teste de bônus (threshold não atingido)`

### 4.4 Verificação Local dos Testes

- [ ] **[Todos]** Rodar `pytest tests/ -v` e confirmar que **todos os testes passam**
- [ ] **[Todos]** Rodar `pytest tests/ -v --tb=short` para ver detalhes de falhas
- [ ] **[P3]** Commit: `test: todos os testes passando localmente`

### 4.5 Configurar GitHub Actions — `.github/workflows/ci.yml`

- [ ] **[P3]** Criar o arquivo `ci.yml` com o conteúdo abaixo:

```yaml
# .github/workflows/ci.yml
name: CI — Testes Automatizados

on:
  push:
    branches: ["main"]
  pull_request:
    branches: ["main"]

jobs:
  test:
    name: Rodar testes com pytest
    runs-on: ubuntu-latest

    steps:
      - name: Checkout do código
        uses: actions/checkout@v4

      - name: Configurar Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Instalar dependências
        run: pip install -e ".[dev]"

      - name: Rodar testes
        run: pytest tests/ -v --tb=short
```

> **Nota:** Como os testes usam mock, **não precisamos** de `GITHUB_TOKEN` no Actions.
> Os testes nunca tocam a API real do GitHub.

- [ ] **[P3]** Commit: `chore: configura GitHub Actions em ci.yml`
- [ ] **[P3]** Fazer push para `main` e verificar se o workflow aparece em Actions
- [ ] **[P3]** Confirmar que o ícone ✅ aparece no repositório
- [ ] **[P3]** Commit: `chore: CI passando no GitHub Actions`

---

## FASE 5 — Documentação e Entrega `(Dias 7–8)`

### 5.1 Completar o README.md

- [ ] **[P3]** Adicionar badge do CI no topo:
  ```markdown
  ![CI](https://github.com/SEU_USER/pr-debt-scanner/actions/workflows/ci.yml/badge.svg)
  ```
- [ ] **[P3]** Commit: `docs: adiciona badge do CI no README`

- [ ] **[P3]** Preencher a seção **Membros da Equipe** (nome completo + RA)
- [ ] **[P3]** Commit: `docs: adiciona membros da equipe no README`

- [ ] **[P3]** Preencher a seção **Objetivo** com 2–3 parágrafos explicando:
  - O que é dívida de testes
  - Como a ferramenta detecta
  - Por que isso é relevante em engenharia de software
- [ ] **[P3]** Commit: `docs: preenche seção de objetivo no README`

- [ ] **[P3]** Preencher a seção **Como Instalar** com os comandos exatos:
  ```bash
  git clone https://github.com/SEU_USER/pr-debt-scanner
  cd pr-debt-scanner
  python -m venv .venv
  source .venv/bin/activate
  pip install -e ".[dev]"
  cp .env.example .env
  # edite o .env e adicione seu GITHUB_TOKEN
  ```
- [ ] **[P3]** Commit: `docs: preenche instruções de instalação no README`

- [ ] **[P3]** Preencher a seção **Como Usar** com exemplos reais:
  ```bash
  # Escanear um PR específico
  pr-debt scan octocat/Hello-World 1

  # Definir um threshold customizado
  pr-debt scan microsoft/vscode 200000 --threshold 30

  # Saída em JSON (útil para integração com outras ferramentas)
  pr-debt scan torvalds/linux 100 --json
  ```
- [ ] **[P3]** Commit: `docs: adiciona exemplos de uso no README`

- [ ] **[P3]** Preencher a seção **Como Rodar os Testes**:
  ```bash
  pytest tests/ -v
  ```
- [ ] **[P3]** Commit: `docs: adiciona instruções para rodar testes no README`

- [ ] **[P3]** Preencher a seção **Tecnologias** com links:
  - [Python 3.11](https://www.python.org/)
  - [Typer](https://typer.tiangolo.com/)
  - [PyGithub](https://pygithub.readthedocs.io/)
  - [Rich](https://rich.readthedocs.io/)
  - [Pytest](https://docs.pytest.org/)
- [ ] **[P3]** Commit: `docs: adiciona seção de tecnologias com links no README`

### 5.2 Revisão Final de Qualidade

- [ ] **[Todos]** Revisar se todos os módulos têm docstrings nas funções principais
- [ ] **[P2]** Commit: `docs: adiciona docstrings em analyzer.py`
- [ ] **[P1]** Commit: `docs: adiciona docstrings em github_client.py`

- [ ] **[Todos]** Rodar `pytest tests/ -v` uma última vez — deve mostrar **≥ 10 testes passando**
- [ ] **[Todos]** Verificar a contagem de commits: `git log --oneline | wc -l` — deve ser **≥ 50**
- [ ] **[Todos]** Verificar que o arquivo `.env` **não** aparece em `git log` (nunca deve ser commitado)

### 5.3 Checklist dos Requisitos da Faculdade

- [ ] Ferramenta funciona via linha de comando (`pr-debt scan ...`)
- [ ] Existe pelo menos 10 testes de unidade em `tests/`
- [ ] `pytest tests/ -v` passa com todos os testes ✅
- [ ] GitHub Actions está configurado e mostrando ✅ no repositório
- [ ] O repositório tem ≥ 50 commits com mensagens descritivas
- [ ] README.md contém: membros, objetivo, tecnologias, instalação, uso e como rodar testes

### 5.4 Preparar os 3 Links de Submissão

- [ ] **[P1]** **Link 1 — Repositório principal:**
  ```
  https://github.com/SEU_USER/pr-debt-scanner
  ```

- [ ] **[P1]** **Link 2 — Pasta de testes:**
  ```
  https://github.com/SEU_USER/pr-debt-scanner/tree/main/tests
  ```

- [ ] **[P1]** **Link 3 — Log do GitHub Actions (última execução bem-sucedida):**
  - Acessar: repositório → aba **Actions** → clicar no último workflow ✅ → copiar a URL da página
  ```
  https://github.com/SEU_USER/pr-debt-scanner/actions/runs/XXXXXXXXXX
  ```

- [ ] **[P1]** Submeter os 3 links no Moodle ✅

---

## Contador de Commits por Fase

| Fase | Descrição | Commits Estimados |
|------|-----------|:-----------------:|
| Fase 1 | Setup e Fundação | ~10 |
| Fase 2 | Core (line_counter + analyzer + github_client) | ~12 |
| Fase 3 | CLI + Reporter + Integração | ~8 |
| Fase 4 | Testes + CI | ~12 |
| Fase 5 | Documentação + Revisão | ~10 |
| **Total** | | **~52 commits** |

---

*Roadmap gerado para o TP de Mineração de Repositórios de Software.*