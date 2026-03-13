"""
Import card data from the-fab-cube/flesh-and-blood-cards dataset.

Downloads card.json and set.json from a pinned GitHub release tag and upserts
all sets, cards, and printings into the database.  Safe to re-run — all
operations are idempotent (INSERT ... ON CONFLICT DO UPDATE).

Usage:
    python -m scripts.import_cards                   # uses CARDS_DATA_VERSION from config
    python -m scripts.import_cards --version v8.1.0  # explicit version override

Data alignment notes:
  - Set.code         is the conflict key for sets
  - Card.source_id   is the conflict key for cards  (the dataset's unique_id)
  - Printing.printing_id is the conflict key for printings (the dataset's unique_id)
  - Foiling codes: S=Standard, R=Rainbow, C=Cold, G=Gold Cold
  - Edition codes:  A=Alpha, F=First, U=Unlimited, N=No specified edition
"""

import argparse
import asyncio
import uuid
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.config import settings
from app.db.models import Card, Printing, Set
from app.db.session import AsyncSessionLocal

# ── constants ─────────────────────────────────────────────────────────────────

_RAW_BASE = (
    "https://raw.githubusercontent.com/the-fab-cube/flesh-and-blood-cards"
    "/{version}/json/english/{filename}"
)

# Values from the-fab-cube types
_KNOWN_CLASSES = {
    "Generic", "Adjudicator", "Assassin", "Bard", "Brute", "Guardian",
    "Illusionist", "Mechanologist", "Merchant", "Necromancer", "Ninja",
    "Pirate", "Ranger", "Runeblade", "Shapeshifter", "Thief", "Warrior", "Wizard",
}
_KNOWN_TALENTS = {
    "Chaos", "Draconic", "Earth", "Elemental", "Ice", "Light", "Lightning",
    "Mystic", "Revered", "Reviled", "Royal", "Shadow",
}

# ── download ──────────────────────────────────────────────────────────────────

def _download(version: str, filename: str) -> list:
    url = _RAW_BASE.format(version=version, filename=filename)
    print(f"  Downloading {url} ...")
    with httpx.Client(timeout=120.0, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()
    data = resp.json()
    print(f"  ->{len(data):,} records")
    return data


# ── helpers ───────────────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _make_uuid() -> uuid.UUID:
    return uuid.uuid4()


def _derive_class(types: list[str]) -> str | None:
    return next((t for t in types if t in _KNOWN_CLASSES), None)


def _derive_talent(types: list[str]) -> str | None:
    return next((t for t in types if t in _KNOWN_TALENTS), None)


def _parse_pitch(raw: str) -> int | None:
    try:
        return int(raw) if raw else None
    except (ValueError, TypeError):
        return None


_DECK_KEYWORDS = ["deck", "classic battles", "first strike"]
_PROMO_KEYWORDS = ["promo", "tokens", "prize cards"]


def _classify_set(name: str) -> str:
    lower = name.lower()
    if any(k in lower for k in _DECK_KEYWORDS):
        return "deck"
    if any(k in lower for k in _PROMO_KEYWORDS):
        return "promo"
    return "booster"


def _chunks(lst: list, n: int):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


# ── upsert helpers ────────────────────────────────────────────────────────────

async def _upsert_sets(session, sets_data: list) -> dict[str, uuid.UUID]:
    """Upsert all sets; return {code: internal_id} mapping."""
    print("\nUpserting sets ...")
    now = _now()
    rows = [
        {
            "id": _make_uuid(),
            "code": s["id"],
            "name": s["name"],
            "source_id": s["unique_id"],
            "set_type": _classify_set(s["name"]),
            "created_at": now,
        }
        for s in sets_data
    ]
    for chunk in _chunks(rows, 200):
        excluded = pg_insert(Set.__table__).excluded
        stmt = (
            pg_insert(Set.__table__)
            .values(chunk)
            .on_conflict_do_update(
                index_elements=["code"],
                set_={"name": excluded.name,
                      "source_id": excluded.source_id,
                      "set_type": excluded.set_type},
            )
        )
        await session.execute(stmt)
    await session.flush()

    result = await session.execute(select(Set.code, Set.id))
    mapping = {row.code: row.id for row in result}
    print(f"  ->{len(mapping):,} sets in DB")
    return mapping


async def _upsert_cards(session, cards_data: list) -> dict[str, uuid.UUID]:
    """Upsert all cards; return {source_id: internal_id} mapping."""
    print("\nUpserting cards ...")
    now = _now()
    rows = []
    for card in cards_data:
        types = card.get("types", [])
        rows.append({
            "id": _make_uuid(),
            "source_id": card["unique_id"],
            "name": card["name"],
            "card_type": card.get("type_text", ""),
            "hero_class": _derive_class(types),
            "talent": _derive_talent(types),
            "pitch": _parse_pitch(card.get("pitch", "")),
            "created_at": now,
        })

    for chunk in _chunks(rows, 200):
        excluded = pg_insert(Card.__table__).excluded
        stmt = (
            pg_insert(Card.__table__)
            .values(chunk)
            .on_conflict_do_update(
                index_elements=["source_id"],
                set_={
                    "name": excluded.name,
                    "card_type": excluded.card_type,
                    "hero_class": excluded.hero_class,
                    "talent": excluded.talent,
                    "pitch": excluded.pitch,
                },
            )
        )
        await session.execute(stmt)
    await session.flush()

    result = await session.execute(
        select(Card.source_id, Card.id).where(Card.source_id.isnot(None))
    )
    mapping = {row.source_id: row.id for row in result}
    print(f"  ->{len(mapping):,} cards in DB")
    return mapping


async def _upsert_printings(
    session,
    cards_data: list,
    set_map: dict[str, uuid.UUID],
    card_map: dict[str, uuid.UUID],
) -> int:
    """Upsert all printings; return count."""
    print("\nUpserting printings ...")
    now = _now()
    rows = []
    skipped = 0

    for card in cards_data:
        card_id = card_map.get(card["unique_id"])
        if card_id is None:
            skipped += 1
            continue
        for p in card.get("printings", []):
            set_id = set_map.get(p["set_id"])
            if set_id is None:
                skipped += 1
                continue
            rows.append({
                "id": _make_uuid(),
                "printing_id": p["unique_id"],
                "card_id": card_id,
                "set_id": set_id,
                "edition": p.get("edition", "N"),
                "foiling": p.get("foiling", "S"),
                "rarity": p.get("rarity", "C"),
                "artists": p.get("artists", []),
                "art_variations": p.get("art_variations", []),
                "image_url": p.get("image_url") or None,
                "tcgplayer_product_id": p.get("tcgplayer_product_id") or None,
                "tcgplayer_url": p.get("tcgplayer_url") or None,
                "created_at": now,
            })

    total = len(rows)
    upserted = 0
    for chunk in _chunks(rows, 500):
        excluded = pg_insert(Printing.__table__).excluded
        stmt = (
            pg_insert(Printing.__table__)
            .values(chunk)
            .on_conflict_do_update(
                index_elements=["printing_id"],
                set_={
                    "card_id": excluded.card_id,
                    "set_id": excluded.set_id,
                    "edition": excluded.edition,
                    "foiling": excluded.foiling,
                    "rarity": excluded.rarity,
                    "artists": excluded.artists,
                    "art_variations": excluded.art_variations,
                    "image_url": excluded.image_url,
                    "tcgplayer_product_id": excluded.tcgplayer_product_id,
                    "tcgplayer_url": excluded.tcgplayer_url,
                },
            )
        )
        await session.execute(stmt)
        upserted += len(chunk)
        await session.flush()
        print(f"  ... {upserted:,} / {total:,}", end="\r")

    print(f"  ->{upserted:,} printings upserted ({skipped} skipped — unknown set/card)")
    return upserted


# ── main ──────────────────────────────────────────────────────────────────────

async def import_data(version: str) -> None:
    print(f"\n=== Importing FAB card data ({version}) ===")

    sets_data = _download(version, "set.json")
    cards_data = _download(version, "card.json")

    async with AsyncSessionLocal() as session:
        set_map = await _upsert_sets(session, sets_data)
        card_map = await _upsert_cards(session, cards_data)
        printing_count = await _upsert_printings(session, cards_data, set_map, card_map)
        await session.commit()

    print(f"\nImport complete:")
    print(f"  Sets     : {len(set_map):>6,}")
    print(f"  Cards    : {len(card_map):>6,}")
    print(f"  Printings: {printing_count:>6,}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import FAB card data")
    parser.add_argument(
        "--version",
        default=settings.cards_data_version,
        help="Dataset release tag (default: %(default)s)",
    )
    args = parser.parse_args()
    asyncio.run(import_data(args.version))
