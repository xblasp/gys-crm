import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.promotion import Promotion


class PromotionRepository:
    """Database operations for reusable promotions."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, promotion: Promotion) -> Promotion:
        self.db.add(promotion)
        self.db.flush()
        return promotion

    def get_by_id(self, promotion_id: uuid.UUID) -> Promotion | None:
        return self.db.get(Promotion, promotion_id)

    def get_by_name(self, name: str) -> Promotion | None:
        statement = select(Promotion).where(Promotion.name == name)
        return self.db.scalar(statement)

    def list(self, *, include_inactive: bool) -> list[Promotion]:
        statement = select(Promotion).order_by(Promotion.name)
        if not include_inactive:
            statement = statement.where(Promotion.is_active.is_(True))
        return list(self.db.scalars(statement))

    def save(self, promotion: Promotion) -> Promotion:
        self.db.add(promotion)
        self.db.commit()
        self.db.refresh(promotion)
        return promotion
