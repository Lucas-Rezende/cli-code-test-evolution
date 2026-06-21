# pr_debt_scanner/analyzer.py
from __future__ import annotations

from pr_debt_scanner.models import FileMetrics, PullRequestMetrics

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

def analyze_pr(
    *,
    number: int,
    title: str,
    state: str,
    url: str,
    author: str,
    files: list[FileMetrics],
    medium_threshold: int = 10,
    high_threshold: int = 50,
) -> PullRequestMetrics:
    """
    Analisa os arquivos de um PR e detecta possível dívida de testes.
    """
    if medium_threshold < 1 or high_threshold <= medium_threshold:
        raise ValueError("Os limites devem satisfazer 1 <= médio < alto.")

    code_files = [
        item
        for item in files
        if item.category == "code" and _meaningful_file_change(item)
    ]
    test_files = [
        item
        for item in files
        if item.category == "test" and _meaningful_file_change(item)
    ]
    code_added = sum(item.added_loc for item in code_files)
    code_removed = sum(item.removed_loc for item in code_files)
    test_added = sum(item.added_loc for item in test_files)
    test_removed = sum(item.removed_loc for item in test_files)
    code_changed = bool(code_files)
    tests_changed = bool(test_files)
    net_code = code_added - code_removed
    net_test = test_added - test_removed

    if code_changed and tests_changed:
        if net_code > 0 and net_test < 0:
            classification = "accompanied_attention"
            label = "Testes alterados, mas com atenção"
            risk = "attention"
            reason = ( "O código cresceu e os testes também foram alterados, mas houve " "mais linhas de teste removidas do que adicionadas.")
            recommendation = ( "Confira se a redução dos testes foi intencional e se os " "cenários removidos continuam cobertos.")
        else:
            classification = "accompanied"
            label = "Acompanhado"
            risk = "none"
            reason = "O PR alterou tanto o código quanto os arquivos de teste."
            recommendation = ("Os testes acompanharam a mudança, o que é um bom sinal. Ainda " "assim, esta análise não verifica a qualidade nem a relação entre eles.")
    elif code_changed:
        classification = "possible_debt"
        label = "Possível dívida de testes"
        if code_added >= high_threshold:
            risk = "high"
        elif code_added >= medium_threshold:
            risk = "medium"
        elif code_added > 0:
            risk = "low"
        else:
            risk = "review"
        reason = "O PR alterou código Python, mas não modificou os testes."
        recommendation = (
            "Confira se o comportamento alterado deveria ter novos testes ou "
            "ajustes nos testes existentes."
            if code_added
            else "Confira se as remoções ou o refactor alteraram algum comportamento."
        )
    elif tests_changed:
        classification = "tests_only"
        label = "Melhoria ou manutenção de testes"
        risk = "none"
        reason = "O PR modificou apenas os arquivos de teste."
        recommendation = (
            "A mudança parece ser uma melhoria ou manutenção da suíte de testes."
        )
    else:
        classification = "neutral"
        label = "Neutro"
        risk = "none"
        reason = "O PR não alterou linhas efetivas de código Python nem de testes."
        recommendation = "Não há nenhuma ação relacionada a testes para este PR."

    return PullRequestMetrics(
        number=number,
        title=title,
        state=state,
        url=url,
        author=author,
        code_added_loc=code_added,
        code_removed_loc=code_removed,
        test_added_loc=test_added,
        test_removed_loc=test_removed,
        code_files_changed=len(code_files),
        test_files_changed=len(test_files),
        classification=classification,
        label=label,
        risk=risk,
        score=code_added if classification == "possible_debt" else 0,
        reason=reason,
        recommendation=recommendation,
        files=files,
    )

def rank_pull_requests(pull_requests: list[PullRequestMetrics]) -> list[PullRequestMetrics]:
    return sorted(
        pull_requests,
        key=lambda item: (
            RISK_ORDER[item.risk],
            item.score,
            item.code_churn,
            item.number,
        ),
        reverse=True,
    )

def classify_python_file(filename: str) -> str | None:
    parts = _parts(filename)
    if not parts[-1].endswith(".py") or set(parts[:-1]) & _EXCLUDED_DIRS:
        return None
    return "test" if is_test_file(filename) else "code"

def _meaningful_file_change(file_metrics: FileMetrics) -> bool:
    return file_metrics.churn > 0 or (file_metrics.category == "test" and file_metrics.status == "renamed")