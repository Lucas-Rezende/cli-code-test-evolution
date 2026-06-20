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
