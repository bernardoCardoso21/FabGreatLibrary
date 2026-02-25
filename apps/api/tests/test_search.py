"""
Tests for cross-set printing search.

GET /search/printings - filtered + paginated across all sets
"""

import pytest
from httpx import AsyncClient

from app.db.models import Card, Printing, Set


# ── helpers ───────────────────────────────────────────────────────────────────

async def _make_set(db, code: str, name: str = "Search Test Set") -> Set:
    s = Set(code=code, name=name)
    db.add(s)
    await db.flush()
    return s


async def _make_card(
    db,
    name: str = "Search Card",
    card_type: str = "Action",
    hero_class: str | None = "Generic",
    talent: str | None = None,
) -> Card:
    card = Card(name=name, card_type=card_type, hero_class=hero_class, talent=talent)
    db.add(card)
    await db.flush()
    return card


async def _make_printing(
    db,
    set_: Set,
    card: Card,
    pid: str,
    foiling: str = "S",
    rarity: str = "C",
    edition: str = "F",
) -> Printing:
    p = Printing(
        printing_id=pid,
        card_id=card.id,
        set_id=set_.id,
        edition=edition,
        foiling=foiling,
        rarity=rarity,
        artists=[],
        art_variations=[],
    )
    db.add(p)
    await db.flush()
    return p


# ── GET /search/printings ─────────────────────────────────────────────────────

class TestSearchPrintings:
    async def test_returns_all_when_no_filters(self, client: AsyncClient, db):
        set_ = await _make_set(db, "SA1", "Search All Set")
        card = await _make_card(db, name="Search All Card")
        await _make_printing(db, set_, card, "SA1-001-S")

        resp = await client.get("/search/printings")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        assert "items" in body
        assert "page" in body
        assert "page_size" in body

    async def test_filter_by_name(self, client: AsyncClient, db):
        set_ = await _make_set(db, "SQ1", "Name Search Set")
        card_a = await _make_card(db, name="Enlightened Strike")
        card_b = await _make_card(db, name="Snatch")
        await _make_printing(db, set_, card_a, "SQ1-001-S")
        await _make_printing(db, set_, card_b, "SQ1-002-S")

        resp = await client.get("/search/printings", params={"q": "Enlightened"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        assert all("enlightened" in item["card"]["name"].lower() for item in body["items"])

    async def test_filter_by_hero_class(self, client: AsyncClient, db):
        set_ = await _make_set(db, "SH1", "Class Search Set")
        ninja = await _make_card(db, name="Ninja Move", hero_class="Ninja")
        brute = await _make_card(db, name="Brute Force", hero_class="Brute")
        await _make_printing(db, set_, ninja, "SH1-001-S")
        await _make_printing(db, set_, brute, "SH1-002-S")

        resp = await client.get("/search/printings", params={"hero_class": "Ninja"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        assert all(item["card"]["hero_class"] == "Ninja" for item in body["items"])

    async def test_filter_by_foiling(self, client: AsyncClient, db):
        set_ = await _make_set(db, "SF2", "Foil Search Set")
        card = await _make_card(db, name="Foil Search Card")
        await _make_printing(db, set_, card, "SF2-001-S", foiling="S")
        await _make_printing(db, set_, card, "SF2-001-C", foiling="C")

        resp = await client.get("/search/printings", params={"foiling": "C"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        assert all(item["foiling"] == "C" for item in body["items"])

    async def test_filter_by_rarity(self, client: AsyncClient, db):
        set_ = await _make_set(db, "SR2", "Rarity Search Set")
        card = await _make_card(db, name="Rare Search Card")
        await _make_printing(db, set_, card, "SR2-001-C", rarity="C")
        await _make_printing(db, set_, card, "SR2-001-R", foiling="R", rarity="M")

        resp = await client.get("/search/printings", params={"rarity": "M"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        assert all(item["rarity"] == "M" for item in body["items"])

    async def test_filter_by_set_code(self, client: AsyncClient, db):
        set_a = await _make_set(db, "SSA", "Set Search A")
        set_b = await _make_set(db, "SSB", "Set Search B")
        card_a = await _make_card(db, name="Set A Only Card")
        card_b = await _make_card(db, name="Set B Only Card")
        await _make_printing(db, set_a, card_a, "SSA-001-S")
        await _make_printing(db, set_b, card_b, "SSB-001-S")

        resp = await client.get("/search/printings", params={"set_code": "SSA"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["set"]["code"] == "SSA"

    async def test_filter_by_card_type(self, client: AsyncClient, db):
        set_ = await _make_set(db, "ST1", "Type Search Set")
        attack = await _make_card(db, name="Attack Card", card_type="Ninja Action Attack")
        instant = await _make_card(db, name="Instant Card", card_type="Generic Instant")
        await _make_printing(db, set_, attack, "ST1-001-S")
        await _make_printing(db, set_, instant, "ST1-002-S")

        resp = await client.get("/search/printings", params={"card_type": "Attack"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        assert all("attack" in item["card"]["card_type"].lower() for item in body["items"])

    async def test_cross_set_search(self, client: AsyncClient, db):
        set_a = await _make_set(db, "CXA", "Cross Set A")
        set_b = await _make_set(db, "CXB", "Cross Set B")
        card = await _make_card(db, name="Cross Set Ninja", hero_class="Ninja")
        await _make_printing(db, set_a, card, "CXA-001-S")
        await _make_printing(db, set_b, card, "CXB-001-S")

        resp = await client.get("/search/printings", params={"hero_class": "Ninja"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 2

    async def test_pagination(self, client: AsyncClient, db):
        set_ = await _make_set(db, "PGS", "Paginate Search Set")
        for i in range(5):
            card = await _make_card(db, name=f"Paginated Search Card {i:02d}")
            await _make_printing(db, set_, card, f"PGS-{i:03d}-S")

        resp = await client.get("/search/printings", params={"set_code": "PGS", "page": 2, "page_size": 2})
        assert resp.status_code == 200
        body = resp.json()
        assert body["page"] == 2
        assert body["page_size"] == 2
        assert len(body["items"]) == 2
        assert body["total"] == 5

    async def test_page_size_over_limit_returns_422(self, client: AsyncClient):
        resp = await client.get("/search/printings", params={"page_size": 101})
        assert resp.status_code == 422
