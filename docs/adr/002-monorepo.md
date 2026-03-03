# ADR 002 — Monorepo Layout

**Date:** 2026-03-03
**Status:** Accepted

---

## Context

The project is a full-stack web application: a FastAPI backend (`apps/api/`) and a Next.js frontend (`apps/web/`). The backend is the source of truth for the API contract, and the frontend consumes types generated from the backend's OpenAPI schema (`packages/types/`).

We had to decide whether to keep everything in one repository or split the backend and frontend into separate repositories.

## Decision

We use a **monorepo** with the following layout:

```
FabGreatLibrary/
  apps/api/        FastAPI backend
  apps/web/        Next.js frontend
  packages/types/  Generated TypeScript types (shared)
  infra/docker/    Docker Compose
```

The rejected alternative was **separate repositories** — one for the backend, one for the frontend.

### Why monorepo

1. **Shared type generation.** `packages/types/index.ts` is generated from the backend's OpenAPI schema and imported directly by the frontend via a `@fabgreat/types` path alias. In a split-repo setup this package would need to be published (npm / private registry) or duplicated on every schema change.

2. **Atomic cross-cutting changes.** When a backend schema changes (e.g. a new field on `PrintingWithCard`), the frontend update, the type regen, and the backend change can land in a single pull request. With separate repos, this requires coordinated PRs and versioned package bumps.

3. **Single CI pipeline.** One workflow file can run backend tests and the frontend build in parallel jobs, with a single green badge representing the whole system.

4. **Simpler onboarding.** A single `git clone` gives a new contributor the entire system. There is no "which repo do I clone first?" confusion.

### Why not separate repos

Separate repos are appropriate when teams are large, release cadences differ significantly, or the backend is consumed by multiple unrelated frontends. None of those conditions apply here: this is a solo portfolio project with one backend and one frontend that evolve together.

## Consequences

**Positive:**
- Type sharing is zero-cost (local path alias, no publishing step).
- Cross-cutting changes are a single PR.
- CI covers the full stack in one place.

**Negative:**
- Both frontend and backend developers must clone the entire repository, including code they may not work on. Acceptable at this scale.
- Monorepo tooling (Turborepo, Nx) would help if the project grows; currently not needed.
