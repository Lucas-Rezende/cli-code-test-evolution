## Integrantes
- Lucas Momede Barreto Rezende
- Lucas Wiermann Cobo da Silva
- Luiza Sodré Salgado

## Explicação do sistema
A ideia inicial consiste em validar se o crescimento do código (conforme métricas como linhas de código, novas funcionalidades, PRs, etc) está sendo acompanhado por testes, i.e., se a validação do que está sendo implementado está ocorrendo, visando evitar eventuais problemas.

Após análise, a abordagem será focada em detectar Dívida de Testes em Pull Requests: um PR que adiciona muitas linhas de código (ignorando adições de comentários) sem alterar arquivos de teste (ex: test/, tests/) será sinalizado como uma possível não adição de testes.

## Possíveis tecnologias utilizadas
PyGithub (ou semelhantes), visando dar get nos artefatos necessários, oriundos do GitHub.
Os artefatos analisados serão, em suma, pull requests, linhas de código (e seu tipo, caso sejam apenas comentários, poderia ser utilizado o tree-sitter para diferenciar) e testes (quantidade de funções/métodos de teste e linhas de código de teste). Para o CLI, a princípio será utilizado o typer.


## 4 - Como executar:
  Crie uma máquina virtual
  ```bash
  python -m venv venv 
  source venv/bin/activate
  ```

  Atualmente para rodar o único teste que funciona:
  ```bash
  python3 -m unittest tests/test_line_counter.py
  ```
