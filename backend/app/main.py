"""
GyS CRM — Backend Principal (FastAPI)
=====================================
Taller de Marinera Garbo & Salero Semillero de Campeones (Sedes Los Olivos & Comas)

Este archivo configura e inicializa el servidor FastAPI, gestionando:
- Inclusión de routers modulares (Clientes, Membresías, Pagos, Clases, Dashboard, etc.)
- Configuración de CORS y middleware de seguridad
- Montaje de archivos estáticos y despacho del Single Page Application (SPA)
- Ciclo de vida (lifespan) con migración ligera automática y carga de datos iniciales
"""

import os
import sys
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from backend.app.api.auth import router as auth_router
from backend.app.api.backup import router as backup_router
from backend.app.api.classes import router as classes_router
from backend.app.api.clients import router as clients_router
from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.interactions import router as interactions_router
from backend.app.api.memberships import router as memberships_router
from backend.app.api.payments import router as payments_router
from backend.app.api.promotions import router as promotions_router
from backend.app.api.public import router as public_router
from backend.app.core.config import get_settings
from backend.app.db.base import Base
from backend.app.db.session import SessionLocal, engine
from backend.app.models.class_session import ClassSession
from backend.app.models.client import Client
from backend.app.models.interaction import Interaction
from backend.app.models.membership import Membership
from backend.app.models.payment import Payment
from backend.app.models.promotion import Promotion
from backend.app.services.auth import AuthService

settings = get_settings()

def seed_initial_demo_data() -> None:
    """
    Inicializa datos de demostración y realiza migraciones ligeras idempotentes.
    
    Verifica y añade dinámicamente columnas necesarias si SQLite no las tiene,
    e inserta registros base (usuarios, promociones, clases y alumnos) si la base
    de datos se encuentra vacía o recién inicializada.
    """
    # Auto-add new columns to SQLite if they are missing
    try:
        with engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE clients ADD COLUMN retired_at TIMESTAMP"))
                conn.commit()
            except Exception:
                pass
            try:
                conn.execute(text("ALTER TABLE memberships ADD COLUMN is_recurring BOOLEAN DEFAULT 1"))
                conn.commit()
            except Exception:
                pass
            try:
                conn.execute(text("ALTER TABLE memberships ADD COLUMN auto_renew BOOLEAN DEFAULT 1"))
                conn.commit()
            except Exception:
                pass
    except Exception:
        pass

    db = SessionLocal()
    try:
        Base.metadata.create_all(bind=engine)
        auth_service = AuthService(db)
        auth_service.seed_initial_users_if_empty()

        if db.query(Client).count() < 10:
            from scripts.seed_demo_data import clear_and_seed_database
            clear_and_seed_database(db)
            return

            promos = [
                Promotion(
                    name="Descuento de S/ 20 por recomendación",
                    description="Descuento aplicado al alumno por traer un amigo/familiar referido.",
                    discount_type="fixed_amount",
                    discount_value=Decimal("20.00"),
                    is_active=True,
                ),
                Promotion(
                    name="Exoneración de Matrícula",
                    description="Matrícula 100% gratuita por campaña promocional.",
                    discount_type="enrollment_fee_waiver",
                    discount_value=Decimal("0.00"),
                    is_active=True,
                ),
                Promotion(
                    name="Descuento 10% Fiestas Patrias",
                    description="10% de descuento en la mensualidad regular.",
                    discount_type="percentage",
                    discount_value=Decimal("10.00"),
                    is_active=True,
                ),
            ]
            db.add_all(promos)
            db.commit()

        # 4. Seed Default Classes for Los Olivos & Comas if empty
        if not db.query(ClassSession).first():
            now = datetime.now()
            classes = [
                ClassSession(
                    name="Marinera Infantil Semillero (4-11 años)",
                    class_type="group",
                    branch="Los Olivos",
                    level="inicial",
                    age_group="infantil",
                    shift_time="Lunes y Miércoles 4:00 - 5:30 PM",
                    starts_at=now + timedelta(days=1, hours=16),
                    ends_at=now + timedelta(days=1, hours=17, minutes=30),
                    capacity=15,
                    price=Decimal("150.00"),
                    instructor_name="Prof. Carlos Mendoza",
                    notes="Sede Los Olivos - Sala Principal",
                ),
                ClassSession(
                    name="Marinera Juvenil & Adultos (12+ años)",
                    class_type="group",
                    branch="Los Olivos",
                    level="intermedio",
                    age_group="juvenil",
                    shift_time="Martes y Jueves 6:30 - 8:00 PM",
                    starts_at=now + timedelta(days=2, hours=18, minutes=30),
                    ends_at=now + timedelta(days=2, hours=20),
                    capacity=18,
                    price=Decimal("150.00"),
                    instructor_name="Prof. Andrea Benavides",
                    notes="Sede Los Olivos",
                ),
                ClassSession(
                    name="Marinera Campeones Concurso (Avanzado)",
                    class_type="group",
                    branch="Comas",
                    level="campeones",
                    age_group="todas las edades",
                    shift_time="Sábados 4:00 - 6:30 PM",
                    starts_at=now + timedelta(days=3, hours=16),
                    ends_at=now + timedelta(days=3, hours=18, minutes=30),
                    capacity=12,
                    price=Decimal("180.00"),
                    instructor_name="Prof. Carlos Mendoza",
                    notes="Sede Comas - Preparación intensiva",
                ),
                ClassSession(
                    name="Clase Particular Pareja Concurso",
                    class_type="private",
                    branch="Comas",
                    level="avanzado",
                    age_group="todas las edades",
                    shift_time="Viernes 5:00 - 6:00 PM (Coordinado)",
                    starts_at=now + timedelta(days=4, hours=17),
                    ends_at=now + timedelta(days=4, hours=18),
                    capacity=1,
                    price=Decimal("60.00"),
                    instructor_name="Prof. Andrea Benavides",
                    notes="Coordinación directa",
                ),
            ]
            db.add_all(classes)
            db.commit()

        # 5. Seed Initial Clients & Memberships if empty
        if not db.query(Client).first():
            c1 = Client(
                first_name="Lucía",
                last_name="García Torres",
                dni="74892154",
                whatsapp="+51 987654321",
                phone="+51 987654321",
                birth_year=2015,
                is_minor=True,
                guardian_name="Carmen Torres",
                guardian_phone="+51 987654321",
                guardian_relationship="Madre",
                guardian_dni="09876543",
                preferred_branch="Los Olivos",
                status="active",
                acquisition_source="whatsapp",
                notes="Alumna destacada, asiste turno tardes.",
            )
            c2 = Client(
                first_name="Mateo",
                last_name="Rojas Quispe",
                dni="71239845",
                whatsapp="+51 999888777",
                phone="+51 999888777",
                birth_year=2013,
                is_minor=True,
                guardian_name="Luis Rojas",
                guardian_phone="+51 999888777",
                guardian_relationship="Padre",
                preferred_branch="Comas",
                status="active",
                acquisition_source="referral",
                referrer_name="Carmen Torres",
                referrer_phone="+51 987654321",
                notes="Recomendado por Carmen Torres (recibió descuento S/ 20).",
            )
            c3 = Client(
                first_name="Valeria",
                last_name="Mendoza Vega",
                whatsapp="+51 955444333",
                phone="+51 955444333",
                birth_year=2003,
                is_minor=False,
                preferred_branch="Los Olivos",
                status="interested",
                acquisition_source="instagram",
                notes="Preguntó precios y horarios. Se coordinará clase de prueba.",
            )
            db.add_all([c1, c2, c3])
            db.commit()

            # Add sample memberships & payments
            current_month = datetime.now().strftime("%Y-%m")
            today = date.today()
            
            m1 = Membership(
                client_id=c1.id,
                branch="Los Olivos",
                class_type="grupal_mensual",
                plan_name="Mensualidad Marinera Infantil (8 clases)",
                period_month=current_month,
                start_date=today - timedelta(days=20),
                end_date=today + timedelta(days=3),  # Expiring in 3 days (shows in alert!)
                classes_total=8,
                classes_attended=7,
                price=Decimal("150.00"),
                discount_applied=Decimal("0.00"),
                final_price=Decimal("150.00"),
                payment_status="paid",
                status="active",
            )
            m2 = Membership(
                client_id=c2.id,
                branch="Comas",
                class_type="grupal_mensual",
                plan_name="Mensualidad Marinera Comas (8 clases)",
                period_month=current_month,
                start_date=today - timedelta(days=10),
                end_date=today + timedelta(days=20),
                classes_total=8,
                classes_attended=3,
                price=Decimal("150.00"),
                discount_applied=Decimal("20.00"),
                final_price=Decimal("130.00"),
                payment_status="paid",
                status="active",
            )
            db.add_all([m1, m2])
            db.commit()

            # Payments
            p1 = Payment(
                client_id=c1.id,
                membership_id=m1.id,
                amount=Decimal("150.00"),
                payment_date=datetime.now() - timedelta(days=20),
                period_month=current_month,
                concept="mensualidad",
                shift_detail="Lunes y Miércoles 4:00 - 5:30 PM",
                payment_method="yape",
                transaction_reference="YAPE-489123",
                branch="Los Olivos",
                registered_by="Directora General",
                status="completed",
            )
            p2 = Payment(
                client_id=c2.id,
                membership_id=m2.id,
                amount=Decimal("130.00"),
                payment_date=datetime.now() - timedelta(days=10),
                period_month=current_month,
                concept="mensualidad",
                shift_detail="Sábados 4:00 - 6:30 PM",
                payment_method="plin",
                transaction_reference="PLIN-908122",
                branch="Comas",
                registered_by="Administrador Comas",
                status="completed",
            )
            db.add_all([p1, p2])

            # Sample interaction
            it = Interaction(
                client_id=c3.id,
                channel="instagram",
                motive="precios_y_horarios",
                summary="Consultó por horarios para adultos en Los Olivos. Se enviaron horarios y precios.",
                result="pidio_informacion",
                attended_by="Directora General",
                next_followup_date=datetime.now() + timedelta(days=2),
                reminder_active=True,
            )
            db.add(it)
            db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestor de contexto para el ciclo de vida de la aplicación FastAPI.
    
    Ejecuta tareas de inicio (inicialización de tablas y datos demo) omitiendo
    el sembrado durante la ejecución de pruebas unitarias automatizadas (pytest).
    """
    if "pytest" not in sys.modules:
        try:
            seed_initial_demo_data()
        except Exception:
            pass
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="CRM Integral para el Taller de Marinera Garbo & Salero Semillero de Campeones (Los Olivos & Comas)",
    lifespan=lifespan,
)

# CORS middleware for web frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth_router)
app.include_router(clients_router)
app.include_router(classes_router)
app.include_router(promotions_router)
app.include_router(interactions_router)
app.include_router(memberships_router)
app.include_router(payments_router)
app.include_router(dashboard_router)
app.include_router(public_router)
app.include_router(backup_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """
    Endpoint de sondeo de salud (Healthcheck) para balanceadores y monitoreo de uptime.
    """
    return {
        "status": "ok",
        "application": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }


# Static files mount for Web SPA
frontend_path = Path(__file__).resolve().parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

    @app.get("/", include_in_schema=False)
    def serve_frontend_spa() -> FileResponse:
        """
        Sirve el punto de entrada principal (index.html) del Single Page Application (SPA).
        """
        index_file = frontend_path / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return FileResponse(frontend_path / "index.html")
