from collections.abc import Generator
from datetime import date, timedelta

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


def test_membership_lifecycle_and_5_day_expiration(client: TestClient) -> None:
    # 1. Create client
    client_res = client.post(
        "/clients",
        json={"first_name": "Mariana", "last_name": "Paredes", "preferred_branch": "Comas"},
    )
    client_id = client_res.json()["id"]

    today = date.today()
    in_3_days = today + timedelta(days=3)

    # 2. Create membership expiring in 3 days (within 5-day alert threshold)
    mem_res = client.post(
        "/memberships",
        json={
            "client_id": client_id,
            "branch": "Comas",
            "class_type": "grupal_mensual",
            "plan_name": "Mensualidad Marinera Comas (8 clases)",
            "period_month": "2026-08",
            "start_date": str(today - timedelta(days=25)),
            "end_date": str(in_3_days),
            "classes_total": 8,
            "price": 150.00,
            "discount_applied": 20.00,  # Descuento S/ 20
            "payment_status": "pending",
        },
    )
    assert mem_res.status_code == 201
    membership_data = mem_res.json()
    assert float(membership_data["final_price"]) == 130.00
    membership_id = membership_data["id"]

    # 3. Check 5-day expiration alert endpoint (Section 6.4)
    expiring_res = client.get("/memberships/expiring?days=5")
    assert expiring_res.status_code == 200
    expiring_items = expiring_res.json()
    assert any(m["id"] == membership_id for m in expiring_items)


def test_payment_and_cancellation_with_audit(client: TestClient) -> None:
    # 1. Create client and membership
    client_res = client.post(
        "/clients",
        json={"first_name": "Carlos", "last_name": "Ramos", "preferred_branch": "Los Olivos"},
    )
    client_id = client_res.json()["id"]

    today = date.today()
    mem_res = client.post(
        "/memberships",
        json={
            "client_id": client_id,
            "branch": "Los Olivos",
            "class_type": "grupal_mensual",
            "plan_name": "Mensualidad Marinera Los Olivos",
            "period_month": "2026-08",
            "start_date": str(today),
            "end_date": str(today + timedelta(days=30)),
            "classes_total": 8,
            "price": 150.00,
            "payment_status": "pending",
        },
    )
    membership_id = mem_res.json()["id"]

    # 2. Record payment via Yape
    payment_res = client.post(
        "/payments",
        json={
            "client_id": client_id,
            "membership_id": membership_id,
            "amount": 150.00,
            "period_month": "2026-08",
            "concept": "mensualidad",
            "payment_method": "yape",
            "transaction_reference": "YAPE-998877",
            "branch": "Los Olivos",
            "registered_by": "Directora General",
        },
    )
    assert payment_res.status_code == 201
    payment_id = payment_res.json()["id"]
    assert payment_res.json()["status"] == "completed"

    # Membership should now be paid
    updated_mem = client.get(f"/memberships/{membership_id}").json()
    assert updated_mem["payment_status"] == "paid"

    # 3. Anulación de pago con motivo y autorizador (Section 6.5)
    cancel_res = client.post(
        f"/payments/{payment_id}/cancel",
        json={
            "cancellation_reason": "Error en el monto y duplicidad de Yape",
            "cancelled_by": "Directora General",
        },
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"
    assert cancel_res.json()["cancelled_by"] == "Directora General"

    # Membership reverts to pending
    reverted_mem = client.get(f"/memberships/{membership_id}").json()
    assert reverted_mem["payment_status"] == "pending"


def test_recurring_monthly_cycle_auto_generation(client: TestClient) -> None:
    # 1. Create active client without manual membership dates
    c_res = client.post(
        "/clients",
        json={
            "first_name": "Luciana",
            "last_name": "Espinoza",
            "status": "active",
            "preferred_branch": "Los Olivos",
        },
    )
    assert c_res.status_code == 201
    client_id = c_res.json()["id"]

    # 2. Query memberships for period 2026-09
    list_res = client.get("/memberships?period_month=2026-09&branch=Los Olivos")
    assert list_res.status_code == 200
    mems = list_res.json()
    
    # Active student must automatically have recurring membership created for 2026-09
    student_mem = next((m for m in mems if m["client_id"] == client_id), None)
    assert student_mem is not None
    assert student_mem["period_month"] == "2026-09"
    assert student_mem["start_date"] == "2026-09-01"
    assert student_mem["end_date"] == "2026-09-30"
    assert student_mem["classes_total"] == 8
    assert student_mem["payment_status"] == "pending"
    assert student_mem["is_recurring"] is True


def test_student_retirement_and_reactivation_flow(client: TestClient) -> None:
    # 1. Get retirement reasons list
    reasons_res = client.get("/clients/retirement-reasons/list")
    assert reasons_res.status_code == 200
    reasons = reasons_res.json()
    assert len(reasons) >= 8

    # 2. Create active student
    c_res = client.post(
        "/clients",
        json={
            "first_name": "Rodrigo",
            "last_name": "Salazar",
            "status": "active",
            "preferred_branch": "Comas",
        },
    )
    client_id = c_res.json()["id"]

    # Student has membership created
    mems_before = client.get(f"/memberships?client_id={client_id}").json()
    assert len(mems_before) >= 1
    assert mems_before[0]["status"] == "active"

    # 3. Retire student with preset reason
    retire_res = client.post(
        f"/clients/{client_id}/retire",
        json={
            "reason": "cruce_horarios",
            "notes": "Cruce con clases en la universidad por las noches.",
            "retired_by": "Directora General",
        },
    )
    assert retire_res.status_code == 200
    retired_client = retire_res.json()
    assert retired_client["status"] == "retired"
    assert retired_client["is_active"] is False
    assert "Cruce de Horarios" in retired_client["uninterested_reason"]

    # 4. Check active membership was cancelled
    mems_after = client.get(f"/memberships?client_id={client_id}").json()
    assert any(m["status"] == "cancelled" for m in mems_after)

    # 5. Check timeline has retirement event
    timeline = client.get(f"/clients/{client_id}/timeline").json()
    assert any("Baja / Retiro" in item["title"] or "retiro" in item["title"].lower() for item in timeline)

    # 6. Reactivate student
    reactivate_res = client.post(
        f"/clients/{client_id}/reactivate",
        json={
            "reactivated_by": "Directora General",
            "notes": "Retomó clases tras cambio de turno.",
        },
    )
    assert reactivate_res.status_code == 200
    active_client = reactivate_res.json()
    assert active_client["status"] == "active"
    assert active_client["is_active"] is True
