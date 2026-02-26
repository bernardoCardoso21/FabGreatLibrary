"""
Tests for GET /missing endpoint.
"""

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, hash_password
from app.db.models import Card, OwnedPrinting, Printing, Set, User


# ── helpers ───────────────────────────────────────────────────────────────────

async def _make_user(db, email: str = "miss@example.com") -> User:
    user = User(email=email, hashed_password=hash_password("password"))
    db.add(user)
    await db.flush()
    return user


def _auth(user: User) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user.email)}"}


async def _make_set(db, code: str) -> Set:
    s = Set(code=code, name=f"Set {code}")
    db.add(s)
    await db.flush()
    return s


async def _make_card(db, name: str = "Missing Card") -> Card:
    card = Card(name=name, card_type="Action", hero_class="Generic")
    db.add(card)
    await db.flush()
    return card


async def _make_printing(
    db, set_: Set, card: Card, pid: str, foiling: str = "S", rarity: str = "C"
) -> Printing:
    p = Printing(
        printing_id=pid,
        card_id=card.id,
        set_id=set_.id,
        edition="F",
        foiling=foiling,
        rarity=rarity,
        artists=[],
        art_variations=[],
    )
    db.add(p)
    await db.flush()
    return p


async def _own(db, user: User, printing: Printing, qty: int = 1) -> OwnedPrinting:
    op = OwnedPrinting(user_id=user.id, printing_id=printing.id, qty=qty)
    db.add(op)
    await db.flush()
    return op


# ── GET /missing ──────────────────────────────────────────────────────────────

class TestGetMissing:
    async def test_requires_auth(self, client: AsyncClient):
        resp = await client.get("/missing")
        assert resp.status_code == 401

    async def test_returns_unowned_printings(self, client: AsyncClient, db):
        user = await _make_user(db, "missall@example.com")
        set_ = await _make_set(db, "MSS")
        card = await _make_card(db, "Missing Card")
        printing = await _make_printing(db, set_, card, "MSS-001-S")

        resp = await client.get(
            "/missing", params={"set_id": str(set_.id)}, headers=_auth(user)
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["id"] == str(printing.id)

    async def test_excludes_owned(self, client: AsyncClient, db):
        user = await _make_user(db, "missown@example.com")
        set_ = await _make_set(db, "MEX")
        card = await _make_card(db, "Excluded Card")
        printing = await _make_printing(db, set_, card, "MEX-001-S")
        await _own(db, user, printing)

        resp = await client.get(
            "/missing", params={"set_id": str(set_.id)}, headers=_auth(user)
        )
        assert resp.status_code == 200
        data = resp.json()
        ids = [item["id"] for item in data["items"]]
        assert str(printing.id) not in ids

    async def test_filter_by_set_id(self, client: AsyncClient, db):
        user = await _make_user(db, "missset@example.com")
        set_a = await _make_set(db, "MFA")
        set_b = await _make_set(db, "MFB")
        card = await _make_card(db, "Filter Set Card")
        await _make_printing(db, set_a, card, "MFA-001-S")
        await _make_printing(db, set_b, card, "MFB-001-S")

        resp = await client.get(
            "/missing", params={"set_id": str(set_a.id)}, headers=_auth(user)
        )
        assert resp.status_code == 200
        data = resp.json()
        set_codes = {item["set"]["code"] for item in data["items"]}
        assert "MFA" in set_codes
        assert "MFB" not in set_codes

    async def test_filter_by_foiling(self, client: AsyncClient, db):
        user = await _make_user(db, "missfoi@example.com")
        set_ = await _make_set(db, "MFF")
        card = await _make_card(db, "Foil Filter Card")
        await _make_printing(db, set_, card, "MFF-001-S", foiling="S")
        await _make_printing(db, set_, card, "MFF-001-R", foiling="R")

        resp = await client.get(
            "/missing",
            params={"set_id": str(set_.id), "foiling": "R"},
            headers=_auth(user),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert all(item["foiling"] == "R" for item in data["items"])

    async def test_empty_when_all_owned(self, client: AsyncClient, db):
        user = await _make_user(db, "missempty@example.com")
        set_ = await _make_set(db, "MEM")
        card = await _make_card(db, "Empty Set Card")
        printing = await _make_printing(db, set_, card, "MEM-001-S")
        await _own(db, user, printing)

        resp = await client.get(
            "/missing", params={"set_id": str(set_.id)}, headers=_auth(user)
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []
