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
    """Issue a new opaque refresh token for a user.

    The token value is a random UUID string. Expiry is set to
    ``settings.refresh_token_expire_days`` days from now (UTC).

    Args:
        session: Active async database session.
        user_id: ID of the user the token belongs to.

    Returns:
        The persisted RefreshToken (flushed but not yet committed).
    """
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
    """Validate a refresh token and return it with its associated user loaded.

    A token is considered invalid if it does not exist in the database,
    has already been revoked (``revoked_at`` is set), or has passed its
    ``expires_at`` timestamp. Callers should immediately rotate the token
    (revoke + issue new) after a successful use.

    Args:
        session: Active async database session.
        token: The opaque refresh token string presented by the client.

    Returns:
        The RefreshToken with ``.user`` eagerly loaded, or None if the
        token is unknown, revoked, or expired.
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
    """Mark a refresh token as revoked, preventing future use.

    If the token does not exist or is already revoked this is a no-op —
    callers do not need to check beforehand. Used by ``POST /auth/logout``
    to invalidate the client's session server-side.

    Args:
        session: Active async database session.
        token: The opaque refresh token string to revoke.
    """
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.token == token)
    )
    rt = result.scalar_one_or_none()
    if rt is not None and rt.revoked_at is None:
        rt.revoked_at = _now()
