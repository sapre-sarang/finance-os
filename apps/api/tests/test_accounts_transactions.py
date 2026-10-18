from fastapi.testclient import TestClient
from financeos_db.models import Account
from sqlalchemy import select
from sqlalchemy.orm import Session

from tests.conftest import new_account


def add_transaction(client: TestClient, account_id: object, amount: int, **extra: object) -> dict:  # type: ignore[type-arg]
    body = {
        "account_id": account_id,
        "occurred_on": "2025-03-04",
        "amount_minor": amount,
        "description": "Test Cafe",
    } | extra
    response = client.post("/transactions", json=body)
    assert response.status_code == 201, response.text
    return response.json()  # type: ignore[no-any-return]


def test_account_crud_roundtrip(signed_in: TestClient) -> None:
    account = new_account(signed_in)
    assert account["balance_minor"] == 100000

    updated = signed_in.put(
        f"/accounts/{account['id']}",
        json={"name": "Renamed", "kind": "savings", "currency": "INR", "opening_balance_minor": 5},
    )
    assert updated.status_code == 200 and updated.json()["name"] == "Renamed"
    assert [a["name"] for a in signed_in.get("/accounts").json()] == ["Renamed"]

    assert signed_in.delete(f"/accounts/{account['id']}").status_code == 204
    assert signed_in.get("/accounts").json() == []


def test_account_rejects_invalid_input(signed_in: TestClient) -> None:
    bad = {"name": "X", "kind": "checking", "currency": "ZZZ", "opening_balance_minor": 0}
    assert signed_in.post("/accounts", json=bad).status_code == 422
    assert (
        signed_in.post("/accounts", json=bad | {"currency": "INR", "kind": "bogus"}).status_code
        == 422
    )
    assert (
        signed_in.post("/accounts", json=bad | {"currency": "INR", "name": ""}).status_code == 422
    )
    assert signed_in.get("/accounts").json() == []


def test_account_identifier_is_encrypted_at_rest(signed_in: TestClient, engine) -> None:  # type: ignore[no-untyped-def]
    new_account(signed_in, identifier="SYNTH000012345678")

    with Session(engine) as session:
        stored = session.scalar(select(Account.identifier_encrypted))
    assert stored is not None and b"12345678" not in stored
    assert signed_in.get("/accounts").json()[0]["identifier_hint"] == "…5678"


def test_balance_is_opening_plus_transactions(signed_in: TestClient) -> None:
    account = new_account(signed_in, opening_balance_minor=100000)
    add_transaction(signed_in, account["id"], -2550)
    add_transaction(signed_in, account["id"], 1000)

    assert signed_in.get("/accounts").json()[0]["balance_minor"] == 100000 - 2550 + 1000
    assert signed_in.get("/summary").json()["net_worth"] == [
        {"currency": "INR", "net_worth_minor": 98450}
    ]


def test_transaction_inherits_account_currency_and_defuses_formulas(
    signed_in: TestClient,
) -> None:
    account = new_account(signed_in, currency="USD")
    created = add_transaction(signed_in, account["id"], -100, description="=HYPERLINK(1)")
    assert created["currency"] == "USD"
    assert created["description"].startswith("'=")


def test_transaction_validation_failures_persist_nothing(signed_in: TestClient) -> None:
    account = new_account(signed_in)
    base = {"account_id": account["id"], "occurred_on": "2025-03-04", "amount_minor": 1}
    for bad in (
        {"description": ""},
        {"description": "ok", "occurred_on": "1850-01-01"},
        {"description": "ok", "amount_minor": 1.5},
        {"description": "ok", "amount_minor": 10**16},
    ):
        assert signed_in.post("/transactions", json=base | bad).status_code == 422, bad
    assert signed_in.get("/transactions").json()["total"] == 0


def test_transaction_update_delete_and_paging(signed_in: TestClient) -> None:
    account = new_account(signed_in)
    for day in range(1, 4):
        add_transaction(signed_in, account["id"], -100, occurred_on=f"2025-03-0{day}")

    page = signed_in.get("/transactions", params={"limit": 2}).json()
    assert page["total"] == 3 and len(page["items"]) == 2
    assert page["items"][0]["occurred_on"] == "2025-03-03"

    target = page["items"][0]["id"]
    edited = signed_in.put(
        f"/transactions/{target}",
        json={
            "account_id": account["id"],
            "occurred_on": "2025-03-03",
            "amount_minor": -999,
            "description": "Edited",
        },
    )
    assert edited.json()["amount_minor"] == -999
    assert signed_in.delete(f"/transactions/{target}").status_code == 204
    assert signed_in.get("/transactions").json()["total"] == 2


def test_users_cannot_see_or_touch_each_others_data(
    signed_in: TestClient, other_client: TestClient
) -> None:
    account = new_account(signed_in)
    created = add_transaction(signed_in, account["id"], -100)

    assert other_client.get("/accounts").json() == []
    assert other_client.get("/transactions").json()["total"] == 0
    assert other_client.delete(f"/accounts/{account['id']}").status_code == 404
    assert other_client.delete(f"/transactions/{created['id']}").status_code == 404
    forged = {
        "account_id": account["id"],
        "occurred_on": "2025-03-04",
        "amount_minor": 1,
        "description": "x",
    }
    assert other_client.post("/transactions", json=forged).status_code == 404


def test_currency_cannot_change_after_transactions_exist(signed_in: TestClient) -> None:
    account = new_account(signed_in)
    add_transaction(signed_in, account["id"], -100)
    response = signed_in.put(
        f"/accounts/{account['id']}",
        json={"name": "A", "kind": "checking", "currency": "USD", "opening_balance_minor": 0},
    )
    assert response.status_code == 409
