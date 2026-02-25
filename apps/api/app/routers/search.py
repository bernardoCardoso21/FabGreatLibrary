from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.cards import PaginatedPrintings
from app.services import cards as card_service

router = APIRouter(tags=["search"])


@router.get("/search/printings", response_model=PaginatedPrintings)
async def search_printings(
    q: str | None = Query(default=None, description="Search by card name"),
    rarity: str | None = Query(default=None, description="Exact rarity code (C, R, M, L, F, T, P)"),
    foiling: str | None = Query(default=None, description="Foiling code: S=Standard, R=Rainbow, C=Cold, G=Gold Cold"),
    edition: str | None = Query(default=None, description="Edition code: A=Alpha, F=First, U=Unlimited, N=None"),
    hero_class: str | None = Query(default=None, description="Hero class (e.g. Ninja, Wizard)"),
    talent: str | None = Query(default=None, description="Talent (e.g. Shadow, Light)"),
    card_type: str | None = Query(default=None, description="Partial match on card type text"),
    set_code: str | None = Query(default=None, description="Filter to a specific set by code"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    printings, total = await card_service.list_printings(
        db,
        q=q,
        rarity=rarity,
        foiling=foiling,
        edition=edition,
        hero_class=hero_class,
        talent=talent,
        card_type=card_type,
        set_code=set_code,
        page=page,
        page_size=page_size,
    )
    return PaginatedPrintings(items=printings, total=total, page=page, page_size=page_size)
