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
- **Typer:** disponibiliza a interface de linha de comando `code-test-evo`.
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
code-test-evo scan owner/repository --pr 418
```

Um intervalo inclusivo de PRs:

```bash
code-test-evo scan owner/repository --range 280:290 --state closed
```

Todos os PRs abertos:

```bash
code-test-evo scan owner/repository --all --state open
```

Também é possível informar diretamente a URL de um PR:

```bash
code-test-evo scan https://github.com/owner/repository/pull/418
```

O resultado é mostrado no terminal e salvo por padrão em
`code-test-evo-report.html`. Para escolher outro arquivo:

```bash
code-test-evo scan owner/repository --pr 42 --output reports/pr-42.html
```

No Windows, caso o ambiente não esteja ativado, use:

```powershell
.\.venv\Scripts\code-test-evo.exe scan Baekalfen/PyBoy --pr 418
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

### 6. Uso de IA no desenvolvimento desta ferramenta

A IA atuou como uma assistente contínua (estilo pair-programming), desde a concepção arquitetural até as rotinas de controle de versão.

#### Modelos utilizados
Uma combinação de diferentes modelos de linguagem foi empregada:

- Google Gemini Pro 3.1: utilizado para tarefas de maior complexidade analítica, definição de regras de negócio e raciocínio estrutural.
- Google Gemini Flash 3.5: empregado para consultas, iterações rápidas e respostas de baixa latência.
- OpenAI ChatGPT GPT-4o/4o mini: utilizado majoritariamente para tirar dúvidas a respeito de características das bibliotecas utilizadas e como integrá-las ao projeto.
- OpenAI GPT-5.5 com Codex: focado na geração direta, análise sintática e manipulação de funções e blocos de código, a fim de tornar o sistema mais coeso.

#### Fases e áreas de aplicação dos modelos de IA
1. Planejamento e arquitetura inicial

A partir do contexto inicial (um sistema capaz de ler PRs e identificar a presença ou ausência de testes associados ao código modificado), a IA foi utilizada para estruturar um plano de desenvolvimento, assim como sugerir a arquitetura inicial (divisão de pastas, utilização de arquivos para controle de dependências). Isso incluiu um guia passo a passo, sugestões de fluxo de dados e estratégias para dividir as tarefas entre os integrantes do grupo. Como resposta final, a IA gerou um roadmap com o passo a passo detalhado de cada etapa para consolidar o projeto inicialmente.

2. Desenvolvimento e integração

O desenvolvimento foi realizado com o auxílio da IA nos seguintes aspectos:
- Inclusão de features: durante a evolução do sistema, a IA auxiliou na idealização e na implementação de novas funcionalidades, garantindo que as adições fossem compatíveis com a arquitetura estabelecida.
- Suporte técnico: os modelos serviram como uma base de conhecimento iterativa para tirar dúvidas específicas sobre a linguagem de programação base e as bibliotecas utilizadas para integração com a API do Github, para parsing e para facilitação da integração com CLI.
- Correção de código (debugging): os modelos de IA auxiliaram na identificação, isolamento e resolução de erros de sintaxe, comportamentos inesperados, exceções lançadas pelas bibliotecas e gargalos lógicos durante a execução do programa.

3. Qualidade e padronização do código

A IA auxiliou na otimização da manutenibilidade do projeto. O código foi progressivamente reorganizado através de sugestões para:
- Extração de funções longas para funções auxiliares, servindo também para reutilização.
- Implementação de dataclasses para o mapeamento e transporte estruturado dos dados (ex: metadados do PR, arquivos alterados, status dos testes).
- Geração de Testes: a IA foi utilizada para acelerar a escrita da suíte de testes do projeto, gerando casos de uso, mocks de respostas da API do Github e validações. Os modelos de IA foram essenciais especialmente para entender e implementar a utilização dos mocks.

4. Versionamento e documentação

De forma a manter o repositório o mais organizado, reastreável e documentado possível, a IA foi utilizada nas seguintes tarefas:
- Nomenclatura de commits: a IA foi utilizada para ler os diffs das alterações locais e sugerir nomes e descrições de commits padronizados.
- Docstring: a IA foi utilizada para gerar descrições dos métodos de forma a tornar mais claro e conciso o desenvolvimento entre os membros da equipe, de forma a facilitar a utilização das funções, métodos e classes criados pelos membros.
