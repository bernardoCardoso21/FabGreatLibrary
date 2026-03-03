# ADR 001 — Strategy B: One Printing Row per Foiling

**Date:** 2026-03-03
**Status:** Accepted

---

## Context

The Flesh & Blood card game issues each card in multiple foiling variants (Standard, Rainbow, Cold, Gold Cold) and across multiple set editions (Alpha, First, Unlimited, No edition). The source dataset — [the-fab-cube/flesh-and-blood-cards](https://github.com/the-fab-cube/flesh-and-blood-cards) — already represents each foiling variant as a distinct record with its own stable `unique_id`.

We needed to decide how to model this in the `printings` table and how to track user ownership.

Two strategies were on the table:

- **Strategy A:** One `Printing` row per (card, set, edition) combination with a JSON array column (`foil_types`) listing available foiling variants. Ownership would then need a separate `foil_type` column on `owned_printings`.
- **Strategy B:** One `Printing` row per (card, set, edition, foiling) combination — mirroring the source dataset directly. Ownership is tracked by `(user_id, printing_id)` alone.

## Decision

We adopted **Strategy B**.

The source dataset's `unique_id` is already scoped to a single foiling variant, making Strategy B a direct structural mirror of the data we import. This means:

1. The import script (`scripts/import_cards.py`) can use `unique_id` as a natural upsert key with no transformation.
2. Ownership is a simple unique constraint on `(user_id, printing_id)` — no additional `foil_type` discriminator column is needed on `owned_printings`.
3. Filtering printings by foiling (`?foiling=R`) is a plain equality filter on a regular column, not a JSON containment query.
4. Each printing row carries its own `image_url`, `rarity`, and `artists` — values that can legitimately differ between foiling variants of the same card.

## Consequences

**Positive:**
- No JSON array querying; all filters use standard SQL equality/range operators.
- Ownership model is minimal: one unique constraint, one `qty` integer, done.
- Import is idempotent (`ON CONFLICT (printing_id) DO UPDATE`) with no fan-out logic needed.

**Negative:**
- The `printings` table is larger (~14,000 rows for the current dataset vs ~5,000 under Strategy A). This is not a practical concern at this scale.
- To answer "what foiling variants exist for this card?" you query `printings` filtered by `card_id`, rather than reading a single JSON field. The query is straightforward but slightly less obvious to a new reader.
