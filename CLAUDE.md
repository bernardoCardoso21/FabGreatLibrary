# CLAUDE.md — FabGreat Library

## Stack

| Layer | Choice |
|---|---|
| Backend | FastAPI + SQLAlchemy 2.0 (async) + Alembic + Postgres |
| Auth | JWT access token (short-lived) + opaque refresh token (DB-stored) |
| Frontend | Next.js 16 (App Router) + TypeScript + Tailwind v4 + shadcn/ui + TanStack Query |
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
    schemas/
      auth.py              Pydantic schemas for auth endpoints
      cards.py             SetOut, SetSummary, CardListItem, CardDetail, PrintingWithCard, Paginated*
      collection.py        OwnedPrintingOut, UpsertItemRequest, BulkRequest, ItemResult
    services/
      user.py              create_user, get_user_by_email
      auth.py              create/use/revoke refresh tokens
      cards.py             list_sets_with_counts, list_cards, list_printings, get_card, get_set
      collection.py        get_collection_summary, upsert_item, bulk_apply
      wishlist.py          create_wishlist (enforces free-tier limit)
  alembic/                 migrations
  scripts/
    import_cards.py        Downloads + upserts the-fab-cube dataset (make import-cards)
    seed.py                Dev seed data (make seed)
  tests/
    conftest.py            db + client fixtures (per-test rollback)
    test_auth.py
    test_cards.py
    test_sets.py
    test_search.py
    test_collection.py
    test_constraints.py

apps/web/                  Next.js frontend (App Router)
  app/                     Pages
  components/ui/           shadcn/ui components
  lib/                     API client, utilities

packages/types/            Generated TS types from OpenAPI (do not edit by hand)
infra/docker/              docker-compose.yml
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

## Test setup (critical notes)

- Do NOT set `asyncio_default_fixture_loop_scope` in `pyproject.toml` — asyncpg binds connections to the event loop.
- `db` fixture creates a fresh engine per test and rolls back the transaction after.
- `client` fixture patches `db.commit = db.flush` so route-level commits stay inside the test transaction.
- `import app.db.models` MUST come before `from app.main import app` in conftest — otherwise `app` is shadowed by the package.
- Test emails must use real TLDs (e.g. `@example.com`); email-validator rejects `.local`.

## OpenAPI / type generation

The backend is the source of truth for the API contract. After any endpoint change:

```bash
# Export schema
cd apps/api && python -c "
import json; from app.main import app
print(json.dumps(app.openapi()))
" > ../../packages/types/openapi.json

# Generate TS types
cd packages/types && npx openapi-typescript openapi.json -o index.ts
```

Frontend must import types from `packages/types/` — no manual type duplication.

## Key Make targets

```
make up            Start Postgres (detached)
make api-dev       FastAPI on :8000 (hot-reload)
make web-dev       Next.js on :3000 (hot-reload)
make migrate       alembic upgrade head
make seed          Insert dev seed data (idempotent)
make import-cards  Download + upsert full card dataset (idempotent)
make test          pytest -v
```

## Environment

- Root `.env` (copy from `.env.example`) — consumed by Docker Compose and the API.
- `apps/web/.env.local` (copy from `.env.local.example`) — consumed by Next.js.
- Never commit `.env` or `.env.local`.
