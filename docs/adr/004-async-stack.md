# ADR 004 — Async Python Stack (FastAPI + SQLAlchemy 2.0 + asyncpg)

**Date:** 2026-03-03
**Status:** Accepted

---

## Context

We needed to choose a Python web framework and database access layer for the backend API. The main contenders in the Python ecosystem are:

- **Flask** — mature, synchronous, minimal
- **Django (+ Django REST Framework)** — batteries-included, synchronous ORM, large ecosystem
- **FastAPI** — modern, async-native, automatic OpenAPI generation, Pydantic validation

For the database driver:
- **psycopg2** — the standard synchronous Postgres adapter
- **asyncpg** — async-native Postgres driver, used with SQLAlchemy 2.0's async engine

## Decision

We use **FastAPI + SQLAlchemy 2.0 (async engine) + asyncpg**.

### Why FastAPI

1. **Async-native.** FastAPI is built on Starlette and runs on an ASGI server (Uvicorn). Every request handler can be a coroutine, so I/O-bound work (DB queries, external HTTP calls) never blocks the event loop. Flask and Django's standard ORMs are synchronous and block the thread for every query.

2. **Automatic OpenAPI.** FastAPI generates a `/openapi.json` schema from route signatures and Pydantic models at startup — no separate spec file to maintain. This is the foundation for `packages/types/`: `openapi-typescript` consumes that schema and generates the TypeScript client types, keeping backend and frontend in sync automatically.

3. **Pydantic v2 validation.** Request and response models are Pydantic classes. Validation, serialization, and JSON schema generation are handled by the same model definition, eliminating the duplicated "serializer" layer common in DRF.

4. **Type-annotated by design.** FastAPI uses Python type hints for dependency injection, route parameter parsing, and response models. This integrates naturally with modern Python tooling (mypy, Pyright, IDE completion) and makes the codebase self-documenting.

### Why SQLAlchemy 2.0 async + asyncpg

1. **Full async query pipeline.** SQLAlchemy 2.0 ships a first-class async API (`AsyncSession`, `async with`, `await session.execute(...)`). Combined with asyncpg as the driver, every database call is non-blocking.

2. **Familiar ORM surface.** SQLAlchemy's declarative ORM is well-understood, well-documented, and supports complex relationships, eager loading (`selectinload`), and upserts (`on_conflict_do_update`) — all used in this project.

3. **Alembic migrations.** SQLAlchemy and Alembic are designed to work together. The async migration environment required a small `run_sync` wrapper in `env.py`, but is otherwise standard.

### Why not Flask / Django

Flask would require either a sync-only design or significant async bolting-on (Quart, async SQLAlchemy). Django's ORM does not have a mature async story at the depth this project uses, and DRF adds a serializer layer that duplicates what Pydantic already provides. Neither generates an OpenAPI schema automatically.

## Consequences

**Positive:**
- Request handling is non-blocking; the server can handle concurrent requests efficiently with a single process.
- The OpenAPI schema is always up to date — it is generated from the live application, not a separate file.
- Type safety flows from Python route definitions through to TypeScript frontend types via the generated schema.

**Negative:**
- Async Python has sharper edges than sync code: mixing sync and async code (e.g. in Alembic's `env.py`) requires care. The test fixture setup is more complex because asyncpg binds connections to the event loop — each test needs its own engine instance.
- FastAPI's dependency injection system has a learning curve compared to Flask's simplicity. The payoff is clean, testable, composable handler dependencies.
