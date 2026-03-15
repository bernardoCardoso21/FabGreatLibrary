import uuid

from pydantic import BaseModel, Field


class SetOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    code: str
    name: str
    image_url: str | None
    set_type: str


class SetSummary(BaseModel):
    """Set with aggregate counts; owned_count is None when unauthenticated."""

    id: uuid.UUID = Field(description="Unique set identifier.")
    code: str = Field(description="Short set code (e.g. 'WTR', 'ARC').")
    name: str = Field(description="Full set name (e.g. 'Welcome to Rathe').")
    image_url: str | None = Field(description="URL to the set's logo or key art, if available.")
    set_type: str = Field(description="Category: booster, deck, or promo.")
    printing_count: int = Field(description="Total number of distinct printings (card x edition x foiling) in this set.")
    owned_count: int | None = Field(
        description="Number of those printings the authenticated user owns at least one copy of. "
                    "Null when the request is unauthenticated."
    )


class CardListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID = Field(description="Unique card identifier.")
    name: str = Field(description="Card name.")
    card_type: str = Field(description="Card type text (e.g. 'Action', 'Attack Action — Ninja').")
    hero_class: str | None = Field(description="Hero class this card belongs to (e.g. 'Ninja', 'Wizard'). Null for generic cards.")
    talent: str | None = Field(description="Talent affinity (e.g. 'Shadow', 'Light'). Null if the card has no talent.")
    pitch: int | None = Field(description="Pitch value (0–3). Null for cards that cannot be pitched.")


class PrintingOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    printing_id: str
    set: SetOut
    edition: str
    foiling: str
    rarity: str
    artists: list
    art_variations: list
    image_url: str | None
    tcgplayer_product_id: str | None
    tcgplayer_url: str | None


class PrintingWithCard(BaseModel):
    """Printing with nested card and set info — used in list/search endpoints."""

    model_config = {"from_attributes": True}

    id: uuid.UUID = Field(description="Unique printing identifier.")
    printing_id: str = Field(description="Dataset-stable printing identifier (e.g. 'WTR000').")
    edition: str = Field(description="Edition code: A=Alpha, F=First, U=Unlimited, N=No specified edition.")
    foiling: str = Field(description="Foiling code: S=Standard, R=Rainbow, C=Cold, G=Gold Cold.")
    rarity: str = Field(description="Rarity code: C=Common, R=Rare, M=Majestic, L=Legendary, F=Fabled, T=Token, P=Promo.")
    artists: list = Field(description="List of artist names credited on this printing.")
    art_variations: list = Field(description="List of art variation identifiers, if the card has alternate art in the same printing.")
    image_url: str | None = Field(description="URL to the card image for this specific printing, if available.")
    tcgplayer_product_id: str | None = Field(description="TCGplayer product ID for this printing, if available.")
    tcgplayer_url: str | None = Field(description="Direct TCGplayer listing URL for this printing, if available.")
    card: CardListItem = Field(description="The card this printing belongs to.")
    set: SetOut = Field(description="The set this printing belongs to.")


class CardDetail(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    card_type: str
    hero_class: str | None
    talent: str | None
    pitch: int | None
    printings: list[PrintingOut]


class PlaysetCardItem(BaseModel):
    """Card-level row for playset mode — aggregated ownership across all printings."""

    id: uuid.UUID = Field(description="Unique card identifier.")
    name: str = Field(description="Card name.")
    card_type: str = Field(description="Card type text.")
    hero_class: str | None = Field(description="Hero class (e.g. 'Ninja'). Null for generic cards.")
    talent: str | None = Field(description="Talent affinity. Null if none.")
    pitch: int | None = Field(description="Pitch value (1-3). Null for non-pitchable cards.")
    rarity: str = Field(description="Rarity code of the first printing in this set.")
    image_url: str | None = Field(description="Image URL from the first printing in this set.")
    target: int = Field(description="Number of copies needed: 1 for Heroes, 3 for everything else.")
    owned_qty: int | None = Field(description="Total copies owned across all printings. Null when unauthenticated.")
    default_printing_id: str = Field(description="UUID of a representative printing (for +1 upsert).")


class PaginatedPlaysetCards(BaseModel):
    items: list[PlaysetCardItem] = Field(description="Cards on the current page.")
    total: int = Field(description="Total number of cards matching the current filters.")
    page: int = Field(description="Current page number (1-based).")
    page_size: int = Field(description="Number of items per page.")


class PaginatedCards(BaseModel):
    items: list[CardListItem] = Field(description="Cards on the current page.")
    total: int = Field(description="Total number of cards matching the current filters.")
    page: int = Field(description="Current page number (1-based).")
    page_size: int = Field(description="Number of items per page.")


class PaginatedPrintings(BaseModel):
    items: list[PrintingWithCard] = Field(description="Printings on the current page.")
    total: int = Field(description="Total number of printings matching the current filters.")
    page: int = Field(description="Current page number (1-based).")
    page_size: int = Field(description="Number of items per page.")
