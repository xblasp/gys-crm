import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.models.client import Client
from backend.app.models.interaction import Interaction
from backend.app.repositories.class_session import ClassSessionRepository
from backend.app.repositories.client import ClientRepository
from backend.app.repositories.client_discount import ClientDiscountRepository
from backend.app.repositories.enrollment import EnrollmentRepository
from backend.app.repositories.interaction import InteractionRepository
from backend.app.repositories.payment import PaymentRepository
from backend.app.schemas.interaction import (
    ClientTimelineItem,
    InteractionCreate,
    InteractionResult,
    InteractionUpdate,
)


class InteractionService:
    """Business logic for interactions, follow-ups, and the client 360 timeline."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = InteractionRepository(db)
        self.client_repo = ClientRepository(db)
        self.enrollment_repo = EnrollmentRepository(db)
        self.class_repo = ClassSessionRepository(db)
        self.discount_repo = ClientDiscountRepository(db)

    def create_interaction(self, data: InteractionCreate) -> Interaction:
        client = self.client_repo.get_by_id(data.client_id)
        if client is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found.",
            )

        interaction = Interaction(
            client_id=data.client_id,
            interaction_date=data.interaction_date or datetime.now(),
            channel=data.channel.value,
            motive=data.motive.value,
            summary=data.summary,
            result=data.result.value,
            uninterested_reason=data.uninterested_reason,
            attended_by=data.attended_by,
            next_followup_date=data.next_followup_date,
            reminder_active=data.reminder_active,
        )

        # Update client status & uninterested reason if applicable
        if data.result == InteractionResult.SE_INSCRIBIO:
            client.status = "active"
            client.is_active = True
        elif data.uninterested_reason:
            client.uninterested_reason = data.uninterested_reason

        self.client_repo.save(client)
        self.repository.create(interaction)
        return self.repository.save(interaction)

    def list_interactions(
        self,
        *,
        client_id: uuid.UUID | None = None,
        channel: str | None = None,
        result: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Interaction]:
        if client_id is not None:
            return self.repository.list_by_client(client_id)
        return self.repository.list_all(channel=channel, result=result, offset=offset, limit=limit)

    def get_interaction(self, interaction_id: uuid.UUID) -> Interaction:
        interaction = self.repository.get_by_id(interaction_id)
        if interaction is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interaction not found.",
            )
        return interaction

    def update_interaction(
        self, interaction_id: uuid.UUID, data: InteractionUpdate
    ) -> Interaction:
        interaction = self.get_interaction(interaction_id)
        values = data.model_dump(exclude_unset=True)
        for key, value in values.items():
            if hasattr(value, "value"):
                value = value.value
            setattr(interaction, key, value)
        return self.repository.save(interaction)

    def list_pending_reminders(self) -> list[Interaction]:
        return self.repository.list_pending_reminders()

    def get_client_timeline(self, client_id: uuid.UUID) -> list[ClientTimelineItem]:
        """Builds a unified chronological timeline for a client (Section 3.7)."""
        client = self.client_repo.get_by_id(client_id)
        if client is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found.",
            )

        timeline: list[ClientTimelineItem] = []

        # 1. Interactions
        interactions = self.repository.list_by_client(client_id)
        for it in interactions:
            timeline.append(
                ClientTimelineItem(
                    event_type="interaction",
                    title=f"Contacto por {it.channel.upper()}: {it.motive.replace('_', ' ').capitalize()}",
                    description=f"{it.summary} | Resultado: {it.result.replace('_', ' ')}",
                    timestamp=it.interaction_date,
                    author_or_channel=it.attended_by,
                    status_or_result=it.result,
                )
            )

        # 2. Enrollments & Class Attendances
        enrollments = self.enrollment_repo.list_by_client(client_id)
        for en in enrollments:
            cls = self.class_repo.get_by_id(en.class_session_id)
            cls_name = cls.name if cls else "Clase"
            timeline.append(
                ClientTimelineItem(
                    event_type="enrollment",
                    title=f"Inscripción en {cls_name}",
                    description=f"Estado: {en.status} | Horario: {cls.starts_at.strftime('%d/%m/%Y %H:%M') if cls else ''}",
                    timestamp=en.created_at,
                    author_or_channel="Sistema",
                    status_or_result=en.status,
                )
            )

        # 3. Payments
        from backend.app.models.payment import Payment
        from sqlalchemy import select
        payments_stmt = select(Payment).where(Payment.client_id == client_id).order_by(Payment.payment_date.desc())
        payments = list(self.db.scalars(payments_stmt))
        for p in payments:
            timeline.append(
                ClientTimelineItem(
                    event_type="payment",
                    title=f"Pago S/ {p.amount:.2f} ({p.concept.capitalize()})",
                    description=f"Método: {p.payment_method.capitalize()} | Periodo: {p.period_month} | Estado: {p.status}",
                    timestamp=p.payment_date,
                    author_or_channel=p.registered_by,
                    status_or_result=p.status,
                    amount=float(p.amount),
                )
            )

        # 4. Discounts applied
        discounts = self.discount_repo.list_by_client(client_id)
        for d in discounts:
            timeline.append(
                ClientTimelineItem(
                    event_type="discount",
                    title=f"Descuento aplicado: {d.promotion_name}",
                    description=f"Motivo: {d.reason} | Valor: {d.discount_value}",
                    timestamp=d.applied_at,
                    author_or_channel=d.applied_by,
                    status_or_result="applied",
                    amount=float(d.discount_value),
                )
            )

        # Sort all events chronologically descending (newest first)
        timeline.sort(key=lambda x: x.timestamp, reverse=True)
        return timeline
