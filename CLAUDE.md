# CLAUDE.md — FabGreat Library

## Stack

| Layer | Choice |
|---|---|
| Backend | FastAPI + SQLAlchemy 2.0 (async) + Alembic + Postgres |
| Auth | JWT access token (short-lived) + opaque refresh token (DB-stored) |
| Frontend | Next.js 16 (App Router) + TypeScript + Tailwind v4 + shadcn/ui + TanStack Query v5 |
| Types | TS client/types generated from OpenAPI spec (`packages/types/`) |
| Card data | the-fab-cube/flesh-and-blood-cards dataset (pinned release, imported via script) |
| Local infra | Docker Compose (Postgres + optional pgAdmin) |

## Repo layout

```
apps/api/                  FastAPI backend
  app/
    core/
      config.py            pydantic-settings (reads .env)
      security.py          hash_password, verify_password, JWT create/decode
      deps.py              get_current_user, get_optional_user FastAPI deps
    db/
      base.py              SQLAlchemy declarative Base
      models.py            All ORM models (7 tables)
      session.py           AsyncSessionLocal, get_db dependency
    routers/
      auth.py              /auth/* — register, token, refresh, logout, me
      sets.py              /sets, /sets/{id}/printings
      cards.py             /cards, /cards/{id}
      search.py            /search/printings
      collection.py        /collection/summary, /collection/items, /collection/bulk
      missing.py           /missing — unowned printings (filtered, paginated)
      wishlist.py          /wishlists — CRUD; 402 on free-tier limit
    schemas/
      auth.py              Pydantic schemas for auth endpoints
      cards.py             SetOut, SetSummary, CardListItem, CardDetail, PrintingWithCard, Paginated*
      collection.py        OwnedPrintingOut, UpsertItemRequest, BulkRequest, ItemResult
      wishlist.py          WishlistFilter, WishlistCreate, WishlistOut
    services/
      user.py              create_user, get_user_by_email
      auth.py              create/use/revoke refresh tokens
      cards.py             list_sets_with_counts, list_cards, list_printings, get_card, get_set
      collection.py        get_collection_summary, upsert_item, bulk_apply, get_missing_printings
      wishlist.py          create_wishlist, list_wishlists, delete_wishlist (enforces free-tier limit)
  alembic/                 migrations
  scripts/
    import_cards.py        Downloads + upserts the-fab-cube dataset
    seed.py                Dev seed data (idempotent)
  tests/
    conftest.py            db + client fixtures (per-test rollback)
    test_auth.py
    test_cards.py
    test_sets.py
    test_search.py
    test_collection.py
    test_constraints.py
    test_wishlists.py
    test_missing.py

apps/web/                  Next.js 16 (App Router)
  app/
    page.tsx               Landing page with API health check + CTAs
    login/page.tsx         Login form → stores token → redirects to /sets
    register/page.tsx      Register form → stores token → redirects to /sets
    sets/
      page.tsx             Set grid — completion bars when authenticated
      [id]/page.tsx        Printings table — search/filter, +1 increment, bulk actions
    missing/
      page.tsx             Missing printings — filters, table, save/load/delete wishlist
    layout.tsx             Root layout wrapping Providers + Navbar
    globals.css
  components/
    navbar.tsx             Nav + logout; reads auth state via useEffect (no SSR flash)
    providers.tsx          QueryClientProvider wrapper ('use client')
    ui/                    shadcn/ui — badge, card, button, checkbox, input
  lib/
    api.ts                 Typed API client — re-exports generated types, contains 11 API functions
    auth.ts                Token helpers — getToken / setToken / clearToken (localStorage)

packages/types/            Generated TS types from OpenAPI (do not edit by hand)
infra/docker/              docker-compose.yml
docs/
  adr/
    001-strategy-b-printings.md
    002-monorepo.md
    003-jwt-refresh-tokens.md
    004-async-stack.md
CHANGELOG.md               Keep a Changelog format — one entry per phase
```

## Workflow rules

1. **One task at a time.** Complete the current numbered task, then stop.
2. **After every task** provide: (a) what changed, (b) how to run/verify, (c) what the next task is.
3. **Do not start the next task** until explicitly instructed.
4. **Every endpoint** must have at minimum: one happy-path test + one failure-path test.
5. **If anything is unclear** after reading the spec or existing code, use `AskUserQuestion` — do not guess.
6. **Keep code simple and conventional.** No clever abstractions; no features beyond what the current task requires.

## Domain invariants

- Ownership is tracked by `(user_id, printing_id)` — unique constraint in DB (Strategy B: foiling is encoded in the Printing row itself).
- `qty` must be ≥ 1 when a row exists; setting `qty = 0` **deletes** the row — enforced in service layer.
- `qty` may never go negative.
- Free tier: maximum **1 saved wishlist** per user — enforced in the service layer, not the DB.
- Wishlist stores a `filter_json` blob (set_id, traits, etc.) plus a name.
- No condition tracking — quantity only.

## Data model (key relationships)

```
users ──< refresh_tokens
users ──< wishlists
users ──< owned_printings >── printings >── cards
                               printings >── sets
```

## Card dataset (Strategy B)

- Source: `the-fab-cube/flesh-and-blood-cards` GitHub release (pinned to `CARDS_DATA_VERSION`, default `v8.1.0`).
- One `Printing` row = one specific foiling of a card in a set edition.
- Foiling codes: `S`=Standard, `R`=Rainbow, `C`=Cold, `G`=Gold Cold.
- Edition codes: `A`=Alpha, `F`=First, `U`=Unlimited, `N`=No specified edition.
- Import is idempotent (`ON CONFLICT DO UPDATE`). Re-running `make import-cards` is safe.

## Current API surface

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | — | Create account, returns tokens |
| POST | `/auth/token` | — | Login (OAuth2 form), returns tokens |
| POST | `/auth/refresh` | — | Rotate refresh token |
| POST | `/auth/logout` | Bearer | Revoke refresh token |
| GET | `/auth/me` | Bearer | Current user info |
| GET | `/sets` | Optional | Sets with printing_count + owned_count |
| GET | `/sets/{id}/printings` | — | Printings in a set (filtered, paginated) |
| GET | `/cards` | — | Cards (filtered, paginated) |
| GET | `/cards/{id}` | — | Card detail with all printings |
| GET | `/search/printings` | — | Cross-set printing search |
| GET | `/collection/summary` | Bearer | Owned printings with detail |
| POST | `/collection/items` | Bearer | Upsert single item qty |
| POST | `/collection/bulk` | Bearer | Atomic bulk actions |
| GET | `/missing` | Bearer | Unowned printings — filtered by set_id, card_id, edition, foiling, rarity, artists |
| POST | `/wishlists` | Bearer | Create wishlist; 402 if one already exists |
| GET | `/wishlists` | Bearer | List user's wishlists |
| DELETE | `/wishlists/{id}` | Bearer | Delete wishlist; 404 if not found or wrong user |

## Frontend conventions

- **Token storage:** `localStorage` key `fab_access_token` — read via `getToken()` in `lib/auth.ts`.
- **Auth state in components:** always read token inside `useEffect` to avoid SSR hydration mismatches.
- **Next.js 16 params:** dynamic route params are `Promise<{id: string}>` — unwrap with `use(params)` from React 19.
- **Query keys:** `['sets', token]`, `['set-printings', setId, filters]`, `['collection', setId]`, `['missing', filters]`, `['wishlists']`.
- **After any mutation** that changes ownership: invalidate `['collection', setId]` and `['sets']` so completion bars update.
- **Auth redirect on protected pages:** read token in `useEffect`; if null call `router.push('/login')` and return null until ready.
- **shadcn components** installed: badge, card, button, checkbox, input.

## Test setup (critical notes)

- Do NOT set `asyncio_default_fixture_loop_scope` in `pyproject.toml` — asyncpg binds connections to the event loop.
- `db` fixture creates a fresh engine per test and rolls back the transaction after.
- `client` fixture patches `db.commit = db.flush` so route-level commits stay inside the test transaction.
- `import app.db.models` MUST come before `from app.main import app` in conftest — otherwise `app` is shadowed by the package.
- Test emails must use real TLDs (e.g. `@example.com`); email-validator rejects `.local`.
- Tests that insert sets must use codes that don't exist in the real dataset (avoid real codes like WTR, ARC, etc.). Use short synthetic codes like `TSTA`, `CNT`, `SP1`.
- Tests asserting an empty DB will fail after `make import-cards` — use `isinstance(resp.json(), list)` instead of `== []`.

## OpenAPI / type generation

The backend is the single source of truth for the API contract. `packages/types/index.ts` is
**committed** — no regen needed to build. After any backend schema change, regenerate:

```bash
# bash (Git Bash / Linux / macOS)
cd apps/api && .venv/Scripts/python -c "import json; from app.main import app; print(json.dumps(app.openapi()))" > ../../packages/types/openapi.json
cd packages/types && npx openapi-typescript openapi.json -o index.ts
```

```powershell
# PowerShell (Windows)
cd apps\api; .venv\Scripts\python -c "import json; from app.main import app; print(json.dumps(app.openapi()))" | Out-File -FilePath ..\..\packages\types\openapi.json -Encoding utf8
cd packages\types; npx openapi-typescript openapi.json -o index.ts
```

`apps/web/lib/api.ts` re-exports all backend types via `@fabgreat/types` alias (configured in
`apps/web/tsconfig.json`). **Do not add manual interface definitions** for backend schemas —
they will drift. Only `PrintingFilters` and `MissingFilters` (frontend-only query param
groupings) live in `api.ts` itself.

## Key commands

`make` targets work in Git Bash / Linux / macOS. On Windows PowerShell use the direct equivalents.

| Task | `make` | PowerShell |
|---|---|---|
| Start Postgres | `make up` | `docker compose -f infra/docker/docker-compose.yml up -d` |
| FastAPI dev server | `make api-dev` | `cd apps/api; .venv\Scripts\uvicorn app.main:app --reload --port 8000` |
| Next.js dev server | `make web-dev` | `cd apps/web; npm run dev` |
| Run migrations | `make migrate` | `cd apps/api; .venv\Scripts\alembic upgrade head` |
| Seed dev data | `make seed` | `cd apps/api; .venv\Scripts\python -m scripts.seed` |
| Import card dataset | `make import-cards` | `cd apps/api; .venv\Scripts\python -m scripts.import_cards` |
| Run tests | `make test` | `cd apps/api; .venv\Scripts\pytest -v` |

## Environment

- Root `.env` (copy from `.env.example`) — consumed by Docker Compose and the API.
- `apps/web/.env.local` (copy from `.env.local.example`) — consumed by Next.js.
- Never commit `.env` or `.env.local`.
