# FabGreat Library — Development Roadmap

## Completed phases

| Phase | Deliverable |
|---|---|
| 0 — Scaffold | Monorepo, Docker, Makefile, FastAPI skeleton, Next.js landing page |
| 1 — Domain | ORM models, Alembic migrations, seed script, wishlist service |
| 2 — Auth | Register, login, refresh token rotation, logout, `/me` |
| 3 — Catalog | `GET /cards`, `GET /cards/{id}`, `GET /sets` |
| 4 — Browse | Set printings, cross-set search, per-field filtering |
| 5 — Collection | Backend: summary, upsert, atomic bulk · Frontend: set grid, +1 increment, bulk select |
| 6 — Missing / Wishlists | `GET /missing`, wishlist CRUD (402 gate), missing page with save/load/delete |
| 7 — Types | openapi-typescript generates `packages/types/index.ts`; `api.ts` re-exports via `@fabgreat/types` |
| Docs — OpenAPI | Field descriptions, endpoint summaries, error response docs on all schemas and routers |
| Docs | ADRs (`docs/adr/`), service-layer docstrings, `CHANGELOG.md` |
| CI/CD | GitHub Actions (backend + frontend + e2e jobs), `railway.toml` + `vercel.json` |
| UI/UX | Card images, hero landing, dark mode, empty states, demo account |
| Playwright | 14 E2E tests (auth, sets, collection, missing/wishlists), wired into CI |

---

## Upcoming work

---

### Deploy

**Goal:** live public URL, suitable for a CV or portfolio link.

#### Prerequisites — create accounts before starting this phase

- [ ] **Railway account** (https://railway.app) — sign up with GitHub. Hosts the FastAPI backend and a managed PostgreSQL database. Railway reads `railway.toml` from the repo to know how to build and start the API. Free trial gives $5 credit; after that the Hobby plan is $5/month. Needed because Vercel only runs Node.js/Edge — it cannot host a Python backend or a Postgres instance.
- [ ] **Vercel account** (https://vercel.com) — sign up with GitHub. Hosts the Next.js frontend on their edge CDN. Vercel reads `vercel.json` from the repo to know how to build the app. The free Hobby tier is enough for a portfolio project. Needed because Railway can serve static files but has no edge CDN and no built-in Next.js optimisations (ISR, image optimisation, etc.).

#### Steps

- [x] **Backend prod changes:**
  - CORS origins read from env var (`settings.cors_origins`) — done in CI/CD phase
  - `railway.toml` + `vercel.json` config files — done in CI/CD phase
- [ ] **Railway** — connect repo, add PostgreSQL plugin, inject env vars (`DATABASE_URL`, `SECRET_KEY`, `CORS_ORIGINS`), run `import-cards` once via Railway shell
- [ ] **Vercel** — connect repo, set `NEXT_PUBLIC_API_URL` to the Railway URL, set root directory to `apps/web`
- [ ] **Custom domain** (~10 USD/year via Cloudflare Registrar)
- [ ] **README badge** — link to live site
