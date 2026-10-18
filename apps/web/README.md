# apps/web

The React + TypeScript frontend, planned as a Vite single-page application.

**Status:** empty — not yet scaffolded.

Will contain:
- `src/` — application entry point, pages, and UI components
- API client code for requests to `apps/api`
- UI styling (Tailwind)

The frontend handles presentation and client-side validation. Financial
business rules and persistence belong in the Python backend and
`packages/core`; the browser must never connect directly to the database.
