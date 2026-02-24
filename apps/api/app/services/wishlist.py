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
