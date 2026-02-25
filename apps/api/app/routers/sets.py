import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_optional_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.cards import PaginatedPrintings, SetSummary
from app.services import cards as card_service

router = APIRouter(tags=["sets"])


@router.get("/sets", response_model=list[SetSummary])
async def get_sets(
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    rows = await card_service.list_sets_with_counts(
        db, user_id=current_user.id if current_user else None
    )
    return [
        SetSummary(
            id=row["set"].id,
            code=row["set"].code,
            name=row["set"].name,
            image_url=row["set"].image_url,
            printing_count=row["printing_count"],
            owned_count=row["owned_count"],
        )
        for row in rows
    ]


@router.get("/sets/{set_id}/printings", response_model=PaginatedPrintings)
async def get_set_printings(
    set_id: uuid.UUID,
    q: str | None = Query(default=None, description="Search by card name"),
    rarity: str | None = Query(default=None, description="Exact rarity code (C, R, M, L, F, T, P)"),
    foiling: str | None = Query(default=None, description="Foiling code: S=Standard, R=Rainbow, C=Cold, G=Gold Cold"),
    edition: str | None = Query(default=None, description="Edition code: A=Alpha, F=First, U=Unlimited, N=None"),
    hero_class: str | None = Query(default=None, description="Hero class (e.g. Ninja, Wizard)"),
    talent: str | None = Query(default=None, description="Talent (e.g. Shadow, Light)"),
    card_type: str | None = Query(default=None, description="Partial match on card type text"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    set_ = await card_service.get_set(db, set_id)
    if set_ is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Set not found")

    printings, total = await card_service.list_printings(
        db,
        set_id=set_id,
        q=q,
        rarity=rarity,
        foiling=foiling,
        edition=edition,
        hero_class=hero_class,
        talent=talent,
        card_type=card_type,
        page=page,
        page_size=page_size,
    )
    return PaginatedPrintings(items=printings, total=total, page=page, page_size=page_size)
