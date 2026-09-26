import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.interaction import (
    InteractionCreate,
    InteractionRead,
    InteractionUpdate,
)
from backend.app.services.interaction import InteractionService

router = APIRouter(prefix="/interactions", tags=["Interactions & CRM"])

DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post("", response_model=InteractionRead, status_code=status.HTTP_201_CREATED)
def create_interaction(data: InteractionCreate, db: DatabaseSession) -> InteractionRead:
    return InteractionService(db).create_interaction(data)


@router.get("", response_model=list[InteractionRead])
def list_interactions(
    db: DatabaseSession,
    client_id: uuid.UUID | None = None,
    channel: str | None = None,
    result: str | None = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[InteractionRead]:
    return InteractionService(db).list_interactions(
        client_id=client_id,
        channel=channel,
        result=result,
        offset=offset,
        limit=limit,
    )


@router.get("/reminders", response_model=list[InteractionRead])
def list_pending_reminders(db: DatabaseSession) -> list[InteractionRead]:
    return InteractionService(db).list_pending_reminders()


@router.get("/{interaction_id}", response_model=InteractionRead)
def get_interaction(interaction_id: uuid.UUID, db: DatabaseSession) -> InteractionRead:
    return InteractionService(db).get_interaction(interaction_id)


@router.patch("/{interaction_id}", response_model=InteractionRead)
def update_interaction(
    interaction_id: uuid.UUID,
    data: InteractionUpdate,
    db: DatabaseSession,
) -> InteractionRead:
    return InteractionService(db).update_interaction(interaction_id, data)
