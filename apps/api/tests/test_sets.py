"""
Tests for set endpoints.

GET /sets                    - set list with printing counts + optional owned_count
GET /sets/{set_id}/printings - printings in a set, filtered + paginated
"""

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, hash_password
from app.db.models import Card, OwnedPrinting, Printing, Set, User


# ── helpers ───────────────────────────────────────────────────────────────────

async def _make_user(db, email: str = "user@example.com") -> User:
    user = User(email=email, hashed_password=hash_password("password"))
    db.add(user)
    await db.flush()
    return user


def _auth_header(user: User) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user.email)}"}


async def _make_set(db, code: str, name: str = "Test Set", set_type: str = "booster") -> Set:
    s = Set(code=code, name=name, set_type=set_type)
    db.add(s)
    await db.flush()
    return s


async def _make_card(
    db,
    name: str = "Test Card",
    card_type: str = "Action",
    hero_class: str | None = "Generic",
    talent: str | None = None,
    pitch: int | None = None,
) -> Card:
    card = Card(name=name, card_type=card_type, hero_class=hero_class, talent=talent, pitch=pitch)
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


# ── GET /sets ─────────────────────────────────────────────────────────────────

class TestGetSets:
    async def test_returns_sets_with_printing_count(self, client: AsyncClient, db):
        set_ = await _make_set(db, "CNT", "Count Test Set")
        card = await _make_card(db, name="Count Card")
        await _make_printing(db, set_, card, "CNT-001-S")
        await _make_printing(db, set_, card, "CNT-001-R", foiling="R")

        resp = await client.get("/sets", params={"collection_mode": "master_set"})
        assert resp.status_code == 200
        entry = next(s for s in resp.json() if s["code"] == "CNT")
        assert entry["printing_count"] == 2

    async def test_owned_count_is_none_when_unauthenticated(self, client: AsyncClient, db):
        await _make_set(db, "UNA", "Unauth Set")

        resp = await client.get("/sets")
        assert resp.status_code == 200
        entry = next(s for s in resp.json() if s["code"] == "UNA")
        assert entry["owned_count"] is None

    async def test_owned_count_when_authenticated(self, client: AsyncClient, db):
        set_ = await _make_set(db, "OWN", "Owned Set")
        card = await _make_card(db, name="Owned Card")
        printing = await _make_printing(db, set_, card, "OWN-001-S")

        user = await _make_user(db, "own@example.com")
        db.add(OwnedPrinting(user_id=user.id, printing_id=printing.id, qty=2))
        await db.flush()

        resp = await client.get(
            "/sets",
            params={"collection_mode": "master_set"},
            headers=_auth_header(user),
        )
        assert resp.status_code == 200
        entry = next(s for s in resp.json() if s["code"] == "OWN")
        assert entry["owned_count"] == 1

    async def test_empty_set_has_zero_printing_count(self, client: AsyncClient, db):
        await _make_set(db, "EMP", "Empty Set")

        resp = await client.get("/sets")
        assert resp.status_code == 200
        entry = next(s for s in resp.json() if s["code"] == "EMP")
        assert entry["printing_count"] == 0

    async def test_returns_list(self, client: AsyncClient):
        resp = await client.get("/sets")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_filter_by_set_type(self, client: AsyncClient, db):
        await _make_set(db, "BT1", "Booster One", set_type="booster")
        await _make_set(db, "DK1", "Deck One", set_type="deck")

        resp = await client.get("/sets", params={"set_type": "deck"})
        assert resp.status_code == 200
        codes = [s["code"] for s in resp.json() if s["code"] in ("BT1", "DK1")]
        assert codes == ["DK1"]

    async def test_no_filter_returns_all_types(self, client: AsyncClient, db):
        await _make_set(db, "BT2", "Booster Two", set_type="booster")
        await _make_set(db, "PR2", "Promo Two", set_type="promo")

        resp = await client.get("/sets")
        assert resp.status_code == 200
        codes = {s["code"] for s in resp.json()}
        assert "BT2" in codes
        assert "PR2" in codes

    async def test_playset_mode_counts_distinct_cards(self, client: AsyncClient, db):
        set_ = await _make_set(db, "PLS", "Playset Set")
        card = await _make_card(db, name="Playset Card", card_type="Action")
        await _make_printing(db, set_, card, "PLS-001-S", foiling="S")
        await _make_printing(db, set_, card, "PLS-001-R", foiling="R")

        resp = await client.get("/sets", params={"collection_mode": "playset"})
        assert resp.status_code == 200
        entry = next(s for s in resp.json() if s["code"] == "PLS")
        assert entry["printing_count"] == 1
        assert entry["collection_mode"] == "playset"

    async def test_master_set_mode_counts_all_printings(self, client: AsyncClient, db):
        set_ = await _make_set(db, "MAS", "Master Set")
        card = await _make_card(db, name="Master Card", card_type="Action")
        await _make_printing(db, set_, card, "MAS-001-S", foiling="S")
        await _make_printing(db, set_, card, "MAS-001-R", foiling="R")

        resp = await client.get("/sets", params={"collection_mode": "master_set"})
        assert resp.status_code == 200
        entry = next(s for s in resp.json() if s["code"] == "MAS")
        assert entry["printing_count"] == 2
        assert entry["collection_mode"] == "master_set"

    async def test_playset_hero_target_is_1(self, client: AsyncClient, db):
        set_ = await _make_set(db, "PHR", "Playset Hero Set")
        hero = await _make_card(db, name="Ira", card_type="Hero", hero_class="Ninja")
        p = await _make_printing(db, set_, hero, "PHR-001-S")

        user = await _make_user(db, "hero@example.com")
        db.add(OwnedPrinting(user_id=user.id, printing_id=p.id, qty=1))
        await db.flush()

        resp = await client.get(
            "/sets",
            params={"collection_mode": "playset"},
            headers=_auth_header(user),
        )
        assert resp.status_code == 200
        entry = next(s for s in resp.json() if s["code"] == "PHR")
        assert entry["printing_count"] == 1
        assert entry["owned_count"] == 1

    async def test_playset_non_hero_target_is_3(self, client: AsyncClient, db):
        set_ = await _make_set(db, "P3T", "Playset 3 Target")
        card = await _make_card(db, name="Strike", card_type="Action")
        p1 = await _make_printing(db, set_, card, "P3T-001-S")
        p2 = await _make_printing(db, set_, card, "P3T-001-R", foiling="R")

        user = await _make_user(db, "playset3@example.com")
        db.add(OwnedPrinting(user_id=user.id, printing_id=p1.id, qty=2))
        db.add(OwnedPrinting(user_id=user.id, printing_id=p2.id, qty=1))
        await db.flush()

        resp = await client.get(
            "/sets",
            params={"collection_mode": "playset"},
            headers=_auth_header(user),
        )
        assert resp.status_code == 200
        entry = next(s for s in resp.json() if s["code"] == "P3T")
        assert entry["owned_count"] == 1

    async def test_playset_non_hero_under_target(self, client: AsyncClient, db):
        set_ = await _make_set(db, "PUN", "Playset Under")
        card = await _make_card(db, name="Block", card_type="Defense Reaction")
        p = await _make_printing(db, set_, card, "PUN-001-S")

        user = await _make_user(db, "under@example.com")
        db.add(OwnedPrinting(user_id=user.id, printing_id=p.id, qty=2))
        await db.flush()

        resp = await client.get(
            "/sets",
            params={"collection_mode": "playset"},
            headers=_auth_header(user),
        )
        assert resp.status_code == 200
        entry = next(s for s in resp.json() if s["code"] == "PUN")
        assert entry["owned_count"] == 0


# ── GET /sets/{set_id}/printings ──────────────────────────────────────────────

class TestGetSetPrintings:
    async def test_returns_printings_for_set(self, client: AsyncClient, db):
        set_ = await _make_set(db, "SP1", "Set Printings 1")
        card = await _make_card(db, name="SP Card")
        await _make_printing(db, set_, card, "SP1-001-S")

        resp = await client.get(f"/sets/{set_.id}/printings")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["printing_id"] == "SP1-001-S"
        assert body["items"][0]["card"]["name"] == "SP Card"
        assert body["items"][0]["set"]["code"] == "SP1"

    async def test_filter_by_foiling(self, client: AsyncClient, db):
        set_ = await _make_set(db, "SF1", "Foil Filter Set")
        card = await _make_card(db, name="Foil Card")
        await _make_printing(db, set_, card, "SF1-001-S", foiling="S")
        await _make_printing(db, set_, card, "SF1-001-R", foiling="R")

        resp = await client.get(f"/sets/{set_.id}/printings", params={"foiling": "R"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["foiling"] == "R"

    async def test_filter_by_rarity(self, client: AsyncClient, db):
        set_ = await _make_set(db, "SR1", "Rarity Filter Set")
        card = await _make_card(db, name="Rarity Card")
        await _make_printing(db, set_, card, "SR1-001-C", rarity="C")
        await _make_printing(db, set_, card, "SR1-001-R", foiling="R", rarity="R")

        resp = await client.get(f"/sets/{set_.id}/printings", params={"rarity": "R"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["rarity"] == "R"

    async def test_filter_by_name(self, client: AsyncClient, db):
        set_ = await _make_set(db, "SN1", "Name Filter Set")
        card_a = await _make_card(db, name="Strike Alpha")
        card_b = await _make_card(db, name="Block Beta")
        await _make_printing(db, set_, card_a, "SN1-001-S")
        await _make_printing(db, set_, card_b, "SN1-002-S")

        resp = await client.get(f"/sets/{set_.id}/printings", params={"q": "Strike"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["card"]["name"] == "Strike Alpha"

    async def test_filter_by_hero_class(self, client: AsyncClient, db):
        set_ = await _make_set(db, "SC1", "Class Filter Set")
        ninja_card = await _make_card(db, name="Ninja Strike", hero_class="Ninja")
        wizard_card = await _make_card(db, name="Wizard Bolt", hero_class="Wizard")
        await _make_printing(db, set_, ninja_card, "SC1-001-S")
        await _make_printing(db, set_, wizard_card, "SC1-002-S")

        resp = await client.get(f"/sets/{set_.id}/printings", params={"hero_class": "Ninja"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["card"]["hero_class"] == "Ninja"

    async def test_pagination(self, client: AsyncClient, db):
        set_ = await _make_set(db, "PG1", "Pagination Set")
        for i in range(5):
            card = await _make_card(db, name=f"Paged Card {i:02d}")
            await _make_printing(db, set_, card, f"PG1-{i:03d}-S")

        resp = await client.get(f"/sets/{set_.id}/printings", params={"page": 2, "page_size": 2})
        assert resp.status_code == 200
        body = resp.json()
        assert body["page"] == 2
        assert body["page_size"] == 2
        assert len(body["items"]) == 2
        assert body["total"] == 5

    async def test_unknown_set_returns_404(self, client: AsyncClient):
        import uuid
        resp = await client.get(f"/sets/{uuid.uuid4()}/printings")
        assert resp.status_code == 404

    async def test_page_size_over_limit_returns_422(self, client: AsyncClient, db):
        set_ = await _make_set(db, "LM1", "Limit Set")
        resp = await client.get(f"/sets/{set_.id}/printings", params={"page_size": 101})
        assert resp.status_code == 422


# ── GET /sets/{set_id}/cards (playset mode) ──────────────────────────────────

class TestGetSetCards:
    async def test_groups_printings_by_card(self, client: AsyncClient, db):
        set_ = await _make_set(db, "PSC", "Playset Cards Set")
        card = await _make_card(db, name="Grouped Card", card_type="Action")
        await _make_printing(db, set_, card, "PSC-001-S", foiling="S")
        await _make_printing(db, set_, card, "PSC-001-R", foiling="R")
        await _make_printing(db, set_, card, "PSC-001-C", foiling="C")

        resp = await client.get(f"/sets/{set_.id}/cards")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["name"] == "Grouped Card"
        assert body["items"][0]["target"] == 3

    async def test_hero_target_is_1(self, client: AsyncClient, db):
        set_ = await _make_set(db, "PHC", "Playset Hero Cards")
        hero = await _make_card(db, name="Test Hero", card_type="Hero", hero_class="Ninja")
        await _make_printing(db, set_, hero, "PHC-001-S")

        resp = await client.get(f"/sets/{set_.id}/cards")
        assert resp.status_code == 200
        item = resp.json()["items"][0]
        assert item["target"] == 1

    async def test_owned_qty_aggregated(self, client: AsyncClient, db):
        set_ = await _make_set(db, "POQ", "Playset Owned Qty")
        card = await _make_card(db, name="Owned Card", card_type="Action")
        p1 = await _make_printing(db, set_, card, "POQ-001-S")
        p2 = await _make_printing(db, set_, card, "POQ-001-R", foiling="R")

        user = await _make_user(db, "pqty@example.com")
        db.add(OwnedPrinting(user_id=user.id, printing_id=p1.id, qty=2))
        db.add(OwnedPrinting(user_id=user.id, printing_id=p2.id, qty=1))
        await db.flush()

        resp = await client.get(
            f"/sets/{set_.id}/cards",
            headers=_auth_header(user),
        )
        assert resp.status_code == 200
        item = resp.json()["items"][0]
        assert item["owned_qty"] == 3
        assert item["target"] == 3

    async def test_owned_qty_null_unauthenticated(self, client: AsyncClient, db):
        set_ = await _make_set(db, "PNU", "Playset Null")
        card = await _make_card(db, name="Null Card", card_type="Action")
        await _make_printing(db, set_, card, "PNU-001-S")

        resp = await client.get(f"/sets/{set_.id}/cards")
        assert resp.status_code == 200
        assert resp.json()["items"][0]["owned_qty"] is None

    async def test_unknown_set_returns_404(self, client: AsyncClient):
        import uuid
        resp = await client.get(f"/sets/{uuid.uuid4()}/cards")
        assert resp.status_code == 404

    async def test_filter_by_name(self, client: AsyncClient, db):
        set_ = await _make_set(db, "PFN", "Playset Filter Name")
        c1 = await _make_card(db, name="Alpha Strike", card_type="Action")
        c2 = await _make_card(db, name="Beta Block", card_type="Defense Reaction")
        await _make_printing(db, set_, c1, "PFN-001-S")
        await _make_printing(db, set_, c2, "PFN-002-S")

        resp = await client.get(f"/sets/{set_.id}/cards", params={"q": "Alpha"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["name"] == "Alpha Strike"
