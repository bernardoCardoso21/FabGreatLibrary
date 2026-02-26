import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.models import Printing, User
from app.db.session import get_db
from app.schemas.collection import (
    BulkRequest,
    ItemResult,
    OwnedPrintingOut,
    UpsertItemRequest,
)
from app.services import collection as collection_service

router = APIRouter(prefix="/collection", tags=["collection"])


def _printing_ids_exist_stmt(ids: list[uuid.UUID]):
    return select(Printing.id).where(Printing.id.in_(ids))


@router.get(
    "/summary",
    response_model=list[OwnedPrintingOut],
    summary="Get owned printings",
    description=(
        "Return all printings the authenticated user owns, with full card and set detail. "
        "Use `set_id` to scope the results to a single set — useful for computing per-set completion."
    ),
)
async def get_summary(
    set_id: uuid.UUID | None = Query(default=None, description="Scope results to a specific set."),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await collection_service.get_collection_summary(
        db, user_id=current_user.id, set_id=set_id
    )


@router.post(
    "/items",
    response_model=ItemResult,
    summary="Upsert item quantity",
    description=(
        "Set an exact quantity for a single printing. "
        "Creates the ownership record if it does not exist. "
        "Setting `qty` to 0 removes the printing from the collection entirely."
    ),
    responses={404: {"description": "Printing not found."}},
)
async def upsert_item(
    body: UpsertItemRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    printing = (
        await db.execute(select(Printing).where(Printing.id == body.printing_id))
    ).scalar_one_or_none()
    if printing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Printing not found")

    op = await collection_service.upsert_item(
        db, user_id=current_user.id, printing_id=body.printing_id, qty=body.qty
    )
    await db.commit()
    return ItemResult(printing_id=body.printing_id, qty=op.qty if op else None)


@router.post(
    "/bulk",
    response_model=list[ItemResult],
    summary="Bulk update collection",
    description=(
        "Apply multiple collection actions atomically. "
        "All printing IDs are validated before any change is made — "
        "if any ID is invalid the entire request is rejected with 404."
    ),
    responses={404: {"description": "One or more printing IDs were not found."}},
)
async def bulk_apply(
    body: BulkRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Validate all printing IDs exist before applying anything
    requested_ids = [item.printing_id for item in body.items]
    found_ids = set(
        (await db.execute(_printing_ids_exist_stmt(requested_ids))).scalars().all()
    )
    missing = set(requested_ids) - found_ids
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Printing(s) not found: {[str(i) for i in missing]}",
        )

    results = await collection_service.bulk_apply(
        db,
        user_id=current_user.id,
        items=[item.model_dump() for item in body.items],
    )
    await db.commit()
    return [ItemResult(**r) for r in results]
