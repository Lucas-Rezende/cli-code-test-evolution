# cli_code_test_evolution/repository_parser.py
from __future__ import annotations
import re
from dataclasses import dataclass
from urllib.parse import urlparse

class RepositoryInputError(ValueError):
    """Entrada de repositório ou seleção de PR inválida."""

@dataclass(frozen=True)
class RepositoryReference:
    full_name: str
    pr_number: int | None = None

_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

def normalize_repository(value: str) -> RepositoryReference:
    raw = value.strip().rstrip("/")
    if not raw:
        raise RepositoryInputError("Informe um repositório.")

    if raw.startswith(("http://", "https://")):
        parsed = urlparse(raw)
        if parsed.hostname not in {"github.com", "www.github.com"}:
            raise RepositoryInputError("Apenas URLs do GitHub são aceitas.")
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) < 2:
            raise RepositoryInputError("URL de repositório incompleta.")
        owner, repository = parts[0], parts[1]
        if repository.endswith(".git"):
            repository = repository[:-4]
        pr_number = None
        if len(parts) >= 4 and parts[2] == "pull":
            if not parts[3].isdigit() or len(parts) != 4:
                raise RepositoryInputError("URL de Pull Request inválida.")
            pr_number = int(parts[3])
        elif len(parts) > 2:
            raise RepositoryInputError(
                "Use a URL do repositório ou a URL direta de um Pull Request."
            )
        full_name = f"{owner}/{repository}"
    else:
        full_name = raw[:-4] if raw.endswith(".git") else raw
        pr_number = None

    if not _NAME_RE.fullmatch(full_name):
        raise RepositoryInputError(
            "Use owner/repository ou uma URL HTTPS do GitHub."
        )
    return RepositoryReference(full_name=full_name, pr_number=pr_number)

def parse_pr_range(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d+):(\d+)", value.strip())
    if not match:
        raise RepositoryInputError("O intervalo deve usar o formato START:END.")
    start, end = map(int, match.groups())
    if start < 1 or end < start:
        raise RepositoryInputError("O intervalo de PRs é inválido.")
    return start, end

def validate_selection(
    embedded_pr: int | None,
    pr_number: int | None,
    pr_range: str | None,
    all_prs: bool,
) -> tuple[str, int | tuple[int, int] | None]:
    selected = sum(
        [
            embedded_pr is not None,
            pr_number is not None,
            pr_range is not None,
            all_prs,
        ]
    )
    if selected != 1:
        raise RepositoryInputError(
            "Escolha exatamente uma opção: URL de PR, --pr, --range ou --all."
        )
    if embedded_pr is not None:
        return "pr", embedded_pr
    if pr_number is not None:
        if pr_number < 1:
            raise RepositoryInputError("O número do PR deve ser positivo.")
        return "pr", pr_number
    if pr_range is not None:
        return "range", parse_pr_range(pr_range)
    return "all", None