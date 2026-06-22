import json

from cli_code_test_evolution.models import AnalysisReport, FileMetrics
from cli_code_test_evolution.analyzer import analyze_pr
from cli_code_test_evolution.reporter import (
    print_report,
    write_html_report,
    write_json_report,
)


def report():
    pr = analyze_pr(
        number=9,
        title="<script>alert(1)</script>",
        state="open",
        url="https://github.com/o/r/pull/9",
        author="user",
        files=[
            FileMetrics(
                filename="src/a.py",
                category="code",
                status="modified",
                added_loc=12,
            )
        ],
    )
    return AnalysisReport(
        repository="o/r",
        selection="PR #9",
        state_filter="all",
        generated_at="2026-06-21T00:00:00+00:00",
        pull_requests=[pr],
    )


def test_writes_self_contained_escaped_html(tmp_path):
    output = write_html_report(report(), tmp_path / "report.html")
    content = output.read_text(encoding="utf-8")

    assert "Possível dívida de testes" in content
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in content
    assert "<script>alert(1)</script>" not in content
    assert "não executa os testes" in content


def test_writes_valid_json(tmp_path):
    output = write_json_report(report(), tmp_path / "report.json")
    data = output.read_text(encoding="utf-8")
    payload = json.loads(data)
    assert payload["repository"] == "o/r"
    assert payload["pull_requests"][0]["net_code_loc"] == 12
