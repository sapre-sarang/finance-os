import pytest

from financeos_core.imports.sanitize import clean_text


@pytest.mark.parametrize("raw", ["=SUM(A1)", "+1", "-2", "@x", "\t=SUM(A1)"])
def test_defuses_formula_prefixes(raw: str) -> None:
    assert clean_text(raw).startswith("'")


def test_leading_tab_is_stripped_not_kept() -> None:
    assert clean_text("\tcmd") == "cmd"


def test_leaves_normal_text_alone() -> None:
    assert clean_text("Test Cafe") == "Test Cafe"


def test_collapses_whitespace_and_strips_control_characters() -> None:
    assert clean_text("  Test \x00 \n  Cafe  ") == "Test Cafe"
