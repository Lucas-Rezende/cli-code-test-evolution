# cli_code_test_evolution/main.py
from __future__ import annotations

from pathlib import Path

import typer
from typing import Optional

from cli_code_test_evolution.github_client import GitHubClientError
from cli_code_test_evolution.reporter import (
    print_report,
    write_html_report,
    write_json_report,
)

from cli_code_test_evolution.repository_parser import (
    RepositoryInputError,
    normalize_repository,
    validate_selection,
)
from cli_code_test_evolution.scanner import scan_repository

app = typer.Typer(
    name="code-test-evo",
    help="Detecta dívida de testes em Pull Requests do GitHub.",
    add_completion=False,
)


def _run_scan(
    repository: str,
    pr_number: int | None,
    pr_range: str | None,
    pr_list: str | None,
    all_prs: bool,
    state: str,
    medium_threshold: int,
    high_threshold: int,
    output: Path,
    json_output: Path | None,
) -> None:
    try:
        reference = normalize_repository(repository)
        selection_kind, selection_value = validate_selection(
            reference.pr_number,
            pr_number,
            pr_range,
            pr_list,
            all_prs,
        )
        report = scan_repository(
            reference.full_name,
            selection_kind,
            selection_value,
            state=state,
            medium_threshold=medium_threshold,
            high_threshold=high_threshold,
        )
        html_report_path = write_html_report(report, output)
        if json_output is not None:
            json_report_path = write_json_report(report, json_output)
    except (RepositoryInputError, GitHubClientError, ValueError) as exc:
        typer.echo(f"Erro: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    print_report(report)
    typer.echo(f"\nRelatório HTML: {html_report_path}")

    if json_output is not None:
        typer.echo(f"Relatório JSON: {json_report_path}")

    if any(item.classification == "possible_debt" for item in report.pull_requests):
        raise typer.Exit(code=1)


@app.command()
def scan(
    repo: str = typer.Argument(
        ...,
        help="Repositório no formato owner/repo (ex: octocat/Hello-World) ou URL do repositório",
    ),
    pr_number: int | None = typer.Option(
        None, "--pr", help="Um PR específico."),
    pr_range: str | None = typer.Option(
        None,
        "--range",
        help="Intervalo inclusivo no formato START:END.",
    ),
    pr_list: str | None = typer.Option(
        None,
        "--list",
        help="Lista de PRs no formato PR1,PR2,...,PRn.",
    ),
    all_prs: bool = typer.Option(False, "--all", help="Analisa todos os PRs."),
    state: str = typer.Option(
        "all",
        "--state",
        help="Filtro de estado: open, closed ou all.",
    ),
    medium_threshold: int = typer.Option(
        10,
        "--medium-threshold",
        min=1,
        help="LOC adicionadas sem testes para risco médio.",
    ),
    high_threshold: int = typer.Option(
        50,
        "--high-threshold",
        min=2,
        help="LOC adicionadas sem testes para risco alto.",
    ),
    output: Path = typer.Option(
        Path("code-test-evo-report.html"),
        "--output",
        "-o",
        help="Caminho do relatório HTML.",
    ),
    json_output: Optional[Path] = typer.Option(
        None,
        "--json",
        help="Caminho do relatório JSON. Caso não especificado, não gera o relatório em JSON.",
    ),
) -> None:
    """Analisa um PR, um intervalo ou todos os PRs sem clonar o repositório."""
    _run_scan(
        repo,
        pr_number,
        pr_range,
        pr_list,
        all_prs,
        state,
        medium_threshold,
        high_threshold,
        output,
        json_output,
    )


@app.command("scan-repo", hidden=True)
def scan_repo(
    repository: str = typer.Argument(...),
    state: str = typer.Option("all", "--state"),
    medium_threshold: int = typer.Option(10, "--medium-threshold", min=1),
    high_threshold: int = typer.Option(50, "--high-threshold", min=2),
    output: Path = typer.Option(
        Path("code-test-evo-report.html"), "--output", "-o"),
    json_output: Path | None = typer.Option(None, "--json"),
) -> None:
    """Alias de compatibilidade para scan REPOSITORY --all."""
    _run_scan(
        repository,
        None,
        None,
        None,
        True,
        state,
        medium_threshold,
        high_threshold,
        output,
        json_output,
    )


if __name__ == "__main__":
    app()
