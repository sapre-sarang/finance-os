# scripts

One-off developer and maintenance scripts (e.g., database reset, fixture
generation), primarily written in Python for backend/database workflows and
Node.js where frontend tooling requires it. Not part of the application
runtime.

**Status:** empty — not yet scaffolded.

Any script that touches data must only ever operate on local/dev databases
seeded with synthetic data — never point one of these at a database holding
real financial data.
