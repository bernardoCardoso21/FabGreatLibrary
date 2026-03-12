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

---

## Upcoming work (in order)

---

### 1. CI/CD

**Goal:** every push to `main` is automatically verified; merges only happen when green.

- [x] **GitHub Actions — CI** (`.github/workflows/ci.yml`):
  - Trigger: push + PR to `main`
  - Jobs:
    - `backend`: spin up Postgres service container, run `pytest -v`
    - `frontend`: run `npm run build` (catches type errors) + `npm run lint`
- [x] **CD** — `railway.toml` + `vercel.json` config files; CORS origins from env var
- [x] **Branch protection** — require CI green before merge to `main`

---

### 2. UI/UX

**Goal:** looks like a real product, not a homework project.

- [x] **Card images** — render `image_url` from `PrintingWithCard` in the printings table (data already there)
- [x] **Landing page** — hero section + live stats bar (hits `/sets` on load, shows real counts)
- [x] **Dark mode** — Tailwind v4 + shadcn/ui, theme toggle in navbar, persisted to localStorage
- [x] **Empty states** — friendly message when filters return no results, with clear-filters links
- [x] **Demo account** — pre-seeded user (`demo@fabgreatlibrary.com` / `demo1234`) with ~300 owned printings

---

### 3. Playwright — E2E tests

**Goal:** automated browser tests covering critical user paths.

- [ ] Install Playwright in `apps/web/`
- [ ] Test suite (`apps/web/tests/`):
  - Auth flow: register → redirect to /sets; login → redirect to /sets; logout
  - Browse: set grid loads; clicking a set opens printings table
  - Collection: +1 increment updates qty; bulk clear removes items
  - Missing: filters update results; save wishlist → appears in panel; delete wishlist
- [ ] Wire Playwright into CI (separate job, runs against built app)

---

### 4. Deploy

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

---

## Notes

- Always complete CI before UI work — lets you iterate with confidence
- Playwright before deploy — go live with browser coverage, not just unit tests
- 92 backend tests currently passing; Next.js build clean
