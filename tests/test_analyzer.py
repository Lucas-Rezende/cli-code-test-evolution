import unittest

from cli_code_test_evolution.analyzer import (
    analyze_pr,
    classify_python_file,
    is_test_file,
    rank_pull_requests,
)
from cli_code_test_evolution.models import FileMetrics

def make_mock_file(
    filename: str,
    category: str,
    added: int = 0,
    removed: int = 0,
    status: str = "modified",
) -> FileMetrics:
    """Cria um arquivo com as métricas usadas pelo analisador."""
    return FileMetrics(
        filename=filename,
        category=category,
        status=status,
        added_loc=added,
        removed_loc=removed,
    )

def analyze(files: list[FileMetrics], number: int = 1):
    """Executa a análise com os dados básicos de um PR fictício."""
    return analyze_pr(
        number=number,
        title="PR de teste",
        state="open",
        url=f"https://github.com/owner/repo/pull/{number}",
        author="usuario",
        files=files,
    )

class TestFindTestsFiles(unittest.TestCase):
    def test_is_test_file_por_diretorio(self):
        assert is_test_file("tests/test_main.py") is True
        assert is_test_file(r"test\test_api.py") is True

    def test_is_test_file_por_sufixo(self):
        assert is_test_file("src/utils_test.py") is True

    def test_is_test_file_arquivo_normal(self):
        assert is_test_file("cli_code_test_evolution/analyzer.py") is False

    def test_classifica_arquivos_python(self):
        assert classify_python_file("src/service.py") == "code"
        assert classify_python_file("tests/test_service.py") == "test"
        assert classify_python_file("README.md") is None
        assert classify_python_file(".venv/lib/example.py") is None

class TestDetectaDivida(unittest.TestCase):

    def test_analyze_pr_detecta_divida(self):
        files = [make_mock_file("src/main.py", "code", added=60)]

        result = analyze(files)

        assert result.classification == "possible_debt"
        assert result.risk == "high"
        assert result.code_added_loc == 60
        assert result.test_files_changed == 0

    def test_analyze_pr_sem_divida_com_testes(self):
        files = [
            make_mock_file("src/main.py", "code", added=60),
            make_mock_file("tests/test_main.py", "test", added=1),
        ]

        result = analyze(files)

        assert result.classification == "accompanied"
        assert result.risk == "none"
        assert result.test_files_changed == 1

    def test_analyze_pr_divida_abaixo_threshold(self):
        files = [make_mock_file("src/utils.py", "code", added=9)]

        result = analyze(files)

        assert result.classification == "possible_debt"
        assert result.risk == "low"

    def test_analyze_pr_aplica_riscos(self):
        medium = analyze(
            [make_mock_file("src/medium.py", "code", added=10)]
        )
        high = analyze(
            [make_mock_file("src/high.py", "code", added=50)]
        )

        assert medium.risk == "medium"
        assert high.risk == "high"
        assert high.score == 50

    def test_analyze_pr_somente_testes(self):
        files = [make_mock_file("tests/test_main.py", "test", added=2)]

        result = analyze(files)

        assert result.classification == "tests_only"

    def test_analyze_pr_neutro(self):
        assert analyze([]).classification == "neutral"

    def test_analyze_pr_reducao_de_testes_com_crescimento(self):
        files = [
            make_mock_file("src/main.py", "code", added=5),
            make_mock_file(
                "tests/test_main.py",
                "test",
                added=1,
                removed=4,
            ),
        ]

        result = analyze(files)

        assert result.classification == "accompanied_attention"
        assert result.risk == "attention"
        assert result.net_test_loc == -3

    def test_analyze_pr_somente_remove_codigo(self):
        files = [make_mock_file("src/main.py", "code", removed=20)]

        result = analyze(files)

        assert result.classification == "possible_debt"
        assert result.risk == "review"
        assert result.score == 0

    def test_alteracao_sem_loc_e_rename(self):
        comment_only = analyze(
            [make_mock_file("src/main.py", "code")]
        )
        renamed_code = analyze(
            [make_mock_file("src/old.py", "code", status="renamed")]
        )
        renamed_test = analyze(
            [
                make_mock_file(
                    "tests/old.py",
                    "test",
                    status="renamed",
                )
            ]
        )

        assert comment_only.classification == "neutral"
        assert renamed_code.classification == "neutral"
        assert renamed_test.classification == "tests_only"

    def test_rank_pull_requests(self):
        low = analyze(
            [make_mock_file("src/low.py", "code", added=3)],
            number=1,
        )
        high = analyze(
            [make_mock_file("src/high.py", "code", added=70)],
            number=2,
        )
        accompanied = analyze(
            [
                make_mock_file("src/main.py", "code", added=100),
                make_mock_file("tests/test_main.py", "test", added=1),
            ],
            number=3,
        )

        ranked = rank_pull_requests([accompanied, low, high])

        assert [item.number for item in ranked] == [2, 1, 3]

if __name__ == "__main__":
    unittest.main()
