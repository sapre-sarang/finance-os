# packages/core

Framework-agnostic Python domain logic, used by `apps/api` and tests/scripts.
No FastAPI or database client — keep this package focused on finance rules.

**Status:** scaffolded. Zero runtime dependencies; dev tools are pytest, mypy (strict) and ruff.

## Commands

Run from `packages/core` (requires [uv](https://docs.astral.sh/uv/)):

```
uv sync          # create .venv and install dev tools
uv run pytest    # unit tests
uv run mypy      # strict type check
uv run ruff check
```

## Contents

- `money.py` — `Money`: signed integer minor units plus an ISO currency; parses decimal strings, never floats.
- `imports/models.py` — `ParsedTransaction`, the normalized row every parser produces.
- `imports/csv_parser.py` — `parse_csv` with a per-bank `CsvLayout`; rejects the whole file on any bad row, enforces size and row limits.
- `imports/sanitize.py` — control-character stripping and spreadsheet-formula defusing for statement text.
- `imports/dedupe.py` — `select_new_transactions`: matches by external id (e.g. OFX FITID) or by key *count*, so re-imports add nothing and genuine repeat purchases stay separate.

Still to come: OFX, QIF and text-PDF parsers; categorization rule engine; net-worth and budget calculation.

Anything here must be unit-testable without a running database or API server.
Test data is built in code with obviously synthetic values (statement file
extensions such as `.qif`/`.ofx` are gitignored on purpose).
