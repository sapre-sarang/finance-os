# FinanceOS

A personal finance operating system: one place to see bank accounts, UPI,
cards, mandates/subscriptions, investments, and net worth — without handing
your financial data to a third party or paying for infrastructure before the
product has proven itself.

> **Status:** Pre-MVP. This repository currently contains project scaffolding
> and planning documents only. No application code, dependencies, or real
> financial data exist yet.

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

Nothing is installable yet — this is intentional until the first module is
scaffolded. Once the frontend and backend are scaffolded:

1. Install [Node.js LTS](https://nodejs.org/) and [pnpm](https://pnpm.io/) for the React frontend.
2. Install Python 3.11 or newer for the API and domain package.
3. Copy `config.example.yml` to `config.yml` for local non-secret settings.
4. Copy `.env.example` to `.env` and fill in local credentials (never commit `.env`).
5. Run a local PostgreSQL instance (Docker Compose file to be added in `docs/`).
6. Install frontend dependencies with `pnpm install`.
7. Create a Python virtual environment and install the backend dependencies from `apps/api`.
8. Apply database migrations and start the API and frontend using their documented development commands.

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
