  # CLAUDE.md — FabGreat Library

## Stack

| Layer | Choice |
|---|---|
| Backend | FastAPI + SQLAlchemy 2.0 (async) + Alembic + Postgres |
| Auth | JWT access token (short-lived) + refresh token (DB-stored) |
| Frontend | Next.js 16 (App Router) + TypeScript + Tailwind v4 + shadcn/ui + TanStack Query |
| Types | TS client/types generated from OpenAPI spec (`packages/types/`) |
| Local infra | Docker Compose (Postgres); Redis optional, not required for MVP |

## Repo layout

```
apps/api/          FastAPI backend
  app/
    core/          config, security utilities
    db/            models, session, base
    routers/       one file per feature domain
    services/      business logic (no SQL in routers)
  alembic/         migrations
  tests/

apps/web/          Next.js frontend
  app/             App Router pages
  components/ui/   shadcn components
  lib/             API client, utilities

packages/types/    generated TS types from OpenAPI (do not edit by hand)
infra/docker/      docker-compose.yml
```

## Workflow rules

1. **One task at a time.** Complete the current numbered task, then stop.
2. **After every task** provide: (a) what changed, (b) how to run/verify, (c) what the next task is.
3. **Do not start the next task** until explicitly instructed.
4. **Every endpoint** must have at minimum: one happy-path test + one failure-path test.
5. **If anything is unclear** after reading the spec or existing code, call `askUserQuestionTool` — do not guess.
6. **Keep code simple and conventional.** No clever abstractions; no features beyond what the current task requires.

## Domain invariants

- Ownership is tracked by `(user_id, printing_id, foil_type)` — unique constraint in DB.
- `qty` must be ≥ 1 when a row exists; setting `qty = 0` **deletes** the row (enforced in service layer).
- `qty` may never go negative.
- Free tier: maximum **1 saved wishlist** per user — enforced in the service layer, not only the DB.
- Wishlist stores a `filter_json` blob (set_id, traits, etc.) plus a name.
- No condition tracking — quantity only.

## OpenAPI-first / type generation

- The backend is the source of truth for the API contract.
- After any endpoint change, regenerate types:
  ```bash
  # export schema
  cd apps/api && python -c "
  import json; from app.main import app
  print(json.dumps(app.openapi()))
  " > ../../packages/types/openapi.json

  # generate TS client (Phase 7 wires this up fully)
  cd packages/types && npx openapi-typescript openapi.json -o index.ts
  ```
- Frontend must import types from `packages/types/` — no manual type duplication.

## Key Make targets

```
make up          start Postgres
make api-dev     FastAPI on :8000 (hot-reload)
make web-dev     Next.js on :3000 (hot-reload)
make migrate     alembic upgrade head
make test        pytest -v
```

## Environment

- Root `.env` (copy from `.env.example`) — consumed by Docker Compose and the API.
- `apps/web/.env.local` (copy from `.env.local.example`) — consumed by Next.js.
- Never commit `.env` or `.env.local`.
