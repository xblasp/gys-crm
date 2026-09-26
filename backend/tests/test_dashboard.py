from collections.abc import Generator
from datetime import datetime

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


def test_monthly_dashboard_metrics_and_quarterly_comparison(client: TestClient) -> None:
    current_month = datetime.now().strftime("%Y-%m")

    # 1. Create clients with different acquisition channels
    c1 = client.post(
        "/clients",
        json={
            "first_name": "Ana",
            "last_name": "Beltrán",
            "status": "active",
            "acquisition_source": "whatsapp",
            "preferred_branch": "Los Olivos",
        },
    ).json()

    c2 = client.post(
        "/clients",
        json={
            "first_name": "Pedro",
            "last_name": "Castillo",
            "status": "active",
            "acquisition_source": "instagram",
            "preferred_branch": "Comas",
        },
    ).json()

    # 2. Record payments in different modalities (Section 7.5)
    # Grupal mensual S/ 150
    client.post(
        "/payments",
        json={
            "client_id": c1["id"],
            "amount": 150.00,
            "period_month": current_month,
            "concept": "mensualidad",
            "payment_method": "yape",
            "branch": "Los Olivos",
            "registered_by": "Directora General",
        },
    )

    # Particular S/ 200
    client.post(
        "/payments",
        json={
            "client_id": c2["id"],
            "amount": 200.00,
            "period_month": current_month,
            "concept": "paquete_particular",
            "payment_method": "transferencia",
            "branch": "Comas",
            "registered_by": "Administrador Comas",
        },
    )

    # 3. Query Dashboard endpoint
    res = client.get(f"/dashboard/monthly?period_month={current_month}")
    assert res.status_code == 200
    dash = res.json()

    # Verify Section 7.1 Key Monthly Metrics
    assert float(dash["total_revenue"]) == 350.00
    assert dash["active_clients"] == 2
    assert dash["new_clients"] == 2

    # Verify Section 7.2 3-Month Sales Trend List
    assert len(dash["three_months_sales"]) == 3
    assert any(s["period_month"] == current_month and float(s["total_sales"]) == 350.00 for s in dash["three_months_sales"])

    # Verify Section 7.5 Modality Breakdown
    mod_totals = {m["modality"]: float(m["total_amount"]) for m in dash["revenue_by_modality"]}
    assert mod_totals.get("mensualidad") == 150.00
    assert mod_totals.get("paquete_particular") == 200.00

    # Verify Section 7.6 Channels
    channels = {c["source"]: c["clients_count"] for c in dash["acquisition_channels"]}
    assert channels.get("whatsapp", 0) >= 1
    assert channels.get("instagram", 0) >= 1
