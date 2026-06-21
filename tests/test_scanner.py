from types import SimpleNamespace

from cli_code_test_evolution.scanner import scan_repository


def test_scanner_fetches_base_and_head_content_and_aggregates(monkeypatch):
    changed_file = SimpleNamespace(
        filename="src/calculate.py",
        previous_filename=None,
        status="modified",
        additions=1,
        deletions=1,
        patch="@@ -1 +1 @@\n-x = 1\n+x = 2\n",
    )
    pr = SimpleNamespace(
        number=3,
        title="Change calculation",
        state="closed",
        html_url="https://github.com/o/r/pull/3",
        user=SimpleNamespace(login="dev"),
        base=SimpleNamespace(sha="base"),
        head=SimpleNamespace(sha="head"),
    )
    repository = object()
    calls = []

    monkeypatch.setattr("cli_code_test_evolution.scanner.get_repository", lambda name: repository)
    monkeypatch.setattr(
        "cli_code_test_evolution.scanner.select_pull_requests",
        lambda *args: SimpleNamespace(pull_requests=[pr], skipped=[]),
    )
    monkeypatch.setattr(
        "cli_code_test_evolution.scanner.get_pr_files", lambda pull_request: [changed_file]
    )

    def content(repo, path, ref):
        calls.append((path, ref))
        return "x = 1\n" if ref == "base" else "x = 2\n"

    monkeypatch.setattr("cli_code_test_evolution.scanner.get_file_content", content)

    report = scan_repository("o/r", "pr", 3)

    assert calls == [("src/calculate.py", "base"), ("src/calculate.py", "head")]
    assert report.pull_requests[0].code_added_loc == 1
    assert report.pull_requests[0].code_removed_loc == 1
    assert report.pull_requests[0].classification == "possible_debt"
