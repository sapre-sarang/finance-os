# packages/core

Framework-agnostic Python domain logic, used by `apps/api` and tests/scripts.
No FastAPI or database client — keep this package focused on finance rules.

**Status:** empty — not yet scaffolded.

Will contain:
- Money/currency types and arithmetic (integer minor-units or fixed-point decimals; no floats)
- Transaction categorization rule engine
- Statement de-duplication logic
- Net-worth and budget calculation

Anything here must be unit-testable without a running database or API server.
