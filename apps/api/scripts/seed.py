"""
Dev seed script -- idempotent.

Creates:
  - 1 test user       (test@fab.local / test)
  - 1 sample set      (WTR -- Welcome to Rathe, Alpha)
  - 1 sample card     (Enlightened Strike)
  - 1 sample printing (WTR110, Common, standard foil)
  - 1 demo user       (demo@fabgreatlibrary.com / demo1234)
    with a realistic collection (~300 owned printings across multiple sets)

Run from apps/api/:
    python -m scripts.seed
"""

import asyncio
import random

from sqlalchemy import func, select

from app.core.security import hash_password
from app.db.models import Card, OwnedPrinting, Printing, Set, User
from app.db.session import AsyncSessionLocal

# -- seed data -----------------------------------------------------------------

TEST_USER_EMAIL = "test@fab.local"
TEST_USER_PASSWORD = "test"

DEMO_USER_EMAIL = "demo@fabgreatlibrary.com"
DEMO_USER_PASSWORD = "demo1234"
DEMO_COLLECTION_SIZE = 300

SAMPLE_SET = {
    "code": "WTR",
    "name": "Welcome to Rathe",
}

SAMPLE_CARD = {
    "name": "Enlightened Strike",
    "card_type": "Generic Action Attack",
    "hero_class": "Generic",
    "talent": None,
    "pitch": 2,
}

SAMPLE_PRINTING = {
    "printing_id": "WTR110-seed",
    "rarity": "C",
    "edition": "A",
    "foiling": "S",
    "artists": [],
    "art_variations": [],
    "image_url": None,
}


# -- helpers -------------------------------------------------------------------

def _log(action: str, label: str) -> None:
    print(f"  [{action:8s}] {label}")


async def _seed_user(session, email: str, password: str) -> User:
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(email=email, hashed_password=hash_password(password))
        session.add(user)
        _log("created", f"user  {email}")
    else:
        _log("exists", f"user  {email}")
    return user


async def _seed_demo_collection(session, user: User) -> None:
    existing = await session.execute(
        select(func.count()).select_from(OwnedPrinting).where(
            OwnedPrinting.user_id == user.id
        )
    )
    count = existing.scalar_one()
    if count > 0:
        _log("exists", f"demo collection ({count} items)")
        return

    total_printings = (
        await session.execute(select(func.count()).select_from(Printing))
    ).scalar_one()
    if total_printings == 0:
        _log("skipped", "demo collection (no printings imported yet)")
        return

    sample_size = min(DEMO_COLLECTION_SIZE, total_printings)
    result = await session.execute(
        select(Printing.id).order_by(func.random()).limit(sample_size)
    )
    printing_ids = [row[0] for row in result.all()]

    random.seed(42)
    for pid in printing_ids:
        qty = random.choices([1, 2, 3], weights=[60, 25, 15])[0]
        session.add(OwnedPrinting(user_id=user.id, printing_id=pid, qty=qty))

    _log("created", f"demo collection ({len(printing_ids)} items)")


# -- seed logic ----------------------------------------------------------------

async def seed() -> None:
    async with AsyncSessionLocal() as session:
        # -- test user ---------------------------------------------------------
        await _seed_user(session, TEST_USER_EMAIL, TEST_USER_PASSWORD)

        # -- sample set --------------------------------------------------------
        result = await session.execute(
            select(Set).where(Set.code == SAMPLE_SET["code"])
        )
        set_ = result.scalar_one_or_none()
        if set_ is None:
            set_ = Set(**SAMPLE_SET)
            session.add(set_)
            _log("created", f"set   {SAMPLE_SET['code']} -- {SAMPLE_SET['name']}")
        else:
            _log("exists", f"set   {SAMPLE_SET['code']}")

        await session.flush()

        # -- sample card -------------------------------------------------------
        result = await session.execute(
            select(Card).where(Card.name == SAMPLE_CARD["name"])
        )
        card = result.scalar_one_or_none()
        if card is None:
            card = Card(**SAMPLE_CARD)
            session.add(card)
            _log("created", f"card  {SAMPLE_CARD['name']}")
        else:
            _log("exists", f"card  {SAMPLE_CARD['name']}")

        await session.flush()

        # -- sample printing ---------------------------------------------------
        result = await session.execute(
            select(Printing).where(
                Printing.printing_id == SAMPLE_PRINTING["printing_id"]
            )
        )
        printing = result.scalar_one_or_none()
        if printing is None:
            printing = Printing(
                **SAMPLE_PRINTING,
                card_id=card.id,
                set_id=set_.id,
            )
            session.add(printing)
            _log(
                "created",
                f"print {SAMPLE_PRINTING['printing_id']} "
                f"({SAMPLE_CARD['name']}, {SAMPLE_PRINTING['rarity']})",
            )
        else:
            _log("exists", f"print {SAMPLE_PRINTING['printing_id']}")

        # -- demo user + collection --------------------------------------------
        await session.flush()
        demo_user = await _seed_user(session, DEMO_USER_EMAIL, DEMO_USER_PASSWORD)
        await session.flush()
        await _seed_demo_collection(session, demo_user)

        await session.commit()

    print("\nSeed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
