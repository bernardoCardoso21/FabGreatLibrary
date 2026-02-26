import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WishlistFilter(BaseModel):
    card_id: uuid.UUID | None = Field(default=None, description="Scope to printings of a specific card.")
    set_id: uuid.UUID | None = Field(default=None, description="Scope to printings in a specific set.")
    edition: str | None = Field(default=None, description="Edition code: A=Alpha, F=First, U=Unlimited, N=No specified edition.")
    foiling: str | None = Field(default=None, description="Foiling code: S=Standard, R=Rainbow, C=Cold, G=Gold Cold.")
    rarity: str | None = Field(default=None, description="Exact rarity code: C=Common, R=Rare, M=Majestic, L=Legendary, F=Fabled, T=Token, P=Promo.")
    artists: str | None = Field(default=None, description="Substring match against the artists array (case-insensitive).")


class WishlistCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255, description="Display name for the wishlist.")
    filter_json: WishlistFilter = Field(
        default_factory=WishlistFilter,
        description="Filter criteria that define which missing printings this wishlist tracks.",
    )


class WishlistOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Unique wishlist identifier.")
    name: str = Field(description="Display name for the wishlist.")
    filter_json: WishlistFilter = Field(description="Saved filter criteria.")
    created_at: datetime = Field(description="UTC timestamp when the wishlist was created.")
    updated_at: datetime = Field(description="UTC timestamp of the last update.")
