import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class Interaction(Base):
    """
    Entidad de Bitácora y Seguimiento Comercial (CRM / Leads).
    
    Registra cada contacto sostenido con el cliente o prospecto:
    - channel: Canal de origen ('whatsapp', 'presencial', 'llamada', 'tiktok', 'instagram', 'web').
    - motive: Motivo ('precios_y_horarios', 'visita_local', 'clase_prueba', 'seguimiento').
    - result: Resultado comercial ('se_inscribio', 'vino_a_probarse', 'lo_pensara', 'no_respondio').
    - next_followup_date / reminder_active: Programación de alertas automáticas para llamadas de seguimiento.
    """

    __tablename__ = "interactions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    interaction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now(), index=True
    )
    channel: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # whatsapp, presencial, llamada, tiktok, instagram, web
    motive: Mapped[str] = mapped_column(
        String(150), nullable=False
    )  # precios_y_horarios, visita_local, particulares, clase_prueba, seguimiento
    summary: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # Detalle de lo conversado: turnos, horarios, precios
    result: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # pidio_informacion, vino_a_probarse, se_inscribio, lo_pensara, no_respondio
    uninterested_reason: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # precio, horario, ubicacion, lo_pensara, otros
    attended_by: Mapped[str] = mapped_column(
        String(150), nullable=False
    )  # Usuario o recepcionista que atendió
    next_followup_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    reminder_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false", index=True
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
