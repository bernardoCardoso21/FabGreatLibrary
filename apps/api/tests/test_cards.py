"""
Tests for card catalog endpoints.

GET /sets          - list all sets
GET /cards         - filtered + paginated card list
GET /cards/{id}    - card detail with printings
"""

import uuid

import pytest
from httpx import AsyncClient

from app.db.models import Card, Printing, Set


# ── helpers ───────────────────────────────────────────────────────────────────

async def _make_set(db, code: str = "TST", name: str = "Test Set") -> Set:
    s = Set(code=code, name=name)
    db.add(s)
    await db.flush()
    return s


async def _make_card(
    db,
    name: str = "Enlightened Strike",
    card_type: str = "Generic Action Attack",
    hero_class: str | None = "Generic",
    talent: str | None = None,
    pitch: int | None = None,
) -> Card:
    card = Card(name=name, card_type=card_type, hero_class=hero_class, talent=talent, pitch=pitch)
    db.add(card)
    await db.flush()
    return card


async def _make_printing(db, set_: Set, card: Card, pid: str = "TST-001-S") -> Printing:
    p = Printing(
        printing_id=pid,
        card_id=card.id,
        set_id=set_.id,
        edition="F",
        foiling="S",
        rarity="C",
        artists=["Test Artist"],
        art_variations=[],
    )
    db.add(p)
    await db.flush()
    return p


# ── GET /sets ─────────────────────────────────────────────────────────────────

class TestGetSets:
    async def test_returns_all_sets(self, client: AsyncClient, db):
        await _make_set(db, "TSTA", "Test Set A")
        await _make_set(db, "TSTB", "Test Set B")

        resp = await client.get("/sets")
        assert resp.status_code == 200
        codes = [s["code"] for s in resp.json()]
        assert "TSTA" in codes
        assert "TSTB" in codes

    async def test_returns_list(self, client: AsyncClient):
        resp = await client.get("/sets")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_set_shape(self, client: AsyncClient, db):
        await _make_set(db, "SHP", "Shape Test Set")

        resp = await client.get("/sets")
        assert resp.status_code == 200
        first = next(s for s in resp.json() if s["code"] == "SHP")
        assert "id" in first
        assert first["name"] == "Shape Test Set"
        assert "image_url" in first


# ── GET /cards ────────────────────────────────────────────────────────────────

class TestGetCards:
    async def test_returns_paginated_results(self, client: AsyncClient, db):
        await _make_card(db, name="Alpha Strike")
        await _make_card(db, name="Beta Strike")

        resp = await client.get("/cards")
        assert resp.status_code == 200
        body = resp.json()
        assert body["page"] == 1
        assert body["page_size"] == 20
        assert body["total"] >= 2
        assert len(body["items"]) >= 2

    async def test_filter_by_name(self, client: AsyncClient, db):
        await _make_card(db, name="Enlightened Strike")
        await _make_card(db, name="Snatch")

        resp = await client.get("/cards", params={"name": "Enlightened"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        assert all("enlightened" in item["name"].lower() for item in body["items"])

    async def test_filter_by_hero_class(self, client: AsyncClient, db):
        await _make_card(db, name="Ninja Card", hero_class="Ninja")
        await _make_card(db, name="Warrior Card", hero_class="Warrior")

        resp = await client.get("/cards", params={"hero_class": "Ninja"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        assert all(item["hero_class"] == "Ninja" for item in body["items"])

    async def test_filter_by_pitch(self, client: AsyncClient, db):
        await _make_card(db, name="Red Strike", pitch=1)
        await _make_card(db, name="Blue Strike", pitch=3)

        resp = await client.get("/cards", params={"pitch": 1})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        assert all(item["pitch"] == 1 for item in body["items"])

    async def test_filter_by_set_code(self, client: AsyncClient, db):
        set_a = await _make_set(db, "SETA", "Set A")
        set_b = await _make_set(db, "SETB", "Set B")
        card_a = await _make_card(db, name="Set A Card")
        card_b = await _make_card(db, name="Set B Card")
        await _make_printing(db, set_a, card_a, "SETA-001-S")
        await _make_printing(db, set_b, card_b, "SETB-001-S")

        resp = await client.get("/cards", params={"set_code": "SETA"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["name"] == "Set A Card"

    async def test_pagination_page_size(self, client: AsyncClient, db):
        for i in range(5):
            await _make_card(db, name=f"Paginated Card {i:02d}")

        resp = await client.get("/cards", params={"page": 1, "page_size": 3})
        assert resp.status_code == 200
        body = resp.json()
        assert body["page"] == 1
        assert body["page_size"] == 3
        assert len(body["items"]) == 3

    async def test_page_size_over_limit_returns_422(self, client: AsyncClient):
        resp = await client.get("/cards", params={"page_size": 101})
        assert resp.status_code == 422

    async def test_invalid_page_returns_422(self, client: AsyncClient):
        resp = await client.get("/cards", params={"page": 0})
        assert resp.status_code == 422


# ── GET /cards/{id} ───────────────────────────────────────────────────────────

class TestGetCard:
    async def test_returns_card_with_printings(self, client: AsyncClient, db):
        set_ = await _make_set(db, "DTST", "Detail Test Set")
        card = await _make_card(db, name="Detail Test Card", pitch=2)
        await _make_printing(db, set_, card, "DTST-001-S")

        resp = await client.get(f"/cards/{card.id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "Detail Test Card"
        assert body["pitch"] == 2
        assert len(body["printings"]) == 1
        p = body["printings"][0]
        assert p["foiling"] == "S"
        assert p["edition"] == "F"
        assert p["set"]["code"] == "DTST"

    async def test_multiple_printings_all_returned(self, client: AsyncClient, db):
        set_ = await _make_set(db, "MPRT", "Multi Print Set")
        card = await _make_card(db, name="Multi Printing Card")
        await _make_printing(db, set_, card, "MPRT-001-S")
        rainbow = Printing(
            printing_id="MPRT-001-R",
            card_id=card.id,
            set_id=set_.id,
            edition="F",
            foiling="R",
            rarity="C",
            artists=[],
            art_variations=[],
        )
        db.add(rainbow)
        await db.flush()

        resp = await client.get(f"/cards/{card.id}")
        assert resp.status_code == 200
        assert len(resp.json()["printings"]) == 2

    async def test_unknown_id_returns_404(self, client: AsyncClient):
        resp = await client.get(f"/cards/{uuid.uuid4()}")
        assert resp.status_code == 404
