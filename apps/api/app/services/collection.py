"""
Collection service — owns all mutation logic for OwnedPrinting rows.

Invariants enforced here (not in DB):
  - qty must be >= 1 when a row exists
  - qty = 0 deletes the row
  - qty cannot be set negative
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import OwnedPrinting, Printing


async def get_collection_summary(
    session: AsyncSession,
    user_id: uuid.UUID,
    set_id: uuid.UUID | None = None,
) -> list[OwnedPrinting]:
    """Return all owned printings for a user, optionally filtered to one set."""
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
    """
    Set qty for (user, printing).
    - qty = 0  → delete the row, return None
    - qty > 0  → insert or update, return OwnedPrinting
    - qty < 0  → raises ValueError
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

    if action == "set_qty":
        return await upsert_item(session, user_id, printing_id, qty)  # type: ignore[arg-type]

    if action == "mark_playset":
        return await upsert_item(session, user_id, printing_id, 3)

    if action == "clear":
        return await upsert_item(session, user_id, printing_id, 0)

    raise ValueError(f"Unknown action: {action}")


async def bulk_apply(
    session: AsyncSession,
    user_id: uuid.UUID,
    items: list[dict],
) -> list[dict]:
    """
    Apply a list of actions atomically.
    Each item: {printing_id, action, qty?}
    Returns: [{printing_id, qty}] — qty=None means row was deleted.
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
