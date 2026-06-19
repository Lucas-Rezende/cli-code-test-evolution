import re

# Padrões de linhas a ignorar (após remover o '+' inicial)
_IGNORE_PATTERNS = [
    re.compile(r'^\s*#'),    # comentário Python
    re.compile(r'^\s*$'),    # linha em branco ou só espaços
    re.compile(r'^\s*"""'),  # início/fim de docstring
    re.compile(r"^\s*'''"),  # início/fim de docstring (aspas simples)
]

def count_effective_lines(patch: str | None) -> int:
    """
    Conta linhas de código efetivas adicionadas em um diff (patch).
    Ignora comentários, linhas em branco e docstrings.
    Retorna 0 se o patch for None (ex: arquivos binários).
    """
    if not patch:
        return 0

    count = 0
    for line in patch.splitlines():
        # Só nos interessa linhas adicionadas
        if not line.startswith('+') or line.startswith('+++'):
            continue
        # Remove o '+' inicial para analisar o conteúdo
        code = line[1:]
        # Verifica se a linha deve ser ignorada
        if not any(pattern.match(code) for pattern in _IGNORE_PATTERNS):
            count += 1

    return count