# pr_debt_scanner/analyzer.py
from pr_debt_scanner.models import FileMetrics, PullRequestMetrics
from __future__ import annotations

_TEST_DIRS = frozenset({"test", "tests"})
_EXCLUDED_DIRS = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "env",
        "__pycache__",
        "build",
        "dist",
        "site-packages",
    }
)

RISK_ORDER = {
    "high": 7,
    "medium": 6,
    "attention": 5,
    "review": 4,
    "low": 3,
    "none": 0,
}

def _parts(filename: str) -> list[str]:
    return filename.replace("\\", "/").lower().split("/")

def is_test_file(filename: str) -> bool:
    """
    Detecta se um arquivo é de teste pela sua localização ou nome.
    Exemplos que retornam True:
      - tests/test_main.py
      - src/test_utils.py
      - utils_test.py
    """
    parts = _parts(filename)
    basename = parts[-1]
    return (
        bool(set(parts[:-1]) & _TEST_DIRS)          # está em diretório de teste
        or basename.startswith("test_")  # nome começa com test_
        or basename.endswith("_test.py")  # nome termina com _test.py
    )


def analyze_pr(files: list, threshold: int = 50) -> dict:
    """
    Analisa os arquivos de um PR e detecta possível dívida de testes.

    Retorna um dicionário com:
      - total_code_lines: int  — linhas efetivas adicionadas (não-teste)
      - has_test_changes: bool — se algum arquivo de teste foi alterado
      - has_debt: bool         — True se há dívida detectada
      - analyzed_files: list   — lista de arquivos analisados com detalhes
    """
    total_code_lines = 0
    has_test_changes = False
    analyzed_files = []

    for f in files:
        file_is_test = is_test_file(f.filename)
        if file_is_test:
            has_test_changes = True
        else:
            lines = count_effective_lines(f.patch)
            total_code_lines += lines
            analyzed_files.append({
                "filename": f.filename,
                "effective_lines": lines,
            })

    has_debt = (total_code_lines >= threshold) and not has_test_changes

    return {
        "total_code_lines": total_code_lines,
        "has_test_changes": has_test_changes,
        "has_debt": has_debt,
        "threshold": threshold,
        "analyzed_files": analyzed_files,
    }
