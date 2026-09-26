import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.models.client_discount import ClientDiscount
from backend.app.repositories.client import ClientRepository
from backend.app.repositories.client_discount import ClientDiscountRepository
from backend.app.repositories.promotion import PromotionRepository
from backend.app.schemas.promotion import ClientDiscountCreate


class ClientDiscountService:
    """Records promotion applications without losing their original terms."""

    def __init__(self, db: Session) -> None:
        self.client_repository = ClientRepository(db)
        self.discount_repository = ClientDiscountRepository(db)
        self.promotion_repository = PromotionRepository(db)

    def apply_discount(self, client_id: uuid.UUID, data: ClientDiscountCreate) -> ClientDiscount:
        if self.client_repository.get_by_id(client_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found.",
            )

        values = data.model_dump()
        if data.promotion_id:
            promotion = self.promotion_repository.get_by_id(data.promotion_id)
            if promotion is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Promotion not found.",
                )
            if not promotion.is_active:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Promotion is inactive and cannot be applied.",
                )
            values.update(
                promotion_id=promotion.id,
                promotion_name=promotion.name,
                discount_type=promotion.discount_type,
                discount_value=promotion.discount_value,
            )

        discount = ClientDiscount(
            client_id=client_id,
            promotion_id=values["promotion_id"],
            promotion_name=values["promotion_name"],
            discount_type=values["discount_type"],
            discount_value=values["discount_value"],
            applies_to=values["applies_to"],
            reason=values["reason"],
            applied_by=values["applied_by"],
        )
        self.discount_repository.create(discount)
        return self.discount_repository.save(discount)

    def list_discounts(self, client_id: uuid.UUID) -> list[ClientDiscount]:
        if self.client_repository.get_by_id(client_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found.",
            )
        return self.discount_repository.list_by_client(client_id)
