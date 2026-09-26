import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.class_session import ClassSession


class ClassSessionRepository:
    """Database operations for scheduled classes."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, class_session: ClassSession) -> ClassSession:
        self.db.add(class_session)
        self.db.flush()
        return class_session

    def get_by_id(self, class_session_id: uuid.UUID) -> ClassSession | None:
        return self.db.get(ClassSession, class_session_id)

    def list(
        self,
        *,
        include_cancelled: bool = False,
        branch: str | None = None,
        class_type: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[ClassSession]:
        statement = select(ClassSession).order_by(ClassSession.starts_at).offset(offset).limit(limit)
        if not include_cancelled:
            statement = statement.where(ClassSession.is_cancelled.is_(False))
        if branch is not None and branch != "Todas":
            statement = statement.where(ClassSession.branch == branch)
        if class_type is not None:
            statement = statement.where(ClassSession.class_type == class_type)
        return list(self.db.scalars(statement))

    def save(self, class_session: ClassSession) -> ClassSession:
        self.db.add(class_session)
        self.db.commit()
        self.db.refresh(class_session)
        return class_session
