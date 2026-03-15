"""
SQLAlchemy 2.0 ORM models for FabGreat Library.

Table summary
─────────────
users           – registered accounts
sets            – FAB product sets (e.g. "Welcome to Rathe")
cards           – abstract card concept (name, type, class, talent, pitch)
printings       – one row per (card, set, edition, foiling) combination
owned_printings – user ownership: (user, printing) → qty
wishlists       – saved filter views; free tier capped at 1 per user
refresh_tokens  – opaque refresh tokens for JWT auth

Data source alignment (Strategy B)
───────────────────────────────────
Matches the-fab-cube/flesh-and-blood-cards dataset structure.
Each printing row represents one specific foiling of a card in a set edition.
source_id fields store the dataset's stable unique_id for upsert-based imports.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


# ── helpers ───────────────────────────────────────────────────────────────────

def _uuid() -> uuid.UUID:
    return uuid.uuid4()


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── users ─────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    collection_mode: Mapped[str] = mapped_column(
        String(16), nullable=False, default="playset"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    owned_printings: Mapped[list[OwnedPrinting]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    wishlists: Mapped[list[Wishlist]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


# ── sets ──────────────────────────────────────────────────────────────────────

class Set(Base):
    __tablename__ = "sets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid
    )
    # Short code from the official API, e.g. "WTR", "ARC"
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Stable unique_id from the-fab-cube dataset; used as upsert key during imports
    source_id: Mapped[str | None] = mapped_column(String(21), nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    set_type: Mapped[str] = mapped_column(String(16), nullable=False, default="booster", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    printings: Mapped[list[Printing]] = relationship(back_populates="set")


# ── cards ─────────────────────────────────────────────────────────────────────

class Card(Base):
    """Abstract card concept — one row per unique card name/pitch combination."""

    __tablename__ = "cards"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid
    )
    # Stable unique_id from the-fab-cube dataset; unique so it can be the upsert key
    source_id: Mapped[str | None] = mapped_column(
        String(21), unique=True, nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    # Full type text, e.g. "Ninja Action Attack"
    card_type: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    # Hero class: "Ninja", "Wizard", "Brute", etc.  Stored as "hero_class" to
    # avoid the SQL reserved word "class".
    hero_class: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    # Talent: "Shadow", "Light", "Earth", etc.
    talent: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    # Pitch value: 1 (red), 2 (yellow), 3 (blue), None for non-pitchable cards
    pitch: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    printings: Mapped[list[Printing]] = relationship(back_populates="card")


# ── printings ─────────────────────────────────────────────────────────────────

class Printing(Base):
    """
    One specific foiling of a card in a set edition.

    Aligns with the-fab-cube dataset: each printing row = one (card, set, edition,
    foiling) combination. The source dataset's unique_id is stored as printing_id
    and is the stable upsert key.

    Foiling codes (from dataset):
      S = Standard (non-foil)
      R = Rainbow Foil
      C = Cold Foil
      G = Gold Cold Foil

    Edition codes:
      A = Alpha  |  F = First  |  U = Unlimited  |  N = No specified edition
    """

    __tablename__ = "printings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid
    )
    # Stable unique_id from the-fab-cube dataset
    printing_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cards.id"), nullable=False, index=True
    )
    set_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sets.id"), nullable=False, index=True
    )
    # Edition of this specific printing (A/F/U/N)
    edition: Mapped[str] = mapped_column(String(4), nullable=False, default="N")
    # Single foiling type for this printing (S/R/C/G)
    foiling: Mapped[str] = mapped_column(String(4), nullable=False, default="S")
    # e.g. "C", "R", "M", "L", "F", "T", "P"
    rarity: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    # Artist name(s) for this printing
    artists: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # Art variation codes, e.g. ["EA", "AA"]
    art_variations: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    tcgplayer_product_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tcgplayer_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    card: Mapped[Card] = relationship(back_populates="printings")
    set: Mapped[Set] = relationship(back_populates="printings")
    owned_by: Mapped[list[OwnedPrinting]] = relationship(
        back_populates="printing", cascade="all, delete-orphan"
    )


# ── owned_printings ───────────────────────────────────────────────────────────

class OwnedPrinting(Base):
    """
    Ownership record: a user owns `qty` copies of a specific printing.

    The foiling type is now encoded in the Printing row itself (Strategy B),
    so the unique key is simply (user_id, printing_id).

    Invariants:
    - qty >= 1  (qty = 0 → delete the row, not update)
    - (user_id, printing_id) is unique
    """

    __tablename__ = "owned_printings"
    __table_args__ = (
        UniqueConstraint("user_id", "printing_id", name="uq_owned_printing"),
        CheckConstraint("qty >= 1", name="ck_owned_printing_qty_positive"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    printing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("printings.id"), nullable=False, index=True
    )
    qty: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, onupdate=_now
    )

    user: Mapped[User] = relationship(back_populates="owned_printings")
    printing: Mapped[Printing] = relationship(back_populates="owned_by")


# ── wishlists ─────────────────────────────────────────────────────────────────

class Wishlist(Base):
    """
    A saved filter view.  Free-tier users are limited to 1 wishlist;
    this is enforced in the service layer (not a DB constraint).
    """

    __tablename__ = "wishlists"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    filter_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, onupdate=_now
    )

    user: Mapped[User] = relationship(back_populates="wishlists")


# ── refresh_tokens ────────────────────────────────────────────────────────────

class RefreshToken(Base):
    """
    Opaque refresh token stored in the DB.
    Revoked by setting revoked_at; expired rows can be purged by a cron job.
    """

    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid
    )
    token: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    user: Mapped[User] = relationship(back_populates="refresh_tokens")
