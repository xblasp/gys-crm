import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class ClassSession(Base):
    """
    Entidad de Sesión de Clase y Horarios Programados.
    
    Define los horarios de entrenamiento de marinera por sede:
    - branch: Sede donde se dicta la clase ('Los Olivos', 'Comas').
    - level / age_group: Nivel ('inicial', 'intermedio', 'avanzado') y grupo de edad ('infantil', 'juvenil_adultos').
    - capacity: Aforo máximo por aula para control de sobrecupo y asistencias.
    - instructor_name: Profesor o campeona a cargo del turno.
    """

    __tablename__ = "class_sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    class_type: Mapped[str] = mapped_column(String(20), nullable=False)
    branch: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="Los Olivos", index=True
    )
    level: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="intermedio"
    )
    age_group: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="todas las edades"
    )
    shift_time: Mapped[str | None] = mapped_column(String(50), nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    instructor_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_cancelled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
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
