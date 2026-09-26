import json
import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.models.audit_log import AuditLog
from backend.app.models.client import Client
from backend.app.models.interaction import Interaction
from backend.app.repositories.client import ClientRepository
from backend.app.schemas.client import (
    RETIREMENT_REASON_LABELS,
    ClientCreate,
    ClientStatus,
    ClientUpdate,
    _validate_referral_details,
)
from backend.app.services.membership import MembershipService


class ClientService:
    """Business rules for the client module."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ClientRepository(db)

    def create_client(self, data: ClientCreate) -> Client:
        if data.dni and self.repository.get_by_dni(data.dni):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A client with this DNI already exists.",
            )
        values = data.model_dump()
        if values.get("birth_year") and (datetime.now().year - values["birth_year"]) < 18:
            values["is_minor"] = True
        client = Client(**values)
        self.repository.create(client)
        saved_client = self.repository.save(client)

        # If created as active, automatically generate current month's membership cycle
        if saved_client.status == ClientStatus.ACTIVE.value:
            current_month = datetime.now().strftime("%Y-%m")
            mem_service = MembershipService(self.db)
            mem_service.ensure_monthly_cycles_for_period(current_month, branch=saved_client.preferred_branch)

        return saved_client

    def list_clients(
        self,
        *,
        include_inactive: bool = False,
        client_status: ClientStatus | None = None,
        branch: str | None = None,
        is_minor: bool | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Client]:
        return self.repository.list(
            include_inactive=include_inactive,
            status=client_status.value if client_status else None,
            branch=branch,
            is_minor=is_minor,
            search=search,
            offset=offset,
            limit=limit,
        )

    def get_client(self, client_id: uuid.UUID) -> Client:
        client = self.repository.get_by_id(client_id)
        if client is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found.",
            )
        return client

    def update_client(self, client_id: uuid.UUID, data: ClientUpdate) -> Client:
        client = self.get_client(client_id)
        values = data.model_dump(exclude_unset=True)

        dni = values.get("dni")
        if dni and (existing_client := self.repository.get_by_dni(dni)) and existing_client.id != client.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A client with this DNI already exists.",
            )

        _validate_referral_details(
            values.get("acquisition_source", client.acquisition_source),
            values.get("referrer_name", client.referrer_name),
            values.get("referrer_phone", client.referrer_phone),
        )
        if "birth_year" in values and values["birth_year"]:
            values["is_minor"] = (datetime.now().year - values["birth_year"]) < 18

        for field_name, value in values.items():
            setattr(client, field_name, value)
        if "status" in values:
            client.is_active = values["status"] != ClientStatus.RETIRED.value
        return self.repository.save(client)

    def retire_client(
        self,
        client_id: uuid.UUID,
        reason: str,
        notes: str | None = None,
        retired_by: str = "Administrador",
    ) -> Client:
        """Formal student retirement flow with mandatory reason, cancellation of memberships, and audit logging."""
        client = self.get_client(client_id)
        
        # Translate reason key to friendly label if found
        reason_label = RETIREMENT_REASON_LABELS.get(reason, reason)

        client.status = ClientStatus.RETIRED.value
        client.is_active = False
        client.uninterested_reason = reason_label
        client.retired_at = datetime.now()
        if notes:
            note_str = f"Motivo de Retiro: {reason_label}. Nota: {notes}"
            client.notes = f"{client.notes}\n{note_str}".strip() if client.notes else note_str

        # 1. Cancel active/pending memberships for this client
        mem_service = MembershipService(self.db)
        mem_service.cancel_client_memberships_on_retirement(client_id, reason_label)

        # 2. Add Timeline / Interaction event
        summary_text = f"Baja / Retiro registrado. Motivo: {reason_label}."
        if notes:
            summary_text += f" Observaciones: {notes}"

        interaction = Interaction(
            client_id=client.id,
            channel="presencial",
            motive="retiro_alumno",
            summary=summary_text,
            result="se_retiro",
            uninterested_reason=reason_label,
            attended_by=retired_by,
        )
        self.db.add(interaction)

        # 3. Add immutable Audit Log
        audit_log = AuditLog(
            action="CLIENT_RETIRED",
            entity_type="client",
            entity_id=str(client.id),
            performed_by=retired_by,
            details=json.dumps({"reason": reason_label, "notes": notes, "client_name": f"{client.first_name} {client.last_name}"}, ensure_ascii=False),
        )
        self.db.add(audit_log)

        self.repository.save(client)
        self.db.commit()
        return client

    def reactivate_client(
        self,
        client_id: uuid.UUID,
        reactivated_by: str = "Administrador",
        notes: str | None = None,
    ) -> Client:
        """Reactivates a retired or interested student and generates their monthly cycle."""
        client = self.get_client(client_id)
        client.status = ClientStatus.ACTIVE.value
        client.is_active = True
        client.retired_at = None

        current_month = datetime.now().strftime("%Y-%m")
        mem_service = MembershipService(self.db)
        mem_service.ensure_monthly_cycles_for_period(current_month, branch=client.preferred_branch)

        # Interaction & Audit
        interaction = Interaction(
            client_id=client.id,
            channel="presencial",
            motive="reincorporacion",
            summary=f"Alumno reactivado e inscrito en el ciclo mensual {current_month}. {notes or ''}".strip(),
            result="se_inscribio",
            attended_by=reactivated_by,
        )
        self.db.add(interaction)

        audit_log = AuditLog(
            action="CLIENT_REACTIVATED",
            entity_type="client",
            entity_id=str(client.id),
            performed_by=reactivated_by,
            details=json.dumps({"client_name": f"{client.first_name} {client.last_name}", "notes": notes}, ensure_ascii=False),
        )
        self.db.add(audit_log)

        self.repository.save(client)
        self.db.commit()
        return client

    def deactivate_client(self, client_id: uuid.UUID) -> None:
        """Legacy helper for backward compatibility."""
        self.retire_client(client_id, reason="Otro Motivo", notes="Baja directa")
