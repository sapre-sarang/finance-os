import base64
import os
from collections.abc import Iterator

import psycopg
import pytest
from app.config import REPO_ROOT, Settings, load_dotenv, load_settings
from app.main import create_app
from app.security import hash_password
from fastapi.testclient import TestClient
from financeos_db.models import Base, User
from financeos_db.session import make_engine, make_session_factory
from sqlalchemy import text

TEST_DB = "finance_os_test"
PASSWORD = "synthetic-password-1"


@pytest.fixture(scope="session")
def settings() -> Settings:
    load_dotenv(REPO_ROOT / ".env")
    os.environ["DATABASE_NAME"] = TEST_DB
    loaded = load_settings()

    admin = loaded.database_url.set(database="postgres").render_as_string(hide_password=False)
    with psycopg.connect(admin.replace("+psycopg", ""), autocommit=True) as connection:
        exists = connection.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (TEST_DB,)
        ).fetchone()
        if not exists:
            connection.execute(f'CREATE DATABASE "{TEST_DB}"')
    return loaded


@pytest.fixture(scope="session")
def engine(settings: Settings):  # type: ignore[no-untyped-def]
    engine = make_engine(settings.database_url.render_as_string(hide_password=False))
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(autouse=True)
def clean_tables(engine) -> None:  # type: ignore[no-untyped-def]
    with engine.begin() as connection:
        connection.execute(
            text("TRUNCATE users, user_sessions, accounts, transactions, import_batches CASCADE")
        )


@pytest.fixture
def client(settings: Settings, engine) -> Iterator[TestClient]:  # type: ignore[no-untyped-def]
    with TestClient(create_app(settings)) as test_client:
        yield test_client


@pytest.fixture
def make_user(engine):  # type: ignore[no-untyped-def]
    def _make(username: str) -> None:
        with make_session_factory(engine)() as session:
            session.add(User(username=username, password_hash=hash_password(PASSWORD)))
            session.commit()

    return _make


@pytest.fixture
def signed_in(client: TestClient, make_user) -> TestClient:  # type: ignore[no-untyped-def]
    make_user("test-user")
    response = client.post("/auth/login", json={"username": "test-user", "password": PASSWORD})
    assert response.status_code == 200
    return client


@pytest.fixture
def other_client(settings: Settings, make_user) -> Iterator[TestClient]:  # type: ignore[no-untyped-def]
    make_user("other-user")
    with TestClient(create_app(settings)) as test_client:
        response = test_client.post(
            "/auth/login", json={"username": "other-user", "password": PASSWORD}
        )
        assert response.status_code == 200
        yield test_client


def new_account(client: TestClient, **overrides: object) -> dict[str, object]:
    body = {
        "name": "Test Checking",
        "kind": "checking",
        "currency": "INR",
        "opening_balance_minor": 100000,
    } | overrides
    response = client.post("/accounts", json=body)
    assert response.status_code == 201, response.text
    result: dict[str, object] = response.json()
    return result


def valid_key() -> str:
    return base64.urlsafe_b64encode(b"0" * 32).decode()
