import re
from dataclasses import dataclass
from decimal import Decimal

MINOR_UNIT_DIGITS = {"INR": 2, "USD": 2, "EUR": 2, "GBP": 2, "JPY": 0}

_PLAIN_NUMBER = re.compile(r"^[+-]?\d+(\.\d+)?$")


class MoneyError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Money:
    """Signed amount in the currency's smallest unit (paise, cents)."""

    minor: int
    currency: str

    def __post_init__(self) -> None:
        if isinstance(self.minor, bool) or not isinstance(self.minor, int):
            raise MoneyError("minor units must be an integer")
        if self.currency not in MINOR_UNIT_DIGITS:
            raise MoneyError(f"unsupported currency: {self.currency!r}")

    @classmethod
    def from_decimal_string(cls, text: str, currency: str) -> "Money":
        digits = MINOR_UNIT_DIGITS.get(currency)
        if digits is None:
            raise MoneyError(f"unsupported currency: {currency!r}")

        cleaned = text.strip()
        negative = cleaned.startswith("(") and cleaned.endswith(")")
        if negative:
            cleaned = cleaned[1:-1]
        cleaned = cleaned.replace(",", "").replace(" ", "")

        if not _PLAIN_NUMBER.match(cleaned):
            raise MoneyError(f"not a valid amount: {text!r}")

        value = Decimal(cleaned)
        if -value.as_tuple().exponent > digits:  # type: ignore[operator]
            raise MoneyError(f"{text!r} has more than {digits} decimal places for {currency}")

        minor = int(value.scaleb(digits))
        return cls(-minor if negative else minor, currency)

    def to_decimal(self) -> Decimal:
        return Decimal(self.minor).scaleb(-MINOR_UNIT_DIGITS[self.currency])

    def is_zero(self) -> bool:
        return self.minor == 0

    def __neg__(self) -> "Money":
        return Money(-self.minor, self.currency)

    def __add__(self, other: "Money") -> "Money":
        self._require_same_currency(other)
        return Money(self.minor + other.minor, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        self._require_same_currency(other)
        return Money(self.minor - other.minor, self.currency)

    def _require_same_currency(self, other: "Money") -> None:
        if self.currency != other.currency:
            raise MoneyError(f"currency mismatch: {self.currency} vs {other.currency}")
