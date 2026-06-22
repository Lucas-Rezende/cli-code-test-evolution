# cli_code_test_evolution/reporter.py
from __future__ import annotations

import json
from html import escape
from pathlib import Path

from rich.console import Console
from rich.table import Table

from cli_code_test_evolution.models import AnalysisReport, PullRequestMetrics

_RISK_LABELS = {
    "high": "Alto",
    "medium": "Médio",
    "attention": "Atenção",
    "review": "Revisão",
    "low": "Baixo",
    "none": "Nenhum",
}

def _totals(report: AnalysisReport) -> dict[str, int]:
    prs = report.pull_requests
    return {
        "prs": len(prs),
        "code_added": sum(item.code_added_loc for item in prs),
        "code_removed": sum(item.code_removed_loc for item in prs),
        "test_added": sum(item.test_added_loc for item in prs),
        "test_removed": sum(item.test_removed_loc for item in prs),
        "accompanied": sum(
            item.classification.startswith("accompanied") for item in prs
        ),
        "debt": sum(item.classification == "possible_debt" for item in prs),
        "tests_only": sum(item.classification == "tests_only" for item in prs),
        "neutral": sum(item.classification == "neutral" for item in prs),
    }

def print_report(report: AnalysisReport, *, as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return

    console = Console()
    totals = _totals(report)
    console.print(
        f"\n[bold]PR Debt Scanner[/bold] · {report.repository} · {report.selection}"
    )
    console.print(
        f"{totals['prs']} PR(s) · código +{totals['code_added']}/"
        f"-{totals['code_removed']} LOC · testes +{totals['test_added']}/"
        f"-{totals['test_removed']} LOC"
    )
    table = Table(show_lines=False)
    table.add_column("PR")
    table.add_column("Código", justify="right")
    table.add_column("Testes", justify="right")
    table.add_column("Classificação")
    table.add_column("Risco")
    for item in report.pull_requests:
        table.add_row(
            f"#{item.number}",
            f"+{item.code_added_loc}/-{item.code_removed_loc}",
            f"+{item.test_added_loc}/-{item.test_removed_loc}",
            item.label,
            _RISK_LABELS[item.risk],
        )
    console.print(table)
    if report.skipped_prs:
        console.print(
            "[yellow]PRs ignorados ou fora do filtro:[/yellow] "
            + ", ".join(f"#{number}" for number in report.skipped_prs)
        )


def _pr_row(item: PullRequestMetrics) -> str:
    return f"""
    <tr>
      <td><a href="{escape(item.url)}">#{item.number}</a><small>{escape(item.title)}</small></td>
      <td class="number">+{item.code_added_loc}<br><span>-{item.code_removed_loc}</span></td>
      <td class="number">+{item.test_added_loc}<br><span>-{item.test_removed_loc}</span></td>
      <td><span class="pill classification-{escape(item.classification)}">{escape(item.label)}</span></td>
      <td><span class="pill risk-{escape(item.risk)}">{escape(_RISK_LABELS[item.risk])}</span></td>
      <td class="number">{item.score}</td>
    </tr>"""


def _pr_details(item: PullRequestMetrics) -> str:
    file_rows = []
    for file_metrics in item.files:
        note = (
            f'<span class="warning">{escape(file_metrics.note)}</span>'
            if file_metrics.note
            else ""
        )
        file_rows.append(
            f"""
            <tr>
              <td><code>{escape(file_metrics.filename)}</code>{note}</td>
              <td>{escape(file_metrics.category)}</td>
              <td>{escape(file_metrics.status)}</td>
              <td class="number">+{file_metrics.added_loc}</td>
              <td class="number">-{file_metrics.removed_loc}</td>
              <td class="number">{file_metrics.net_loc:+d}</td>
              <td class="number">{file_metrics.churn}</td>
            </tr>"""
        )
    if not file_rows:
        file_rows.append(
            '<tr><td colspan="7">Nenhum arquivo Python relevante.</td></tr>'
        )
    return f"""
    <details>
      <summary>
        <strong>#{item.number} · {escape(item.title)}</strong>
        <span class="pill risk-{escape(item.risk)}">{escape(_RISK_LABELS[item.risk])}</span>
      </summary>
      <div class="detail-body">
        <p><strong>Por quê:</strong> {escape(item.reason)}</p>
        <p><strong>Recomendação:</strong> {escape(item.recommendation)}</p>
        <p class="metrics">Código líquido {item.net_code_loc:+d}, churn {item.code_churn} ·
        Testes líquidos {item.net_test_loc:+d}, churn {item.test_churn}</p>
        <div class="table-wrap"><table>
          <thead><tr><th>Arquivo</th><th>Tipo</th><th>Status</th><th>+LOC</th><th>-LOC</th><th>Líquido</th><th>Churn</th></tr></thead>
          <tbody>{''.join(file_rows)}</tbody>
        </table></div>
      </div>
    </details>"""


def write_html_report(report: AnalysisReport, output: str | Path) -> Path:
    output_path = Path(output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    totals = _totals(report)
    denominator = max(totals["prs"], 1)
    distribution = [
        ("Acompanhados", totals["accompanied"], "green"),
        ("Possíveis dívidas", totals["debt"], "red"),
        ("Somente testes", totals["tests_only"], "blue"),
        ("Neutros", totals["neutral"], "gray"),
    ]
    segments = "".join(
        f'<span class="{color}" style="width:{count / denominator * 100:.2f}%"></span>'
        for _, count, color in distribution
        if count
    )
    legend = "".join(
        f"<li><i class='{color}'></i>{escape(label)} <strong>{count}</strong></li>"
        for label, count, color in distribution
    )
    skipped = (
        "<p class='notice'>PRs ignorados ou fora do filtro: "
        + ", ".join(f"#{number}" for number in report.skipped_prs)
        + "</p>"
        if report.skipped_prs
        else ""
    )

    html = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PR Debt Scanner · {escape(report.repository)}</title>
<style>
:root{{--bg:#f5f7fb;--surface:#fff;--text:#172033;--muted:#667085;--line:#e4e7ec;--red:#d92d20;--red-bg:#fef3f2;--green:#067647;--green-bg:#ecfdf3;--blue:#175cd3;--blue-bg:#eff8ff;--amber:#b54708;--amber-bg:#fffaeb}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 Inter,Segoe UI,Arial,sans-serif}}
main{{max-width:1180px;margin:auto;padding:42px 24px 70px}} h1{{font-size:32px;margin:0 0 6px}} h2{{margin-top:36px}} p{{color:var(--muted)}}
.eyebrow{{color:#6941c6;font-weight:700;text-transform:uppercase;letter-spacing:.08em;font-size:12px}}
.notice{{background:#fff8e7;border-left:4px solid #f79009;padding:12px 16px;color:#7a2e0e;border-radius:8px}}
.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:24px 0}} .card{{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:18px;box-shadow:0 1px 2px #1018280a}} .card strong{{display:block;font-size:28px}} .card span{{color:var(--muted)}}
.distribution{{height:16px;background:#e9edf3;border-radius:999px;overflow:hidden;display:flex}} .distribution span{{height:100%}} .green{{background:#12b76a}} .red{{background:#f04438}} .blue{{background:#2e90fa}} .gray{{background:#98a2b3}}
.legend{{display:flex;gap:22px;flex-wrap:wrap;list-style:none;padding:0}} .legend i{{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:7px}}
.table-wrap{{overflow-x:auto}} table{{width:100%;border-collapse:collapse;background:var(--surface)}} th,td{{padding:13px 12px;text-align:left;border-bottom:1px solid var(--line)}} th{{font-size:12px;text-transform:uppercase;color:var(--muted)}} td small{{display:block;color:var(--muted);max-width:330px}} td span{{color:var(--muted)}} .number{{font-variant-numeric:tabular-nums;text-align:right}}
.pill{{display:inline-block;padding:4px 9px;border-radius:999px;font-size:12px;font-weight:700;white-space:nowrap}} .risk-high,.risk-medium,.classification-possible_debt{{color:var(--red);background:var(--red-bg)}} .risk-low,.risk-review,.risk-attention,.classification-accompanied_attention{{color:var(--amber);background:var(--amber-bg)}} .risk-none,.classification-accompanied{{color:var(--green);background:var(--green-bg)}} .classification-tests_only{{color:var(--blue);background:var(--blue-bg)}} .classification-neutral{{color:#475467;background:#f2f4f7}}
details{{background:#fff;border:1px solid var(--line);border-radius:12px;margin:12px 0;overflow:hidden}} summary{{cursor:pointer;padding:17px;display:flex;justify-content:space-between;gap:12px}} .detail-body{{border-top:1px solid var(--line);padding:4px 17px 17px}} .metrics{{font-family:ui-monospace,Consolas,monospace}} code{{font-size:12px}} .warning{{display:block;color:var(--amber);font-size:12px}}
footer{{margin-top:36px;color:var(--muted);font-size:13px}}
@media(max-width:760px){{.cards{{grid-template-columns:repeat(2,1fr)}} main{{padding:26px 14px}}}}
</style>
</head>
<body><main>
  <div class="eyebrow">Análise estrutural de Pull Requests</div>
  <h1>{escape(report.repository)}</h1>
  <p>{escape(report.selection)} · filtro de estado: {escape(report.state_filter)}</p>
  <p class="notice"><strong>O que este relatório prova:</strong> se mudanças efetivas em código Python foram acompanhadas por mudanças efetivas em arquivos de teste. Ele não executa os testes, não mede cobertura e não prova a qualidade ou relação contextual dos testes.</p>
  {skipped}
  <section class="cards">
    <div class="card"><strong>{totals['prs']}</strong><span>PRs analisados</span></div>
    <div class="card"><strong>{totals['debt']}</strong><span>possíveis dívidas</span></div>
    <div class="card"><strong>+{totals['code_added']} / -{totals['code_removed']}</strong><span>LOC de código</span></div>
    <div class="card"><strong>+{totals['test_added']} / -{totals['test_removed']}</strong><span>LOC de teste</span></div>
  </section>
  <section>
    <h2>Visão geral</h2>
    <div class="distribution">{segments}</div>
    <ul class="legend">{legend}</ul>
  </section>
  <section>
    <h2>Ranking de atenção</h2>
    <div class="table-wrap"><table>
      <thead><tr><th>PR</th><th>Código + / -</th><th>Testes + / -</th><th>Classificação</th><th>Risco</th><th>Score</th></tr></thead>
      <tbody>{''.join(_pr_row(item) for item in report.pull_requests)}</tbody>
    </table></div>
  </section>
  <section>
    <h2>Detalhes auditáveis</h2>
    {''.join(_pr_details(item) for item in report.pull_requests)}
  </section>
  <footer>Gerado em {escape(report.generated_at)}. LOC efetivas ignoram linhas vazias, comentários e docstrings Python reconhecidas.</footer>
</main></body></html>"""
    output_path.write_text(html, encoding="utf-8")
    return output_path
