# cli_code_test_evolution/line_counter.py
from __future__ import annotations

import ast
import io
import tokenize
from dataclasses import dataclass, field

from unidiff import PatchSet

from cli_code_test_evolution.models import IgnoredLines

@dataclass
class PythonPatchMetrics:
    added_loc: int = 0
    removed_loc: int = 0
    ignored_added: IgnoredLines = field(default_factory=IgnoredLines)
    ignored_removed: IgnoredLines = field(default_factory=IgnoredLines)
    analyzable: bool = True
    note: str | None = None

def _docstring_lines(source: str) -> set[int]:
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return set()

    lines: set[int] = set()
    nodes = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    for node in ast.walk(tree):
        if not isinstance(node, nodes) or not node.body:
            continue
        first = node.body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            end = getattr(first, "end_lineno", first.lineno)
            lines.update(range(first.lineno, end + 1))
    return lines


def _line_kinds(source: str) -> dict[int, str]:
    raw_lines = source.splitlines()
    kinds = {
        number: ("blank" if not text.strip() else "unknown")
        for number, text in enumerate(raw_lines, start=1)
    }

    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for token in tokens:
            if token.type in {
                tokenize.ENDMARKER,
                tokenize.INDENT,
                tokenize.DEDENT,
                tokenize.NEWLINE,
                tokenize.NL,
            }:
                continue
            start, end = token.start[0], token.end[0]
            if token.type == tokenize.COMMENT:
                for number in range(start, end + 1):
                    if kinds.get(number) != "code":
                        kinds[number] = "comment"
                continue
            for number in range(start, end + 1):
                kinds[number] = "code"
    except (tokenize.TokenError, IndentationError):
        pass

    for number in _docstring_lines(source):
        if number in kinds:
            kinds[number] = "docstring"
    return kinds

def _patch_set(patch: str) -> PatchSet:
    text = patch
    if text.lstrip().startswith("@@"):
        text = f"--- a/file.py\n+++ b/file.py\n{text}"
    return PatchSet(io.StringIO(text))

def _changed_line_numbers(patch: str) -> tuple[set[int], set[int]]:
    added: set[int] = set()
    removed: set[int] = set()
    for patched_file in _patch_set(patch):
        for hunk in patched_file:
            for line in hunk:
                if line.is_added and line.target_line_no is not None:
                    added.add(line.target_line_no)
                elif line.is_removed and line.source_line_no is not None:
                    removed.add(line.source_line_no)
    return added, removed

def _count(numbers: set[int], kinds: dict[int, str]) -> tuple[int, IgnoredLines]:
    effective = 0
    ignored = IgnoredLines()
    for number in numbers:
        kind = kinds.get(number, "unknown")
        if kind == "blank":
            ignored.blank += 1
        elif kind == "comment":
            ignored.comments += 1
        elif kind == "docstring":
            ignored.docstrings += 1
        else:
            effective += 1
    return effective, ignored

def analyze_python_patch(
    patch: str | None,
    old_content: str | None,
    new_content: str | None,
    *,
    expected_added: int | None = None,
    expected_removed: int | None = None,
) -> PythonPatchMetrics:
    """Conta LOC Python efetivas adicionadas e removidas em um patch."""
    if not patch:
        return PythonPatchMetrics(
            analyzable=False,
            note="Patch ausente, binário ou grande demais para a API do GitHub.",
        )

    try:
        added_numbers, removed_numbers = _changed_line_numbers(patch)
    except Exception as exc:
        return PythonPatchMetrics(
            analyzable=False,
            note=f"Patch inválido: {exc}",
        )

    if (
        (expected_added is not None and len(added_numbers) != expected_added)
        or (
            expected_removed is not None
            and len(removed_numbers) != expected_removed
        )
    ):
        return PythonPatchMetrics(
            analyzable=False,
            note=(
                "Patch truncado pela API do GitHub; LOC não foram estimadas "
                "para evitar um resultado parcial."
            ),
        )

    if added_numbers and new_content is None:
        return PythonPatchMetrics(
            analyzable=False,
            note="Conteúdo novo indisponível; LOC adicionadas não foram estimadas.",
        )
    if removed_numbers and old_content is None:
        return PythonPatchMetrics(
            analyzable=False,
            note="Conteúdo anterior indisponível; LOC removidas não foram estimadas.",
        )

    added_loc, ignored_added = _count(
        added_numbers,
        _line_kinds(new_content or ""),
    )
    removed_loc, ignored_removed = _count(
        removed_numbers,
        _line_kinds(old_content or ""),
    )
    return PythonPatchMetrics(
        added_loc=added_loc,
        removed_loc=removed_loc,
        ignored_added=ignored_added,
        ignored_removed=ignored_removed,
    )
    
def count_effective_lines(patch: str | None) -> int:
    """
    Conta linhas de código efetivas adicionadas em um diff (patch).
    Ignora comentários, linhas em branco e docstrings.
    Retorna 0 se o patch for None (ex: arquivos binários).
    """
    if not patch:
        return 0
    
    raw_added = [
        line[1:]
        for line in patch.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]
    if not raw_added:
        return 0

    synthetic = "\n".join(raw_added)
    effective, _ = _count(set(range(1, len(raw_added) + 1)), _line_kinds(synthetic))
    return effective
