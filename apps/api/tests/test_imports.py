from fastapi.testclient import TestClient

from tests.conftest import new_account

LAYOUT = {
    "date_column": "Date",
    "description_column": "Narration",
    "date_format": "%d/%m/%Y",
    "amount_column": "Amount",
    "reference_column": "",
}

STATEMENT = (
    "Date,Narration,Amount\n"
    "04/03/2025,Test Cafe,-100.00\n"
    "04/03/2025,Test Cafe,-100.00\n"
    "05/03/2025,Test Employer Salary,50000.00\n"
)


def post(client: TestClient, path: str, account_id: object, content: str, **extra: object):  # type: ignore[no-untyped-def]
    data = {"account_id": str(account_id)} | LAYOUT | {k: str(v) for k, v in extra.items()}
    return client.post(path, data=data, files={"file": ("statement.csv", content.encode())})


def balance(client: TestClient) -> int:
    return int(client.get("/accounts").json()[0]["balance_minor"])


def test_inspect_lists_headers_for_column_mapping(signed_in: TestClient) -> None:
    response = signed_in.post("/imports/inspect", files={"file": ("s.csv", STATEMENT.encode())})
    assert response.json()["headers"] == ["Date", "Narration", "Amount"]
    assert len(response.json()["sample_rows"]) == 3


def test_preview_saves_nothing(signed_in: TestClient) -> None:
    account = new_account(signed_in, opening_balance_minor=0)
    response = post(signed_in, "/imports/preview", account["id"], STATEMENT)

    assert response.status_code == 200
    assert response.json()["new_count"] == 3
    assert signed_in.get("/transactions").json()["total"] == 0


def test_commit_adds_rows_and_reimport_adds_nothing(signed_in: TestClient) -> None:
    account = new_account(signed_in, opening_balance_minor=0)

    first = post(signed_in, "/imports/commit", account["id"], STATEMENT)
    assert first.json() == {"added": 3, "already_imported": 0, "skipped_by_you": 0}
    assert balance(signed_in) == -10000 - 10000 + 5000000

    again = post(signed_in, "/imports/commit", account["id"], STATEMENT)
    assert again.json() == {"added": 0, "already_imported": 3, "skipped_by_you": 0}
    assert signed_in.get("/transactions").json()["total"] == 3
    assert balance(signed_in) == 4980000

    preview = post(signed_in, "/imports/preview", account["id"], STATEMENT).json()
    assert preview["already_imported_count"] == 3
    assert all(row["already_imported"] for row in preview["rows"])


def test_overlapping_statement_adds_only_the_new_rows(signed_in: TestClient) -> None:
    account = new_account(signed_in, opening_balance_minor=0)
    post(signed_in, "/imports/commit", account["id"], STATEMENT)

    overlap = STATEMENT + "06/03/2025,Test Shop,-20.00\n"
    result = post(signed_in, "/imports/commit", account["id"], overlap)
    assert result.json()["added"] == 1


def test_manual_entry_is_recognised_as_already_present(signed_in: TestClient) -> None:
    account = new_account(signed_in, opening_balance_minor=0)
    signed_in.post(
        "/transactions",
        json={
            "account_id": account["id"],
            "occurred_on": "2025-03-05",
            "amount_minor": 5000000,
            "description": "Test Employer Salary",
        },
    )
    result = post(signed_in, "/imports/commit", account["id"], STATEMENT)
    assert result.json()["added"] == 2
    assert result.json()["already_imported"] == 1


def test_rows_the_user_skips_are_not_saved(signed_in: TestClient) -> None:
    account = new_account(signed_in, opening_balance_minor=0)
    result = post(signed_in, "/imports/commit", account["id"], STATEMENT, skip_rows="2")
    assert result.json() == {"added": 2, "already_imported": 0, "skipped_by_you": 1}


def test_bank_reference_dedupes_even_when_description_changes(signed_in: TestClient) -> None:
    account = new_account(signed_in, opening_balance_minor=0)
    layout = {"reference_column": "Ref"}
    first = "Date,Narration,Amount,Ref\n04/03/2025,Test Cafe,-100.00,R1\n"
    renamed = "Date,Narration,Amount,Ref\n04/03/2025,TEST CAFE POS 42,-100.00,R1\n"

    assert post(signed_in, "/imports/commit", account["id"], first, **layout).json()["added"] == 1
    assert post(signed_in, "/imports/commit", account["id"], renamed, **layout).json()["added"] == 0


def test_one_bad_row_rejects_the_whole_file_and_saves_nothing(signed_in: TestClient) -> None:
    account = new_account(signed_in, opening_balance_minor=0)
    bad = STATEMENT + "31/02/2025,Test Shop,-5.00\n"

    response = post(signed_in, "/imports/commit", account["id"], bad)

    assert response.status_code == 422
    assert response.json()["detail"]["problems"][0].startswith("line 5")
    assert signed_in.get("/transactions").json()["total"] == 0


def test_oversized_upload_is_refused(signed_in: TestClient, client: TestClient) -> None:
    account = new_account(signed_in, opening_balance_minor=0)
    limit = client.app.state.settings.max_upload_bytes  # type: ignore[attr-defined]
    huge = "Date,Narration,Amount\n" + "x" * (limit + 1)
    assert post(signed_in, "/imports/commit", account["id"], huge).status_code == 413


def test_import_into_someone_elses_account_is_not_found(
    signed_in: TestClient, other_client: TestClient
) -> None:
    account = new_account(signed_in)
    assert post(other_client, "/imports/commit", account["id"], STATEMENT).status_code == 404


def test_imports_require_sign_in(client: TestClient) -> None:
    response = client.post("/imports/inspect", files={"file": ("s.csv", b"a,b")})
    assert response.status_code == 401
