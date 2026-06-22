import pytest

from cli_code_test_evolution.repository_parser import (
    RepositoryInputError,
    normalize_repository,
    parse_pr_range,
    parse_pr_list,
    validate_selection,
)


@pytest.mark.parametrize(
    ("value", "expected", "pr"),
    [
        ("owner/repo", "owner/repo", None),
        ("https://github.com/owner/repo", "owner/repo", None),
        ("https://github.com/owner/repo.git", "owner/repo", None),
        ("https://github.com/owner/repo/pull/42", "owner/repo", 42),
    ],
)
def test_normalizes_supported_repository_inputs(value, expected, pr):
    result = normalize_repository(value)

    assert result.full_name == expected
    assert result.pr_number == pr


@pytest.mark.parametrize(
    "value",
    ["", "owner", "https://gitlab.com/owner/repo", "https://github.com/o/r/issues"],
)
def test_rejects_invalid_repository_inputs(value):
    with pytest.raises(RepositoryInputError):
        normalize_repository(value)


def test_parses_inclusive_range_and_rejects_reverse_range():
    assert parse_pr_range("10:20") == (10, 20)
    with pytest.raises(RepositoryInputError):
        parse_pr_range("20:10")


def test_parses_list():
    assert parse_pr_list("1,2,3") == [1, 2, 3]


@pytest.mark.parametrize("value", ["", "1,", ",1", "A,B"])
def test_reject_parses_list(value):
    with pytest.raises(RepositoryInputError):
        parse_pr_list(value)


def test_selection_must_be_exclusive():
    assert validate_selection(None, 7, None, None, False) == ("pr", 7)
    assert validate_selection(7, None, None, None, False) == ("pr", 7)
    assert validate_selection(None, None, "2:4", None,
                              False) == ("range", (2, 4))
    assert validate_selection(
        None, None, None, "123,456", False) == ("list", [123, 456])
    assert validate_selection(None, None, None, None, True) == ("all", None)
    with pytest.raises(RepositoryInputError):
        validate_selection(None, 7, None, None, True)
