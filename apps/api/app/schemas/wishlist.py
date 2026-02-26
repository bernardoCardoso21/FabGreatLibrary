import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WishlistFilter(BaseModel):
    card_id: uuid.UUID | None = None
    set_id: uuid.UUID | None = None
    edition: str | None = None
    foiling: str | None = None
    rarity: str | None = None
    artists: str | None = None  # substring match against JSON array


class WishlistCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    filter_json: WishlistFilter = Field(default_factory=WishlistFilter)


class WishlistOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    filter_json: WishlistFilter
    created_at: datetime
    updated_at: datetime
