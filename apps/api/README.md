# apps/api

The Python + FastAPI backend for the application.

**Status:** scaffolded. Python is pinned to 3.13. Depends on `packages/core`
and `packages/db` as editable local packages.

## Commands

Run from `apps/api` (requires [uv](https://docs.astral.sh/uv/) and a running Postgres — see `packages/db/README.md`):

```
uv sync                                          # install
uv run python -m app.cli migrate                 # apply migrations to the dev database
uv run python -m app.cli create-user <username>  # prompts for a password (12+ chars)
uv run uvicorn --factory app.main:create_app --reload   # serves on 127.0.0.1:8000
uv run pytest                                    # tests (use the finance_os_test database)
uv run mypy
uv run ruff check
```

Credentials are read from the repo-root `.env`; non-secret settings from `config.yml`.

## Endpoints

All routes except `/health` and `/auth/login` require a valid session cookie.

- `POST /auth/login`, `POST /auth/logout`, `GET /auth/me` — HttpOnly, SameSite=Strict cookie; only a hash of the token is stored; five failed attempts per username lock sign-in for five minutes.
- `GET/POST /accounts`, `PUT/DELETE /accounts/{id}`
- `GET/POST /transactions`, `PUT/DELETE /transactions/{id}`
- `POST /imports/inspect` (headers and sample rows), `/imports/preview` (writes nothing), `/imports/commit` (re-parses and re-checks duplicates on the server; all rows or none)
- `GET /summary` (net worth per currency), `GET /currencies`

Every query is scoped to the signed-in user; the user is never taken from the request body.

## Known gaps

- CSV is the only import format so far; OFX, QIF and text PDF are next.
- The login throttle is in memory, so it resets on restart and is per process.
- The API has no CORS configuration on purpose: the web app reaches it through its `/api` proxy (same origin).
