from fastapi import APIRouter
from financeos_core.money import MINOR_UNIT_DIGITS
from financeos_db.models import Account
from pydantic import BaseModel
from sqlalchemy import select

from app.deps import CurrentUser, DbSession
from app.services.accounts import transaction_totals

router = APIRouter(tags=["summary"])


class CurrencyTotal(BaseModel):
    currency: str
    net_worth_minor: int


class SummaryOut(BaseModel):
    net_worth: list[CurrencyTotal]


class CurrencyInfo(BaseModel):
    code: str
    minor_unit_digits: int


@router.get("/summary", response_model=SummaryOut)
def summary(user: CurrentUser, session: DbSession) -> SummaryOut:
    """Net worth per currency: the sum of all balances (liabilities hold negative ones)."""
    accounts = session.scalars(select(Account).where(Account.user_id == user.id)).all()
    totals = transaction_totals(session, [a.id for a in accounts])
    by_currency: dict[str, int] = {}
    for account in accounts:
        balance = account.opening_balance_minor + totals.get(account.id, 0)
        by_currency[account.currency] = by_currency.get(account.currency, 0) + balance
    return SummaryOut(
        net_worth=[
            CurrencyTotal(currency=c, net_worth_minor=v) for c, v in sorted(by_currency.items())
        ]
    )


@router.get("/currencies", response_model=list[CurrencyInfo])
def currencies(user: CurrentUser) -> list[CurrencyInfo]:
    return [CurrencyInfo(code=c, minor_unit_digits=d) for c, d in MINOR_UNIT_DIGITS.items()]
