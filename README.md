# FinanceOS

A personal finance operating system: one place to see bank accounts, UPI,
cards, mandates/subscriptions, investments, and net worth — without handing
your financial data to a third party or paying for infrastructure before the
product has proven itself.

> **Status:** Pre-MVP, first vertical slice. Sign-in, accounts, transactions,
> net worth and CSV statement import (with de-duplication) work end to end.
> OFX, QIF, PDF, categorization, budgets and recurring items are not built
> yet. No real financial data is in the repository.

## Product Vision

Most personal finance tools either lock core features behind a subscription
or require linking live bank credentials through a paid aggregator (Plaid,
Salt Edge, etc.) from day one. FinanceOS starts from the opposite end: build
a genuinely useful net-worth and cash-flow picture from data the user already
has (CSV/PDF statement exports, manual entries), with zero recurring API
cost, and only add paid integrations later if the product earns them.

Guiding principles:

- **Privacy-first.** The user's financial data is sensitive by default. No
  real data in version control, no third-party analytics on transaction
  content, no silent telemetry.
- **Local-first ingestion.** MVP relies on manual entry and statement
  imports (CSV/PDF/OFX/QIF), not live bank-account linking.
- **Zero-API-budget.** No paid SaaS dependency is required to run or develop
  the product. See [Technology Stack](#technology-stack).
- **Boring, auditable code.** Financial software should be easy to review,
  not clever.

## Scope

### In scope (MVP)

- Manual account & transaction entry
- CSV / OFX / QIF statement import with a de-duplication pass
- Rule-based transaction categorization (merchant/keyword rules, user-editable)
- Recurring payments & mandates tracking (subscriptions, EMIs, SIPs)
- Manual investment holdings tracking (equities, mutual funds, FDs, etc.)
- Net worth over time (assets − liabilities)
- Budgets vs. actuals, basic reports and dashboards
- Multi-currency support at the data level (display defaults to one currency)

### Explicitly out of scope (for now)

- Live bank-account aggregation (Plaid/Salt Edge/Yodlee or India's AA
  framework) — paid, and a larger security surface than the MVP needs
- AI/LLM-powered categorization or insights (would require a paid API or a
  self-hosted model; revisit post-MVP)
- Multi-user / family sharing, mobile apps, notifications
- Brokerage/exchange API integrations

## Technology Stack

Chosen to be fully functional at **zero recurring cost** at MVP scale, while
staying on a path that scales up later without a rewrite.

| Layer | Choice | Why |
|---|---|---|
| Frontend | React + TypeScript (strict mode), built with Vite | A dedicated client application with a clear API boundary |
| Backend | Python + FastAPI | Typed REST API with automatic OpenAPI documentation |
| Styling | Tailwind CSS | No design-system license, fast iteration |
| Database | PostgreSQL | Free locally via Docker; free hosted tiers (Neon, Supabase) are enough for an MVP's data volume |
| ORM / migrations | SQLAlchemy + Alembic | Python-native persistence with explicit, auditable schema migrations |
| Validation | Zod (frontend) + Pydantic (API) | Validate data at both the client and server boundaries |
| Data fetching/cache | TanStack Query | Avoids hand-rolled client cache bugs |
| Testing | Vitest (frontend) + pytest (backend) + Playwright (e2e) | Free and open source |
| CI | GitHub Actions | Free minutes tier is sufficient for a solo/small-team MVP |
| Hosting (when ready) | Static frontend host + Python API host + Neon/Supabase DB, free tiers | No infra cost until usage genuinely outgrows free limits |
| Statement parsing | Local parsing libraries (CSV, OFX/QIF, PDF text extraction) | No paid document-parsing API |
| Categorization | Rule-based engine (keyword/merchant match, user-editable rules) | No LLM API cost; deterministic and auditable |

No component here requires a credit card to get the MVP running end to end.
If a future need (e.g. real OCR for scanned statements, or AI-assisted
categorization) justifies a paid API, that's a deliberate, separate decision
— not a default.

## Repository Structure

```
finance-os/
├── apps/
│   ├── web/              # React + TypeScript frontend (Vite)
│   └── api/              # Python + FastAPI backend and HTTP endpoints
├── packages/
│   ├── core/             # Framework-agnostic Python domain logic (money, dates, categorization)
│   ├── db/               # SQLAlchemy models, Alembic migrations, seed scripts
│   └── config/           # Shared frontend and Python tooling configuration
├── docs/                 # Architecture decisions, data model notes, threat model
├── scripts/              # One-off dev/maintenance scripts
├── config.example.yml    # Non-secret application and service settings
├── .github/workflows/    # CI pipelines (added once code exists)
├── CLAUDE.md             # Guidelines for AI-assisted development on this repo
├── README.md             # This file
└── .env.example          # Credential variable names (no real values)
```

See each directory's `README.md` for details on what belongs there.

## Setup

1. Install [Node.js LTS](https://nodejs.org/), [pnpm](https://pnpm.io/) and [uv](https://docs.astral.sh/uv/). `uv` downloads the pinned Python 3.13 itself.
2. Copy `config.example.yml` to `config.yml` for local non-secret settings.
3. Copy `.env.example` to `.env` and fill in local credentials (never commit `.env`).
4. Have a PostgreSQL server running and create the `finance_os` role and the `finance_os_dev` / `finance_os_test` databases — see [packages/db/README.md](./packages/db/README.md). This machine reuses its existing Postgres container instead of starting a new one.
5. In `apps/api`: `uv sync`, then `uv run python -m app.cli migrate`, then `uv run python -m app.cli create-user <username>`, then `uv run uvicorn --factory app.main:create_app --reload`.
6. In `apps/web`: `pnpm install`, then `pnpm dev`, and open http://127.0.0.1:5173.

A root `Makefile` wraps all of this: `make setup`, `make migrate`, `make create-user APP_USER=<name>`, `make dev` (API and web together), `make check` (lint, type-check and every test suite). Run `make help` for the list. On Windows, `winget install ezwinports.make` provides `make`. Each module's README lists its own commands.

`config.yml` holds non-secret runtime settings such as service URLs, ports,
and database host/name. `.env` is reserved for credentials such as database
username/password and the authentication secret. Keep local `config.yml` and
`.env` out of version control; update the example templates when defaults
change.

This section will be updated as each piece lands.

## Planned Modules

1. **Accounts & Transactions** — manual CRUD + CSV/OFX/QIF import, de-duplication
2. **Categorization** — rule engine with user-defined merchant/keyword rules
3. **Recurring & Mandates** — detect and track subscriptions, EMIs, SIPs
4. **Investments** — manual holdings (equities, MFs, FDs, bonds) and valuation history
5. **Net Worth** — assets − liabilities over time, trend charts
6. **Budgets & Reports** — monthly budgets vs. actuals, category breakdowns
7. **(Future, deliberate opt-in)** — live account aggregation, AI insights, multi-user

## Contributing / AI-Assisted Development

This project uses AI coding assistants as part of the development workflow.
See [CLAUDE.md](./CLAUDE.md) for coding guidelines, security requirements,
and the expected development workflow — read it before generating or
reviewing code in this repo.
