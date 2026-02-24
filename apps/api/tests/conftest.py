"""
Shared pytest fixtures.

DB isolation strategy
─────────────────────
Each test gets a fresh engine + connection whose transaction is rolled back
after the test.  A per-test engine avoids asyncpg event-loop conflicts that
arise when a session-scoped engine is shared across function-scoped tests.

HTTP client fixture
───────────────────
`client` overrides the `get_db` dependency with the test session so that
routes and tests share the same rolled-back transaction.  It also patches
`session.commit → session.flush` so route-level commits don't actually
commit to the DB, keeping all writes inside the test transaction.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

import app.db.models  # noqa: F401 — registers all models on Base.metadata; must be first to avoid shadowing the `app` name below
from app.core.config import settings
from app.db.session import get_db
from app.main import app


@pytest.fixture()
async def db() -> AsyncSession:
    """
    Yields an AsyncSession for one test.
    All writes are rolled back when the test ends.
    """
    engine = create_async_engine(
        settings.database_url,
        connect_args={"ssl": settings.database_ssl},
    )
    conn = await engine.connect()
    await conn.begin()
    session = AsyncSession(bind=conn, expire_on_commit=False)
    try:
        yield session
    finally:
        await session.close()
        await conn.rollback()
        await conn.close()
        await engine.dispose()


@pytest.fixture()
async def client(db: AsyncSession) -> AsyncClient:
    """
    Yields an AsyncClient whose requests run inside the test transaction.

    - get_db is overridden to yield the test session.
    - session.commit is patched to session.flush so route-level commits
      stay within the transaction and get rolled back with everything else.
    """
    db.commit = db.flush  # type: ignore[method-assign]

    async def _get_test_db():
        yield db

    app.dependency_overrides[get_db] = _get_test_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
