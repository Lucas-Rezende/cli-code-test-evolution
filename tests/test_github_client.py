# Teste gerado totalmente por IA
import os
import unittest
from unittest.mock import MagicMock, patch
from github import Github, GithubException

from pr_debt_scanner.github_client import get_github_client, get_pr_files
def make_mock_file(filename: str, patch: str | None) -> MagicMock:
    """Cria um mock de PullRequestFile do PyGithub."""
    f = MagicMock()
    f.filename = filename
    f.patch = patch
    return f

class TestGithubClient(unittest.TestCase):

    @patch.dict(os.environ, {"GITHUB_TOKEN": "token_falso_para_testes"}, clear=True)
    def test_get_github_client_com_token(self):
        """Testa se o cliente é instanciado corretamente quando o token existe."""
        client = get_github_client()
        self.assertIsInstance(client, Github)

    @patch.dict(os.environ, {}, clear=True)
    def test_get_github_client_sem_token(self):
        """Testa se lança um EnvironmentError quando não há token."""
        # Usa assertRaisesRegex para validar não só a exceção, mas também a mensagem
        with self.assertRaisesRegex(EnvironmentError, "Variável GITHUB_TOKEN não encontrada"):
            get_github_client()

    @patch("pr_debt_scanner.github_client.get_github_client")
    def test_get_pr_files_sucesso(self, mock_get_client):
        """Testa a obtenção bem-sucedida da lista de ficheiros de um PR."""
        # 1. Configurar a cadeia de mocks
        mock_client = MagicMock()
        mock_repo = MagicMock()
        mock_pr = MagicMock()

        mock_get_client.return_value = mock_client
        mock_client.get_repo.return_value = mock_repo
        mock_repo.get_pull.return_value = mock_pr

        # 2. Configurar os ficheiros simulados
        mock_files = [
            make_mock_file("src/main.py", "+x = 1"),
            make_mock_file("tests/test_main.py", "+assert x == 1")
        ]
        mock_pr.get_files.return_value = mock_files

        # 3. Executar a função que queremos testar
        files = get_pr_files("octocat/Hello-World", 1)

        self.assertEqual(len(files), 2)
        self.assertEqual(files[0].filename, "src/main.py")
        self.assertEqual(files[1].filename, "tests/test_main.py")
        
        mock_client.get_repo.assert_called_once_with("octocat/Hello-World")
        mock_repo.get_pull.assert_called_once_with(1)

    @patch("pr_debt_scanner.github_client.get_github_client")
    def test_get_pr_files_erro_github(self, mock_get_client):
        """Testa o comportamento quando a API do GitHub devolve um erro (ex: Repo não encontrado)."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Criar e configurar a exceção simulada do PyGithub
        excecao_simulada = GithubException(status=404, data={"message": "Not Found"})
        mock_client.get_repo.side_effect = excecao_simulada

        # Validar o SystemExit com a mensagem de erro correta
        with self.assertRaisesRegex(SystemExit, "Erro ao acessar o GitHub: Not Found"):
            get_pr_files("repo/inexistente", 999)

if __name__ == '__main__':
    unittest.main()