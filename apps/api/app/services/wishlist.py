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
    """Return the number of wishlists the user currently owns.

    Args:
        session: Active async database session.
        user_id: ID of the user to count wishlists for.

    Returns:
        Integer count (0 or more).
    """
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
    """Create a new named wishlist storing a set of missing-printings filter criteria.

    Enforces the free-tier limit: a user may hold at most ``MAX_FREE_WISHLISTS``
    (currently 1) wishlists at a time. Deleting the existing wishlist re-opens
    the slot. The limit is checked here in the service layer — the database has
    no corresponding constraint.

    Args:
        session: Active async database session.
        user_id: ID of the user creating the wishlist.
        name: Human-readable label for the wishlist.
        filter_json: Arbitrary dict of filter criteria (set_id, foiling, rarity,
            etc.) to be persisted and reapplied later.

    Returns:
        The newly created Wishlist (flushed but not yet committed).

    Raises:
        WishlistLimitError: If the user already has ``MAX_FREE_WISHLISTS`` wishlists.
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
    """Return all wishlists for a user ordered by creation date (oldest first).

    Args:
        session: Active async database session.
        user_id: ID of the user whose wishlists to retrieve.

    Returns:
        List of Wishlist objects (may be empty).
    """
    result = await session.execute(
        select(Wishlist).where(Wishlist.user_id == user_id).order_by(Wishlist.created_at)
    )
    return list(result.scalars().all())


async def delete_wishlist(session: AsyncSession, user_id: UUID, wishlist_id: UUID) -> None:
    """Delete a wishlist, verifying it belongs to the requesting user.

    Ownership is checked before deletion: a wishlist belonging to another user
    is treated identically to a non-existent one (raises ``WishlistNotFoundError``
    in both cases) to avoid leaking wishlist existence to other users.
    Deleting a wishlist re-opens the free-tier slot for a new one.

    Args:
        session: Active async database session.
        user_id: ID of the authenticated user making the request.
        wishlist_id: UUID of the wishlist to delete.

    Raises:
        WishlistNotFoundError: If the wishlist does not exist or belongs to a
            different user.
    """
    wishlist = await session.get(Wishlist, wishlist_id)
    if wishlist is None or wishlist.user_id != user_id:
        raise WishlistNotFoundError()
    await session.delete(wishlist)
    await session.flush()
