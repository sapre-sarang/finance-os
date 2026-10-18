from fastapi.testclient import TestClient

from tests.conftest import PASSWORD


def test_health_needs_no_sign_in(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_financial_routes_reject_anonymous_requests(client: TestClient) -> None:
    for path in ("/accounts", "/transactions", "/summary", "/auth/me", "/currencies"):
        assert client.get(path).status_code == 401, path


def test_login_sets_httponly_strict_cookie(client: TestClient, make_user) -> None:  # type: ignore[no-untyped-def]
    make_user("test-user")
    response = client.post("/auth/login", json={"username": "test-user", "password": PASSWORD})

    assert response.status_code == 200
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=strict" in cookie
    assert client.get("/auth/me").json() == {"username": "test-user"}


def test_wrong_password_and_unknown_user_look_the_same(client: TestClient, make_user) -> None:  # type: ignore[no-untyped-def]
    make_user("test-user")
    wrong = client.post("/auth/login", json={"username": "test-user", "password": "nope"})
    unknown = client.post("/auth/login", json={"username": "nobody", "password": PASSWORD})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


def test_logout_invalidates_the_session(signed_in: TestClient) -> None:
    assert signed_in.get("/auth/me").status_code == 200
    assert signed_in.post("/auth/logout").status_code == 204
    assert signed_in.get("/auth/me").status_code == 401


def test_repeated_failures_are_throttled(client: TestClient, make_user) -> None:  # type: ignore[no-untyped-def]
    make_user("test-user")
    for _ in range(5):
        client.post("/auth/login", json={"username": "test-user", "password": "bad"})
    blocked = client.post("/auth/login", json={"username": "test-user", "password": PASSWORD})
    assert blocked.status_code == 429
