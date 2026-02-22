# FabGreat Library

Flesh & Blood collection tracker — monorepo with a FastAPI backend and Next.js frontend.

## Prerequisites

| Tool | Min version | Notes |
|---|---|---|
| Python | 3.11 | `python --version` |
| Node.js | 20 | `node --version` |
| Docker + Docker Compose | 24 / v2 | `docker compose version` |
| make | any | see install note below |

### Install `make` on Windows (one-time)

```powershell
# In PowerShell / Windows Terminal
winget install GnuWin32.Make
# Restart Git Bash after installing so PATH is updated
```

---

## Quick start (first time)

### 1. Copy env files

```bash
# Root .env — read by Docker Compose and the API
cp .env.example .env

# Frontend .env.local — read by Next.js
cp apps/web/.env.local.example apps/web/.env.local
```

### 2. Start Postgres

```bash
make up
# Postgres is ready when: docker compose -f infra/docker/docker-compose.yml ps
# shows db as "healthy"
```

### 3. Set up the API

```bash
make api-install        # creates apps/api/.venv and installs all deps
```

> **First run only.** After that, the venv is reused.

### 4. Run database migrations

```bash
make migrate            # alembic upgrade head
```

> There are no migrations yet in Phase 0. This will be a no-op until Phase 1.

### 5. Start the API dev server

```bash
make api-dev            # http://localhost:8000
```

### 6. Start the frontend dev server (new terminal)

```bash
make web-dev            # http://localhost:3000
```

Open **http://localhost:3000** — the landing page shows an **Online** badge when the API is reachable.

---

## Daily dev workflow

```bash
make up          # ensure Postgres is running
make api-dev     # terminal 1 — FastAPI on :8000
make web-dev     # terminal 2 — Next.js on :3000
```

Stopping everything:

```bash
make down        # stops all Docker Compose services
```

---

## Running tests

```bash
make test        # pytest -v inside apps/api
```

---

## Verifying Phase 0 acceptance criteria

| Criterion | How to verify |
|---|---|
| Postgres starts | `make up` → `docker compose -f infra/docker/docker-compose.yml ps` shows `db (healthy)` |
| API health check | `curl http://localhost:8000/health` → `{"status":"ok"}` |
| Frontend displays status | Open http://localhost:3000 → badge shows **Online** |

---

## Project structure

```
FabGreatLibrary/
├── apps/
│   ├── api/                   # FastAPI backend
│   │   ├── app/
│   │   │   ├── core/
│   │   │   │   └── config.py  # Settings via pydantic-settings
│   │   │   └── main.py        # FastAPI app + /health endpoint
│   │   ├── tests/
│   │   └── pyproject.toml
│   └── web/                   # Next.js frontend
│       ├── app/
│       │   ├── layout.tsx
│       │   └── page.tsx       # Landing page — polls /health
│       ├── components/ui/     # shadcn/ui components
│       └── package.json
├── infra/
│   └── docker/
│       └── docker-compose.yml # Postgres (+ optional pgAdmin)
├── packages/
│   └── types/                 # Generated TS types (Phase 7)
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
make api-dev       FastAPI dev server — hot-reload, port 8000
make migrate       alembic upgrade head
make migrate-down  alembic downgrade -1
make test          pytest -v

make web-install   npm install for the frontend
make web-dev       Next.js dev server — hot-reload, port 3000
make web-build     Next.js production build

make install       api-install + web-install
make help          Print this list
```

---

## Environment variables

All variables live in `.env` (root) and `apps/web/.env.local`.
Copy from the `.example` files — never commit real secrets.

### Root `.env`

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_USER` | `fab` | Postgres username |
| `POSTGRES_PASSWORD` | `fab` | Postgres password |
| `POSTGRES_DB` | `fabgreat` | Postgres database name |
| `POSTGRES_HOST` | `localhost` | Postgres host |
| `POSTGRES_PORT` | `5432` | Postgres port |
| `DATABASE_URL` | `postgresql+asyncpg://fab:fab@localhost:5432/fabgreat` | Full async DSN used by the API |
| `SECRET_KEY` | `change-me-in-production` | JWT signing key — **change in production** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | JWT access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | JWT refresh token lifetime |
| `PGADMIN_EMAIL` | `admin@fab.local` | pgAdmin login (optional) |
| `PGADMIN_PASSWORD` | `admin` | pgAdmin password (optional) |
| `PGADMIN_PORT` | `5050` | pgAdmin port (optional) |

### `apps/web/.env.local`

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Base URL the browser uses to reach the API |

---

## Optional: pgAdmin

```bash
make up-tools
# Open http://localhost:5050
# Login: admin@fab.local / admin
# Add server: host=db, port=5432, user/pass from .env
```
