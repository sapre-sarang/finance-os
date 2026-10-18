# packages/db

Database schema, migrations, and field encryption (SQLAlchemy 2 + Alembic +
PostgreSQL via psycopg 3).

**Status:** scaffolded. Python is pinned to 3.13 (`.python-version`) because
newer interpreters lack prebuilt wheels for some dependencies on Windows.

## Contents

- `src/financeos_db/models.py` — `User`, `UserSession` (stores only a SHA-256 of the cookie token), `Account`, `Transaction`, `ImportBatch`. Money is `BigInteger` minor units plus a currency code; timestamps are timezone-aware UTC; a transaction's `occurred_on` date is separate from `created_at`.
- `src/financeos_db/crypto.py` — `FieldCipher` (Fernet) for sensitive columns; `accounts.identifier_encrypted` uses it. The key comes from `ENCRYPTION_KEY`.
- `alembic/` — migrations. The URL comes from `DATABASE_URL`; use `uv run python -m app.cli migrate` from `apps/api` rather than calling Alembic by hand.

## Local database

FinanceOS uses the shared Postgres container already running on this machine
(`D:\workspace\docker-apps\postgres`, port 5432); it does not start its own.
One-time setup, as the container's admin user, with the password from your
`.env` (`DATABASE_USERNAME` / `DATABASE_PASSWORD`):

```sql
CREATE ROLE finance_os LOGIN PASSWORD '<DATABASE_PASSWORD>';
CREATE DATABASE finance_os_dev  OWNER finance_os;
CREATE DATABASE finance_os_test OWNER finance_os;
```

`finance_os_test` is used by the API test suite and is wiped on every run.
No real data belongs in either database from a test or fixture.

## Changing the schema

Edit `models.py`, then from `packages/db` with `DATABASE_URL` set:
`uv run alembic revision --autogenerate -m "describe change"` and review the
generated file before committing it.
