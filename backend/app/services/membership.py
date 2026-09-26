import calendar
import uuid
from datetime import date, timedelta
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.models.membership import Membership
from backend.app.repositories.client import ClientRepository
from backend.app.repositories.membership import MembershipRepository
from backend.app.schemas.membership import (
    MembershipCreate,
    MembershipRead,
    MembershipUpdate,
)


class MembershipService:
    """Business rules for client memberships and monthly recurring cycles."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = MembershipRepository(db)
        self.client_repository = ClientRepository(db)

    def create_membership(self, data: MembershipCreate) -> Membership:
        client = self.client_repository.get_by_id(data.client_id)
        if client is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found.",
            )

        final_price = data.price - data.discount_applied
        membership = Membership(
            client_id=data.client_id,
            branch=data.branch,
            class_type=data.class_type.value if hasattr(data.class_type, "value") else str(data.class_type),
            plan_name=data.plan_name,
            period_month=data.period_month,
            start_date=data.start_date,
            end_date=data.end_date,
            classes_total=data.classes_total,
            classes_attended=0,
            price=data.price,
            discount_applied=data.discount_applied,
            final_price=final_price,
            payment_status=data.payment_status.value if hasattr(data.payment_status, "value") else str(data.payment_status),
            status="active",
            is_recurring=data.is_recurring,
            auto_renew=data.auto_renew,
            notes=data.notes,
            is_active=True,
        )

        # Make sure client is marked active
        if client.status != "active":
            client.status = "active"
            client.is_active = True
            self.client_repository.save(client)

        self.repository.create(membership)
        return self.repository.save(membership)

    def ensure_monthly_cycles_for_period(
        self,
        period_month: str,
        branch: str | None = None,
    ) -> list[Membership]:
        """Ensures that all active students have their monthly membership cycle generated for period_month."""
        try:
            year, month = map(int, period_month.split("-"))
            _, last_day = calendar.monthrange(year, month)
            start_date = date(year, month, 1)
            end_date = date(year, month, last_day)
        except Exception:
            return []

        # Find active clients
        active_clients = self.client_repository.list(
            status="active",
            branch=branch,
            include_inactive=False,
            limit=1000,
        )

        existing_memberships = self.repository.list_all(
            period_month=period_month,
            branch=branch,
            limit=1000,
        )
        existing_client_ids = {m.client_id for m in existing_memberships}

        created_memberships: list[Membership] = []
        for client in active_clients:
            if client.id not in existing_client_ids:
                branch_name = client.preferred_branch or branch or "Los Olivos"
                new_mem = Membership(
                    client_id=client.id,
                    branch=branch_name,
                    class_type="grupal_mensual",
                    plan_name="Mensualidad Marinera (8 clases)",
                    period_month=period_month,
                    start_date=start_date,
                    end_date=end_date,
                    classes_total=8,
                    classes_attended=0,
                    price=Decimal("150.00"),
                    discount_applied=Decimal("0.00"),
                    final_price=Decimal("150.00"),
                    payment_status="pending",
                    status="active",
                    is_recurring=True,
                    auto_renew=True,
                    notes="Cuota generada automáticamente para el periodo mensual.",
                    is_active=True,
                )
                self.repository.create(new_mem)
                created_memberships.append(new_mem)

        if created_memberships:
            self.db.commit()

        return created_memberships

    def cancel_client_memberships_on_retirement(
        self,
        client_id: uuid.UUID,
        reason: str,
    ) -> list[Membership]:
        """Cancels all active or pending memberships when a student is retired."""
        memberships = self.repository.list_by_client(client_id)
        cancelled: list[Membership] = []
        for mem in memberships:
            if mem.status in ["active", "expiring_soon"] or mem.payment_status == "pending":
                mem.status = "cancelled"
                mem.auto_renew = False
                mem.is_active = False
                note_str = f"Cancelada por retiro del alumno. Motivo: {reason}"
                mem.notes = f"{mem.notes}\n{note_str}".strip() if mem.notes else note_str
                cancelled.append(self.repository.save(mem))
        return cancelled

    def list_memberships(
        self,
        *,
        client_id: uuid.UUID | None = None,
        branch: str | None = None,
        period_month: str | None = None,
        status: str | None = None,
        payment_status: str | None = None,
        auto_generate: bool = True,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Membership]:
        if client_id is not None:
            return self.repository.list_by_client(client_id)

        # Auto-ensure current period monthly cycles so active students always show up
        if period_month and auto_generate:
            self.ensure_monthly_cycles_for_period(period_month, branch=branch)

        return self.repository.list_all(
            branch=branch,
            period_month=period_month,
            status=status,
            payment_status=payment_status,
            offset=offset,
            limit=limit,
        )

    def get_membership(self, membership_id: uuid.UUID) -> Membership:
        membership = self.repository.get_by_id(membership_id)
        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Membership not found.",
            )
        return membership

    def update_membership(
        self, membership_id: uuid.UUID, data: MembershipUpdate
    ) -> Membership:
        membership = self.get_membership(membership_id)
        values = data.model_dump(exclude_unset=True)
        for key, value in values.items():
            if hasattr(value, "value"):
                value = value.value
            setattr(membership, key, value)
        return self.repository.save(membership)

    def list_expiring_soon(self, days_threshold: int = 5, branch: str | None = None) -> list[Membership]:
        return self.repository.list_expiring_soon(days_threshold=days_threshold, branch=branch)
