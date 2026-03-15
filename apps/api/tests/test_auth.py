"""
Tests for auth endpoints:
  POST /auth/register
  POST /auth/token
  POST /auth/refresh
  POST /auth/logout
  GET  /auth/me
"""

import pytest
from httpx import AsyncClient


# ── helpers ───────────────────────────────────────────────────────────────────

async def _register(client: AsyncClient, email: str, password: str = "secret") -> dict:
    """Register a user and return the parsed JSON response."""
    resp = await client.post("/auth/register", json={"email": email, "password": password})
    assert resp.status_code == 201, resp.text
    return resp.json()


# ── register ──────────────────────────────────────────────────────────────────

class TestRegister:
    async def test_happy_path_returns_tokens(self, client: AsyncClient):
        data = await _register(client, "reg@example.com")
        assert data["token_type"] == "bearer"
        assert data["access_token"]
        assert data["refresh_token"]

    async def test_duplicate_email_returns_409(self, client: AsyncClient):
        await _register(client, "dup@example.com")
        resp = await client.post(
            "/auth/register", json={"email": "dup@example.com", "password": "x"}
        )
        assert resp.status_code == 409


# ── login ─────────────────────────────────────────────────────────────────────

class TestLogin:
    async def test_happy_path_returns_tokens(self, client: AsyncClient):
        await _register(client, "login@example.com", "pass123")
        resp = await client.post(
            "/auth/token",
            data={"username": "login@example.com", "password": "pass123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"]
        assert data["refresh_token"]

    async def test_wrong_password_returns_401(self, client: AsyncClient):
        await _register(client, "wp@example.com", "correct")
        resp = await client.post(
            "/auth/token",
            data={"username": "wp@example.com", "password": "wrong"},
        )
        assert resp.status_code == 401

    async def test_unknown_email_returns_401(self, client: AsyncClient):
        resp = await client.post(
            "/auth/token",
            data={"username": "nobody@example.com", "password": "x"},
        )
        assert resp.status_code == 401


# ── refresh ───────────────────────────────────────────────────────────────────

class TestRefresh:
    async def test_happy_path_returns_new_access_token(self, client: AsyncClient):
        tokens = await _register(client, "refresh@example.com")
        resp = await client.post(
            "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"]

    async def test_invalid_token_returns_401(self, client: AsyncClient):
        resp = await client.post(
            "/auth/refresh", json={"refresh_token": "not-a-real-token"}
        )
        assert resp.status_code == 401


# ── logout ────────────────────────────────────────────────────────────────────

class TestLogout:
    async def test_revokes_refresh_token(self, client: AsyncClient):
        tokens = await _register(client, "logout@example.com")
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Logout — should succeed
        resp = await client.post(
            "/auth/logout",
            json={"refresh_token": tokens["refresh_token"]},
            headers=headers,
        )
        assert resp.status_code == 204

        # Refresh with the now-revoked token — should fail
        resp = await client.post(
            "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        assert resp.status_code == 401

    async def test_requires_bearer_auth(self, client: AsyncClient):
        tokens = await _register(client, "logout2@example.com")
        resp = await client.post(
            "/auth/logout", json={"refresh_token": tokens["refresh_token"]}
        )
        assert resp.status_code == 401


# ── me ────────────────────────────────────────────────────────────────────────

class TestMe:
    async def test_returns_current_user(self, client: AsyncClient):
        tokens = await _register(client, "me@example.com")
        resp = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "me@example.com"
        assert data["is_active"] is True
        assert "hashed_password" not in data

    async def test_no_token_returns_401(self, client: AsyncClient):
        resp = await client.get("/auth/me")
        assert resp.status_code == 401

    async def test_invalid_token_returns_401(self, client: AsyncClient):
        resp = await client.get(
            "/auth/me", headers={"Authorization": "Bearer garbage"}
        )
        assert resp.status_code == 401

    async def test_includes_collection_mode_default(self, client: AsyncClient):
        tokens = await _register(client, "mode@example.com")
        resp = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert resp.status_code == 200
        assert resp.json()["collection_mode"] == "playset"


# ── PATCH /auth/me ───────────────────────────────────────────────────────────

class TestUpdateMe:
    async def test_update_collection_mode(self, client: AsyncClient):
        tokens = await _register(client, "patch@example.com")
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        resp = await client.patch(
            "/auth/me",
            json={"collection_mode": "master_set"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["collection_mode"] == "master_set"

        resp = await client.get("/auth/me", headers=headers)
        assert resp.json()["collection_mode"] == "master_set"

    async def test_invalid_mode_returns_422(self, client: AsyncClient):
        tokens = await _register(client, "bad@example.com")
        resp = await client.patch(
            "/auth/me",
            json={"collection_mode": "invalid"},
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert resp.status_code == 422

    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        resp = await client.patch(
            "/auth/me", json={"collection_mode": "playset"}
        )
        assert resp.status_code == 401
