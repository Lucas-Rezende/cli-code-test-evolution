# pr_debt_scanner/analyzer.py
from pr_debt_scanner.line_counter import count_effective_lines

_TEST_DIRS = frozenset({"test", "tests", "spec", "specs"})


def is_test_file(filename: str) -> bool:
    """
    Detecta se um arquivo é de teste pela sua localização ou nome.
    Exemplos que retornam True:
      - tests/test_main.py
      - src/test_utils.py
      - utils_test.py
    """
    parts = filename.lower().split("/")
    basename = parts[-1]
    dirs = set(parts[:-1])

    return (
        bool(dirs & _TEST_DIRS)          # está em diretório de teste
        or basename.startswith("test_")  # nome começa com test_
        or basename.endswith("_test.py")  # nome termina com _test.py
    )
