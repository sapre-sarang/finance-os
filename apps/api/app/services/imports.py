import uuid
from collections import Counter
from dataclasses import dataclass

from financeos_core.imports.csv_parser import CsvLayout, parse_csv
from financeos_core.imports.dedupe import (
    DedupeResult,
    TransactionKey,
    build_key,
    select_new_transactions,
)
from financeos_core.imports.models import ParsedTransaction
from financeos_db.models import Account, Transaction
from sqlalchemy import select
from sqlalchemy.orm import Session


@dataclass(frozen=True, slots=True)
class ImportPlan:
    parsed: tuple[ParsedTransaction, ...]
    dedupe: DedupeResult


def plan_csv_import(
    session: Session, account: Account, data: bytes, layout: CsvLayout, max_bytes: int
) -> ImportPlan:
    parsed = parse_csv(data, layout, max_bytes=max_bytes)
    first = min(t.occurred_on for t in parsed)
    last = max(t.occurred_on for t in parsed)

    stored_rows = session.execute(
        select(
            Transaction.occurred_on,
            Transaction.amount_minor,
            Transaction.currency,
            Transaction.description,
        ).where(
            Transaction.account_id == account.id,
            Transaction.external_id.is_(None),
            Transaction.occurred_on.between(first, last),
        )
    )
    existing_keys: Counter[TransactionKey] = Counter(build_key(*row) for row in stored_rows)

    incoming_ids = [t.external_id for t in parsed if t.external_id is not None]
    existing_ids = set(
        session.scalars(
            select(Transaction.external_id).where(
                Transaction.account_id == account.id, Transaction.external_id.in_(incoming_ids)
            )
        )
    )
    dedupe = select_new_transactions(
        parsed,
        existing_keys=existing_keys,
        existing_external_ids={i for i in existing_ids if i is not None},
    )
    return ImportPlan(parsed, dedupe)


def lock_account(session: Session, account_id: uuid.UUID) -> None:
    """Serialise concurrent imports into one account so counts cannot race."""
    session.execute(select(Account.id).where(Account.id == account_id).with_for_update())
