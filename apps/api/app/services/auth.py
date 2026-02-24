"""
Auth service — refresh token lifecycle.
"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.db.models import RefreshToken


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def create_refresh_token(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> RefreshToken:
    rt = RefreshToken(
        token=str(uuid.uuid4()),
        user_id=user_id,
        expires_at=_now() + timedelta(days=settings.refresh_token_expire_days),
    )
    session.add(rt)
    await session.flush()
    return rt


async def use_refresh_token(
    session: AsyncSession,
    token: str,
) -> RefreshToken | None:
    """
    Return the RefreshToken (with .user loaded) if it is valid.
    Returns None when the token is unknown, revoked, or expired.
    """
    result = await session.execute(
        select(RefreshToken)
        .where(RefreshToken.token == token)
        .options(selectinload(RefreshToken.user))
    )
    rt = result.scalar_one_or_none()
    if rt is None or rt.revoked_at is not None or rt.expires_at <= _now():
        return None
    return rt


async def revoke_refresh_token(session: AsyncSession, token: str) -> None:
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.token == token)
    )
    rt = result.scalar_one_or_none()
    if rt is not None and rt.revoked_at is None:
        rt.revoked_at = _now()
