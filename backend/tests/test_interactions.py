from collections.abc import Generator
from datetime import datetime, timedelta

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


def test_create_interaction_and_check_timeline(client: TestClient) -> None:
    # 1. Create client
    client_res = client.post(
        "/clients",
        json={
            "first_name": "Valeria",
            "last_name": "Mendoza",
            "dni": "72345678",
            "whatsapp": "+51 987654321",
            "birth_year": 2016,  # Minor
            "guardian_name": "Rosa Mendoza",
            "guardian_phone": "+51 987654321",
            "guardian_relationship": "Madre",
            "preferred_branch": "Los Olivos",
            "acquisition_source": "whatsapp",
        },
    )
    assert client_res.status_code == 201
    client_id = client_res.json()["id"]

    # 2. Register interaction (WhatsApp asking prices)
    interaction_res = client.post(
        "/interactions",
        json={
            "client_id": client_id,
            "channel": "whatsapp",
            "motive": "precios_y_horarios",
            "summary": "Consultó por marinera infantil sábados. Se enviaron horarios 4-6pm y precio S/ 150.",
            "result": "pidio_informacion",
            "attended_by": "Directora General",
            "reminder_active": True,
        },
    )
    assert interaction_res.status_code == 201
    assert interaction_res.json()["channel"] == "whatsapp"
    assert interaction_res.json()["reminder_active"] is True

    # 3. Check reminders list
    reminders_res = client.get("/interactions/reminders")
    assert reminders_res.status_code == 200
    assert len(reminders_res.json()) >= 1

    # 4. Check client 360 timeline
    timeline_res = client.get(f"/clients/{client_id}/timeline")
    assert timeline_res.status_code == 200
    timeline = timeline_res.json()
    assert len(timeline) >= 1
    assert "WHATSAPP" in timeline[0]["title"]


def test_interaction_enrollment_updates_client_status(client: TestClient) -> None:
    client_res = client.post(
        "/clients",
        json={
            "first_name": "Diego",
            "last_name": "Alvarez",
            "whatsapp": "+51 999111222",
            "status": "interested",
        },
    )
    client_id = client_res.json()["id"]

    # Interaction with result 'se_inscribio'
    client.post(
        "/interactions",
        json={
            "client_id": client_id,
            "channel": "presencial",
            "motive": "clase_prueba",
            "summary": "Asistió a clase de prueba y decidió inscribirse en el grupo de los sábados.",
            "result": "se_inscribio",
            "attended_by": "Recepción Los Olivos",
        },
    )

    # Verify client status changed to active
    updated_client = client.get(f"/clients/{client_id}").json()
    assert updated_client["status"] == "active"
    assert updated_client["is_active"] is True
