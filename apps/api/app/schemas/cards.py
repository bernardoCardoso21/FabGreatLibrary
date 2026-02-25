import uuid

from pydantic import BaseModel


class SetOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    code: str
    name: str
    image_url: str | None


class SetSummary(BaseModel):
    """Set with aggregate counts; owned_count is None when unauthenticated."""

    id: uuid.UUID
    code: str
    name: str
    image_url: str | None
    printing_count: int
    owned_count: int | None


class CardListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    card_type: str
    hero_class: str | None
    talent: str | None
    pitch: int | None


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

    id: uuid.UUID
    printing_id: str
    edition: str
    foiling: str
    rarity: str
    artists: list
    art_variations: list
    image_url: str | None
    tcgplayer_product_id: str | None
    tcgplayer_url: str | None
    card: CardListItem
    set: SetOut


class CardDetail(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    card_type: str
    hero_class: str | None
    talent: str | None
    pitch: int | None
    printings: list[PrintingOut]


class PaginatedCards(BaseModel):
    items: list[CardListItem]
    total: int
    page: int
    page_size: int


class PaginatedPrintings(BaseModel):
    items: list[PrintingWithCard]
    total: int
    page: int
    page_size: int
