import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class Client(Base):
    """
    Entidad de Alumno / Prospecto (Lead) en el CRM.
    
    Representa a cualquier persona que solicita información o está matriculada en el taller:
    - Prospectos (interested): Personas que contactan por WhatsApp, web o referidos.
    - Alumnos Activos (active): Alumnos con membresía vigente y clases asignadas.
    - Alumnos Retirados (retired): Alumnos que formalizaron su baja por cruce de horarios, economía, etc.
    - Soporte para Menores de Edad: Datos obligatorios del Padre/Madre/Apoderado.
    """

    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    dni: Mapped[str | None] = mapped_column(String(8), nullable=True, unique=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    whatsapp: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    birth_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_minor: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    guardian_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    guardian_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    guardian_relationship: Mapped[str | None] = mapped_column(String(50), nullable=True)
    guardian_dni: Mapped[str | None] = mapped_column(String(8), nullable=True)
    preferred_branch: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="interested", server_default="interested", index=True
    )
    acquisition_source: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="other"
    )
    referrer_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    referrer_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    uninterested_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)
    retired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
