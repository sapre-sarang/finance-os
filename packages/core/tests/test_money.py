from decimal import Decimal

import pytest

from financeos_core.money import Money, MoneyError


def test_parses_decimal_string_into_minor_units() -> None:
    assert Money.from_decimal_string("1234.56", "INR") == Money(123456, "INR")


def test_parses_indian_digit_grouping() -> None:
    assert Money.from_decimal_string("1,00,000.50", "INR") == Money(10000050, "INR")


def test_parses_negative_forms() -> None:
    assert Money.from_decimal_string("-10.00", "USD") == Money(-1000, "USD")
    assert Money.from_decimal_string("(10.00)", "USD") == Money(-1000, "USD")


def test_whole_number_and_zero_decimal_currency() -> None:
    assert Money.from_decimal_string("500", "INR") == Money(50000, "INR")
    assert Money.from_decimal_string("500", "JPY") == Money(500, "JPY")


def test_one_paisa_is_exact_where_a_float_would_drift() -> None:
    total = Money(0, "INR")
    for _ in range(10):
        total = total + Money.from_decimal_string("0.10", "INR")
    assert total == Money(100, "INR")


@pytest.mark.parametrize("text", ["", "abc", "1.2.3", "12.345", "1e3", "$5.00", "--5"])
def test_rejects_invalid_amounts(text: str) -> None:
    with pytest.raises(MoneyError):
        Money.from_decimal_string(text, "INR")


def test_rejects_extra_precision_for_zero_decimal_currency() -> None:
    with pytest.raises(MoneyError):
        Money.from_decimal_string("5.5", "JPY")


def test_rejects_unknown_currency() -> None:
    with pytest.raises(MoneyError):
        Money(100, "XYZ")


def test_rejects_non_integer_minor_units() -> None:
    with pytest.raises(MoneyError):
        Money(1.5, "INR")  # type: ignore[arg-type]
    with pytest.raises(MoneyError):
        Money(True, "INR")


def test_arithmetic_requires_same_currency() -> None:
    with pytest.raises(MoneyError):
        Money(100, "INR") + Money(100, "USD")


def test_subtraction_and_negation() -> None:
    assert Money(500, "INR") - Money(200, "INR") == Money(300, "INR")
    assert -Money(500, "INR") == Money(-500, "INR")


def test_to_decimal() -> None:
    assert Money(123456, "INR").to_decimal() == Decimal("1234.56")
    assert Money(-5, "INR").to_decimal() == Decimal("-0.05")
