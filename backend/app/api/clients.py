import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.client import (
    RETIREMENT_REASON_LABELS,
    ClientCreate,
    ClientRead,
    ClientReactivateRequest,
    ClientRetireRequest,
    ClientStatus,
    ClientUpdate,
    RetirementReason,
)
from backend.app.schemas.interaction import ClientTimelineItem
from backend.app.schemas.promotion import ClientDiscountCreate, ClientDiscountRead
from backend.app.services.client import ClientService
from backend.app.services.client_discount import ClientDiscountService
from backend.app.services.interaction import InteractionService

router = APIRouter(prefix="/clients", tags=["Clients"])

DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("/retirement-reasons/list")
def list_retirement_reasons() -> list[dict[str, str]]:
    """Returns the list of predefined reasons for student withdrawal."""
    return [
        {"key": key, "label": label}
        for key, label in RETIREMENT_REASON_LABELS.items()
    ]


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
def create_client(data: ClientCreate, db: DatabaseSession) -> ClientRead:
    return ClientService(db).create_client(data)


@router.get("", response_model=list[ClientRead])
def list_clients(
    db: DatabaseSession,
    include_inactive: bool = False,
    status: ClientStatus | None = None,
    branch: str | None = None,
    is_minor: bool | None = None,
    search: str | None = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[ClientRead]:
    return ClientService(db).list_clients(
        include_inactive=include_inactive,
        client_status=status,
        branch=branch,
        is_minor=is_minor,
        search=search,
        offset=offset,
        limit=limit,
    )


@router.get("/{client_id}", response_model=ClientRead)
def get_client(client_id: uuid.UUID, db: DatabaseSession) -> ClientRead:
    return ClientService(db).get_client(client_id)


@router.patch("/{client_id}", response_model=ClientRead)
def update_client(
    client_id: uuid.UUID,
    data: ClientUpdate,
    db: DatabaseSession,
) -> ClientRead:
    return ClientService(db).update_client(client_id, data)


@router.post("/{client_id}/retire", response_model=ClientRead)
def retire_client(
    client_id: uuid.UUID,
    data: ClientRetireRequest,
    db: DatabaseSession,
) -> ClientRead:
    """Formal student retirement flow with mandatory reason and cancellation of active memberships."""
    return ClientService(db).retire_client(
        client_id=client_id,
        reason=data.reason,
        notes=data.notes,
        retired_by=data.retired_by,
    )


@router.post("/{client_id}/reactivate", response_model=ClientRead)
def reactivate_client(
    client_id: uuid.UUID,
    data: ClientReactivateRequest,
    db: DatabaseSession,
) -> ClientRead:
    """Reactivates a retired student and creates current monthly membership cycle."""
    return ClientService(db).reactivate_client(
        client_id=client_id,
        reactivated_by=data.reactivated_by,
        notes=data.notes,
    )


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_client(client_id: uuid.UUID, db: DatabaseSession) -> Response:
    ClientService(db).deactivate_client(client_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{client_id}/discounts", response_model=ClientDiscountRead, status_code=status.HTTP_201_CREATED)
def apply_client_discount(
    client_id: uuid.UUID,
    data: ClientDiscountCreate,
    db: DatabaseSession,
) -> ClientDiscountRead:
    return ClientDiscountService(db).apply_discount(client_id, data)


@router.get("/{client_id}/discounts", response_model=list[ClientDiscountRead])
def list_client_discounts(client_id: uuid.UUID, db: DatabaseSession) -> list[ClientDiscountRead]:
    return ClientDiscountService(db).list_discounts(client_id)


@router.get("/{client_id}/timeline", response_model=list[ClientTimelineItem])
def get_client_timeline(client_id: uuid.UUID, db: DatabaseSession) -> list[ClientTimelineItem]:
    return InteractionService(db).get_client_timeline(client_id)
