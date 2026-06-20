# pr_debt_scanner/github_client.py
import os
from github import Github, GithubException, Auth
from github.PullRequest import PullRequest
from dotenv import load_dotenv
from typing import Iterable

load_dotenv()


def get_github_client() -> Github:
    """Cria e retorna um cliente autenticado do PyGithub."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise EnvironmentError(
            "Variável GITHUB_TOKEN não encontrada. "
            "Crie um arquivo .env com GITHUB_TOKEN=seu_token."
        )
    auth = Auth.Token(token)
    return Github(auth=auth)


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
        raise SystemExit(
            f"Erro ao acessar o GitHub: {e.data.get('message', str(e))}")

def get_pr_files_from_pr(pr: PullRequest) -> list:
    return list(pr.get_files())

def get_prs(repo_name: str, include_closeds: bool = False) -> Iterable[PullRequest]:
    """
    Busca a lista de Pull Requests de um repositório.

    Args:
        repo_name: No formato "owner/repo" (ex: "torvalds/linux")
        include_closeds: True para incluir Pull Requests fechadas

    Returns:
        Lista de objetos PullRequestFile do PyGithub.

    Raises:
        SystemExit: Se o repo ou PR não existirem, ou o token for inválido.
    """
    try:
        client = get_github_client()
        repo = client.get_repo(repo_name)
        state = 'all' if include_closeds else 'open'
        return repo.get_pulls(state=state)
    except GithubException as e:
        raise SystemExit(
            f"Erro ao acessar o GitHub: {e.data.get('message', str(e))}")
