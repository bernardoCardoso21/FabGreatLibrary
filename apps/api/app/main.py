from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth as auth_router
from app.routers import cards as cards_router
from app.routers import search as search_router
from app.routers import sets as sets_router

app = FastAPI(
    title="FabGreat API",
    description="Flesh and Blood collection tracker",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(sets_router.router)
app.include_router(cards_router.router)
app.include_router(search_router.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
