import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.membership import (
    MembershipCreate,
    MembershipRead,
    MembershipUpdate,
)
from backend.app.services.membership import MembershipService

router = APIRouter(prefix="/memberships", tags=["Memberships & Subscriptions"])

DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post("", response_model=MembershipRead, status_code=status.HTTP_201_CREATED)
def create_membership(data: MembershipCreate, db: DatabaseSession) -> MembershipRead:
    return MembershipService(db).create_membership(data)


@router.post("/generate-monthly-cycles", response_model=list[MembershipRead])
def generate_monthly_cycles(
    db: DatabaseSession,
    period_month: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    branch: str | None = None,
) -> list[MembershipRead]:
    """Generates and ensures recurring monthly billing cycles for all active students in period_month."""
    return MembershipService(db).ensure_monthly_cycles_for_period(
        period_month=period_month,
        branch=branch,
    )


@router.get("", response_model=list[MembershipRead])
def list_memberships(
    db: DatabaseSession,
    client_id: uuid.UUID | None = None,
    branch: str | None = None,
    period_month: str | None = None,
    status: str | None = None,
    payment_status: str | None = None,
    auto_generate: bool = True,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[MembershipRead]:
    return MembershipService(db).list_memberships(
        client_id=client_id,
        branch=branch,
        period_month=period_month,
        status=status,
        payment_status=payment_status,
        auto_generate=auto_generate,
        offset=offset,
        limit=limit,
    )


@router.get("/expiring", response_model=list[MembershipRead])
def list_expiring_soon(
    db: DatabaseSession,
    days: Annotated[int, Query(ge=1, le=30)] = 5,
    branch: str | None = None,
) -> list[MembershipRead]:
    """Section 6.4: Returns memberships expiring within the next 5 days."""
    return MembershipService(db).list_expiring_soon(days_threshold=days, branch=branch)


@router.get("/{membership_id}", response_model=MembershipRead)
def get_membership(membership_id: uuid.UUID, db: DatabaseSession) -> MembershipRead:
    return MembershipService(db).get_membership(membership_id)


@router.patch("/{membership_id}", response_model=MembershipRead)
def update_membership(
    membership_id: uuid.UUID,
    data: MembershipUpdate,
    db: DatabaseSession,
) -> MembershipRead:
    return MembershipService(db).update_membership(membership_id, data)
