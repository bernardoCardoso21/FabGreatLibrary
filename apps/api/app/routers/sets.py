import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_optional_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.cards import PaginatedPlaysetCards, PaginatedPrintings, SetSummary
from app.services import cards as card_service

router = APIRouter(tags=["sets"])


@router.get(
    "/sets",
    response_model=list[SetSummary],
    summary="List all sets",
    description=(
        "Return all sets with their total printing count. "
        "When authenticated, each set also includes the number of distinct printings the user owns (`owned_count`). "
        "Unauthenticated requests receive `owned_count: null`."
    ),
)
async def get_sets(
    set_type: str | None = Query(default=None, description="Filter by category: booster, deck, or promo."),
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    rows = await card_service.list_sets_with_counts(
        db,
        user_id=current_user.id if current_user else None,
        set_type=set_type,
    )
    return [
        SetSummary(
            id=row["set"].id,
            code=row["set"].code,
            name=row["set"].name,
            image_url=row["set"].image_url,
            set_type=row["set"].set_type,
            printing_count=row["printing_count"],
            owned_count=row["owned_count"],
        )
        for row in rows
    ]


@router.get(
    "/sets/{set_id}/printings",
    response_model=PaginatedPrintings,
    summary="List printings in a set",
    description="Return a paginated list of printings belonging to the given set, with optional filters.",
    responses={404: {"description": "Set not found."}},
)
async def get_set_printings(
    set_id: uuid.UUID,
    q: str | None = Query(default=None, description="Partial card name search (case-insensitive)."),
    rarity: str | None = Query(default=None, description="Exact rarity code: C=Common, R=Rare, M=Majestic, L=Legendary, F=Fabled, T=Token, P=Promo."),
    foiling: str | None = Query(default=None, description="Foiling code: S=Standard, R=Rainbow, C=Cold, G=Gold Cold."),
    edition: str | None = Query(default=None, description="Edition code: A=Alpha, F=First, U=Unlimited, N=No specified edition."),
    hero_class: str | None = Query(default=None, description="Filter by hero class (e.g. Ninja, Wizard)."),
    talent: str | None = Query(default=None, description="Filter by talent (e.g. Shadow, Light)."),
    card_type: str | None = Query(default=None, description="Partial match on card type text (e.g. 'Attack Action')."),
    page: int = Query(default=1, ge=1, description="Page number (1-based)."),
    page_size: int = Query(default=20, ge=1, le=100, description="Number of results per page (max 100)."),
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


@router.get(
    "/sets/{set_id}/cards",
    response_model=PaginatedPlaysetCards,
    summary="List cards in a set (playset mode)",
    description=(
        "Return cards in the set grouped by card (not by printing). "
        "Each row has aggregated ownership and a target qty (1 for Heroes, 3 for others)."
    ),
    responses={404: {"description": "Set not found."}},
)
async def get_set_cards(
    set_id: uuid.UUID,
    q: str | None = Query(default=None, description="Partial card name search (case-insensitive)."),
    rarity: str | None = Query(default=None, description="Exact rarity code."),
    hero_class: str | None = Query(default=None, description="Filter by hero class."),
    talent: str | None = Query(default=None, description="Filter by talent."),
    card_type: str | None = Query(default=None, description="Partial match on card type text."),
    page: int = Query(default=1, ge=1, description="Page number (1-based)."),
    page_size: int = Query(default=20, ge=1, le=100, description="Number of results per page (max 100)."),
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    set_ = await card_service.get_set(db, set_id)
    if set_ is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Set not found")

    items, total = await card_service.list_playset_cards(
        db,
        set_id=set_id,
        user_id=current_user.id if current_user else None,
        q=q,
        rarity=rarity,
        hero_class=hero_class,
        talent=talent,
        card_type=card_type,
        page=page,
        page_size=page_size,
    )
    return PaginatedPlaysetCards(items=items, total=total, page=page, page_size=page_size)
