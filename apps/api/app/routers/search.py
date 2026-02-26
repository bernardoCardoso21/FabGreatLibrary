from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.cards import PaginatedPrintings
from app.services import cards as card_service

router = APIRouter(tags=["search"])


@router.get(
    "/search/printings",
    response_model=PaginatedPrintings,
    summary="Search printings across all sets",
    description=(
        "Cross-set printing search with full filter support. "
        "Unlike `GET /sets/{id}/printings`, this endpoint is not scoped to a single set "
        "and can locate a specific foiling or edition of a card regardless of which set it appears in."
    ),
)
async def search_printings(
    q: str | None = Query(default=None, description="Partial card name search (case-insensitive)."),
    rarity: str | None = Query(default=None, description="Exact rarity code: C=Common, R=Rare, M=Majestic, L=Legendary, F=Fabled, T=Token, P=Promo."),
    foiling: str | None = Query(default=None, description="Foiling code: S=Standard, R=Rainbow, C=Cold, G=Gold Cold."),
    edition: str | None = Query(default=None, description="Edition code: A=Alpha, F=First, U=Unlimited, N=No specified edition."),
    hero_class: str | None = Query(default=None, description="Filter by hero class (e.g. Ninja, Wizard)."),
    talent: str | None = Query(default=None, description="Filter by talent (e.g. Shadow, Light)."),
    card_type: str | None = Query(default=None, description="Partial match on card type text (e.g. 'Attack Action')."),
    set_code: str | None = Query(default=None, description="Filter to a specific set by set code (e.g. 'WTR')."),
    page: int = Query(default=1, ge=1, description="Page number (1-based)."),
    page_size: int = Query(default=20, ge=1, le=100, description="Number of results per page (max 100)."),
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
