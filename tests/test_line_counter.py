import unittest
from difflib import unified_diff

from cli_code_test_evolution.line_counter import (
    analyze_python_patch,
    count_effective_lines,
)

def make_patch(old: str, new: str) -> str:
    """Cria um patch no formato unified diff."""
    return "".join(
        unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile="a/example.py",
            tofile="b/example.py",
        )
    )

class TestLineCounter(unittest.TestCase):

    def test_conta_linha_de_codigo(self):
        patch = "+x = 1\n"
        assert count_effective_lines(patch) == 1

    def test_ignora_comentario(self):
        patch = "+# isso é um comentário\n"
        assert count_effective_lines(patch) == 0

    def test_ignora_linha_em_branco(self):
        patch = "+\n+   \n"
        assert count_effective_lines(patch) == 0

    def test_ignora_cabecalho_diff(self):
        patch = "+++ b/arquivo.py\n+x = 1\n"
        assert count_effective_lines(patch) == 1

    def test_patch_none_retorna_zero(self):
        assert count_effective_lines(None) == 0

    def test_nao_conta_linhas_removidas(self):
        patch = "-x = 1\n"
        assert count_effective_lines(patch) == 0


class TestPythonPatchCounter(unittest.TestCase):

    def test_conta_codigo_adicionado_removido_e_ignorado(self):
        old = '"""documentação antiga"""\n# comentário antigo\nx = 1\n'
        new = (
            '"""documentação nova"""\n'
            "# comentário novo\n"
            "x = 2  # comentário inline\n"
            "\n"
            "@decorator\n"
            "def calculate():\n"
            "    return 3\n"
        )

        result = analyze_python_patch(make_patch(old, new), old, new)

        assert result.added_loc == 4
        assert result.removed_loc == 1
        assert result.ignored_added.blank == 1
        assert result.ignored_added.comments == 1
        assert result.ignored_added.docstrings == 1
        assert result.ignored_removed.comments == 1
        assert result.ignored_removed.docstrings == 1

    def test_ignora_docstrings_de_modulo_classe_e_funcao(self):
        old = ""
        new = '''"""módulo"""
class Service:
    """classe"""
    def run(self):
        """função"""
        return True
'''

        result = analyze_python_patch(make_patch(old, new), old, new)

        assert result.added_loc == 3
        assert result.ignored_added.docstrings == 3

    def test_string_multilinha_atribuida_conta_como_codigo(self):
        old = ""
        new = 'QUERY = """select\nfrom table\nwhere active = 1"""\n'

        result = analyze_python_patch(make_patch(old, new), old, new)

        assert result.added_loc == 3
        assert result.ignored_added.docstrings == 0

    def test_arquivo_novo_e_removido(self):
        new = "import os\n\nVALUE = 1\n"

        added = analyze_python_patch(make_patch("", new), None, new)
        removed = analyze_python_patch(make_patch(new, ""), new, None)

        assert added.added_loc == 2
        assert added.removed_loc == 0
        assert removed.added_loc == 0
        assert removed.removed_loc == 2

    def test_patch_ausente_nao_e_analisavel(self):
        result = analyze_python_patch(None, "x = 1\n", "x = 2\n")

        assert result.analyzable is False
        assert result.added_loc == 0
        assert "Patch ausente" in result.note

    def test_conteudo_necessario_ausente_nao_estima_loc(self):
        result = analyze_python_patch(
            "@@ -1 +1 @@\n-x = 1\n+x = 2\n",
            "x = 1\n",
            None,
        )

        assert result.analyzable is False
        assert result.added_loc == 0

    def test_patch_truncado_nao_retorna_resultado_parcial(self):
        result = analyze_python_patch(
            "@@ -1 +1 @@\n-x = 1\n+x = 2\n",
            "x = 1\n",
            "x = 2\n",
            expected_added=20,
            expected_removed=10,
        )

        assert result.analyzable is False
        assert result.added_loc == 0
        assert "truncado" in result.note


if __name__ == "__main__":
    unittest.main()
