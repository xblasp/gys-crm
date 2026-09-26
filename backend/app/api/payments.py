import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.payment import (
    PaymentCancel,
    PaymentCreate,
    PaymentRead,
)
from backend.app.services.payment import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments & Cashflow"])

DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post("", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
def create_payment(data: PaymentCreate, db: DatabaseSession) -> PaymentRead:
    return PaymentService(db).create_payment(data)


@router.get("", response_model=list[PaymentRead])
def list_payments(
    db: DatabaseSession,
    client_id: uuid.UUID | None = None,
    branch: str | None = None,
    period_month: str | None = None,
    payment_method: str | None = None,
    concept: str | None = None,
    status: str | None = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[PaymentRead]:
    return PaymentService(db).list_payments(
        client_id=client_id,
        branch=branch,
        period_month=period_month,
        payment_method=payment_method,
        concept=concept,
        status=status,
        offset=offset,
        limit=limit,
    )


@router.get("/{payment_id}", response_model=PaymentRead)
def get_payment(payment_id: uuid.UUID, db: DatabaseSession) -> PaymentRead:
    return PaymentService(db).get_payment(payment_id)


@router.post("/{payment_id}/cancel", response_model=PaymentRead)
def cancel_payment(
    payment_id: uuid.UUID,
    data: PaymentCancel,
    db: DatabaseSession,
) -> PaymentRead:
    """Section 6.5: Anulación de pagos con motivo y usuario autorizador."""
    return PaymentService(db).cancel_payment(payment_id, data)
