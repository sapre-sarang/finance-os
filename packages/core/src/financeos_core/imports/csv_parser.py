import csv
import io
from dataclasses import dataclass
from datetime import datetime

from financeos_core.imports.errors import StatementParseError
from financeos_core.imports.models import ParsedTransaction
from financeos_core.imports.sanitize import clean_text
from financeos_core.money import Money, MoneyError

DEFAULT_MAX_BYTES = 5 * 1024 * 1024
DEFAULT_MAX_ROWS = 50_000
_MAX_REPORTED_PROBLEMS = 20


@dataclass(frozen=True, slots=True)
class CsvLayout:
    """Where each field lives in one bank's CSV export.

    Provide either `amount_column` (signed, negative = outflow) or both
    `debit_column` and `credit_column` (each positive).
    """

    currency: str
    date_column: str
    description_column: str
    date_format: str
    amount_column: str | None = None
    debit_column: str | None = None
    credit_column: str | None = None
    reference_column: str | None = None

    def __post_init__(self) -> None:
        has_signed = self.amount_column is not None
        has_split = self.debit_column is not None and self.credit_column is not None
        if has_signed == has_split:
            raise ValueError("use either amount_column or both debit_column and credit_column")

    def required_columns(self) -> list[str]:
        columns = [self.date_column, self.description_column]
        if self.amount_column is not None:
            columns.append(self.amount_column)
        else:
            columns.extend(c for c in (self.debit_column, self.credit_column) if c is not None)
        if self.reference_column is not None:
            columns.append(self.reference_column)
        return columns


def inspect_csv(
    data: bytes, *, max_bytes: int = DEFAULT_MAX_BYTES, sample_rows: int = 5
) -> tuple[list[str], list[list[str]]]:
    """Header names and a few raw rows, so a user can map columns before importing."""
    if len(data) > max_bytes:
        raise StatementParseError([f"file is larger than {max_bytes} bytes"])
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise StatementParseError(["file is not valid UTF-8 text"]) from None

    reader = csv.reader(io.StringIO(text, newline=""))
    headers = next(reader, None)
    if not headers or not any(h.strip() for h in headers):
        raise StatementParseError(["file has no header row"])
    rows = [row for _, row in zip(range(sample_rows), reader, strict=False)]
    return [h.strip() for h in headers], rows


def parse_csv(
    data: bytes,
    layout: CsvLayout,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
    max_rows: int = DEFAULT_MAX_ROWS,
) -> tuple[ParsedTransaction, ...]:
    if len(data) > max_bytes:
        raise StatementParseError([f"file is larger than {max_bytes} bytes"])

    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise StatementParseError(["file is not valid UTF-8 text"]) from None

    reader = csv.DictReader(io.StringIO(text, newline=""))
    missing = [c for c in layout.required_columns() if c not in (reader.fieldnames or [])]
    if missing:
        raise StatementParseError([f"missing columns: {', '.join(missing)}"])

    transactions: list[ParsedTransaction] = []
    problems: list[str] = []

    for line_number, row in enumerate(reader, start=2):
        if line_number - 1 > max_rows:
            raise StatementParseError([f"file has more than {max_rows} rows"])
        if not any((value or "").strip() for value in row.values() if isinstance(value, str)):
            continue
        try:
            transactions.append(_parse_row(row, layout))
        except (ValueError, MoneyError) as error:
            if len(problems) < _MAX_REPORTED_PROBLEMS:
                problems.append(f"line {line_number}: {error}")

    if problems:
        raise StatementParseError(problems)
    if not transactions:
        raise StatementParseError(["file contains no transactions"])
    return tuple(transactions)


def _parse_row(row: dict[str, str | None], layout: CsvLayout) -> ParsedTransaction:
    occurred_on = datetime.strptime(_cell(row, layout.date_column), layout.date_format).date()
    description = clean_text(_cell(row, layout.description_column))

    reference = None
    if layout.reference_column is not None:
        reference = clean_text(_cell(row, layout.reference_column)) or None

    return ParsedTransaction(
        occurred_on=occurred_on,
        amount=_parse_amount(row, layout),
        description=description,
        external_id=reference,
    )


def _parse_amount(row: dict[str, str | None], layout: CsvLayout) -> Money:
    if layout.amount_column is not None:
        return Money.from_decimal_string(_cell(row, layout.amount_column), layout.currency)

    debit = _optional_amount(row, layout.debit_column, layout.currency)
    credit = _optional_amount(row, layout.credit_column, layout.currency)
    if debit is None and credit is None:
        raise ValueError("neither debit nor credit has an amount")
    if debit is not None and credit is not None and not (debit.is_zero() or credit.is_zero()):
        raise ValueError("both debit and credit have an amount")
    if debit is not None and not debit.is_zero():
        return -debit
    return credit if credit is not None else Money(0, layout.currency)


def _optional_amount(row: dict[str, str | None], column: str | None, currency: str) -> Money | None:
    if column is None:
        return None
    value = (row.get(column) or "").strip()
    return Money.from_decimal_string(value, currency) if value else None


def _cell(row: dict[str, str | None], column: str) -> str:
    value = row.get(column)
    if value is None:
        raise ValueError(f"missing value for {column!r}")
    return value
