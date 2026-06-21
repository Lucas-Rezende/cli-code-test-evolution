from pathlib import Path

from typer.testing import CliRunner

from cli_code_test_evolution.main import app
from cli_code_test_evolution.models import AnalysisReport

runner = CliRunner()


def empty_report() -> AnalysisReport:
    return AnalysisReport(
        repository="owner/repo",
        selection="PR #1",
        state_filter="all",
        generated_at="2026-06-21T00:00:00+00:00",
        pull_requests=[],
    )


def test_scan_accepts_repository_and_specific_pr(monkeypatch, tmp_path):
    captured = {}

    def fake_scan(repository, kind, value, **kwargs):
        captured.update(repository=repository, kind=kind, value=value)
        return empty_report()

    monkeypatch.setattr("cli_code_test_evolution.main.scan_repository", fake_scan)
    output = tmp_path / "report.html"

    result = runner.invoke(
        app,
        ["scan", "https://github.com/owner/repo", "--pr", "1", "-o", str(output)],
    )

    assert result.exit_code == 0
    assert captured == {"repository": "owner/repo", "kind": "pr", "value": 1}
    assert output.exists()
    assert "Relatório HTML" in result.stdout


def test_scan_accepts_direct_pr_url(monkeypatch, tmp_path):
    captured = {}

    def fake_scan(repository, kind, value, **kwargs):
        captured.update(kind=kind, value=value)
        return empty_report()

    monkeypatch.setattr("cli_code_test_evolution.main.scan_repository", fake_scan)

    result = runner.invoke(
        app,
        [
            "scan",
            "https://github.com/owner/repo/pull/8",
            "-o",
            str(tmp_path / "report.html"),
        ],
    )

    assert result.exit_code == 0
    assert captured == {"kind": "pr", "value": 8}


def test_scan_rejects_ambiguous_selection():
    result = runner.invoke(
        app,
        ["scan", "owner/repo", "--pr", "1", "--all"],
    )

    assert result.exit_code == 2
    assert "exatamente uma opção" in result.output
