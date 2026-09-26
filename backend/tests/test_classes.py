from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.main import app


@pytest.fixture()
def client() -> Generator[TestClient]:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session]:
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def create_client_record(client: TestClient, *, email: str = "lucia@example.com") -> dict[str, object]:
    response = client.post(
        "/clients",
        json={
            "first_name": "Lucía",
            "last_name": "García",
            "email": email,
        },
    )
    assert response.status_code == 201
    return response.json()


def create_class_session(client: TestClient, *, capacity: int = 12) -> dict[str, object]:
    response = client.post(
        "/class-sessions",
        json={
            "name": "Marinera - nivel inicial",
            "class_type": "group",
            "starts_at": "2026-09-01T18:00:00+02:00",
            "ends_at": "2026-09-01T19:00:00+02:00",
            "capacity": capacity,
            "instructor_name": "Xavier",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_create_group_and_private_class_sessions(client: TestClient) -> None:
    group_class = create_class_session(client)
    assert group_class["class_type"] == "group"
    assert group_class["is_cancelled"] is False

    private_response = client.post(
        "/class-sessions",
        json={
            "name": "Clase privada",
            "class_type": "private",
            "starts_at": "2026-09-02T18:00:00+02:00",
            "capacity": 1,
        },
    )
    assert private_response.status_code == 201

    invalid_response = client.post(
        "/class-sessions",
        json={
            "name": "Clase privada incorrecta",
            "class_type": "private",
            "starts_at": "2026-09-02T19:00:00+02:00",
            "capacity": 2,
        },
    )
    assert invalid_response.status_code == 422


def test_enroll_client_and_list_enrollments(client: TestClient) -> None:
    client_record = create_client_record(client)
    class_session = create_class_session(client)

    response = client.post(
        f"/class-sessions/{class_session['id']}/enrollments",
        json={"client_id": client_record["id"], "notes": "Primera clase de prueba."},
    )
    assert response.status_code == 201
    enrollment = response.json()
    assert enrollment["status"] == "booked"

    class_enrollments = client.get(f"/class-sessions/{class_session['id']}/enrollments")
    assert class_enrollments.status_code == 200
    assert class_enrollments.json()[0]["client_id"] == client_record["id"]

    client_enrollments = client.get(f"/clients/{client_record['id']}/enrollments")
    assert client_enrollments.status_code == 200
    assert client_enrollments.json()[0]["class_session_id"] == class_session["id"]


def test_capacity_and_duplicate_enrollment_are_enforced(client: TestClient) -> None:
    first_client = create_client_record(client)
    second_client = create_client_record(client, email="marco@example.com")
    private_class = client.post(
        "/class-sessions",
        json={
            "name": "Clase privada",
            "class_type": "private",
            "starts_at": "2026-09-03T18:00:00+02:00",
            "capacity": 1,
        },
    ).json()

    first_enrollment = client.post(
        f"/class-sessions/{private_class['id']}/enrollments",
        json={"client_id": first_client["id"]},
    )
    assert first_enrollment.status_code == 201

    duplicate = client.post(
        f"/class-sessions/{private_class['id']}/enrollments",
        json={"client_id": first_client["id"]},
    )
    assert duplicate.status_code == 409

    full_class = client.post(
        f"/class-sessions/{private_class['id']}/enrollments",
        json={"client_id": second_client["id"]},
    )
    assert full_class.status_code == 409


def test_cancelling_an_enrollment_frees_a_place(client: TestClient) -> None:
    first_client = create_client_record(client)
    second_client = create_client_record(client, email="marco@example.com")
    private_class = client.post(
        "/class-sessions",
        json={
            "name": "Clase privada",
            "class_type": "private",
            "starts_at": "2026-09-03T18:00:00+02:00",
            "capacity": 1,
        },
    ).json()
    first_enrollment = client.post(
        f"/class-sessions/{private_class['id']}/enrollments",
        json={"client_id": first_client["id"]},
    ).json()

    cancellation = client.delete(f"/enrollments/{first_enrollment['id']}")
    assert cancellation.status_code == 204

    replacement = client.post(
        f"/class-sessions/{private_class['id']}/enrollments",
        json={"client_id": second_client["id"]},
    )
    assert replacement.status_code == 201
