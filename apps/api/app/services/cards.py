import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Card, OwnedPrinting, Printing, Set


async def list_sets_with_counts(
    session: AsyncSession,
    user_id: uuid.UUID | None = None,
) -> list[dict]:
    """Return sets ordered by name, each with printing_count and optional owned_count."""
    sets = list((await session.execute(select(Set).order_by(Set.name))).scalars())
    if not sets:
        return []

    set_ids = [s.id for s in sets]

    count_rows = (
        await session.execute(
            select(Printing.set_id, func.count(Printing.id).label("cnt"))
            .where(Printing.set_id.in_(set_ids))
            .group_by(Printing.set_id)
        )
    ).all()
    count_map = {row.set_id: row.cnt for row in count_rows}

    owned_map: dict = {}
    if user_id is not None:
        owned_rows = (
            await session.execute(
                select(Printing.set_id, func.count(OwnedPrinting.id).label("cnt"))
                .join(OwnedPrinting, OwnedPrinting.printing_id == Printing.id)
                .where(OwnedPrinting.user_id == user_id)
                .where(Printing.set_id.in_(set_ids))
                .group_by(Printing.set_id)
            )
        ).all()
        owned_map = {row.set_id: row.cnt for row in owned_rows}

    return [
        {
            "set": s,
            "printing_count": count_map.get(s.id, 0),
            "owned_count": owned_map.get(s.id, 0) if user_id is not None else None,
        }
        for s in sets
    ]


async def get_set(session: AsyncSession, set_id: uuid.UUID) -> Set | None:
    return (
        await session.execute(select(Set).where(Set.id == set_id))
    ).scalar_one_or_none()


async def list_printings(
    session: AsyncSession,
    *,
    set_id: uuid.UUID | None = None,
    q: str | None = None,
    rarity: str | None = None,
    foiling: str | None = None,
    edition: str | None = None,
    hero_class: str | None = None,
    talent: str | None = None,
    card_type: str | None = None,
    set_code: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Printing], int]:
    stmt = select(Printing).join(Printing.card).join(Printing.set)

    if set_id is not None:
        stmt = stmt.where(Printing.set_id == set_id)
    if set_code:
        stmt = stmt.where(Set.code == set_code)
    if q:
        stmt = stmt.where(Card.name.ilike(f"%{q}%"))
    if rarity:
        stmt = stmt.where(Printing.rarity == rarity)
    if foiling:
        stmt = stmt.where(Printing.foiling == foiling)
    if edition:
        stmt = stmt.where(Printing.edition == edition)
    if hero_class:
        stmt = stmt.where(Card.hero_class == hero_class)
    if talent:
        stmt = stmt.where(Card.talent == talent)
    if card_type:
        stmt = stmt.where(Card.card_type.ilike(f"%{card_type}%"))

    total = (
        await session.execute(select(func.count()).select_from(stmt.subquery()))
    ).scalar_one()

    stmt = (
        stmt
        .options(selectinload(Printing.card), selectinload(Printing.set))
        .order_by(Card.name, Printing.foiling)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all()), total


async def list_sets(session: AsyncSession) -> list[Set]:
    result = await session.execute(select(Set).order_by(Set.name))
    return list(result.scalars().all())


async def list_cards(
    session: AsyncSession,
    *,
    name: str | None = None,
    hero_class: str | None = None,
    talent: str | None = None,
    pitch: int | None = None,
    set_code: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Card], int]:
    q = select(Card)

    if name:
        q = q.where(Card.name.ilike(f"%{name}%"))
    if hero_class:
        q = q.where(Card.hero_class == hero_class)
    if talent:
        q = q.where(Card.talent == talent)
    if pitch is not None:
        q = q.where(Card.pitch == pitch)
    if set_code:
        subq = (
            select(Printing.card_id)
            .join(Printing.set)
            .where(Set.code == set_code)
            .distinct()
            .scalar_subquery()
        )
        q = q.where(Card.id.in_(subq))

    total = (await session.execute(select(func.count()).select_from(q.subquery()))).scalar_one()

    q = q.order_by(Card.name, Card.pitch).offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(q)
    return list(result.scalars().all()), total


async def get_card(session: AsyncSession, card_id: uuid.UUID) -> Card | None:
    result = await session.execute(
        select(Card)
        .where(Card.id == card_id)
        .options(selectinload(Card.printings).selectinload(Printing.set))
    )
    return result.scalar_one_or_none()
