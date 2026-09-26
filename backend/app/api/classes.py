import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.classes import (
    ClassSessionCreate,
    ClassSessionRead,
    ClassSessionUpdate,
    EnrollmentCreate,
    EnrollmentRead,
    EnrollmentUpdate,
)
from backend.app.services.classes import ClassSessionService, EnrollmentService

router = APIRouter(tags=["Classes"])

DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post("/class-sessions", response_model=ClassSessionRead, status_code=status.HTTP_201_CREATED)
def create_class_session(data: ClassSessionCreate, db: DatabaseSession) -> ClassSessionRead:
    return ClassSessionService(db).create_class_session(data)


@router.get("/class-sessions", response_model=list[ClassSessionRead])
def list_class_sessions(
    db: DatabaseSession,
    include_cancelled: bool = False,
    branch: str | None = None,
    class_type: str | None = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[ClassSessionRead]:
    return ClassSessionService(db).list_class_sessions(
        include_cancelled=include_cancelled,
        branch=branch,
        class_type=class_type,
        offset=offset,
        limit=limit,
    )


@router.get("/class-sessions/{class_session_id}", response_model=ClassSessionRead)
def get_class_session(class_session_id: uuid.UUID, db: DatabaseSession) -> ClassSessionRead:
    return ClassSessionService(db).get_class_session(class_session_id)


@router.patch("/class-sessions/{class_session_id}", response_model=ClassSessionRead)
def update_class_session(
    class_session_id: uuid.UUID,
    data: ClassSessionUpdate,
    db: DatabaseSession,
) -> ClassSessionRead:
    return ClassSessionService(db).update_class_session(class_session_id, data)


@router.delete("/class-sessions/{class_session_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_class_session(class_session_id: uuid.UUID, db: DatabaseSession) -> Response:
    ClassSessionService(db).cancel_class_session(class_session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/class-sessions/{class_session_id}/enrollments",
    response_model=EnrollmentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_enrollment(
    class_session_id: uuid.UUID,
    data: EnrollmentCreate,
    db: DatabaseSession,
) -> EnrollmentRead:
    return EnrollmentService(db).create_enrollment(class_session_id, data)


@router.get(
    "/class-sessions/{class_session_id}/enrollments",
    response_model=list[EnrollmentRead],
)
def list_class_enrollments(
    class_session_id: uuid.UUID,
    db: DatabaseSession,
) -> list[EnrollmentRead]:
    return EnrollmentService(db).list_enrollments_for_class(class_session_id)


@router.get("/clients/{client_id}/enrollments", response_model=list[EnrollmentRead])
def list_client_enrollments(client_id: uuid.UUID, db: DatabaseSession) -> list[EnrollmentRead]:
    return EnrollmentService(db).list_enrollments_for_client(client_id)


@router.patch("/enrollments/{enrollment_id}", response_model=EnrollmentRead)
def update_enrollment(
    enrollment_id: uuid.UUID,
    data: EnrollmentUpdate,
    db: DatabaseSession,
) -> EnrollmentRead:
    return EnrollmentService(db).update_enrollment(enrollment_id, data)


@router.delete("/enrollments/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_enrollment(enrollment_id: uuid.UUID, db: DatabaseSession) -> Response:
    EnrollmentService(db).cancel_enrollment(enrollment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
