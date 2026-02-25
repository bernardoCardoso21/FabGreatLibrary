# FabGreat Library

Flesh & Blood TCG collection tracker — monorepo with a FastAPI backend and Next.js frontend.

Track which printings you own, browse the full card catalog, and manage your collection with single-click or bulk updates.

---

## Architecture

```mermaid
graph TB
    subgraph Client["Browser"]
        FE["Next.js 16 (App Router)\nTailwind v4 · shadcn/ui\nTanStack Query"]
    end

    subgraph API["FastAPI :8000"]
        direction TB
        R["Routers\nauth · sets · cards\nsearch · collection"]
        S["Services\nbusiness logic"]
        M["SQLAlchemy Models"]
        R --> S --> M
    end

    subgraph Infra["Docker Compose"]
        PG[("PostgreSQL :5432")]
        PGA["pgAdmin :5050\n(optional)"]
    end

    DS["the-fab-cube/flesh-and-blood-cards\nGitHub Release (pinned)"]

    FE -- "REST / JSON" --> API
    API --> PG
    PGA -.-> PG
    DS -- "make import-cards\n(one-off / idempotent)" --> PG
```

---

## Data model

```mermaid
erDiagram
    users {
        uuid id PK
        string email UK
        string hashed_password
        bool is_active
        bool is_admin
        datetime created_at
    }
    sets {
        uuid id PK
        string code UK
        string name
        string source_id
        string image_url
        datetime created_at
    }
    cards {
        uuid id PK
        string source_id UK
        string name
        string card_type
        string hero_class
        string talent
        int pitch
        datetime created_at
    }
    printings {
        uuid id PK
        string printing_id UK
        uuid card_id FK
        uuid set_id FK
        string edition
        string foiling
        string rarity
        json artists
        json art_variations
        string image_url
        string tcgplayer_product_id
        string tcgplayer_url
        datetime created_at
    }
    owned_printings {
        uuid id PK
        uuid user_id FK
        uuid printing_id FK
        int qty
        datetime updated_at
    }
    wishlists {
        uuid id PK
        uuid user_id FK
        string name
        json filter_json
        datetime created_at
        datetime updated_at
    }
    refresh_tokens {
        uuid id PK
        string token UK
        uuid user_id FK
        datetime expires_at
        datetime revoked_at
        datetime created_at
    }

    users ||--o{ owned_printings : owns
    users ||--o{ wishlists : has
    users ||--o{ refresh_tokens : has
    sets ||--o{ printings : contains
    cards ||--o{ printings : "printed as"
    printings ||--o{ owned_printings : "owned via"
```

> **Strategy B:** one `Printing` row = one specific foiling of a card in a set edition.
> Foiling codes: `S` Standard · `R` Rainbow · `C` Cold · `G` Gold Cold.
> Edition codes: `A` Alpha · `F` First · `U` Unlimited · `N` None.

---

## API overview

### Auth
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | — | Create account, returns access + refresh tokens |
| POST | `/auth/token` | — | Login (OAuth2 form body) |
| POST | `/auth/refresh` | — | Rotate refresh token |
| POST | `/auth/logout` | Bearer | Revoke refresh token |
| GET | `/auth/me` | Bearer | Current user profile |

### Catalog (public)
| Method | Path | Description |
|---|---|---|
| GET | `/sets` | All sets with `printing_count`; `owned_count` when authenticated |
| GET | `/sets/{id}/printings` | Printings in a set — filter by `q`, `rarity`, `foiling`, `edition`, `hero_class`, `talent`, `card_type` |
| GET | `/cards` | Card list — filter by `name`, `hero_class`, `talent`, `pitch`, `set_code` |
| GET | `/cards/{id}` | Card detail with all printings |
| GET | `/search/printings` | Cross-set printing search — all filters above + `set_code` |

### Collection (requires Bearer token)
| Method | Path | Description |
|---|---|---|
| GET | `/collection/summary` | Owned printings with full card/set detail; `?set_id=` to scope to one set |
| POST | `/collection/items` | Upsert `{printing_id, qty}` — qty 0 deletes the row |
| POST | `/collection/bulk` | Atomic batch — actions: `set_qty`, `increment`, `mark_playset` (qty=3), `clear` |

Interactive docs: **http://localhost:8000/docs**

---

## Prerequisites

| Tool | Min version | Check |
|---|---|---|
| Python | 3.11 | `python --version` |
| Node.js | 20 | `node --version` |
| Docker + Docker Compose | 24 / v2 | `docker compose version` |
| make | any | see note below |

### Install `make` on Windows (one-time)

```powershell
winget install GnuWin32.Make
# Restart Git Bash after installing so PATH is updated
```

---

## Quick start

### 1. Copy env files

```bash
cp .env.example .env
cp apps/web/.env.local.example apps/web/.env.local
```

Edit `.env` — at minimum change `SECRET_KEY` for anything beyond local dev.

### 2. Start Postgres

```bash
make up
```

### 3. Install dependencies

```bash
make install        # api-install + web-install
```

### 4. Run migrations

```bash
make migrate        # alembic upgrade head
```

### 5. Import card data

```bash
make import-cards   # downloads ~34 MB from GitHub, upserts ~14k printings — safe to re-run
```

This populates `sets`, `cards`, and `printings` from the pinned `CARDS_DATA_VERSION` release of the [the-fab-cube/flesh-and-blood-cards](https://github.com/the-fab-cube/flesh-and-blood-cards) dataset.

### 6. Start the servers

```bash
# Terminal 1
make api-dev        # http://localhost:8000

# Terminal 2
make web-dev        # http://localhost:3000
```

---

## Daily dev workflow

```bash
make up          # ensure Postgres is running
make api-dev     # terminal 1
make web-dev     # terminal 2
```

```bash
make down        # stop all Docker services
```

---

## Running tests

```bash
make test        # pytest -v (Postgres must be running)
```

Tests use a per-test transaction that is rolled back after each test — no persistent side effects.

---

## Project structure

```
FabGreatLibrary/
├── apps/
│   ├── api/                        FastAPI backend
│   │   ├── app/
│   │   │   ├── core/
│   │   │   │   ├── config.py       Settings (pydantic-settings)
│   │   │   │   ├── security.py     Password hashing + JWT
│   │   │   │   └── deps.py         FastAPI dependencies
│   │   │   ├── db/
│   │   │   │   ├── models.py       ORM models (7 tables)
│   │   │   │   └── session.py      Async session factory
│   │   │   ├── routers/            One file per feature domain
│   │   │   ├── schemas/            Pydantic request/response models
│   │   │   └── services/           Business logic (no SQL in routers)
│   │   ├── scripts/
│   │   │   ├── import_cards.py     Card dataset importer
│   │   │   └── seed.py             Dev seed data
│   │   ├── alembic/                DB migrations
│   │   └── tests/
│   └── web/                        Next.js 16 frontend
│       ├── app/                    App Router pages
│       ├── components/ui/          shadcn/ui components
│       └── lib/                    API client + utilities
├── packages/
│   └── types/                      Generated TS types (from OpenAPI)
├── infra/
│   └── docker/
│       └── docker-compose.yml      Postgres + optional pgAdmin
├── .env.example
├── Makefile
└── README.md
```

---

## Makefile targets

```
make up            Start Postgres (detached)
make up-tools      Start Postgres + pgAdmin (http://localhost:5050)
make down          Stop all Compose services
make logs          Tail Compose logs

make api-install   Create venv + install API deps
make api-dev       FastAPI dev server — hot-reload, :8000
make migrate       alembic upgrade head
make migrate-down  alembic downgrade -1
make seed          Insert dev seed data (idempotent)
make import-cards  Download + upsert card dataset (idempotent)
make test          pytest -v

make web-install   npm install for the frontend
make web-dev       Next.js dev server — hot-reload, :3000
make web-build     Next.js production build

make install       api-install + web-install
make help          Print this list
```

---

## Environment variables

### Root `.env`

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_USER` | `fab` | Postgres username |
| `POSTGRES_PASSWORD` | `fab` | Postgres password |
| `POSTGRES_DB` | `fabgreat` | Database name |
| `POSTGRES_HOST` | `localhost` | Postgres host |
| `POSTGRES_PORT` | `5432` | Postgres port |
| `DATABASE_URL` | `postgresql+asyncpg://fab:fab@localhost:5432/fabgreat` | Full async DSN |
| `DATABASE_SSL` | `false` | Set `true` in production |
| `SECRET_KEY` | `change-me-in-production` | JWT signing key — **change this** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | Refresh token lifetime |
| `CARDS_DATA_VERSION` | `v8.1.0` | Dataset release tag used by `import-cards` |
| `PGADMIN_EMAIL` | `admin@fab.local` | pgAdmin login (optional) |
| `PGADMIN_PASSWORD` | `admin` | pgAdmin password (optional) |
| `PGADMIN_PORT` | `5050` | pgAdmin port (optional) |

### `apps/web/.env.local`

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | API base URL used by the browser |

---

## Optional: pgAdmin

```bash
make up-tools
# Open http://localhost:5050
# Login: admin@fab.local / admin
# Add server: host=db, port=5432, user/pass from .env
```

---

## Phases completed

| Phase | Deliverable |
|---|---|
| 0 | Monorepo scaffold — Docker, Makefile, FastAPI skeleton, Next.js landing page |
| 1 | Domain models, Alembic migrations, dev seed, wishlist service |
| 2 | JWT auth — register, login, refresh, logout, /me |
| 3 | Card catalog read APIs — GET /cards, GET /cards/{id}, GET /sets |
| 4 | Sets + printings + search — GET /sets (with counts), GET /sets/{id}/printings, GET /search/printings |
| 5 | Collection mutations — GET /collection/summary, POST /collection/items, POST /collection/bulk |
