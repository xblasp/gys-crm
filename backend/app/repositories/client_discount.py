import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.client_discount import ClientDiscount


class ClientDiscountRepository:
    """Database operations for client discount history."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, discount: ClientDiscount) -> ClientDiscount:
        self.db.add(discount)
        self.db.flush()
        return discount

    def list_by_client(self, client_id: uuid.UUID) -> list[ClientDiscount]:
        statement = (
            select(ClientDiscount)
            .where(ClientDiscount.client_id == client_id)
            .order_by(ClientDiscount.applied_at.desc())
        )
        return list(self.db.scalars(statement))

    def save(self, discount: ClientDiscount) -> ClientDiscount:
        self.db.add(discount)
        self.db.commit()
        self.db.refresh(discount)
        return discount
