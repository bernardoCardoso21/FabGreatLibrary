"""
Tests for wishlist endpoints.

POST   /wishlists
GET    /wishlists
DELETE /wishlists/{id}
"""

import uuid

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, hash_password
from app.db.models import User


# ── helpers ───────────────────────────────────────────────────────────────────

async def _make_user(db, email: str = "wish@example.com") -> User:
    user = User(email=email, hashed_password=hash_password("password"))
    db.add(user)
    await db.flush()
    return user


def _auth(user: User) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user.email)}"}


# ── POST /wishlists ───────────────────────────────────────────────────────────

class TestCreateWishlist:
    async def test_requires_auth(self, client: AsyncClient):
        resp = await client.post("/wishlists", json={"name": "My List"})
        assert resp.status_code == 401

    async def test_creates_successfully(self, client: AsyncClient, db):
        user = await _make_user(db, "wcreate@example.com")
        resp = await client.post(
            "/wishlists", json={"name": "My List"}, headers=_auth(user)
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "My List"
        assert "id" in data
        assert "created_at" in data

    async def test_returns_402_on_second_create(self, client: AsyncClient, db):
        user = await _make_user(db, "w402@example.com")
        r1 = await client.post("/wishlists", json={"name": "First"}, headers=_auth(user))
        assert r1.status_code == 201
        resp = await client.post("/wishlists", json={"name": "Second"}, headers=_auth(user))
        assert resp.status_code == 402

    async def test_stores_filter_json(self, client: AsyncClient, db):
        user = await _make_user(db, "wfilt@example.com")
        resp = await client.post(
            "/wishlists",
            json={"name": "Cold Foil Majestic", "filter_json": {"foiling": "C", "rarity": "M"}},
            headers=_auth(user),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["filter_json"]["foiling"] == "C"
        assert data["filter_json"]["rarity"] == "M"


# ── GET /wishlists ────────────────────────────────────────────────────────────

class TestGetWishlists:
    async def test_requires_auth(self, client: AsyncClient):
        resp = await client.get("/wishlists")
        assert resp.status_code == 401

    async def test_empty_list(self, client: AsyncClient, db):
        user = await _make_user(db, "wempty@example.com")
        resp = await client.get("/wishlists", headers=_auth(user))
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_returns_own_wishlists_only(self, client: AsyncClient, db):
        user_a = await _make_user(db, "woa@example.com")
        user_b = await _make_user(db, "wob@example.com")

        await client.post("/wishlists", json={"name": "A's List"}, headers=_auth(user_a))

        resp_b = await client.get("/wishlists", headers=_auth(user_b))
        assert resp_b.status_code == 200
        assert resp_b.json() == []

        resp_a = await client.get("/wishlists", headers=_auth(user_a))
        assert resp_a.status_code == 200
        assert len(resp_a.json()) == 1
        assert resp_a.json()[0]["name"] == "A's List"


# ── DELETE /wishlists/{id} ────────────────────────────────────────────────────

class TestDeleteWishlist:
    async def test_requires_auth(self, client: AsyncClient):
        resp = await client.delete(f"/wishlists/{uuid.uuid4()}")
        assert resp.status_code == 401

    async def test_deletes_successfully(self, client: AsyncClient, db):
        user = await _make_user(db, "wdel@example.com")
        create_resp = await client.post(
            "/wishlists", json={"name": "To Delete"}, headers=_auth(user)
        )
        wishlist_id = create_resp.json()["id"]

        resp = await client.delete(f"/wishlists/{wishlist_id}", headers=_auth(user))
        assert resp.status_code == 204

        get_resp = await client.get("/wishlists", headers=_auth(user))
        assert get_resp.json() == []

    async def test_404_on_wrong_user(self, client: AsyncClient, db):
        user_a = await _make_user(db, "wda@example.com")
        user_b = await _make_user(db, "wdb@example.com")
        create_resp = await client.post(
            "/wishlists", json={"name": "A's List"}, headers=_auth(user_a)
        )
        wishlist_id = create_resp.json()["id"]

        resp = await client.delete(f"/wishlists/{wishlist_id}", headers=_auth(user_b))
        assert resp.status_code == 404

    async def test_allows_create_after_delete(self, client: AsyncClient, db):
        user = await _make_user(db, "wrecreate@example.com")
        create_resp = await client.post(
            "/wishlists", json={"name": "First"}, headers=_auth(user)
        )
        wishlist_id = create_resp.json()["id"]
        await client.delete(f"/wishlists/{wishlist_id}", headers=_auth(user))

        resp = await client.post(
            "/wishlists", json={"name": "Second"}, headers=_auth(user)
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "Second"
