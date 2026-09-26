import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from backend.app.models.client import Client


class ClientRepository:
    """Database operations for clients."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, client: Client) -> Client:
        self.db.add(client)
        self.db.flush()
        return client

    def get_by_id(self, client_id: uuid.UUID) -> Client | None:
        return self.db.get(Client, client_id)

    def get_by_dni(self, dni: str) -> Client | None:
        statement = select(Client).where(Client.dni == dni)
        return self.db.scalar(statement)

    def get_by_phone_or_whatsapp(self, phone: str) -> Client | None:
        statement = select(Client).where(or_(Client.phone == phone, Client.whatsapp == phone))
        return self.db.scalar(statement)

    def list(
        self,
        *,
        include_inactive: bool = False,
        status: str | None = None,
        branch: str | None = None,
        is_minor: bool | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Client]:
        statement = select(Client).order_by(Client.last_name, Client.first_name).offset(offset).limit(limit)
        if not include_inactive:
            statement = statement.where(Client.is_active.is_(True))
        if status is not None:
            statement = statement.where(Client.status == status)
        if branch is not None and branch != "Todas":
            statement = statement.where(Client.preferred_branch == branch)
        if is_minor is not None:
            statement = statement.where(Client.is_minor.is_(is_minor))
        if search:
            search_term = f"%{search}%"
            statement = statement.where(
                or_(
                    Client.first_name.ilike(search_term),
                    Client.last_name.ilike(search_term),
                    Client.dni.ilike(search_term),
                    Client.phone.ilike(search_term),
                    Client.whatsapp.ilike(search_term),
                    Client.guardian_name.ilike(search_term),
                )
            )
        return list(self.db.scalars(statement))

    def count(
        self,
        *,
        status: str | None = None,
        branch: str | None = None,
    ) -> int:
        statement = select(Client)
        if status is not None:
            statement = statement.where(Client.status == status)
        if branch is not None and branch != "Todas":
            statement = statement.where(Client.preferred_branch == branch)
        return len(list(self.db.scalars(statement)))

    def save(self, client: Client) -> Client:
        self.db.add(client)
        self.db.commit()
        self.db.refresh(client)
        return client
