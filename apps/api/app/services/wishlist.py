"""
Wishlist service — enforces free-tier max-1 rule.
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Wishlist

MAX_FREE_WISHLISTS = 1


class WishlistLimitError(Exception):
    """Raised when a free-tier user tries to create more than MAX_FREE_WISHLISTS."""


class WishlistNotFoundError(Exception):
    """Raised when a wishlist is not found or does not belong to the requesting user."""


async def get_wishlist_count(session: AsyncSession, user_id: UUID) -> int:
    result = await session.execute(
        select(func.count(Wishlist.id)).where(Wishlist.user_id == user_id)
    )
    return result.scalar_one()


async def create_wishlist(
    session: AsyncSession,
    user_id: UUID,
    name: str,
    filter_json: dict,
) -> Wishlist:
    """
    Create a wishlist for user.
    Raises WishlistLimitError if the user already has MAX_FREE_WISHLISTS.
    """
    count = await get_wishlist_count(session, user_id)
    if count >= MAX_FREE_WISHLISTS:
        raise WishlistLimitError(
            f"Free tier allows a maximum of {MAX_FREE_WISHLISTS} wishlist(s). "
            "Delete the existing wishlist before creating a new one."
        )

    wishlist = Wishlist(user_id=user_id, name=name, filter_json=filter_json)
    session.add(wishlist)
    await session.flush()
    return wishlist


async def list_wishlists(session: AsyncSession, user_id: UUID) -> list[Wishlist]:
    result = await session.execute(
        select(Wishlist).where(Wishlist.user_id == user_id).order_by(Wishlist.created_at)
    )
    return list(result.scalars().all())


async def delete_wishlist(session: AsyncSession, user_id: UUID, wishlist_id: UUID) -> None:
    wishlist = await session.get(Wishlist, wishlist_id)
    if wishlist is None or wishlist.user_id != user_id:
        raise WishlistNotFoundError()
    await session.delete(wishlist)
    await session.flush()
