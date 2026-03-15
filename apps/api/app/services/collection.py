"""
Collection service — owns all mutation logic for OwnedPrinting rows.

Invariants enforced here (not in DB):
  - qty must be >= 1 when a row exists
  - qty = 0 deletes the row
  - qty cannot be set negative
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import OwnedPrinting, Printing


async def get_collection_summary(
    session: AsyncSession,
    user_id: uuid.UUID,
    set_id: uuid.UUID | None = None,
) -> list[OwnedPrinting]:
    """Return a user's owned printings with card and set detail eager-loaded.

    Args:
        session: Active async database session.
        user_id: ID of the authenticated user.
        set_id: If provided, restrict results to printings in this set.

    Returns:
        List of OwnedPrinting rows with ``printing.card`` and ``printing.set``
        populated (no additional queries needed during serialization).
    """
    stmt = (
        select(OwnedPrinting)
        .where(OwnedPrinting.user_id == user_id)
        .options(
            selectinload(OwnedPrinting.printing).selectinload(Printing.card),
            selectinload(OwnedPrinting.printing).selectinload(Printing.set),
        )
    )
    if set_id is not None:
        stmt = stmt.join(OwnedPrinting.printing).where(Printing.set_id == set_id)

    return list((await session.execute(stmt)).scalars().all())


async def upsert_item(
    session: AsyncSession,
    user_id: uuid.UUID,
    printing_id: uuid.UUID,
    qty: int,
) -> OwnedPrinting | None:
    """Insert or update the owned quantity for a (user, printing) pair.

    Business rules enforced here:
    - ``qty = 0`` deletes the row (the DB must never hold a zero-qty record).
    - ``qty > 0`` inserts a new row or updates the existing one.
    - ``qty < 0`` is always rejected.

    Args:
        session: Active async database session.
        user_id: ID of the authenticated user.
        printing_id: UUID of the printing being updated.
        qty: Target quantity. 0 removes the record; positive values set it.

    Returns:
        The upserted OwnedPrinting, or None if the row was deleted (qty=0).

    Raises:
        ValueError: If qty is negative.
    """
    if qty < 0:
        raise ValueError("qty cannot be negative")

    existing = (
        await session.execute(
            select(OwnedPrinting).where(
                OwnedPrinting.user_id == user_id,
                OwnedPrinting.printing_id == printing_id,
            )
        )
    ).scalar_one_or_none()

    if qty == 0:
        if existing:
            await session.delete(existing)
            await session.flush()
        return None

    if existing:
        existing.qty = qty
        await session.flush()
        return existing

    op = OwnedPrinting(user_id=user_id, printing_id=printing_id, qty=qty)
    session.add(op)
    await session.flush()
    return op


async def _apply_action(
    session: AsyncSession,
    user_id: uuid.UUID,
    printing_id: uuid.UUID,
    action: str,
    qty: int | None,
) -> OwnedPrinting | None:
    if action == "increment":
        existing = (
            await session.execute(
                select(OwnedPrinting).where(
                    OwnedPrinting.user_id == user_id,
                    OwnedPrinting.printing_id == printing_id,
                )
            )
        ).scalar_one_or_none()
        new_qty = (existing.qty if existing else 0) + 1
        return await upsert_item(session, user_id, printing_id, new_qty)

    if action == "decrement":
        existing = (
            await session.execute(
                select(OwnedPrinting).where(
                    OwnedPrinting.user_id == user_id,
                    OwnedPrinting.printing_id == printing_id,
                )
            )
        ).scalar_one_or_none()
        new_qty = max(0, (existing.qty if existing else 0) - 1)
        return await upsert_item(session, user_id, printing_id, new_qty)

    if action == "set_qty":
        return await upsert_item(session, user_id, printing_id, qty)  # type: ignore[arg-type]

    if action == "clear":
        return await upsert_item(session, user_id, printing_id, 0)

    raise ValueError(f"Unknown action: {action}")


async def bulk_apply(
    session: AsyncSession,
    user_id: uuid.UUID,
    items: list[dict],
) -> list[dict]:
    """Apply a batch of collection actions atomically within the caller's transaction.

    Supported actions per item:
    - ``increment``: Add 1 to the current qty (creates the row at qty=1 if absent).
    - ``set_qty``: Set qty to the provided value; qty=0 deletes the row.
    - ``clear``: Delete the row (equivalent to set_qty=0).

    Atomicity is guaranteed because all actions run inside the same database
    session. The router validates that all referenced printing IDs exist before
    calling this function; no partial rollback is needed here.

    Args:
        session: Active async database session.
        user_id: ID of the authenticated user performing the bulk update.
        items: List of action dicts, each with keys ``printing_id`` (UUID),
            ``action`` (str), and optionally ``qty`` (int, required for set_qty).

    Returns:
        List of result dicts with ``printing_id`` (UUID) and ``qty`` (int or
        None). A None qty means the row was deleted by a clear or set_qty=0.
    """
    results = []
    for item in items:
        op = await _apply_action(
            session,
            user_id,
            item["printing_id"],
            item["action"],
            item.get("qty"),
        )
        results.append(
            {"printing_id": item["printing_id"], "qty": op.qty if op else None}
        )
    return results
