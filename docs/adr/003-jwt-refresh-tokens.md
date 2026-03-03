# ADR 003 — Opaque DB-Stored Refresh Tokens

**Date:** 2026-03-03
**Status:** Accepted

---

## Context

The application uses short-lived JWT access tokens (15-minute expiry) to authenticate API requests. When the access token expires, the client needs a way to obtain a new one without forcing the user to log in again. This requires a second, longer-lived credential — a refresh token.

Two approaches were considered:

- **Stateless JWT refresh tokens:** the refresh token is itself a signed JWT. The server validates it by checking the signature; no database lookup is required.
- **Opaque refresh tokens stored in the database:** the refresh token is a random string. The server looks it up in a `refresh_tokens` table and checks expiry/revocation there.

## Decision

We use **opaque refresh tokens stored in the database**.

The rejected alternative was **stateless JWT refresh tokens**.

### Why opaque + DB

1. **Logout is real.** With stateless JWTs, a signed token is valid until it expires — there is no server-side way to invalidate it. `POST /auth/logout` would be a no-op from a security standpoint. With DB-stored tokens, logout sets `revoked_at` and the token is immediately dead, regardless of its expiry time.

2. **Token rotation is auditable.** Each `POST /auth/refresh` call issues a new token and marks the old one revoked. The `refresh_tokens` table gives a full history of active sessions, making it straightforward to add features like "log out all devices" later.

3. **Theft detection.** If a refresh token is used after it has already been rotated (i.e. used twice), the second use will find a revoked token. This is a detectable signal of token theft.

4. **The DB overhead is acceptable.** A refresh only happens when the 15-minute access token expires, so the `refresh_tokens` lookup is infrequent relative to normal API traffic. It is not on the hot path.

### Why not stateless JWT refresh

Stateless refresh tokens eliminate the database round-trip on refresh and simplify horizontal scaling (no shared session state). These benefits matter in high-traffic distributed systems. For this project — a single-instance API with Postgres already in the dependency graph — the operational simplicity gain does not outweigh the loss of server-side revocability.

## Consequences

**Positive:**
- `POST /auth/logout` genuinely revokes the session server-side.
- Expired or revoked tokens are immediately rejected.
- The schema supports future "manage active sessions" or "revoke all" features without redesign.

**Negative:**
- Every token refresh requires a DB read + write. Acceptable at this scale; would need a cache (Redis) in a high-traffic deployment.
- The `refresh_tokens` table grows over time and needs periodic cleanup of expired rows (not yet implemented; low priority at current scale).
