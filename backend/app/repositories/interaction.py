import uuid
from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.models.interaction import Interaction


class InteractionRepository:
    """Database operations for client interactions and reminders."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, interaction: Interaction) -> Interaction:
        self.db.add(interaction)
        self.db.flush()
        return interaction

    def get_by_id(self, interaction_id: uuid.UUID) -> Interaction | None:
        return self.db.get(Interaction, interaction_id)

    def list_by_client(self, client_id: uuid.UUID) -> list[Interaction]:
        statement = (
            select(Interaction)
            .where(Interaction.client_id == client_id)
            .order_by(desc(Interaction.interaction_date))
        )
        return list(self.db.scalars(statement))

    def list_all(
        self,
        *,
        channel: str | None = None,
        result: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Interaction]:
        statement = select(Interaction).order_by(desc(Interaction.interaction_date)).offset(offset).limit(limit)
        if channel:
            statement = statement.where(Interaction.channel == channel)
        if result:
            statement = statement.where(Interaction.result == result)
        return list(self.db.scalars(statement))

    def list_pending_reminders(self) -> list[Interaction]:
        statement = (
            select(Interaction)
            .where(Interaction.reminder_active.is_(True))
            .order_by(Interaction.next_followup_date.nulls_last(), desc(Interaction.interaction_date))
        )
        return list(self.db.scalars(statement))

    def save(self, interaction: Interaction) -> Interaction:
        self.db.add(interaction)
        self.db.commit()
        self.db.refresh(interaction)
        return interaction
