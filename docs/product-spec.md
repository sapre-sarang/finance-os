# FinanceOS Product Specification

**Status:** Draft — pre-MVP  
**Product:** FinanceOS  
**Audience:** Product, design, and engineering

This specification translates the product vision and MVP scope in the
[README](../README.md) into user-centered objectives and verifiable
requirements. It follows a concise, iterative PRD structure: user needs,
objectives, scope, requirements, acceptance criteria, and open decisions.
Requirements should be refined as the team learns; this document is not a
prescription for implementation details.

## 1. Problem and product intent

People need a clear picture of their accounts, cash flow, recurring
commitments, investments, and net worth. Existing options can put useful
features behind subscriptions or require linking live bank credentials.
FinanceOS lets an individual build that picture from information they enter
or statement files they already have, while keeping privacy and financial
correctness central.

## 2. Primary persona

### Privacy-conscious individual

An individual who wants to understand their finances across accounts,
transactions, recurring payments, investments, and budgets, but does not
want to provide live bank credentials or send transaction details to
third-party services.

**Needs**

- Enter accounts and transactions manually or import existing statements.
- Correctly identify duplicate transactions and categorize spending.
- See commitments, investments, budgets, and net worth together.
- Retain control of financial data and use the product without paid API
  dependencies.

**Current alternative and pain point:** subscription-based tools or
credential-linked aggregators may introduce costs and privacy concerns.

## 3. Objectives and success criteria

### Product objectives

1. **Build a useful financial overview from user-controlled data.** Manual
   entry and statement imports form the MVP's ingestion paths.
2. **Make financial summaries dependable.** Transaction imports, balances,
   budgets, and net-worth calculations must not silently duplicate or
   misrepresent amounts.
3. **Keep financial data private by default.** Avoid live bank linking,
   third-party analytics on financial content, and unnecessary external
   services.
4. **Keep the MVP affordable to run and develop.** The product must not
   require recurring paid APIs or infrastructure at MVP scale.

### MVP success criteria

- A user can enter accounts and transactions and see them represented in
  reports.
- A user can import supported statement files and review the resulting
  transactions without duplicate imports inflating totals.
- A user can manage categorization rules, recurring commitments, investment
  holdings, and budgets manually.
- Net worth and budget-versus-actual views reflect the underlying records
  using correct financial arithmetic.
- No MVP workflow depends on live bank credentials, a paid API, or
  third-party analytics on transaction content.

Quantitative adoption, performance, and reliability targets have not been
specified in the README and should be set after the first user-validation
cycle.

## 4. MVP scope

| Capability | Included in MVP |
|---|---|
| Accounts and transactions | Manual account and transaction entry; create, read, update, and delete operations |
| Statement imports | CSV, OFX, and QIF imports with a de-duplication pass |
| Categorization | Deterministic merchant/keyword rules that users can edit |
| Recurring payments and mandates | Tracking subscriptions, EMIs, and SIPs |
| Investments | Manual holdings, including equities, mutual funds, and fixed deposits |
| Net worth | Assets minus liabilities over time |
| Budgets and reports | Budgets versus actuals, category breakdowns, basic reports, and dashboards |
| Currency | Currency recorded at the data level; display defaults to one currency |

The README also mentions PDF statements and local PDF text extraction.
Whether PDF import is required for the first MVP release is an open decision
(see [Open decisions](#9-open-decisions)). Scanned-document OCR is not
included.

## 5. Functional requirements and acceptance criteria

### FR-1: Accounts and transactions

Users can maintain account and transaction records through manual entry.

**Acceptance criteria**

- A user can create, view, edit, and delete an account and a transaction.
- A transaction is associated with the appropriate account and retains its
  amount, currency, and as-occurred date.
- Invalid or incomplete input is rejected at the application boundary with
  a useful validation error; invalid data is not persisted.

### FR-2: Statement imports and de-duplication

Users can import supported statement files without turning a repeated import
into duplicate financial activity.

**Acceptance criteria**

- The MVP accepts valid CSV, OFX, and QIF files and produces transaction
  records for review or use.
- Malformed or unsupported input is reported as an import error and does
  not create partial, invalid transaction records.
- Re-importing the same statement does not inflate transaction counts,
  account activity, or reports with duplicate entries.
- Distinct transactions remain distinct, including legitimate repeated
  transactions with the same merchant or amount.
- The import flow applies the project's configured file-size limits and
  validates parsed records before persistence.

### FR-3: Transaction categorization

Users can categorize transactions with editable merchant or keyword rules.

**Acceptance criteria**

- A user can create, edit, and remove a categorization rule.
- Matching transactions receive the rule's category consistently.
- Users can correct a transaction's category without requiring an AI or
  third-party categorization service.
- Given the same transaction and rules, categorization produces the same
  result.

### FR-4: Recurring payments and mandates

Users can track recurring financial commitments, including subscriptions,
EMIs, and SIPs.

**Acceptance criteria**

- A user can record, view, edit, and remove a recurring commitment.
- The record can be identified as a subscription, EMI, SIP, or other
  supported commitment type.
- Recurring commitments are visible in the appropriate overview or report.

### FR-5: Investment holdings

Users can manually track investment holdings, including equities, mutual
funds, and fixed deposits.

**Acceptance criteria**

- A user can record, view, edit, and remove a holding.
- Holdings retain their relevant amount/value and currency without
  converting financial values through binary floating-point arithmetic.
- Investment holdings are included in asset and net-worth views as
  applicable.

### FR-6: Net worth

Users can see net worth over time, calculated as assets minus liabilities.

**Acceptance criteria**

- The displayed net-worth value follows `assets - liabilities`.
- The history represents values at their relevant dates rather than
  relying on the server's local timezone.
- Changes to the underlying accounts or holdings are reflected in the
  corresponding net-worth view.

### FR-7: Budgets and reports

Users can compare budgets with actual activity and inspect basic financial
reports.

**Acceptance criteria**

- A user can create, view, edit, and remove a budget.
- Budget-versus-actual results and category breakdowns are derived from the
  underlying transactions and categories.
- Report totals do not count a transaction more than once.

### FR-8: Multiple currencies

The data model supports amounts in multiple currencies while the display
defaults to one currency.

**Acceptance criteria**

- A stored monetary amount retains its currency.
- The default display currency can be applied consistently across the
  interface.
- No currency conversion is presented as exact unless the applicable
  exchange-rate source and conversion date are defined.

## 6. Cross-cutting quality and privacy requirements

These requirements apply to every MVP capability.

### Financial correctness

- Store and calculate money using integer minor units or a fixed-point
  decimal representation, not binary floating-point arithmetic.
- Keep transaction occurrence dates distinct from import metadata and
  represent timestamps in UTC; do not use the server's local timezone for
  financial-date logic.
- Domain calculations must be testable independently of the web framework
  and persistence layer.
- Logic that affects money, imports, categorization, or net worth must have
  automated tests using synthetic data.

### Privacy and security

- Do not collect live bank credentials or add bank-account aggregation in
  the MVP.
- Do not send transaction content, merchant names, or amounts to product
  analytics or telemetry.
- Require server-side authentication before any API access to financial
  data; never authorize access using a client-supplied user ID.
- Validate and sanitize imports at the boundary, enforce upload-size limits,
  and validate parsed output before it reaches persistence.
- Once persistence exists, encrypt sensitive fields at rest at minimum for
  linked account identifiers and imported raw statement data. Keep
  credentials and encryption keys outside source control and load them from
  environment variables.
- Use only synthetic financial data in tests and fixtures.

### Cost and dependencies

- MVP workflows must function without paid third-party APIs, including
  hosted parsing, enrichment, or AI services.
- Prefer free, open-source, maintainable dependencies; no dependency may
  introduce a required recurring paid service for MVP use.

### Usability and error handling

- Invalid input and failed imports must produce an explicit, actionable
  error; they must not appear successful or silently discard financial
  records.
- Users must be able to review and correct manually entered or imported
  financial information.

## 7. Explicitly out of scope

- Live bank-account aggregation, credential-based linking, and India's
  Account Aggregator framework.
- AI/LLM-powered categorization or insights.
- Multi-user or family sharing, mobile applications, and notifications.
- Brokerage or cryptocurrency-exchange API integrations.
- Paid OCR or other paid document-processing APIs.

These may be reconsidered only through a deliberate, separately scoped
product decision.

## 8. Assumptions and constraints

- The primary user is an individual managing their own finances.
- Users can obtain statement exports from their financial providers; the
  MVP does not connect to those providers.
- Manual entry and local statement parsing are sufficient to validate the
  product before considering integrations.
- The chosen stack is React with strict TypeScript, Python with FastAPI,
  PostgreSQL, and SQLAlchemy/Alembic, as documented in the README.
- The initial product is pre-MVP; hosting, authentication details, UI
  designs, and operational targets remain to be decided as modules are
  scaffolded.

## 9. Open decisions

1. Is text-based PDF import required in the first MVP release, alongside
   CSV, OFX, and QIF?
2. How should potential duplicates be identified and presented for review,
   especially when statement formats lack stable transaction identifiers?
3. Is cross-currency conversion required for MVP reporting? If so, what
   exchange-rate source and valuation date should be used without adding a
   paid dependency?
4. What authentication and deployment model should serve the initial
   individual user while ensuring every financial-data API request is
   authenticated?
5. What budget periods and default categories should be available on first
   use?

## 10. Reference

- [Atlassian: Product requirements](https://www.atlassian.com/agile/product-management/requirements) — concise, iterative PRD guidance emphasizing user needs, objectives, assumptions, scope, and keeping requirements adaptable.
- [FinanceOS README](../README.md) — product vision, MVP scope, technology choices, and planned modules.
- [Repository development and security guidelines](../CLAUDE.md) — implementation constraints for privacy, financial correctness, validation, and testing.
