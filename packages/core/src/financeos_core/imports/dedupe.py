import re
from collections import Counter
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from datetime import date

from financeos_core.imports.models import ParsedTransaction

TransactionKey = tuple[date, int, str, str]

_WHITESPACE_RUN = re.compile(r"\s+")


def build_key(occurred_on: date, minor: int, currency: str, description: str) -> TransactionKey:
    return (occurred_on, minor, currency, _WHITESPACE_RUN.sub(" ", description).strip().casefold())


def transaction_key(transaction: ParsedTransaction) -> TransactionKey:
    return build_key(
        transaction.occurred_on,
        transaction.amount.minor,
        transaction.amount.currency,
        transaction.description,
    )


@dataclass(frozen=True, slots=True)
class DedupeResult:
    new: tuple[ParsedTransaction, ...]
    already_present: tuple[ParsedTransaction, ...]
    is_new: tuple[bool, ...]  # aligned with the incoming sequence


def select_new_transactions(
    incoming: Sequence[ParsedTransaction],
    *,
    existing_keys: Mapping[TransactionKey, int],
    existing_external_ids: Collection[str],
) -> DedupeResult:
    """Split an incoming statement into rows to add and rows the account already has.

    Rows with an external id (e.g. OFX FITID) match on that id alone. Rows
    without one match by key *count*: if the account holds 2 coffees for the
    same key and the file has 3, only 1 is new. `existing_keys` must therefore
    count only stored rows that have no external id, or an id-bearing row would
    swallow a look-alike id-less one.
    """
    seen_ids = set(existing_external_ids)
    consumed: Counter[TransactionKey] = Counter()
    new: list[ParsedTransaction] = []
    already_present: list[ParsedTransaction] = []
    is_new: list[bool] = []

    for transaction in incoming:
        if transaction.external_id is not None:
            is_duplicate = transaction.external_id in seen_ids
            seen_ids.add(transaction.external_id)
        else:
            key = transaction_key(transaction)
            is_duplicate = consumed[key] < existing_keys.get(key, 0)
            if is_duplicate:
                consumed[key] += 1

        (already_present if is_duplicate else new).append(transaction)
        is_new.append(not is_duplicate)

    return DedupeResult(tuple(new), tuple(already_present), tuple(is_new))
