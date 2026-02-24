"""
Tests for domain invariants.

1. owned_printings unique constraint  (user_id, printing_id, foil_type)
2. Wishlist free-tier max-1 enforcement in service layer
"""

import pytest
from sqlalchemy.exc import IntegrityError

from app.db.models import Card, OwnedPrinting, Printing, Set, User
from app.services.wishlist import WishlistLimitError, create_wishlist


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


async def _make_printing(db, set_: Set, card: Card, pid: str = "TST001") -> Printing:
    p = Printing(
        printing_id=pid,
        card_id=card.id,
        set_id=set_.id,
        rarity="Common",
        foil_types=["standard"],
    )
    db.add(p)
    await db.flush()
    return p


# ── owned_printings unique constraint ─────────────────────────────────────────

class TestOwnedPrintingUniqueConstraint:
    async def test_duplicate_raises_integrity_error(self, db):
        """Inserting (user, printing, foil_type) twice must raise IntegrityError."""
        user = await _make_user(db)
        set_ = await _make_set(db)
        card = await _make_card(db)
        printing = await _make_printing(db, set_, card)

        # First insert — succeeds
        db.add(OwnedPrinting(
            user_id=user.id,
            printing_id=printing.id,
            foil_type="standard",
            qty=1,
        ))
        await db.flush()

        # Second insert — same composite key — must fail
        db.add(OwnedPrinting(
            user_id=user.id,
            printing_id=printing.id,
            foil_type="standard",
            qty=2,
        ))
        with pytest.raises(IntegrityError):
            await db.flush()

        # After a DB error the transaction is aborted; rollback resets it so
        # the fixture's connection.rollback() can clean up cleanly.
        await db.rollback()

    async def test_different_foil_type_is_allowed(self, db):
        """Same (user, printing) but different foil_type should be a separate row."""
        user = await _make_user(db, "u2@test.local")
        set_ = await _make_set(db, "TS2")
        card = await _make_card(db, "Other Card")
        printing = await _make_printing(db, set_, card, "TST002")

        db.add(OwnedPrinting(
            user_id=user.id, printing_id=printing.id, foil_type="standard", qty=1
        ))
        db.add(OwnedPrinting(
            user_id=user.id, printing_id=printing.id, foil_type="rainbow", qty=1
        ))
        await db.flush()  # should not raise


# ── wishlist free-tier limit ───────────────────────────────────────────────────

class TestWishlistServiceLimit:
    async def test_first_wishlist_succeeds(self, db):
        """A user with no wishlists can create one."""
        user = await _make_user(db, "w1@test.local")
        wishlist = await create_wishlist(db, user.id, "My Wants", {})
        assert wishlist.id is not None
        assert wishlist.name == "My Wants"

    async def test_second_wishlist_raises_limit_error(self, db):
        """A free-tier user cannot create a second wishlist."""
        user = await _make_user(db, "w2@test.local")
        await create_wishlist(db, user.id, "First", {})

        with pytest.raises(WishlistLimitError):
            await create_wishlist(db, user.id, "Second", {})
