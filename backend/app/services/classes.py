import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.models.class_session import ClassSession
from backend.app.models.enrollment import Enrollment
from backend.app.repositories.class_session import ClassSessionRepository
from backend.app.repositories.client import ClientRepository
from backend.app.repositories.enrollment import EnrollmentRepository
from backend.app.schemas.classes import (
    ClassSessionCreate,
    ClassSessionUpdate,
    EnrollmentCreate,
    EnrollmentStatus,
    EnrollmentUpdate,
    validate_class_details,
)


class ClassSessionService:
    """Business rules for scheduled group and private classes."""

    def __init__(self, db: Session) -> None:
        self.repository = ClassSessionRepository(db)
        self.enrollment_repository = EnrollmentRepository(db)

    def create_class_session(self, data: ClassSessionCreate) -> ClassSession:
        class_session = ClassSession(**data.model_dump())
        self.repository.create(class_session)
        return self.repository.save(class_session)

    def list_class_sessions(
        self,
        *,
        include_cancelled: bool = False,
        branch: str | None = None,
        class_type: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[ClassSession]:
        return self.repository.list(
            include_cancelled=include_cancelled,
            branch=branch,
            class_type=class_type,
            offset=offset,
            limit=limit,
        )

    def get_class_session(self, class_session_id: uuid.UUID) -> ClassSession:
        class_session = self.repository.get_by_id(class_session_id)
        if class_session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class session not found.",
            )
        return class_session

    def update_class_session(
        self,
        class_session_id: uuid.UUID,
        data: ClassSessionUpdate,
    ) -> ClassSession:
        class_session = self.get_class_session(class_session_id)
        for field_name, value in data.model_dump(exclude_unset=True).items():
            setattr(class_session, field_name, value)

        try:
            validate_class_details(
                class_type=class_session.class_type,
                capacity=class_session.capacity,
                starts_at=class_session.starts_at,
                ends_at=class_session.ends_at,
            )
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(error),
            ) from error

        places_taken = self.enrollment_repository.count_places_taken(class_session.id)
        if class_session.capacity < places_taken:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The capacity cannot be lower than the number of active enrollments.",
            )
        return self.repository.save(class_session)

    def cancel_class_session(self, class_session_id: uuid.UUID) -> None:
        class_session = self.get_class_session(class_session_id)
        class_session.is_cancelled = True
        self.repository.save(class_session)


class EnrollmentService:
    """Business rules for registrations in scheduled classes."""

    def __init__(self, db: Session) -> None:
        self.class_sessions = ClassSessionRepository(db)
        self.clients = ClientRepository(db)
        self.repository = EnrollmentRepository(db)

    def create_enrollment(
        self,
        class_session_id: uuid.UUID,
        data: EnrollmentCreate,
    ) -> Enrollment:
        class_session = self._get_class_session(class_session_id)
        self._ensure_class_is_open(class_session)
        client = self._get_client(data.client_id)
        if not client.is_active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An inactive client cannot be enrolled in a class.",
            )
        if self.repository.get_by_client_and_session(
            client_id=data.client_id,
            class_session_id=class_session_id,
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This client is already registered for this class session.",
            )
        self._ensure_places_available(class_session)

        enrollment = Enrollment(class_session_id=class_session_id, **data.model_dump())
        self.repository.create(enrollment)
        return self.repository.save(enrollment)

    def list_enrollments_for_class(self, class_session_id: uuid.UUID) -> list[Enrollment]:
        self._get_class_session(class_session_id)
        return self.repository.list_by_class_session(class_session_id)

    def list_enrollments_for_client(self, client_id: uuid.UUID) -> list[Enrollment]:
        self._get_client(client_id)
        return self.repository.list_by_client(client_id)

    def update_enrollment(
        self,
        enrollment_id: uuid.UUID,
        data: EnrollmentUpdate,
    ) -> Enrollment:
        enrollment = self._get_enrollment(enrollment_id)
        updates = data.model_dump(exclude_unset=True)
        next_status = updates.get("status")

        if next_status in {EnrollmentStatus.BOOKED, EnrollmentStatus.ATTENDED} and enrollment.status == "cancelled":
            class_session = self._get_class_session(enrollment.class_session_id)
            self._ensure_class_is_open(class_session)
            self._ensure_places_available(class_session)

        for field_name, value in updates.items():
            setattr(enrollment, field_name, value)
        return self.repository.save(enrollment)

    def cancel_enrollment(self, enrollment_id: uuid.UUID) -> None:
        enrollment = self._get_enrollment(enrollment_id)
        enrollment.status = EnrollmentStatus.CANCELLED
        self.repository.save(enrollment)

    def _get_class_session(self, class_session_id: uuid.UUID) -> ClassSession:
        class_session = self.class_sessions.get_by_id(class_session_id)
        if class_session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class session not found.",
            )
        return class_session

    def _get_client(self, client_id: uuid.UUID):
        client = self.clients.get_by_id(client_id)
        if client is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found.",
            )
        return client

    def _get_enrollment(self, enrollment_id: uuid.UUID) -> Enrollment:
        enrollment = self.repository.get_by_id(enrollment_id)
        if enrollment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Enrollment not found.",
            )
        return enrollment

    def _ensure_class_is_open(self, class_session: ClassSession) -> None:
        if class_session.is_cancelled:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cancelled class sessions do not accept enrollments.",
            )

    def _ensure_places_available(self, class_session: ClassSession) -> None:
        if self.repository.count_places_taken(class_session.id) >= class_session.capacity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This class session has reached its capacity.",
            )
