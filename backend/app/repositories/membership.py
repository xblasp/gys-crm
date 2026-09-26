import uuid
from datetime import date, timedelta

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.models.membership import Membership


class MembershipRepository:
    """Database operations for memberships and monthly plans."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, membership: Membership) -> Membership:
        self.db.add(membership)
        self.db.flush()
        return membership

    def get_by_id(self, membership_id: uuid.UUID) -> Membership | None:
        return self.db.get(Membership, membership_id)

    def list_by_client(self, client_id: uuid.UUID) -> list[Membership]:
        statement = (
            select(Membership)
            .where(Membership.client_id == client_id)
            .order_by(desc(Membership.start_date))
        )
        return list(self.db.scalars(statement))

    def list_all(
        self,
        *,
        branch: str | None = None,
        period_month: str | None = None,
        status: str | None = None,
        payment_status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Membership]:
        statement = select(Membership).order_by(desc(Membership.end_date)).offset(offset).limit(limit)
        if branch and branch != "Todas":
            statement = statement.where(Membership.branch == branch)
        if period_month:
            statement = statement.where(Membership.period_month == period_month)
        if status:
            statement = statement.where(Membership.status == status)
        if payment_status:
            statement = statement.where(Membership.payment_status == payment_status)
        return list(self.db.scalars(statement))

    def list_expiring_soon(self, days_threshold: int = 5, branch: str | None = None) -> list[Membership]:
        """Returns active memberships that expire within the next N days (Section 6.4)."""
        today = date.today()
        target_date = today + timedelta(days=days_threshold)
        statement = (
            select(Membership)
            .where(
                Membership.is_active.is_(True),
                Membership.status == "active",
                Membership.end_date >= today,
                Membership.end_date <= target_date,
            )
            .order_by(Membership.end_date.asc())
        )
        if branch and branch != "Todas":
            statement = statement.where(Membership.branch == branch)
        return list(self.db.scalars(statement))

    def count_pending_payments(self, period_month: str | None = None, branch: str | None = None) -> int:
        statement = select(Membership).where(
            Membership.is_active.is_(True),
            Membership.payment_status.in_(["pending", "partial"]),
        )
        if period_month:
            statement = statement.where(Membership.period_month == period_month)
        if branch and branch != "Todas":
            statement = statement.where(Membership.branch == branch)
        return len(list(self.db.scalars(statement)))

    def save(self, membership: Membership) -> Membership:
        self.db.add(membership)
        self.db.commit()
        self.db.refresh(membership)
        return membership
