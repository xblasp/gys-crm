import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.promotion import PromotionCreate, PromotionRead, PromotionUpdate
from backend.app.services.promotion import PromotionService

router = APIRouter(prefix="/promotions", tags=["Promotions"])

DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post("", response_model=PromotionRead, status_code=status.HTTP_201_CREATED)
def create_promotion(data: PromotionCreate, db: DatabaseSession) -> PromotionRead:
    return PromotionService(db).create_promotion(data)


@router.get("", response_model=list[PromotionRead])
def list_promotions(
    db: DatabaseSession,
    include_inactive: bool = Query(default=False),
) -> list[PromotionRead]:
    return PromotionService(db).list_promotions(include_inactive=include_inactive)


@router.get("/{promotion_id}", response_model=PromotionRead)
def get_promotion(promotion_id: uuid.UUID, db: DatabaseSession) -> PromotionRead:
    return PromotionService(db).get_promotion(promotion_id)


@router.patch("/{promotion_id}", response_model=PromotionRead)
def update_promotion(
    promotion_id: uuid.UUID,
    data: PromotionUpdate,
    db: DatabaseSession,
) -> PromotionRead:
    return PromotionService(db).update_promotion(promotion_id, data)


@router.delete("/{promotion_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_promotion(promotion_id: uuid.UUID, db: DatabaseSession) -> Response:
    PromotionService(db).deactivate_promotion(promotion_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
