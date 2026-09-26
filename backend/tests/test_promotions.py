from collections.abc import Generator
from decimal import Decimal

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
        json={"first_name": "Lucía", "last_name": "García", "dni": "87654321"},
    )
    assert response.status_code == 201
    return response.json()


def test_promotion_is_applied_as_immutable_client_history(client: TestClient) -> None:
    client_record = create_client_record(client)
    promotion_response = client.post(
        "/promotions",
        json={
            "name": "S/20 por recomendación",
            "description": "Beneficio por traer a un nuevo alumno.",
            "discount_type": "fixed_amount",
            "discount_value": "20.00",
        },
    )
    assert promotion_response.status_code == 201
    promotion = promotion_response.json()

    application = client.post(
        f"/clients/{client_record['id']}/discounts",
        json={
            "promotion_id": promotion["id"],
            "reason": "Recomendó a una nueva alumna.",
            "applied_by": "Administración Los Olivos",
            "applies_to": "membership",
        },
    )
    assert application.status_code == 201
    assert application.json()["promotion_name"] == "S/20 por recomendación"
    assert Decimal(application.json()["discount_value"]) == Decimal("20.00")

    update = client.patch(
        f"/promotions/{promotion['id']}",
        json={"discount_value": "25.00"},
    )
    assert update.status_code == 200

    history = client.get(f"/clients/{client_record['id']}/discounts")
    assert history.status_code == 200
    assert Decimal(history.json()[0]["discount_value"]) == Decimal("20.00")


def test_manual_discount_and_inactive_promotion_rules(client: TestClient) -> None:
    client_record = create_client_record(client)

    manual_discount = client.post(
        f"/clients/{client_record['id']}/discounts",
        json={
            "promotion_name": "Precio especial por paquete de clases",
            "discount_type": "percentage",
            "discount_value": "10.00",
            "reason": "Paquete de ocho clases.",
            "applied_by": "Administración Comas",
        },
    )
    assert manual_discount.status_code == 201
    assert manual_discount.json()["promotion_id"] is None

    promotion = client.post(
        "/promotions",
        json={
            "name": "Matrícula sin costo",
            "discount_type": "enrollment_fee_waiver",
            "discount_value": "0.00",
        },
    ).json()
    assert client.delete(f"/promotions/{promotion['id']}").status_code == 204

    application = client.post(
        f"/clients/{client_record['id']}/discounts",
        json={
            "promotion_id": promotion["id"],
            "reason": "Promoción finalizada.",
            "applied_by": "Administración Comas",
        },
    )
    assert application.status_code == 409
