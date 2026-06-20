# pr_debt_scanner/main.py
import typer
from pr_debt_scanner.github_client import get_pr_files, get_prs, get_pr_files_from_pr
from pr_debt_scanner.analyzer import analyze_pr
from pr_debt_scanner.reporter import print_pr_report, print_prs_report

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
    print_pr_report(repo, pr_number, result, as_json=as_json)
    if result["has_debt"]:
        raise typer.Exit(code=1)  # exit code 1 sinaliza problema (útil em CI)


@app.command("scan-repo")
def scan_repo(
    repo: str = typer.Argument(
        ...,
        help="Repositório no formato owner/repo (ex: octocat/Hello-World)",
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
    include_closeds: bool = typer.Option(
        False,
        "--closed",
        help="Inclui os Pull Requests fechadas",
    ),
):
    """Analisa todas os Pull Requests e faz um ranking de possíveis dívidas de testes."""
    prs = get_prs(repo, include_closeds=include_closeds)
    results = []
    for pr in prs:
        files = get_pr_files_from_pr(pr)
        result = analyze_pr(files, threshold=threshold)
        results.append(
            {
                "state": pr.state,
                "number": pr.number,
                "result": result,
            }
        )

    print_prs_report(repo, results, as_json=as_json)
