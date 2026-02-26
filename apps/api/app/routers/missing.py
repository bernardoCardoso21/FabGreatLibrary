import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.cards import PaginatedPrintings
from app.services import collection as collection_service

router = APIRouter(tags=["missing"])


@router.get("/missing", response_model=PaginatedPrintings)
async def get_missing(
    set_id: uuid.UUID | None = Query(default=None),
    card_id: uuid.UUID | None = Query(default=None),
    edition: str | None = Query(default=None),
    foiling: str | None = Query(default=None),
    rarity: str | None = Query(default=None),
    artists: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await collection_service.get_missing_printings(
        db,
        user_id=current_user.id,
        set_id=set_id,
        card_id=card_id,
        edition=edition,
        foiling=foiling,
        rarity=rarity,
        artists=artists,
        page=page,
        page_size=page_size,
    )
    return PaginatedPrintings(**result)
