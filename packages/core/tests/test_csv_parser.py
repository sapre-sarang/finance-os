from datetime import date

import pytest

from financeos_core.imports.csv_parser import CsvLayout, parse_csv
from financeos_core.imports.errors import StatementParseError
from financeos_core.money import Money

SIGNED = CsvLayout(
    currency="INR",
    date_column="Date",
    description_column="Narration",
    date_format="%d/%m/%Y",
    amount_column="Amount",
    reference_column="Ref",
)

SPLIT = CsvLayout(
    currency="INR",
    date_column="Date",
    description_column="Narration",
    date_format="%d/%m/%Y",
    debit_column="Debit",
    credit_column="Credit",
)


def csv_bytes(*lines: str) -> bytes:
    return "\n".join(lines).encode("utf-8")


def test_parses_signed_amount_layout() -> None:
    data = csv_bytes(
        "Date,Narration,Amount,Ref",
        "04/03/2025,Test Cafe,-100.00,R1",
        "05/03/2025,Test Employer Salary,50000.00,",
    )

    first, second = parse_csv(data, SIGNED)

    assert first.occurred_on == date(2025, 3, 4)
    assert first.amount == Money(-10000, "INR")
    assert first.external_id == "R1"
    assert second.amount == Money(5000000, "INR")
    assert second.external_id is None


def test_day_first_format_is_not_read_as_month_first() -> None:
    data = csv_bytes("Date,Narration,Amount,Ref", "03/04/2025,Test Shop,-1.00,")
    (row,) = parse_csv(data, SIGNED)
    assert row.occurred_on == date(2025, 4, 3)


def test_parses_debit_credit_layout() -> None:
    data = csv_bytes(
        "Date,Narration,Debit,Credit",
        "04/03/2025,Test Cafe,100.00,",
        "05/03/2025,Test Refund,,25.00",
    )

    out, inn = parse_csv(data, SPLIT)

    assert out.amount == Money(-10000, "INR")
    assert inn.amount == Money(2500, "INR")


def test_handles_bom_and_blank_lines() -> None:
    data = b"\xef\xbb\xbf" + csv_bytes(
        "Date,Narration,Amount,Ref", "", "04/03/2025,Test Cafe,-100.00,", ",,,"
    )
    assert len(parse_csv(data, SIGNED)) == 1


def test_formula_injection_in_description_is_defused() -> None:
    data = csv_bytes("Date,Narration,Amount,Ref", '04/03/2025,"=CMD(""x"")",-1.00,')
    (row,) = parse_csv(data, SIGNED)
    assert row.description.startswith("'=")


def test_one_bad_row_rejects_the_whole_file() -> None:
    data = csv_bytes(
        "Date,Narration,Amount,Ref",
        "04/03/2025,Test Cafe,-100.00,",
        "31/02/2025,Test Shop,-5.00,",
        "05/03/2025,Test Shop,12.345,",
    )

    with pytest.raises(StatementParseError) as error:
        parse_csv(data, SIGNED)

    assert len(error.value.problems) == 2
    assert error.value.problems[0].startswith("line 3")
    assert error.value.problems[1].startswith("line 4")


def test_reports_missing_columns() -> None:
    with pytest.raises(StatementParseError, match="missing columns: Amount"):
        parse_csv(csv_bytes("Date,Narration,Ref", "04/03/2025,Test Cafe,"), SIGNED)


def test_rejects_both_debit_and_credit_filled() -> None:
    data = csv_bytes("Date,Narration,Debit,Credit", "04/03/2025,Test Cafe,10.00,5.00")
    with pytest.raises(StatementParseError, match="both debit and credit"):
        parse_csv(data, SPLIT)


def test_rejects_empty_file_body() -> None:
    with pytest.raises(StatementParseError, match="no transactions"):
        parse_csv(csv_bytes("Date,Narration,Amount,Ref"), SIGNED)


def test_rejects_oversized_file() -> None:
    with pytest.raises(StatementParseError, match="larger than"):
        parse_csv(b"x" * 11, SIGNED, max_bytes=10)


def test_rejects_too_many_rows() -> None:
    lines = ["Date,Narration,Amount,Ref"] + ["04/03/2025,Test Cafe,-1.00,"] * 4
    with pytest.raises(StatementParseError, match="more than 3 rows"):
        parse_csv(csv_bytes(*lines), SIGNED, max_rows=3)


def test_rejects_non_utf8_bytes() -> None:
    with pytest.raises(StatementParseError, match="UTF-8"):
        parse_csv(b"\xff\xfe\x00bad", SIGNED)


def test_layout_requires_exactly_one_amount_style() -> None:
    with pytest.raises(ValueError):
        CsvLayout("INR", "Date", "Narration", "%d/%m/%Y")
    with pytest.raises(ValueError):
        CsvLayout(
            "INR", "Date", "Narration", "%d/%m/%Y",
            amount_column="Amount", debit_column="Debit", credit_column="Credit",
        )


def test_inspect_returns_headers_and_sample_rows() -> None:
    from financeos_core.imports.csv_parser import inspect_csv

    data = csv_bytes("Date, Narration ,Amount", *["04/03/2025,Test Cafe,-1.00"] * 8)
    headers, rows = inspect_csv(data)
    assert headers == ["Date", "Narration", "Amount"]
    assert len(rows) == 5


def test_inspect_rejects_empty_file() -> None:
    from financeos_core.imports.csv_parser import inspect_csv

    with pytest.raises(StatementParseError, match="no header"):
        inspect_csv(b"")
