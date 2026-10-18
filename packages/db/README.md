# packages/db

Database schema, migrations, and seed scripts (SQLAlchemy + Alembic +
PostgreSQL).

**Status:** empty — not yet scaffolded.

Will contain:
- SQLAlchemy models and database session setup
- Alembic configuration and versioned migrations
- Python seed scripts with synthetic data only, never real financial data

Sensitive fields (linked account identifiers, raw imported statement blobs)
must be encrypted at rest once this package exists — see the Security
Requirements in the root `CLAUDE.md`.
