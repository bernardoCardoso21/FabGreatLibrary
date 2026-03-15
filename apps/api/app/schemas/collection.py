import uuid
from enum import Enum

from pydantic import BaseModel, Field, model_validator

from app.schemas.cards import PrintingWithCard


class OwnedPrintingOut(BaseModel):
    """An owned printing with full card/set detail and qty."""

    model_config = {"from_attributes": True}

    printing: PrintingWithCard = Field(description="Full printing detail including card and set information.")
    qty: int = Field(description="Number of copies owned. Always >= 1 (rows with qty=0 are deleted).")


class UpsertItemRequest(BaseModel):
    printing_id: uuid.UUID = Field(description="ID of the printing to update.")
    qty: int = Field(ge=0, description="Desired quantity. Set to 0 to remove the printing from the collection.")


class ItemResult(BaseModel):
    """Result of a single collection mutation. qty=None means the row was deleted."""

    printing_id: uuid.UUID = Field(description="ID of the affected printing.")
    qty: int | None = Field(description="Resulting quantity after the operation. Null means the row was deleted (qty reached 0).")


class BulkAction(str, Enum):
    set_qty = "set_qty"
    increment = "increment"
    decrement = "decrement"
    mark_playset = "mark_playset"
    clear = "clear"


class BulkItemRequest(BaseModel):
    printing_id: uuid.UUID = Field(description="ID of the printing to act on.")
    action: BulkAction = Field(
        description=(
            "Action to perform: "
            "'set_qty' sets an exact quantity (requires qty); "
            "'increment' adds 1 to the current quantity; "
            "'decrement' subtracts 1 (removes if qty reaches 0); "
            "'mark_playset' sets quantity to 3; "
            "'clear' removes the printing from the collection."
        )
    )
    qty: int | None = Field(default=None, ge=0, description="Required when action is 'set_qty'. Ignored for all other actions.")

    @model_validator(mode="after")
    def qty_required_for_set_qty(self) -> "BulkItemRequest":
        if self.action == BulkAction.set_qty and self.qty is None:
            raise ValueError("qty is required when action is set_qty")
        return self


class BulkRequest(BaseModel):
    items: list[BulkItemRequest] = Field(min_length=1, description="List of actions to apply atomically. All printing IDs must exist or the entire request is rejected.")
