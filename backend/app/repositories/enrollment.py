import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.enrollment import Enrollment


class EnrollmentRepository:
    """Database operations for class enrollments only."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, enrollment: Enrollment) -> Enrollment:
        self.db.add(enrollment)
        self.db.flush()
        return enrollment

    def get_by_id(self, enrollment_id: uuid.UUID) -> Enrollment | None:
        return self.db.get(Enrollment, enrollment_id)

    def get_by_client_and_session(
        self,
        *,
        client_id: uuid.UUID,
        class_session_id: uuid.UUID,
    ) -> Enrollment | None:
        statement = select(Enrollment).where(
            Enrollment.client_id == client_id,
            Enrollment.class_session_id == class_session_id,
        )
        return self.db.scalar(statement)

    def list_by_class_session(self, class_session_id: uuid.UUID) -> list[Enrollment]:
        statement = select(Enrollment).where(
            Enrollment.class_session_id == class_session_id
        ).order_by(Enrollment.created_at)
        return list(self.db.scalars(statement))

    def list_by_client(self, client_id: uuid.UUID) -> list[Enrollment]:
        statement = select(Enrollment).where(Enrollment.client_id == client_id).order_by(
            Enrollment.created_at.desc()
        )
        return list(self.db.scalars(statement))

    def count_places_taken(self, class_session_id: uuid.UUID) -> int:
        statement = select(func.count()).select_from(Enrollment).where(
            Enrollment.class_session_id == class_session_id,
            Enrollment.status.in_(("booked", "attended")),
        )
        return int(self.db.scalar(statement) or 0)

    def save(self, enrollment: Enrollment) -> Enrollment:
        self.db.add(enrollment)
        self.db.commit()
        self.db.refresh(enrollment)
        return enrollment
