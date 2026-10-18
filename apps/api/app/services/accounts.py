import uuid
from collections.abc import Sequence

from fastapi import HTTPException, status
from financeos_db.models import Account, Transaction, User
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def get_owned_account(session: Session, user: User, account_id: uuid.UUID) -> Account:
    account = session.scalar(
        select(Account).where(Account.id == account_id, Account.user_id == user.id)
    )
    if account is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Account not found")
    return account


def transaction_totals(session: Session, account_ids: Sequence[uuid.UUID]) -> dict[uuid.UUID, int]:
    if not account_ids:
        return {}
    rows = session.execute(
        select(Transaction.account_id, func.coalesce(func.sum(Transaction.amount_minor), 0))
        .where(Transaction.account_id.in_(account_ids))
        .group_by(Transaction.account_id)
    )
    return {account_id: int(total) for account_id, total in rows}
