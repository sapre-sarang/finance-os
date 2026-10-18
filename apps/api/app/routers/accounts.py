import uuid
from typing import Literal

from fastapi import APIRouter, HTTPException, Response, status
from financeos_core.imports.sanitize import clean_text
from financeos_core.money import MINOR_UNIT_DIGITS
from financeos_db.models import Account
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select

from app.deps import Cipher, CurrentUser, DbSession
from app.services.accounts import get_owned_account, transaction_totals

router = APIRouter(tags=["accounts"])

AccountKind = Literal["checking", "savings", "credit_card", "loan", "cash"]
MAX_MINOR = 10**15


class AccountIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    kind: AccountKind
    currency: str
    opening_balance_minor: int = Field(default=0, gt=-MAX_MINOR, lt=MAX_MINOR)
    identifier: str | None = Field(default=None, max_length=34)

    @field_validator("name")
    @classmethod
    def _clean_name(cls, value: str) -> str:
        cleaned = clean_text(value)
        if not cleaned:
            raise ValueError("name cannot be blank")
        return cleaned

    @field_validator("currency")
    @classmethod
    def _known_currency(cls, value: str) -> str:
        if value not in MINOR_UNIT_DIGITS:
            raise ValueError(f"currency must be one of {', '.join(MINOR_UNIT_DIGITS)}")
        return value


class AccountOut(BaseModel):
    id: uuid.UUID
    name: str
    kind: AccountKind
    currency: str
    opening_balance_minor: int
    balance_minor: int
    identifier_hint: str | None


def _to_out(account: Account, total: int, cipher: Cipher) -> AccountOut:
    hint = None
    if account.identifier_encrypted is not None:
        hint = "…" + cipher.decrypt(account.identifier_encrypted)[-4:]
    return AccountOut(
        id=account.id,
        name=account.name,
        kind=account.kind,  # type: ignore[arg-type]
        currency=account.currency,
        opening_balance_minor=account.opening_balance_minor,
        balance_minor=account.opening_balance_minor + total,
        identifier_hint=hint,
    )


@router.get("/accounts", response_model=list[AccountOut])
def list_accounts(user: CurrentUser, session: DbSession, cipher: Cipher) -> list[AccountOut]:
    accounts = session.scalars(
        select(Account).where(Account.user_id == user.id).order_by(Account.created_at)
    ).all()
    totals = transaction_totals(session, [a.id for a in accounts])
    return [_to_out(a, totals.get(a.id, 0), cipher) for a in accounts]


@router.post("/accounts", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
def create_account(
    body: AccountIn, user: CurrentUser, session: DbSession, cipher: Cipher
) -> AccountOut:
    account = Account(
        user_id=user.id,
        name=body.name,
        kind=body.kind,
        currency=body.currency,
        opening_balance_minor=body.opening_balance_minor,
        identifier_encrypted=cipher.encrypt(body.identifier) if body.identifier else None,
    )
    session.add(account)
    session.commit()
    return _to_out(account, 0, cipher)


@router.put("/accounts/{account_id}", response_model=AccountOut)
def update_account(
    account_id: uuid.UUID,
    body: AccountIn,
    user: CurrentUser,
    session: DbSession,
    cipher: Cipher,
) -> AccountOut:
    account = get_owned_account(session, user, account_id)
    account.name = body.name
    account.kind = body.kind
    account.opening_balance_minor = body.opening_balance_minor
    if body.currency != account.currency and transaction_totals(session, [account.id]):
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Currency cannot change once an account has transactions"
        )
    account.currency = body.currency
    if body.identifier:
        account.identifier_encrypted = cipher.encrypt(body.identifier)
    session.commit()
    return _to_out(account, transaction_totals(session, [account.id]).get(account.id, 0), cipher)


@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(account_id: uuid.UUID, user: CurrentUser, session: DbSession) -> Response:
    session.delete(get_owned_account(session, user, account_id))
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
