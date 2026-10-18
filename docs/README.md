# docs

Product requirements, architecture decisions, data model notes, and the
threat model for FinanceOS. Plain Markdown, no build step.

Documents:
- `product-spec.md` — personas, objectives, MVP requirements, acceptance
  criteria, and open product decisions

Planned documents:
- `architecture.md` — React frontend, Python API, domain package, and database boundaries
- `data-model.md` — entities, relationships, money/date conventions
- `threat-model.md` — what we protect against and why (relevant given this
  app handles financial PII)
- `docker-compose.yml` — local PostgreSQL for development (to be added when
  `packages/db` is scaffolded)
