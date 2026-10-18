# CLAUDE.md

Guidance for Claude Code (and any AI assistant) working in this repository.
This file governs how code should be written and reviewed here; it takes
precedence over generic defaults, but not over explicit instructions from
the user in a given conversation.

## Current State

Pre-MVP: every directory under `apps/`, `packages/`, `docs/`, and
`scripts/`, plus `.github/workflows/`, contains only a placeholder
`README.md` describing what it will eventually hold — there is no
scaffolded code, no `package.json`/`pyproject.toml`, no dependencies, and no
build/lint/test commands yet. Don't search for tooling that isn't there;
check each directory's `README.md` and the root [README.md](./README.md)
for what's planned. Once a module is scaffolded, this section (and each
affected directory's README) should be updated with the real commands in
the same change — see "Don't install dependencies or scaffold a framework
without asking" below.

## Project Goals

FinanceOS is a personal finance tracker: accounts, transactions, mandates,
investments, and net worth, built with **zero recurring API/infra cost** at
MVP scale and **privacy as a hard constraint**, not an afterthought. Full
product scope lives in [README.md](./README.md) — read it first for context
on what's in scope and why the stack was chosen.

Two things make this repo different from a typical CRUD app:

1. **The data is sensitive.** Transaction history reveals income, spending
   habits, debts, and relationships. Treat every schema and API decision as
   if it will be reviewed by someone looking for a privacy failure.
2. **The numbers must be correct.** This is not a toy app — a rounding bug
   or a double-counted transaction is a correctness bug, not a cosmetic one.

## Coding Guidelines

- **Use strict typing in both languages.** Enable TypeScript strict mode in
  the React frontend; type Python code and avoid unvalidated `Any`. Prefer
  `unknown` + narrowing in TypeScript.
- **Money is never a `float`.** Store monetary amounts as integers in the
  smallest currency unit (paise/cents) or as a fixed-point decimal type.
  Never do financial arithmetic in JavaScript `number` or Python `float`
  beyond trivial display formatting.
- **Dates and timezones are explicit.** Store timestamps in UTC; store a
  transaction's "as-occurred" date separately from "as-imported" metadata.
  Never rely on the server's local timezone for financial-date logic.
- **Validate at the boundary.** Validate frontend inputs with Zod and
  backend API/import inputs with Pydantic (or equivalent) before they reach
  domain logic. Domain logic trusts its inputs; boundaries don't.
- **No speculative abstraction.** Don't build a generic "integration
  framework" for bank APIs we don't have yet. Build what the current module
  needs; refactor when a second concrete case demands it.
- **No comments explaining *what* the code does.** Name things well instead.
  Comment only non-obvious *why* (e.g., "statement export uses DD/MM/YYYY
  even when locale is en-US — observed in HDFC exports").
- **Keep domain logic framework-agnostic.** Business rules (categorization,
  net-worth calculation, de-duplication) live in `packages/core` as Python
  code, independent of FastAPI and the database layer.

## Security Requirements

These are non-negotiable for this project, not general best practice
suggestions:

1. **Never commit secrets, credentials, or real financial data.** Local
   `.env` files contain credentials only; non-secret runtime settings belong
   in local `config.yml`, based on the checked-in `config.example.yml`.
   Neither local file, API keys, database dumps, nor real statement exports
   may enter version control — see `.gitignore`. If you ever generate test
   fixtures, they must be synthetic (clearly fake names, round numbers,
   obviously fictional account numbers).
2. **No live bank-account linking in this phase.** Do not add Plaid, Salt
   Edge, Yodlee, India's Account Aggregator framework, or any credential-based
   bank integration unless the user explicitly asks for it as a deliberate,
   scoped feature. It is out of scope by default (see README).
3. **No outbound calls to paid third-party APIs** (LLM APIs, OCR services,
   enrichment services) without explicit user approval. The MVP's
   categorization and parsing must work with local, free, open-source
   logic.
4. **Encrypt sensitive fields at rest once persistence exists** — at minimum,
   linked account identifiers and any imported raw statement blobs. Database
   credentials and encryption keys come from environment variables, never
   hardcoded.
5. **Auth before data access, always.** Every API route that touches user
   financial data must check session/auth state server-side — never trust a
   client-supplied user ID.
6. **Validate and sanitize all imports.** Statement parsers (CSV/OFX/QIF/PDF)
   are an attack surface (malformed files, CSV injection, oversized
   uploads). Enforce size limits and strict schema validation on parsed
   output before it reaches the database.
7. **Dependency hygiene.** Before adding a new dependency, prefer
   well-maintained, widely-used packages. Audit frontend dependencies with
   `pnpm audit` and Python dependencies with an appropriate vulnerability
   scanner once the project has dependencies.
8. **No telemetry/analytics on financial data content.** Product analytics,
   if ever added, must be on usage events (e.g., "import completed"), never
   on transaction content, merchant names, or amounts.

## Development Workflow

- **Don't install dependencies or scaffold a framework without asking**
  while the project is still at the planning stage described in this file —
  once the user greenlights starting a specific module (e.g., "scaffold
  apps/web"), proceed normally.
- **Trunk-based, small commits.** Commit logical units of work; write commit
  messages that explain *why*, not a restatement of the diff.
- **Tests accompany logic changes.** Anything in `packages/core` (money math,
  categorization, de-duplication, net-worth calculation) needs Python unit
  tests. API endpoints get at least a happy-path + one validation-failure
  test; frontend behavior gets focused tests.
- **No real data in tests or fixtures, ever.** Use clearly synthetic fixtures.
- **Ask before adding a paid service of any kind** — hosting, APIs, SaaS
  tools — even if it has a "free tier," confirm it fits the zero-budget
  constraint before wiring it in.
- **Keep README.md and this file in sync** with reality: if the stack,
  structure, or security model changes, update both in the same change.
- **Prefer editing over rewriting.** Don't restructure unrelated code while
  implementing a feature; file structural changes as their own commit.

## When In Doubt

If a request would involve connecting to a real bank, storing real
financial data, adding a paid API, or weakening one of the security
requirements above, stop and ask the user rather than proceeding.
