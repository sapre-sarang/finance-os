import uuid
from datetime import date

from fastapi import APIRouter, HTTPException, Query, Response, status
from financeos_core.imports.models import MAX_DESCRIPTION_LENGTH
from financeos_core.imports.sanitize import clean_text
from financeos_db.models import Account, Transaction
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select

from app.deps import CurrentUser, DbSession
from app.routers.accounts import MAX_MINOR
from app.services.accounts import get_owned_account

router = APIRouter(tags=["transactions"])

EARLIEST = date(1990, 1, 1)
LATEST = date(2100, 1, 1)


class TransactionIn(BaseModel):
    account_id: uuid.UUID
    occurred_on: date
    amount_minor: int = Field(gt=-MAX_MINOR, lt=MAX_MINOR)
    description: str = Field(min_length=1, max_length=MAX_DESCRIPTION_LENGTH)

    @field_validator("occurred_on")
    @classmethod
    def _plausible_date(cls, value: date) -> date:
        if not EARLIEST <= value < LATEST:
            raise ValueError("date is out of range")
        return value

    @field_validator("description")
    @classmethod
    def _clean_description(cls, value: str) -> str:
        cleaned = clean_text(value)
        if not cleaned:
            raise ValueError("description cannot be blank")
        return cleaned


class TransactionOut(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    occurred_on: date
    amount_minor: int
    currency: str
    description: str
    imported: bool


class TransactionPage(BaseModel):
    items: list[TransactionOut]
    total: int


def _to_out(transaction: Transaction) -> TransactionOut:
    return TransactionOut(
        id=transaction.id,
        account_id=transaction.account_id,
        occurred_on=transaction.occurred_on,
        amount_minor=transaction.amount_minor,
        currency=transaction.currency,
        description=transaction.description,
        imported=transaction.import_batch_id is not None,
    )


def _get_owned_transaction(
    session: DbSession, user: CurrentUser, transaction_id: uuid.UUID
) -> Transaction:
    transaction = session.scalar(
        select(Transaction)
        .join(Account, Transaction.account_id == Account.id)
        .where(Transaction.id == transaction_id, Account.user_id == user.id)
    )
    if transaction is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transaction not found")
    return transaction


@router.get("/transactions", response_model=TransactionPage)
def list_transactions(
    user: CurrentUser,
    session: DbSession,
    account_id: uuid.UUID | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> TransactionPage:
    owned = select(Account.id).where(Account.user_id == user.id)
    if account_id is not None:
        owned = owned.where(Account.id == account_id)
    condition = Transaction.account_id.in_(owned)

    total = session.scalar(select(func.count()).select_from(Transaction).where(condition)) or 0
    rows = session.scalars(
        select(Transaction)
        .where(condition)
        .order_by(Transaction.occurred_on.desc(), Transaction.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return TransactionPage(items=[_to_out(t) for t in rows], total=total)


@router.post("/transactions", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def create_transaction(
    body: TransactionIn, user: CurrentUser, session: DbSession
) -> TransactionOut:
    account = get_owned_account(session, user, body.account_id)
    transaction = Transaction(
        account_id=account.id,
        occurred_on=body.occurred_on,
        amount_minor=body.amount_minor,
        currency=account.currency,
        description=body.description,
    )
    session.add(transaction)
    session.commit()
    return _to_out(transaction)


@router.put("/transactions/{transaction_id}", response_model=TransactionOut)
def update_transaction(
    transaction_id: uuid.UUID, body: TransactionIn, user: CurrentUser, session: DbSession
) -> TransactionOut:
    transaction = _get_owned_transaction(session, user, transaction_id)
    account = get_owned_account(session, user, body.account_id)
    transaction.account_id = account.id
    transaction.currency = account.currency
    transaction.occurred_on = body.occurred_on
    transaction.amount_minor = body.amount_minor
    transaction.description = body.description
    session.commit()
    return _to_out(transaction)


@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: uuid.UUID, user: CurrentUser, session: DbSession
) -> Response:
    session.delete(_get_owned_transaction(session, user, transaction_id))
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
