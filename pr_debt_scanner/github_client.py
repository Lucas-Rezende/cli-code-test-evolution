# pr_debt_scanner/github_client.py
from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from github import Auth, Github, GithubException

load_dotenv()

class GitHubClientError(RuntimeError):
    """Erro de client durante uma consulta à API do GitHub."""

@dataclass
class PullRequestSelection:
    pull_requests: list[Any]
    skipped: list[int]

def _message(exc: GithubException) -> str:
    data = exc.data if isinstance(exc.data, dict) else {}
    return str(data.get("message") or exc)

def get_github_client() -> Github:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise GitHubClientError(
            "Variável GITHUB_TOKEN não encontrada. "
            "Crie um arquivo .env com GITHUB_TOKEN=seu_token."
        )
    return Github(auth=Auth.Token(token))

def get_repository(full_name: str, client: Github | None = None) -> Any:
    try:
        return (client or get_github_client()).get_repo(full_name)
    except GithubException as exc:
        raise GitHubClientError(
            f"Não foi possível acessar {full_name}: {_message(exc)}"
        ) from exc

def select_pull_requests(
    repository: Any,
    selection_kind: str,
    selection_value: int | tuple[int, int] | None,
    state: str,
) -> PullRequestSelection:
    if state not in {"open", "closed", "all"}:
        raise GitHubClientError("--state deve ser open, closed ou all.")

    if selection_kind == "all":
        try:
            return PullRequestSelection(
                pull_requests=list(repository.get_pulls(state=state)),
                skipped=[],
            )
        except GithubException as exc:
            raise GitHubClientError(
                f"Não foi possível listar os PRs: {_message(exc)}"
            ) from exc

    numbers = (
        [int(selection_value)]
        if selection_kind == "pr"
        else list(range(selection_value[0], selection_value[1] + 1))
    )
    pull_requests: list[Any] = []
    skipped: list[int] = []
    for number in numbers:
        try:
            pr = repository.get_pull(number)
        except GithubException as exc:
            if exc.status == 404 and selection_kind == "range":
                skipped.append(number)
                continue
            raise GitHubClientError(f"Não foi possível acessar o PR #{number}: {_message(exc)}") from exc
        if state == "all" or pr.state == state:
            pull_requests.append(pr)
        else:
            skipped.append(number)
    return PullRequestSelection(pull_requests=pull_requests, skipped=skipped)

def get_pr_files_from_pr(pull_request: Any) -> list[Any]:
    try:
        return list(pull_request.get_files())
    except GithubException as exc:
        raise GitHubClientError(f"Não foi possível obter os arquivos do PR: {_message(exc)}") from exc

def get_file_content(repository: Any, path: str, ref: str) -> str | None:
    try:
        content_file = repository.get_contents(path, ref=ref)
    except GithubException as exc:
        if exc.status in {404, 422}:
            return None
        raise GitHubClientError(f"Não foi possível obter {path} em {ref}: {_message(exc)}") from exc

    if isinstance(content_file, list):
        return None
    try:
        if getattr(content_file, "decoded_content", None) is not None:
            raw = content_file.decoded_content
        else:
            raw = base64.b64decode(content_file.content)
        return raw.decode("utf-8")
    except (UnicodeDecodeError, ValueError):
        return None