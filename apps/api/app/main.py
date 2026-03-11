from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth as auth_router
from app.routers import cards as cards_router
from app.routers import collection as collection_router
from app.routers import missing as missing_router
from app.routers import search as search_router
from app.routers import sets as sets_router
from app.routers import wishlist as wishlist_router

app = FastAPI(
    title="FabGreat API",
    description="""
Flesh and Blood TCG collection tracker API.

Browse the full card catalog (92 sets, 4 200+ cards, 14 000+ printings), track ownership
down to foiling and edition, and manage saved wishlist filters.

## Authentication

Most catalog endpoints are public. Collection and wishlist endpoints require a **Bearer**
token obtained from `POST /auth/token` (login) or `POST /auth/register`.

Refresh tokens are opaque and stored server-side. Call `POST /auth/refresh` to rotate
without re-entering credentials, and `POST /auth/logout` to revoke.

## Pagination

Paginated endpoints accept `page` (1-based) and `page_size` (max 100) query parameters
and return `{ items, total, page, page_size }`.

## Foiling codes

| Code | Meaning |
|------|---------|
| S | Standard (non-foil) |
| R | Rainbow foil |
| C | Cold foil |
| G | Gold Cold foil |

## Edition codes

| Code | Meaning |
|------|---------|
| A | Alpha |
| F | First Edition |
| U | Unlimited |
| N | No specified edition |
""",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(sets_router.router)
app.include_router(cards_router.router)
app.include_router(search_router.router)
app.include_router(collection_router.router)
app.include_router(missing_router.router)
app.include_router(wishlist_router.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
