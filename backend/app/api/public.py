from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.client import Client
from backend.app.models.interaction import Interaction
from backend.app.repositories.class_session import ClassSessionRepository
from backend.app.repositories.client import ClientRepository
from backend.app.repositories.interaction import InteractionRepository
from backend.app.schemas.classes import ClassSessionRead
from backend.app.schemas.public import PublicLeadCreate, PublicLeadResponse

router = APIRouter(prefix="/public", tags=["Public Web Integration"])

DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post("/leads", response_model=PublicLeadResponse, status_code=status.HTTP_201_CREATED)
def submit_web_lead(data: PublicLeadCreate, db: DatabaseSession) -> PublicLeadResponse:
    """Section 9.2: Web leads automatically enter the CRM as potential clients."""
    client_repo = ClientRepository(db)
    interaction_repo = InteractionRepository(db)

    # Check if client with this phone/whatsapp already exists
    contact_phone = data.whatsapp or data.phone or ""
    existing_client = None
    if contact_phone:
        existing_client = client_repo.get_by_phone_or_whatsapp(contact_phone)

    if existing_client:
        client = existing_client
        client.preferred_branch = data.preferred_branch
    else:
        client = Client(
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            whatsapp=data.whatsapp or data.phone,
            email=data.email,
            birth_year=data.birth_year,
            is_minor=data.is_minor,
            guardian_name=data.guardian_name,
            guardian_phone=data.guardian_phone,
            preferred_branch=data.preferred_branch,
            status="interested",
            acquisition_source="web",
            notes=f"Consulta web: {data.message}" if data.message else "Registrado vía formulario web",
        )
        client_repo.create(client)
        client_repo.save(client)

    # Create automatic initial interaction
    interaction = Interaction(
        client_id=client.id,
        channel="web",
        motive="precios_y_horarios" if data.class_interest != "prueba" else "clase_prueba",
        summary=f"Lead Web recibido. Interés: {data.class_interest}. Mensaje: {data.message or 'Sin mensaje adicional'}",
        result="pidio_informacion",
        attended_by="Web Bot / Formulario",
        reminder_active=True,
    )
    interaction_repo.create(interaction)
    interaction_repo.save(interaction)

    return PublicLeadResponse(
        client_id=client.id,
        interaction_id=interaction.id,
        message="¡Gracias por tu interés en el Taller de Marinera Garbo & Salero! Un asesor se contactará contigo.",
        preferred_branch=data.preferred_branch,
    )


@router.get("/schedule", response_model=list[ClassSessionRead])
def get_public_schedule(
    db: DatabaseSession,
    branch: str | None = None,
) -> list[ClassSessionRead]:
    """Section 9.1: Public timetable and branches view."""
    return ClassSessionRepository(db).list(include_cancelled=False, branch=branch)
