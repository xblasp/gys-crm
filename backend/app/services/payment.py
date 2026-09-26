import uuid
from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.models.audit_log import AuditLog
from backend.app.models.payment import Payment
from backend.app.repositories.client import ClientRepository
from backend.app.repositories.membership import MembershipRepository
from backend.app.repositories.payment import PaymentRepository
from backend.app.schemas.payment import (
    PaymentCancel,
    PaymentCreate,
)


class PaymentService:
    """Business logic for payments, receipts, and authorized cancellations."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = PaymentRepository(db)
        self.client_repo = ClientRepository(db)
        self.membership_repo = MembershipRepository(db)

    def create_payment(self, data: PaymentCreate) -> Payment:
        client = self.client_repo.get_by_id(data.client_id)
        if client is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found.",
            )

        if data.membership_id is not None:
            membership = self.membership_repo.get_by_id(data.membership_id)
            if membership is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Membership not found.",
                )
            membership.payment_status = "paid"
            self.membership_repo.save(membership)

        payment = Payment(
            client_id=data.client_id,
            membership_id=data.membership_id,
            amount=data.amount,
            payment_date=data.payment_date or datetime.now(),
            period_month=data.period_month,
            concept=data.concept.value,
            shift_detail=data.shift_detail,
            payment_method=data.payment_method.value,
            transaction_reference=data.transaction_reference,
            branch=data.branch,
            registered_by=data.registered_by,
            status="completed",
            notes=data.notes,
        )

        # Audit creation
        audit = AuditLog(
            action="PAYMENT_CREATED",
            entity_type="payment",
            entity_id=str(payment.id),
            performed_by=data.registered_by,
            details=f"Cobro S/ {data.amount:.2f} registrado por {data.payment_method.value} para {client.first_name} {client.last_name}",
        )
        self.db.add(audit)

        self.repository.create(payment)
        return self.repository.save(payment)

    def list_payments(
        self,
        *,
        client_id: uuid.UUID | None = None,
        branch: str | None = None,
        period_month: str | None = None,
        payment_method: str | None = None,
        concept: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Payment]:
        if client_id is not None:
            return self.repository.list_by_client(client_id)
        return self.repository.list_all(
            branch=branch,
            period_month=period_month,
            payment_method=payment_method,
            concept=concept,
            status=status,
            offset=offset,
            limit=limit,
        )

    def get_payment(self, payment_id: uuid.UUID) -> Payment:
        payment = self.repository.get_by_id(payment_id)
        if payment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found.",
            )
        return payment

    def cancel_payment(self, payment_id: uuid.UUID, data: PaymentCancel) -> Payment:
        """Section 6.5: Cancels/refunds payment with mandatory reason and authorizer."""
        payment = self.get_payment(payment_id)
        if payment.status == "cancelled":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Payment is already cancelled.",
            )

        payment.status = "cancelled"
        payment.cancelled_by = data.cancelled_by
        payment.cancellation_reason = data.cancellation_reason
        payment.cancelled_at = datetime.now()

        if payment.membership_id is not None:
            membership = self.membership_repo.get_by_id(payment.membership_id)
            if membership is not None:
                membership.payment_status = "pending"
                self.membership_repo.save(membership)

        audit = AuditLog(
            action="PAYMENT_CANCELLED",
            entity_type="payment",
            entity_id=str(payment.id),
            performed_by=data.cancelled_by,
            details=f"Pago S/ {payment.amount:.2f} anulado por {data.cancelled_by}. Motivo: {data.cancellation_reason}",
        )
        self.db.add(audit)

        return self.repository.save(payment)
