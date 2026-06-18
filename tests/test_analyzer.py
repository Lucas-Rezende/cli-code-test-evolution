from unittest.mock import MagicMock

def make_mock_file(filename: str, patch: str | None) -> MagicMock:
    """Cria um mock de PullRequestFile do PyGithub."""
    f = MagicMock()
    f.filename = filename
    f.patch = patch
    return f