# Teste gerado totalmente por IA
import os
import unittest
from unittest.mock import MagicMock, patch

from github import Github, GithubException

from cli_code_test_evolution.github_client import (
    GitHubClientError,
    get_file_content,
    get_github_client,
    get_pr_files,
    select_pull_requests,
)

def make_mock_file(filename: str, patch_text: str | None) -> MagicMock:
    """Cria um mock de PullRequestFile do PyGithub."""
    file = MagicMock()
    file.filename = filename
    file.patch = patch_text
    return file


class TestGithubClient(unittest.TestCase):

    @patch.dict(
        os.environ,
        {"GITHUB_TOKEN": "token_falso_para_testes"},
        clear=True,
    )
    def test_get_github_client_com_token(self):
        """Testa se o cliente é instanciado quando o token existe."""
        client = get_github_client()

        self.assertIsInstance(client, Github)

    @patch.dict(os.environ, {}, clear=True)
    def test_get_github_client_sem_token(self):
        """Testa se lança um erro legível quando não há token."""
        with self.assertRaisesRegex(GitHubClientError, "GITHUB_TOKEN"):
            get_github_client()

    def test_get_pr_files_sucesso(self):
        """Testa a obtenção bem-sucedida dos arquivos de um PR."""
        mock_pr = MagicMock()
        mock_files = [
            make_mock_file("src/main.py", "+x = 1"),
            make_mock_file("tests/test_main.py", "+assert x == 1"),
        ]
        mock_pr.get_files.return_value = mock_files

        files = get_pr_files(mock_pr)

        self.assertEqual(len(files), 2)
        self.assertEqual(files[0].filename, "src/main.py")
        self.assertEqual(files[1].filename, "tests/test_main.py")
        mock_pr.get_files.assert_called_once_with()

    def test_get_pr_files_erro_github(self):
        """Testa o comportamento quando a API devolve um erro."""
        mock_pr = MagicMock()
        mock_pr.get_files.side_effect = GithubException(
            status=404,
            data={"message": "Not Found"},
        )

        with self.assertRaisesRegex(
            GitHubClientError,
            "Não foi possível obter os arquivos do PR",
        ):
            get_pr_files(mock_pr)

    def test_seleciona_pr_especifico_e_respeita_estado(self):
        mock_repo = MagicMock()
        mock_pr = MagicMock(number=7, state="closed")
        mock_pr.state = "closed"
        mock_repo.get_pull.return_value = mock_pr

        selected = select_pull_requests(mock_repo, "pr", 7, "open")

        self.assertEqual(selected.pull_requests, [])
        self.assertEqual(selected.skipped, [7])
        mock_repo.get_pull.assert_called_once_with(7)

    def test_seleciona_intervalo_e_ignora_pr_inexistente(self):
        mock_repo = MagicMock()
        pull_2 = MagicMock(number=2, state="open")
        pull_2.number = 2
        pull_2.state = "open"
        pull_4 = MagicMock(number=4, state="closed")
        pull_4.number = 4
        pull_4.state = "closed"

        def get_pull(number):
            if number == 2:
                return pull_2
            if number == 4:
                return pull_4
            raise GithubException(404, {"message": "Not Found"})

        mock_repo.get_pull.side_effect = get_pull

        selected = select_pull_requests(
            mock_repo,
            "range",
            (2, 4),
            "all",
        )

        self.assertEqual(
            [pull.number for pull in selected.pull_requests],
            [2, 4],
        )
        self.assertEqual(selected.skipped, [3])

    def test_seleciona_todos_os_prs(self):
        mock_repo = MagicMock()
        mock_pr = MagicMock(number=1, state="closed")
        mock_pr.state = "closed"
        mock_repo.get_pulls.return_value = [mock_pr]

        selected = select_pull_requests(
            mock_repo,
            "all",
            None,
            "closed",
        )

        self.assertEqual(selected.pull_requests, [mock_pr])
        mock_repo.get_pulls.assert_called_once_with(state="closed")

    def test_get_file_content_sucesso(self):
        mock_repo = MagicMock()
        mock_content = MagicMock()
        mock_content.decoded_content = "ação".encode()
        mock_repo.get_contents.return_value = mock_content

        content = get_file_content(mock_repo, "src/main.py", "sha")

        self.assertEqual(content, "ação")
        mock_repo.get_contents.assert_called_once_with(
            "src/main.py",
            ref="sha",
        )

    def test_get_file_content_inexistente(self):
        mock_repo = MagicMock()
        mock_repo.get_contents.side_effect = GithubException(404,{"message": "Not Found"})
        content = get_file_content(mock_repo, "src/main.py", "sha")
        self.assertIsNone(content)

if __name__ == '__main__':
    unittest.main()