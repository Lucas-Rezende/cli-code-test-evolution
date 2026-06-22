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


def test_scanner_describes_pr_list_and_updates_progress(monkeypatch):
    pull_requests = [
        SimpleNamespace(
            number=2,
            title="PR 2",
            state="closed",
            html_url="https://github.com/o/r/pull/2",
            user=SimpleNamespace(login="dev"),
            base=SimpleNamespace(sha="base"),
            head=SimpleNamespace(sha="head"),
        ),
        SimpleNamespace(
            number=4,
            title="PR 4",
            state="closed",
            html_url="https://github.com/o/r/pull/4",
            user=SimpleNamespace(login="dev"),
            base=SimpleNamespace(sha="base"),
            head=SimpleNamespace(sha="head"),
        ),
    ]
    advances = []

    class FakeProgress:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def add_task(self, description, total):
            advances.append(("total", total))
            return 1

        def advance(self, task):
            advances.append(("advance", task))

    monkeypatch.setattr(
        "cli_code_test_evolution.scanner.get_repository",
        lambda name: object(),
    )
    monkeypatch.setattr(
        "cli_code_test_evolution.scanner.select_pull_requests",
        lambda *args: SimpleNamespace(
            pull_requests=pull_requests,
            skipped=[3],
        ),
    )
    monkeypatch.setattr(
        "cli_code_test_evolution.scanner.get_pr_files",
        lambda pull_request: [],
    )
    monkeypatch.setattr(
        "cli_code_test_evolution.scanner.Progress",
        FakeProgress,
    )

    report = scan_repository("o/r", "list", [2, 3, 4])

    assert report.selection == "PRs #2, #3, #4"
    assert report.skipped_prs == [3]
    assert advances == [("total", 2), ("advance", 1), ("advance", 1)]
