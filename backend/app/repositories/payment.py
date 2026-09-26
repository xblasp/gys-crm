import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from backend.app.models.payment import Payment


class PaymentRepository:
    """Database operations for payments and financial transactions."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, payment: Payment) -> Payment:
        self.db.add(payment)
        self.db.flush()
        return payment

    def get_by_id(self, payment_id: uuid.UUID) -> Payment | None:
        return self.db.get(Payment, payment_id)

    def list_by_client(self, client_id: uuid.UUID) -> list[Payment]:
        statement = (
            select(Payment)
            .where(Payment.client_id == client_id)
            .order_by(desc(Payment.payment_date))
        )
        return list(self.db.scalars(statement))

    def list_all(
        self,
        *,
        branch: str | None = None,
        period_month: str | None = None,
        payment_method: str | None = None,
        concept: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Payment]:
        statement = select(Payment).order_by(desc(Payment.payment_date)).offset(offset).limit(limit)
        if branch and branch != "Todas":
            statement = statement.where(Payment.branch == branch)
        if period_month:
            statement = statement.where(Payment.period_month == period_month)
        if payment_method:
            statement = statement.where(Payment.payment_method == payment_method)
        if concept:
            statement = statement.where(Payment.concept == concept)
        if status:
            statement = statement.where(Payment.status == status)
        return list(self.db.scalars(statement))

    def get_total_revenue_for_month(self, period_month: str, branch: str | None = None) -> Decimal:
        statement = (
            select(func.coalesce(func.sum(Payment.amount), Decimal("0.00")))
            .where(
                Payment.period_month == period_month,
                Payment.status == "completed",
            )
        )
        if branch and branch != "Todas":
            statement = statement.where(Payment.branch == branch)
        return Decimal(str(self.db.scalar(statement) or "0.00"))

    def save(self, payment: Payment) -> Payment:
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment
