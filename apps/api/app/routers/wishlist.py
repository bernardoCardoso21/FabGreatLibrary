import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.wishlist import WishlistCreate, WishlistOut
from app.services import wishlist as wishlist_service
from app.services.wishlist import WishlistLimitError, WishlistNotFoundError

router = APIRouter(prefix="/wishlists", tags=["wishlists"])


@router.post(
    "",
    response_model=WishlistOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a wishlist",
    description=(
        "Save a named filter as a wishlist. Free-tier users may only have **one** wishlist at a time. "
        "Delete the existing wishlist before creating a new one."
    ),
    responses={402: {"description": "Free-tier limit reached — delete the existing wishlist first."}},
)
async def create_wishlist(
    body: WishlistCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        wishlist = await wishlist_service.create_wishlist(
            db,
            user_id=current_user.id,
            name=body.name,
            filter_json=body.filter_json.model_dump(exclude_none=True),
        )
    except WishlistLimitError as exc:
        raise HTTPException(status_code=402, detail=str(exc))
    await db.commit()
    return wishlist


@router.get(
    "",
    response_model=list[WishlistOut],
    summary="List wishlists",
    description="Return all wishlists belonging to the authenticated user, ordered by creation date.",
)
async def list_wishlists(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await wishlist_service.list_wishlists(db, user_id=current_user.id)


@router.delete(
    "/{wishlist_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a wishlist",
    description="Permanently delete a wishlist. This frees the slot so a new wishlist can be created.",
    responses={404: {"description": "Wishlist not found or belongs to a different user."}},
)
async def delete_wishlist(
    wishlist_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await wishlist_service.delete_wishlist(
            db, user_id=current_user.id, wishlist_id=wishlist_id
        )
    except WishlistNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist not found"
        )
    await db.commit()
