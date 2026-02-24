"""
SQLAlchemy 2.0 ORM models for FabGreat Library.

Table summary
─────────────
users           – registered accounts
sets            – FAB product sets (e.g. "Welcome to Rathe Alpha")
cards           – abstract card concept (name, type, class, talent)
printings       – a specific physical print of a card inside a set
owned_printings – user ownership: (user, printing, foil_type) → qty
wishlists       – saved filter views; free tier capped at 1 per user
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    owned_printings: Mapped[list[OwnedPrinting]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    wishlists: Mapped[list[Wishlist]] = relationship(
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
    # Edition distinguishes "Alpha" from "Unlimited" printings of the same set
    edition: Mapped[str | None] = mapped_column(String(64), nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    printings: Mapped[list[Printing]] = relationship(back_populates="set")


# ── cards ─────────────────────────────────────────────────────────────────────

class Card(Base):
    """Abstract card concept — one row per unique card name/variant."""

    __tablename__ = "cards"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    # e.g. "Action", "Attack Action", "Equipment", "Hero", "Token", "Weapon"
    card_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    # Hero class: "Ninja", "Wizard", "Brute", etc.  Stored as "hero_class" to
    # avoid the SQL reserved word "class".
    hero_class: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    # Talent: "Shadow", "Light", "Earth", etc.
    talent: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    printings: Mapped[list[Printing]] = relationship(back_populates="card")


# ── printings ─────────────────────────────────────────────────────────────────

class Printing(Base):
    """
    A specific physical printing of a card inside a set.
    keyed by the official API's printing_id (unique string).
    One printing may be available in multiple foil types; those variants
    are tracked per-user in owned_printings.
    """

    __tablename__ = "printings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid
    )
    # Unique identifier from the official FAB API
    printing_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cards.id"), nullable=False, index=True
    )
    set_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sets.id"), nullable=False, index=True
    )
    # e.g. "Common", "Rare", "Majestic", "Legendary", "Fabled", "Token"
    rarity: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    # List of foil types available for this printing, e.g. ["standard", "rainbow", "cold"]
    foil_types: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    is_promo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    Ownership record: a user owns `qty` copies of a printing in a specific foil type.

    Invariants (enforced here + in service layer):
    - qty >= 1  (qty = 0 → delete the row, not update)
    - (user_id, printing_id, foil_type) is unique
    """

    __tablename__ = "owned_printings"
    __table_args__ = (
        UniqueConstraint("user_id", "printing_id", "foil_type", name="uq_owned_printing"),
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
    foil_type: Mapped[str] = mapped_column(String(32), nullable=False)
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

    filter_json shape (all fields optional):
    {
      "set_id": "<uuid>",
      "rarity": "Majestic",
      "hero_class": "Ninja",
      "talent": "Shadow",
      "card_type": "Action",
      "foil_type": "rainbow",
      "promo_only": true,
      "q": "search term"
    }
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
