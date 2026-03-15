"""
Tests for domain invariants.

1. owned_printings unique constraint  (user_id, printing_id)
"""

import pytest
from sqlalchemy.exc import IntegrityError

from app.db.models import Card, OwnedPrinting, Printing, Set, User


# ── helpers ───────────────────────────────────────────────────────────────────

async def _make_user(db, email: str = "u@test.local") -> User:
    user = User(email=email, hashed_password="x")
    db.add(user)
    await db.flush()
    return user


async def _make_set(db, code: str = "TST") -> Set:
    s = Set(code=code, name="Test Set")
    db.add(s)
    await db.flush()
    return s


async def _make_card(db, name: str = "Test Card") -> Card:
    card = Card(name=name, card_type="Action")
    db.add(card)
    await db.flush()
    return card


async def _make_printing(
    db,
    set_: Set,
    card: Card,
    pid: str = "TST001",
    foiling: str = "S",
) -> Printing:
    p = Printing(
        printing_id=pid,
        card_id=card.id,
        set_id=set_.id,
        edition="N",
        foiling=foiling,
        rarity="C",
        artists=[],
        art_variations=[],
    )
    db.add(p)
    await db.flush()
    return p


# ── owned_printings unique constraint ─────────────────────────────────────────

class TestOwnedPrintingUniqueConstraint:
    async def test_duplicate_raises_integrity_error(self, db):
        """Inserting (user, printing) twice must raise IntegrityError."""
        user = await _make_user(db)
        set_ = await _make_set(db)
        card = await _make_card(db)
        printing = await _make_printing(db, set_, card)

        db.add(OwnedPrinting(user_id=user.id, printing_id=printing.id, qty=1))
        await db.flush()

        db.add(OwnedPrinting(user_id=user.id, printing_id=printing.id, qty=2))
        with pytest.raises(IntegrityError):
            await db.flush()

        await db.rollback()

    async def test_different_printings_are_independent(self, db):
        """Owning two different printings of the same card (e.g. S and R foil)
        is allowed — they are separate Printing rows with distinct printing_ids."""
        user = await _make_user(db, "u2@test.local")
        set_ = await _make_set(db, "TS2")
        card = await _make_card(db, "Other Card")
        standard = await _make_printing(db, set_, card, "TST002-S", foiling="S")
        rainbow = await _make_printing(db, set_, card, "TST002-R", foiling="R")

        db.add(OwnedPrinting(user_id=user.id, printing_id=standard.id, qty=1))
        db.add(OwnedPrinting(user_id=user.id, printing_id=rainbow.id, qty=1))
        await db.flush()  # should not raise
