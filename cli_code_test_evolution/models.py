# cli_code_test_evolution/models.py
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

@dataclass
class IgnoredLines:
    blank: int = 0
    comments: int = 0
    docstrings: int = 0

@dataclass
class FileMetrics:
    filename: str
    category: str
    status: str
    added_loc: int = 0
    removed_loc: int = 0
    ignored_added: IgnoredLines = field(default_factory=IgnoredLines)
    ignored_removed: IgnoredLines = field(default_factory=IgnoredLines)
    analyzable: bool = True
    note: str | None = None

    @property
    def net_loc(self) -> int:
        return self.added_loc - self.removed_loc

    @property
    def churn(self) -> int:
        return self.added_loc + self.removed_loc

@dataclass
class PullRequestMetrics:
    number: int
    title: str
    state: str
    url: str
    author: str
    code_added_loc: int
    code_removed_loc: int
    test_added_loc: int
    test_removed_loc: int
    code_files_changed: int
    test_files_changed: int
    classification: str
    label: str
    risk: str
    score: int
    reason: str
    recommendation: str
    files: list[FileMetrics] = field(default_factory=list)

    @property
    def net_code_loc(self) -> int:
        return self.code_added_loc - self.code_removed_loc

    @property
    def code_churn(self) -> int:
        return self.code_added_loc + self.code_removed_loc

    @property
    def net_test_loc(self) -> int:
        return self.test_added_loc - self.test_removed_loc

    @property
    def test_churn(self) -> int:
        return self.test_added_loc + self.test_removed_loc

@dataclass
class AnalysisReport:
    repository: str
    selection: str
    state_filter: str
    generated_at: str
    pull_requests: list[PullRequestMetrics]
    skipped_prs: list[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for pr_data, pr in zip(data["pull_requests"], self.pull_requests):
            pr_data.update(
                net_code_loc=pr.net_code_loc,
                code_churn=pr.code_churn,
                net_test_loc=pr.net_test_loc,
                test_churn=pr.test_churn,
            )
            for file_data, file_metrics in zip(pr_data["files"], pr.files):
                file_data.update(
                    net_loc=file_metrics.net_loc,
                    churn=file_metrics.churn,
                )
        return data