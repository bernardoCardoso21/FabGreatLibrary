import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.cards import PaginatedPrintings
from app.services import collection as collection_service

router = APIRouter(tags=["missing"])


@router.get(
    "/missing",
    response_model=PaginatedPrintings,
    summary="List unowned printings",
    description=(
        "Return a paginated list of printings that exist in the catalog but are not yet owned "
        "by the authenticated user. Supports the same filters as the set printings endpoint. "
        "Typically used to build a want list or identify collection gaps."
    ),
)
async def get_missing(
    set_id: uuid.UUID | None = Query(default=None, description="Scope to printings in a specific set."),
    card_id: uuid.UUID | None = Query(default=None, description="Scope to printings of a specific card."),
    edition: str | None = Query(default=None, description="Edition code: A=Alpha, F=First, U=Unlimited, N=No specified edition."),
    foiling: str | None = Query(default=None, description="Foiling code: S=Standard, R=Rainbow, C=Cold, G=Gold Cold."),
    rarity: str | None = Query(default=None, description="Exact rarity code: C=Common, R=Rare, M=Majestic, L=Legendary, F=Fabled, T=Token, P=Promo."),
    artists: str | None = Query(default=None, description="Substring match against the artists array (case-insensitive)."),
    page: int = Query(default=1, ge=1, description="Page number (1-based)."),
    page_size: int = Query(default=20, ge=1, le=100, description="Number of results per page (max 100)."),
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
