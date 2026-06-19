import unittest
from unittest.mock import MagicMock

from pr_debt_scanner.analyzer import is_test_file, analyze_pr

def make_mock_file(filename: str, patch: str | None) -> MagicMock:
    """Cria um mock de PullRequestFile do PyGithub."""
    f = MagicMock()
    f.filename = filename
    f.patch = patch
    return f

class TestFindTestsFiles(unittest.TestCase):

    def test_is_test_file_por_diretorio(self):
        assert is_test_file("tests/test_main.py") is True

    def test_is_test_file_por_sufixo(self):
        assert is_test_file("src/utils_test.py") is True

    def test_is_test_file_arquivo_normal(self):
        assert is_test_file("pr_debt_scanner/analyzer.py") is False


class TestDetectaDivida(unittest.TestCase):

    def test_analyze_pr_detecta_divida(self):
        files = [make_mock_file("src/main.py", "+x = 1\n" * 60)]
        result = analyze_pr(files, threshold=50)
        assert result["has_debt"] is True
        assert result["has_test_changes"] is False
        assert result["total_code_lines"] == 60

    def test_analyze_pr_sem_divida_com_testes(self):
        files = [
            make_mock_file("src/main.py", "+x = 1\n" * 60),
            make_mock_file("tests/test_main.py", "+assert x == 1\n"),
        ]
        result = analyze_pr(files, threshold=50)
        assert result["has_debt"] is False
        assert result["has_test_changes"] is True

    def test_analyze_pr_sem_divida_abaixo_threshold(self):
        files = [make_mock_file("src/utils.py", "+x = 1\n" * 10)]
        result = analyze_pr(files, threshold=50)
        assert result["has_debt"] is False

if __name__ == '__main__':
    unittest.main()
