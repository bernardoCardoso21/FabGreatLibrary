"""
Shared pytest fixtures.

DB isolation strategy
─────────────────────
Each test gets a fresh engine + connection whose transaction is rolled back
after the test.  A per-test engine avoids asyncpg event-loop conflicts that
arise when a session-scoped engine is shared across function-scoped tests.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import settings
import app.db.models  # noqa: F401 — registers all models on Base.metadata


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
