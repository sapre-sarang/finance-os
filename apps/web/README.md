# apps/web

The React + TypeScript frontend (Vite, Tailwind CSS v4, TanStack Query, Zod, React Router).

**Status:** first version. TypeScript strict mode is on, and every API response is validated with Zod before use.

## Commands

Run from `apps/web` (requires Node.js LTS and [pnpm](https://pnpm.io/)):

```
pnpm install
pnpm dev         # http://127.0.0.1:5173, proxies /api to the API on 127.0.0.1:8000
pnpm typecheck
pnpm test        # Vitest (money parsing and formatting)
pnpm build
```

Start the API first (see `apps/api/README.md`) and create a user with
`uv run python -m app.cli create-user <username>`.

## Screens

Sign in, Overview (net worth and balances), Accounts, Transactions (add, delete, page, filter by account), and Import (upload, map columns, review, confirm).

## Rules specific to this app

- Amounts never pass through floating point: `src/lib/money.ts` converts between decimal text and integer minor units using string arithmetic.
- Build scripts are not run for dependencies (`pnpm-workspace.yaml` sets `allowBuilds: esbuild: false`); esbuild ships its binary as a separate package.
- Fonts are system fonts and nothing is loaded from third-party hosts.
