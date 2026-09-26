import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class Payment(Base):
    """
    Entidad de Pago y Transacción Financiera de Caja.
    
    Registra todo ingreso monetario por conceptos de mensualidad, matrícula, clases libres o paquetes:
    - concept: Tipo de cobro ('mensualidad', 'matricula', 'clase_libre', 'paquete_particular').
    - payment_method: Canal ('efectivo', 'yape', 'plin', 'transferencia').
    - transaction_reference: Correlativo o N° de operación bancaria/billetera digital (e.g. OP-001045).
    - Auditoría de Anulación: Permite revocar pagos con motivo obligatorio (`cancellation_reason`),
      usuario autorizador (`cancelled_by`) y marca de tiempo (`cancelled_at`).
    """

    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clients.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    client: Mapped["Client"] = relationship("Client", lazy="joined")
    membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("memberships.id", ondelete="SET NULL"), nullable=True, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    payment_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now(), index=True
    )
    period_month: Mapped[str] = mapped_column(
        String(7), nullable=False, index=True
    )  # YYYY-MM (e.g. 2026-08)
    concept: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # mensualidad, matricula, clase_libre, paquete_particular, otro
    shift_detail: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # Turno o detalle del horario
    payment_method: Mapped[str] = mapped_column(
        String(30), nullable=False, index=True
    )  # efectivo, yape, plin, transferencia
    transaction_reference: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # Número de operación Yape/Plin o transferencia
    branch: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="Los Olivos", index=True
    )
    registered_by: Mapped[str] = mapped_column(String(150), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="completed", server_default="completed", index=True
    )  # completed, cancelled, refunded
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancelled_by: Mapped[str | None] = mapped_column(String(150), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
