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


def create_client_record(client: TestClient) -> dict[str, object]:
    response = client.post(
        "/clients",
        json={
            "first_name": "Lucía",
            "last_name": "García",
            "phone": "+34 600 123 456",
            "email": "lucia@example.com",
            "acquisition_source": "referral",
            "referrer_name": "Carmen López",
            "referrer_phone": "+34 600 987 654",
            "notes": "Prefiere clases por la tarde.",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_create_and_get_client(client: TestClient) -> None:
    created = create_client_record(client)

    assert created["first_name"] == "Lucía"
    assert created["acquisition_source"] == "referral"
    assert created["referrer_phone"] == "+34 600 987 654"
    assert created["status"] == "interested"
    assert created["is_active"] is True

    response = client.get(f"/clients/{created['id']}")
    assert response.status_code == 200
    assert response.json()["email"] == "lucia@example.com"


def test_list_clients_excludes_inactive_by_default(client: TestClient) -> None:
    created = create_client_record(client)

    deactivation = client.delete(f"/clients/{created['id']}")
    assert deactivation.status_code == 204

    assert client.get("/clients").json() == []

    response = client.get("/clients?include_inactive=true")
    assert response.status_code == 200
    assert response.json()[0]["is_active"] is False


def test_update_client(client: TestClient) -> None:
    created = create_client_record(client)

    response = client.patch(
        f"/clients/{created['id']}",
        json={"phone": "+34 611 111 111", "acquisition_source": "social_media"},
    )

    assert response.status_code == 200
    assert response.json()["phone"] == "+34 611 111 111"
    assert response.json()["acquisition_source"] == "social_media"


def test_client_registration_captures_contact_and_status(client: TestClient) -> None:
    response = client.post(
        "/clients",
        json={
            "first_name": "María",
            "last_name": "Torres",
            "dni": "12345678",
            "whatsapp": "+51 999 999 999",
            "phone": "+51 999 999 999",
            "birth_year": 2014,
            "status": "active",
            "acquisition_source": "instagram",
        },
    )

    assert response.status_code == 201
    assert response.json()["dni"] == "12345678"
    assert response.json()["whatsapp"] == "+51 999 999 999"
    assert response.json()["status"] == "active"

    duplicate_dni = client.post(
        "/clients",
        json={"first_name": "Otra", "last_name": "Persona", "dni": "12345678"},
    )
    assert duplicate_dni.status_code == 409


def test_referral_requires_name_and_contact_number(client: TestClient) -> None:
    response = client.post(
        "/clients",
        json={
            "first_name": "Paola",
            "last_name": "Rojas",
            "acquisition_source": "referral",
            "referrer_name": "Luis Rojas",
        },
    )

    assert response.status_code == 422


def test_retiring_client_preserves_record_and_marks_it_inactive(client: TestClient) -> None:
    created = create_client_record(client)

    response = client.delete(f"/clients/{created['id']}")
    assert response.status_code == 204

    retired = client.get(f"/clients/{created['id']}")
    assert retired.status_code == 200
    assert retired.json()["status"] == "retired"
    assert retired.json()["is_active"] is False


def test_unknown_client_returns_not_found(client: TestClient) -> None:
    response = client.get("/clients/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json() == {"detail": "Client not found."}
