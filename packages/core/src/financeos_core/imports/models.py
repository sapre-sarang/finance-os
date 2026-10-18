from dataclasses import dataclass
from datetime import date

from financeos_core.money import Money

_EARLIEST_PLAUSIBLE = date(1990, 1, 1)
_LATEST_PLAUSIBLE = date(2100, 1, 1)
MAX_DESCRIPTION_LENGTH = 500


@dataclass(frozen=True, slots=True)
class ParsedTransaction:
    """One statement row. Negative amounts are money going out of the account."""

    occurred_on: date
    amount: Money
    description: str
    external_id: str | None = None

    def __post_init__(self) -> None:
        if not _EARLIEST_PLAUSIBLE <= self.occurred_on < _LATEST_PLAUSIBLE:
            raise ValueError(f"date out of range: {self.occurred_on}")
        if not self.description:
            raise ValueError("description is empty")
        if len(self.description) > MAX_DESCRIPTION_LENGTH:
            raise ValueError("description is too long")
        if self.external_id is not None and not self.external_id:
            raise ValueError("external_id must be None or non-empty")
