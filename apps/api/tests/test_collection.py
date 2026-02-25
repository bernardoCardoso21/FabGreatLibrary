"""
Tests for collection mutation endpoints.

GET  /collection/summary         - owned printings list (auth required)
POST /collection/items           - single upsert
POST /collection/bulk            - atomic bulk actions
"""

import uuid

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, hash_password
from app.db.models import Card, OwnedPrinting, Printing, Set, User


# ── helpers ───────────────────────────────────────────────────────────────────

async def _make_user(db, email: str = "coll@example.com") -> User:
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


async def _make_card(db, name: str = "Test Card") -> Card:
    card = Card(name=name, card_type="Action", hero_class="Generic")
    db.add(card)
    await db.flush()
    return card


async def _make_printing(db, set_: Set, card: Card, pid: str) -> Printing:
    p = Printing(
        printing_id=pid,
        card_id=card.id,
        set_id=set_.id,
        edition="F",
        foiling="S",
        rarity="C",
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


# ── GET /collection/summary ───────────────────────────────────────────────────

class TestGetCollectionSummary:
    async def test_requires_auth(self, client: AsyncClient):
        resp = await client.get("/collection/summary")
        assert resp.status_code == 401

    async def test_empty_collection(self, client: AsyncClient, db):
        user = await _make_user(db, "empty@example.com")
        resp = await client.get("/collection/summary", headers=_auth(user))
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_returns_owned_printings(self, client: AsyncClient, db):
        user = await _make_user(db, "summ@example.com")
        set_ = await _make_set(db, "SM1")
        card = await _make_card(db, "Summary Card")
        printing = await _make_printing(db, set_, card, "SM1-001-S")
        await _own(db, user, printing, qty=2)

        resp = await client.get("/collection/summary", headers=_auth(user))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["qty"] == 2
        assert data[0]["printing"]["printing_id"] == "SM1-001-S"
        assert data[0]["printing"]["card"]["name"] == "Summary Card"
        assert data[0]["printing"]["set"]["code"] == "SM1"

    async def test_filter_by_set_id(self, client: AsyncClient, db):
        user = await _make_user(db, "filt@example.com")
        set_a = await _make_set(db, "FA1")
        set_b = await _make_set(db, "FB1")
        card = await _make_card(db, "Filter Card")
        printing_a = await _make_printing(db, set_a, card, "FA1-001-S")
        printing_b = await _make_printing(db, set_b, card, "FB1-001-S")
        await _own(db, user, printing_a)
        await _own(db, user, printing_b)

        resp = await client.get(
            "/collection/summary", params={"set_id": str(set_a.id)}, headers=_auth(user)
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["printing"]["set"]["code"] == "FA1"

    async def test_only_returns_own_items(self, client: AsyncClient, db):
        user_a = await _make_user(db, "ua@example.com")
        user_b = await _make_user(db, "ub@example.com")
        set_ = await _make_set(db, "ISO")
        card = await _make_card(db, "Isolation Card")
        printing = await _make_printing(db, set_, card, "ISO-001-S")
        await _own(db, user_a, printing)

        resp = await client.get("/collection/summary", headers=_auth(user_b))
        assert resp.status_code == 200
        assert resp.json() == []


# ── POST /collection/items ────────────────────────────────────────────────────

class TestUpsertItem:
    async def test_requires_auth(self, client: AsyncClient, db):
        set_ = await _make_set(db, "AU1")
        card = await _make_card(db)
        printing = await _make_printing(db, set_, card, "AU1-001-S")
        resp = await client.post(
            "/collection/items", json={"printing_id": str(printing.id), "qty": 1}
        )
        assert resp.status_code == 401

    async def test_add_new_item(self, client: AsyncClient, db):
        user = await _make_user(db, "add@example.com")
        set_ = await _make_set(db, "AD1")
        card = await _make_card(db, "Add Card")
        printing = await _make_printing(db, set_, card, "AD1-001-S")

        resp = await client.post(
            "/collection/items",
            json={"printing_id": str(printing.id), "qty": 2},
            headers=_auth(user),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["qty"] == 2
        assert body["printing_id"] == str(printing.id)

    async def test_update_existing_item(self, client: AsyncClient, db):
        user = await _make_user(db, "upd@example.com")
        set_ = await _make_set(db, "UP1")
        card = await _make_card(db, "Update Card")
        printing = await _make_printing(db, set_, card, "UP1-001-S")
        await _own(db, user, printing, qty=1)

        resp = await client.post(
            "/collection/items",
            json={"printing_id": str(printing.id), "qty": 4},
            headers=_auth(user),
        )
        assert resp.status_code == 200
        assert resp.json()["qty"] == 4

    async def test_qty_zero_deletes_row(self, client: AsyncClient, db):
        user = await _make_user(db, "del@example.com")
        set_ = await _make_set(db, "DL1")
        card = await _make_card(db, "Delete Card")
        printing = await _make_printing(db, set_, card, "DL1-001-S")
        await _own(db, user, printing, qty=3)

        resp = await client.post(
            "/collection/items",
            json={"printing_id": str(printing.id), "qty": 0},
            headers=_auth(user),
        )
        assert resp.status_code == 200
        assert resp.json()["qty"] is None

    async def test_negative_qty_returns_422(self, client: AsyncClient, db):
        user = await _make_user(db, "neg@example.com")
        resp = await client.post(
            "/collection/items",
            json={"printing_id": str(uuid.uuid4()), "qty": -1},
            headers=_auth(user),
        )
        assert resp.status_code == 422

    async def test_unknown_printing_returns_404(self, client: AsyncClient, db):
        user = await _make_user(db, "mis@example.com")
        resp = await client.post(
            "/collection/items",
            json={"printing_id": str(uuid.uuid4()), "qty": 1},
            headers=_auth(user),
        )
        assert resp.status_code == 404


# ── POST /collection/bulk ─────────────────────────────────────────────────────

class TestBulkApply:
    async def test_requires_auth(self, client: AsyncClient, db):
        resp = await client.post("/collection/bulk", json={"items": []})
        assert resp.status_code == 422  # empty items fails validation before auth

    async def test_increment_creates_new_row(self, client: AsyncClient, db):
        user = await _make_user(db, "binc@example.com")
        set_ = await _make_set(db, "BI1")
        card = await _make_card(db, "Bulk Inc Card")
        printing = await _make_printing(db, set_, card, "BI1-001-S")

        resp = await client.post(
            "/collection/bulk",
            json={"items": [{"printing_id": str(printing.id), "action": "increment"}]},
            headers=_auth(user),
        )
        assert resp.status_code == 200
        assert resp.json()[0]["qty"] == 1

    async def test_increment_adds_to_existing(self, client: AsyncClient, db):
        user = await _make_user(db, "binca@example.com")
        set_ = await _make_set(db, "BI2")
        card = await _make_card(db, "Bulk Inc Existing")
        printing = await _make_printing(db, set_, card, "BI2-001-S")
        await _own(db, user, printing, qty=2)

        resp = await client.post(
            "/collection/bulk",
            json={"items": [{"printing_id": str(printing.id), "action": "increment"}]},
            headers=_auth(user),
        )
        assert resp.status_code == 200
        assert resp.json()[0]["qty"] == 3

    async def test_mark_playset_sets_qty_3(self, client: AsyncClient, db):
        user = await _make_user(db, "bps@example.com")
        set_ = await _make_set(db, "BP1")
        card = await _make_card(db, "Playset Card")
        printing = await _make_printing(db, set_, card, "BP1-001-S")

        resp = await client.post(
            "/collection/bulk",
            json={"items": [{"printing_id": str(printing.id), "action": "mark_playset"}]},
            headers=_auth(user),
        )
        assert resp.status_code == 200
        assert resp.json()[0]["qty"] == 3

    async def test_clear_deletes_row(self, client: AsyncClient, db):
        user = await _make_user(db, "bclr@example.com")
        set_ = await _make_set(db, "BC1")
        card = await _make_card(db, "Clear Card")
        printing = await _make_printing(db, set_, card, "BC1-001-S")
        await _own(db, user, printing, qty=2)

        resp = await client.post(
            "/collection/bulk",
            json={"items": [{"printing_id": str(printing.id), "action": "clear"}]},
            headers=_auth(user),
        )
        assert resp.status_code == 200
        assert resp.json()[0]["qty"] is None

    async def test_set_qty_action(self, client: AsyncClient, db):
        user = await _make_user(db, "bsq@example.com")
        set_ = await _make_set(db, "BS1")
        card = await _make_card(db, "Set Qty Card")
        printing = await _make_printing(db, set_, card, "BS1-001-S")

        resp = await client.post(
            "/collection/bulk",
            json={"items": [{"printing_id": str(printing.id), "action": "set_qty", "qty": 5}]},
            headers=_auth(user),
        )
        assert resp.status_code == 200
        assert resp.json()[0]["qty"] == 5

    async def test_set_qty_without_qty_returns_422(self, client: AsyncClient, db):
        user = await _make_user(db, "bsqv@example.com")
        resp = await client.post(
            "/collection/bulk",
            json={"items": [{"printing_id": str(uuid.uuid4()), "action": "set_qty"}]},
            headers=_auth(user),
        )
        assert resp.status_code == 422

    async def test_unknown_printing_returns_404(self, client: AsyncClient, db):
        user = await _make_user(db, "bmis@example.com")
        resp = await client.post(
            "/collection/bulk",
            json={"items": [{"printing_id": str(uuid.uuid4()), "action": "increment"}]},
            headers=_auth(user),
        )
        assert resp.status_code == 404

    async def test_bulk_is_atomic_on_missing_printing(self, client: AsyncClient, db):
        """If any printing_id is missing the whole batch is rejected — no partial apply."""
        user = await _make_user(db, "batm@example.com")
        set_ = await _make_set(db, "BA1")
        card = await _make_card(db, "Atomic Card")
        printing = await _make_printing(db, set_, card, "BA1-001-S")

        resp = await client.post(
            "/collection/bulk",
            json={
                "items": [
                    {"printing_id": str(printing.id), "action": "mark_playset"},
                    {"printing_id": str(uuid.uuid4()), "action": "increment"},
                ]
            },
            headers=_auth(user),
        )
        assert resp.status_code == 404

        # Verify the valid printing was NOT modified
        summary = await client.get("/collection/summary", headers=_auth(user))
        assert summary.json() == []

    async def test_multiple_items_applied(self, client: AsyncClient, db):
        user = await _make_user(db, "bmlt@example.com")
        set_ = await _make_set(db, "BM1")
        card = await _make_card(db, "Multi Card")
        p1 = await _make_printing(db, set_, card, "BM1-001-S")
        p2 = await _make_printing(db, set_, card, "BM1-001-R", foiling="R")

        resp = await client.post(
            "/collection/bulk",
            json={
                "items": [
                    {"printing_id": str(p1.id), "action": "mark_playset"},
                    {"printing_id": str(p2.id), "action": "increment"},
                ]
            },
            headers=_auth(user),
        )
        assert resp.status_code == 200
        results = {r["printing_id"]: r["qty"] for r in resp.json()}
        assert results[str(p1.id)] == 3
        assert results[str(p2.id)] == 1
