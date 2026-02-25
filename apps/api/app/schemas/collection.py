import uuid
from enum import Enum

from pydantic import BaseModel, Field, model_validator

from app.schemas.cards import PrintingWithCard


class OwnedPrintingOut(BaseModel):
    """An owned printing with full card/set detail and qty."""

    model_config = {"from_attributes": True}

    printing: PrintingWithCard
    qty: int


class UpsertItemRequest(BaseModel):
    printing_id: uuid.UUID
    qty: int = Field(ge=0, description="Quantity to set. 0 deletes the row.")


class ItemResult(BaseModel):
    """Result of a single collection mutation. qty=None means the row was deleted."""

    printing_id: uuid.UUID
    qty: int | None


class BulkAction(str, Enum):
    set_qty = "set_qty"
    increment = "increment"
    mark_playset = "mark_playset"
    clear = "clear"


class BulkItemRequest(BaseModel):
    printing_id: uuid.UUID
    action: BulkAction
    qty: int | None = Field(default=None, ge=0, description="Required for set_qty action.")

    @model_validator(mode="after")
    def qty_required_for_set_qty(self) -> "BulkItemRequest":
        if self.action == BulkAction.set_qty and self.qty is None:
            raise ValueError("qty is required when action is set_qty")
        return self


class BulkRequest(BaseModel):
    items: list[BulkItemRequest] = Field(min_length=1)
