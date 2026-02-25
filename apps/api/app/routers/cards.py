import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.cards import CardDetail, PaginatedCards
from app.services import cards as card_service

router = APIRouter(tags=["cards"])


@router.get("/cards", response_model=PaginatedCards)
async def get_cards(
    name: str | None = Query(default=None),
    hero_class: str | None = Query(default=None),
    talent: str | None = Query(default=None),
    pitch: int | None = Query(default=None),
    set_code: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    items, total = await card_service.list_cards(
        db,
        name=name,
        hero_class=hero_class,
        talent=talent,
        pitch=pitch,
        set_code=set_code,
        page=page,
        page_size=page_size,
    )
    return PaginatedCards(items=items, total=total, page=page, page_size=page_size)


@router.get("/cards/{card_id}", response_model=CardDetail)
async def get_card(card_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    card = await card_service.get_card(db, card_id)
    if card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    return card
