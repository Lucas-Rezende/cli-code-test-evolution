import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def print_pr_report(repo: str, pr_number: int, result: dict, as_json: bool = False) -> None:
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

    # Veredito
    total = result["total_code_lines"]
    threshold = result["threshold"]
    has_tests = result["has_test_changes"]
    has_debt = result["has_debt"]

    console.print(
        "\nLinhas de código efetivas adicionadas: "
        f"[bold]{total}[/bold] (threshold: {threshold})")

    console.print(
        "Arquivos de teste modificados: "
        f"{'[green]Sim ✓[/green]' if has_tests else '[yellow]Não[/yellow]'}")

    if has_debt:
        console.print(
            Panel(
                "[bold red]⚠ DÍVIDA DE TESTES DETECTADA[/bold red]\n"
                f"Este PR adicionou [bold]{total}[/bold] linhas de código "
                "sem modificar nenhum arquivo de teste.",
                border_style="red"
            )
        )
    else:
        console.print(
            Panel(
                "[bold green]✓ Nenhuma dívida detectada[/bold green]",
                border_style="green"
            )
        )


def print_prs_report(repo: str, results: list[dict], as_json: bool = False) -> None:
    """Exibe o relatório dos Pull Requests de um repositório no terminal."""
    if as_json:
        print(json.dumps(results, indent=2))
        return

    # Cabeçalho
    console.print(f"\n[bold]Analisando:[/bold] {repo}\n")

    for result_dict in results:
        result = result_dict["result"]
        state = result_dict["state"]
        id = result_dict["number"]

        console.print(
            f"\n[bold]Pull request:[/bold] {id} [bold]({state})[/bold]\n")

        # Tabela de arquivos
        table = Table(title="Arquivos Analisados (não-teste)", show_lines=True)
        table.add_column("Arquivo", style="cyan")
        table.add_column("Linhas Efetivas", justify="right")

        for f in result["analyzed_files"]:
            table.add_row(f["filename"], str(f["effective_lines"]))

        console.print(table)

        # Veredito
        total = result["total_code_lines"]
        threshold = result["threshold"]
        has_tests = result["has_test_changes"]
        has_debt = result["has_debt"]

        console.print(
            "\nLinhas de código efetivas adicionadas: "
            f"[bold]{total}[/bold] (threshold: {threshold})")

        console.print(
            "Arquivos de teste modificados: "
            f"{'[green]Sim ✓[/green]' if has_tests else '[yellow]Não[/yellow]'}")

        if has_debt:
            console.print(
                Panel(
                    "[bold red]⚠ DÍVIDA DE TESTES DETECTADA[/bold red]\n"
                    f"Este PR adicionou [bold]{total}[/bold] linhas de código "
                    "sem modificar nenhum arquivo de teste.",
                    border_style="red"
                )
            )
        else:
            console.print(
                Panel(
                    "[bold green]✓ Nenhuma dívida detectada[/bold green]",
                    border_style="green"
                )
            )
