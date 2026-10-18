# apps/api

The Python + FastAPI backend for the application.

**Status:** empty — not yet scaffolded.

Will contain:
- `app/main.py` — API application entry point
- `app/routers/` — HTTP endpoints and boundary validation
- `app/services/` — request orchestration using `packages/core`
- Authentication and authorization checks before financial data access

The API validates incoming requests before invoking domain logic. Database
access goes through `packages/db`; domain rules belong in `packages/core`.
Keep credentials in `.env` and non-secret runtime settings in `config.yml`.
