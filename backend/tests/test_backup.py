import json
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


def test_full_database_export_and_import(client: TestClient) -> None:
    # 1. Create a client and payment
    c_res = client.post(
        "/clients",
        json={
            "first_name": "Fabiana",
            "last_name": "Navarro",
            "dni": "76543210",
            "whatsapp": "+51 912345678",
            "preferred_branch": "Los Olivos",
            "status": "active",
        },
    )
    assert c_res.status_code == 201
    client_id = c_res.json()["id"]

    # 2. Export full database
    export_res = client.get("/backup/export-full")
    assert export_res.status_code == 200
    backup_data = export_res.json()
    assert "data" in backup_data
    assert "metadata" in backup_data
    assert backup_data["metadata"]["counts"]["clients"] >= 1

    # 3. Import full database back
    import_res = client.post("/backup/import-full", json=backup_data)
    assert import_res.status_code == 200
    assert import_res.json()["status"] == "success"


def test_clients_csv_export_and_import(client: TestClient) -> None:
    # 1. Export CSV template
    template_res = client.get("/backup/template-clients-csv")
    assert template_res.status_code == 200
    assert "Nombres" in template_res.text

    # 2. Import CSV data
    sample_csv = (
        "Nombres,Apellidos,DNI,WhatsApp,Telefono,Email,Anio_Nacimiento,Es_Menor,Nombre_Apoderado,Telefono_Apoderado,Parentesco_Apoderado,DNI_Apoderado,Sede_Preferida,Estado,Origen_Captacion,Referido_Por_Nombre,Referido_Por_Telefono,Notas\n"
        "Romina,Quispe Vega,74443322,+51 988776655,,romina@ejemplo.pe,2017,SI,Elena Vega,+51 988776655,Madre,08887766,Los Olivos,active,whatsapp,,,Alumna nueva\n"
        "Mateo,Salas Rivas,71112233,+51 977665544,,mateo@ejemplo.pe,2005,NO,,,,,Comas,interested,instagram,,,Interesado en marinera\n"
    )

    import_res = client.post(
        "/backup/import-clients-csv",
        content=sample_csv,
        headers={"Content-Type": "text/plain"},
    )
    assert import_res.status_code == 200
    result = import_res.json()
    assert result["imported_count"] == 2

    # 3. Verify imported clients exist in CRM
    clients_res = client.get("/clients")
    assert clients_res.status_code == 200
    names = [c["first_name"] for c in clients_res.json()]
    assert "Romina" in names
    assert "Mateo" in names

    # 4. Verify CSV Export
    export_csv_res = client.get("/backup/export-clients-csv")
    assert export_csv_res.status_code == 200
    assert "Romina" in export_csv_res.text
    assert "Mateo" in export_csv_res.text
