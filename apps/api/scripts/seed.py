"""
Dev seed script — idempotent.

Creates:
  - 1 test user     (test@fab.local / test)
  - 1 sample set    (WTR — Welcome to Rathe, Alpha)
  - 1 sample card   (Enlightened Strike)
  - 1 sample printing (WTR110, Common, standard + rainbow foil)

Run from apps/api/:
    python -m scripts.seed
"""

import asyncio

from sqlalchemy import select

from app.core.security import hash_password
from app.db.models import Card, Printing, Set, User
from app.db.session import AsyncSessionLocal

# ── seed data ──────────────────────────────────────────────────────────────────

TEST_USER_EMAIL = "test@fab.local"
TEST_USER_PASSWORD = "test"

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


# ── helpers ────────────────────────────────────────────────────────────────────

def _log(action: str, label: str) -> None:
    print(f"  [{action:8s}] {label}")


# ── seed logic ─────────────────────────────────────────────────────────────────

async def seed() -> None:
    async with AsyncSessionLocal() as session:
        # ── user ──────────────────────────────────────────────────────────────
        result = await session.execute(
            select(User).where(User.email == TEST_USER_EMAIL)
        )
        user = result.scalar_one_or_none()
        if user is None:
            user = User(
                email=TEST_USER_EMAIL,
                hashed_password=hash_password(TEST_USER_PASSWORD),
            )
            session.add(user)
            _log("created", f"user  {TEST_USER_EMAIL}")
        else:
            _log("exists", f"user  {TEST_USER_EMAIL}")

        # ── set ───────────────────────────────────────────────────────────────
        result = await session.execute(
            select(Set).where(Set.code == SAMPLE_SET["code"])
        )
        set_ = result.scalar_one_or_none()
        if set_ is None:
            set_ = Set(**SAMPLE_SET)
            session.add(set_)
            _log("created", f"set   {SAMPLE_SET['code']} — {SAMPLE_SET['name']}")
        else:
            _log("exists", f"set   {SAMPLE_SET['code']}")

        await session.flush()  # get set_.id before creating printing

        # ── card ──────────────────────────────────────────────────────────────
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

        await session.flush()  # get card.id before creating printing

        # ── printing ──────────────────────────────────────────────────────────
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

        await session.commit()

    print("\nSeed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
