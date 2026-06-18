import unittest
from unittest.mock import MagicMock

from pr_debt_scanner.line_counter import count_effective_lines

def make_mock_file(filename: str, patch: str | None) -> MagicMock:
    """Cria um mock de PullRequestFile do PyGithub."""
    f = MagicMock()
    f.filename = filename
    f.patch = patch
    return f

class TestLineCounter(unittest.TestCase):

    def test_conta_linha_de_codigo():
        patch = "+x = 1\n"
        assert count_effective_lines(patch) == 1

    def test_ignora_comentario():
        patch = "+# isso é um comentário\n"
        assert count_effective_lines(patch) == 0

    def test_ignora_linha_em_branco():
        patch = "+\n+   \n"
        assert count_effective_lines(patch) == 0

    def test_ignora_cabecalho_diff():
        patch = "+++ b/arquivo.py\n+x = 1\n"
        assert count_effective_lines(patch) == 1

    def test_patch_none_retorna_zero():
        assert count_effective_lines(None) == 0

    def test_nao_conta_linhas_removidas():
        patch = "-x = 1\n"
        assert count_effective_lines(patch) == 0


if __name__ == '__main__':
    unittest.main()
