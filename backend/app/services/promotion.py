import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models.promotion import Promotion
from backend.app.repositories.promotion import PromotionRepository
from backend.app.schemas.promotion import PromotionCreate, PromotionUpdate, validate_discount_value


class PromotionService:
    """Business rules for the promotion catalogue."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = PromotionRepository(db)

    def create_promotion(self, data: PromotionCreate) -> Promotion:
        if self.repository.get_by_name(data.name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A promotion with this name already exists.",
            )
        promotion = Promotion(**data.model_dump())
        self.repository.create(promotion)
        try:
            return self.repository.save(promotion)
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A promotion with this name already exists.",
            ) from exc

    def list_promotions(self, *, include_inactive: bool) -> list[Promotion]:
        return self.repository.list(include_inactive=include_inactive)

    def get_promotion(self, promotion_id: uuid.UUID) -> Promotion:
        promotion = self.repository.get_by_id(promotion_id)
        if promotion is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Promotion not found.",
            )
        return promotion

    def update_promotion(self, promotion_id: uuid.UUID, data: PromotionUpdate) -> Promotion:
        promotion = self.get_promotion(promotion_id)
        values = data.model_dump(exclude_unset=True)
        if "name" in values:
            existing_promotion = self.repository.get_by_name(values["name"])
            if existing_promotion and existing_promotion.id != promotion.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A promotion with this name already exists.",
                )

        discount_type = values.get("discount_type", promotion.discount_type)
        discount_value = values.get("discount_value", promotion.discount_value)
        validate_discount_value(discount_type, discount_value)
        for field_name, value in values.items():
            setattr(promotion, field_name, value)
        return self.repository.save(promotion)

    def deactivate_promotion(self, promotion_id: uuid.UUID) -> None:
        promotion = self.get_promotion(promotion_id)
        promotion.is_active = False
        self.repository.save(promotion)
