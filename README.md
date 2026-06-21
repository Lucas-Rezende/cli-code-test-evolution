## Integrantes
- Lucas Momede Barreto Rezende
- Lucas Wiermann Cobo da Silva
- Luiza Sodré Salgado

## Explicação do sistema
A ideia inicial consiste em validar se o crescimento do código (conforme métricas como linhas de código, novas funcionalidades, PRs, etc) está sendo acompanhado por testes, i.e., se a validação do que está sendo implementado está ocorrendo, visando evitar eventuais problemas.

Após análise, a abordagem será focada em detectar Dívida de Testes em Pull Requests: um PR que adiciona muitas linhas de código (ignorando adições de comentários) sem alterar arquivos de teste (ex: test/, tests/) será sinalizado como uma possível não adição de testes.

## Tecnologias utilizadas

- **Python 3.10+:** linguagem utilizada no projeto.
- **PyGithub:** consulta repositórios, Pull Requests, arquivos modificados, patches e conteúdos por meio da API do GitHub.
- **Typer:** disponibiliza a interface de linha de comando `pr-debt`.
- **Rich:** formata tabelas e resultados exibidos no terminal.
- **unidiff:** interpreta os patches dos Pull Requests e identifica linhas adicionadas e removidas.
- **`ast` e `tokenize`:** módulos da biblioteca padrão usados para reconhecer código Python, comentários e docstrings.
- **python-dotenv:** carrega o token do GitHub armazenado no arquivo `.env`.
- **pytest:** executa os testes automatizados do projeto.

## Como executar:

O projeto requer versões recentes de Python (3.10 ou superior) e um token do GitHub.

### 1. Clone o repositório

```bash
git clone https://github.com/Lucas-Rezende/cli-code-test-evolution.git
cd cli-code-test-evolution
```

### 2. Crie o ambiente virtual e instale o projeto

Linux, WSL2 ou macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

### 3. Configure o token

Copie `.env.example` para `.env`:

Linux, WSL2 ou macOS:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Edite o arquivo `.env`:

```text
GITHUB_TOKEN=seu_token_aqui
```
O token deve ser real e válido.

### 4. Execute uma análise

Um PR específico:

```bash
pr-debt scan owner/repository --pr 418
```

Um intervalo inclusivo de PRs:

```bash
pr-debt scan owner/repository --range 280:290 --state closed
```

Todos os PRs abertos:

```bash
pr-debt scan owner/repository --all --state open
```

Também é possível informar diretamente a URL de um PR:

```bash
pr-debt scan https://github.com/owner/repository/pull/418
```

O resultado é mostrado no terminal e salvo por padrão em
`pr-debt-report.html`. Para escolher outro arquivo:

```bash
pr-debt scan owner/repository --pr 42 --output reports/pr-42.html
```

No Windows, caso o ambiente não esteja ativado, use:

```powershell
.\.venv\Scripts\pr-debt.exe scan Baekalfen/PyBoy --pr 418
```

### 5. Execute os testes

Linux, WSL2 ou macOS:

```bash
python -m pytest -q
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```