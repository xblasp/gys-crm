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


def test_public_web_lead_ingestion(client: TestClient) -> None:
    # Section 9.2: Web leads auto-ingested into CRM
    response = client.post(
        "/public/leads",
        json={
            "first_name": "Sofía",
            "last_name": "Villanueva",
            "whatsapp": "+51 987654399",
            "email": "sofia@example.com",
            "preferred_branch": "Los Olivos",
            "class_interest": "grupal",
            "message": "Quisiera información para mi hija de 6 años.",
            "is_minor": True,
            "guardian_name": "Carmen Villanueva",
            "guardian_phone": "+51 987654399",
        },
    )
    assert response.status_code == 201
    res_data = response.json()
    assert "client_id" in res_data
    assert "interaction_id" in res_data
    assert res_data["preferred_branch"] == "Los Olivos"

    # Verify the client exists in CRM with source 'web' and status 'interested'
    client_res = client.get(f"/clients/{res_data['client_id']}")
    assert client_res.status_code == 200
    c = client_res.json()
    assert c["acquisition_source"] == "web"
    assert c["status"] == "interested"
    assert c["is_minor"] is True


def test_auth_login_and_user_creation(client: TestClient) -> None:
    # Login with seeded admin
    login_res = client.post(
        "/auth/login",
        json={"username": "admin_general", "password": "adminpassword123"},
    )
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert data["user"]["role"] == "admin_general"

    # Create new branch user
    user_res = client.post(
        "/auth/users",
        json={
            "username": "recepcion_olivos",
            "full_name": "Recepcionista Los Olivos",
            "email": "recepcion@garboysalero.pe",
            "password": "segurapassword123",
            "role": "admin_sede",
            "branch": "Los Olivos",
        },
    )
    assert user_res.status_code == 201
    assert user_res.json()["username"] == "recepcion_olivos"
