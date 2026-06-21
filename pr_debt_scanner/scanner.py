from __future__ import annotations
from datetime import datetime, timezone
from typing import Any

from pr_debt_scanner.analyzer import (analyze_pr, classify_python_file, rank_pull_requests)
from pr_debt_scanner.github_client import (get_file_content, get_pr_files, get_repository, select_pull_requests)
from pr_debt_scanner.line_counter import analyze_python_patch
from pr_debt_scanner.models import AnalysisReport, FileMetrics

def _analyze_file(repository: Any, pull_request: Any, changed_file: Any) -> FileMetrics | None:
    filename = changed_file.filename
    previous_filename = getattr(changed_file, "previous_filename", None)
    category = classify_python_file(filename)
    if category is None and previous_filename:
        category = classify_python_file(previous_filename)
    if category is None:
        return None

    status = getattr(changed_file, "status", "modified")
    old_path = previous_filename or filename
    old_content = (
        None
        if status == "added"
        else get_file_content(repository, old_path, pull_request.base.sha)
    )
    new_content = (
        None
        if status == "removed"
        else get_file_content(repository, filename, pull_request.head.sha)
    )
    metrics = analyze_python_patch(
        getattr(changed_file, "patch", None),
        old_content,
        new_content,
        expected_added=getattr(changed_file, "additions", None),
        expected_removed=getattr(changed_file, "deletions", None),
    )
    return FileMetrics(
        filename=filename,
        category=category,
        status=status,
        added_loc=metrics.added_loc,
        removed_loc=metrics.removed_loc,
        ignored_added=metrics.ignored_added,
        ignored_removed=metrics.ignored_removed,
        analyzable=metrics.analyzable,
        note=metrics.note,
    )

def scan_repository(
    repository_name: str,
    selection_kind: str,
    selection_value: int | tuple[int, int] | None,
    *,
    state: str = "all",
    medium_threshold: int = 10,
    high_threshold: int = 50,
) -> AnalysisReport:
    repository = get_repository(repository_name)
    selected = select_pull_requests(
        repository,
        selection_kind,
        selection_value,
        state,
    )
    results = []
    for pull_request in selected.pull_requests:
        files = [
            result
            for changed_file in get_pr_files(pull_request)
            if (result := _analyze_file(repository, pull_request, changed_file))
            is not None
        ]
        results.append(
            analyze_pr(
                number=pull_request.number,
                title=pull_request.title,
                state=pull_request.state,
                url=pull_request.html_url,
                author=getattr(pull_request.user, "login", "desconhecido"),
                files=files,
                medium_threshold=medium_threshold,
                high_threshold=high_threshold,
            )
        )

    if selection_kind == "pr":
        selection_text = f"PR #{selection_value}"
    elif selection_kind == "range":
        selection_text = f"PRs #{selection_value[0]} a #{selection_value[1]}"
    else:
        selection_text = f"todos os PRs ({state})"

    return AnalysisReport(
        repository=repository_name,
        selection=selection_text,
        state_filter=state,
        generated_at=datetime.now(timezone.utc).isoformat(),
        pull_requests=rank_pull_requests(results),
        skipped_prs=selected.skipped,
    )
