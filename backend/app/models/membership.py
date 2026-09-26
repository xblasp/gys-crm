import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class Membership(Base):
    """
    Entidad de Membresía / Ciclo Mensual de Clases.
    
    Controla el paquete de clases del alumno (generalmente ciclo de 8 clases al mes):
    - period_month: Formato 'YYYY-MM' para reportería mensual y control contable.
    - classes_total / classes_attended: Control de aforo y asistencias consumidas.
    - payment_status: Estado de cobro ('paid', 'pending', 'partial').
    - status: Vigencia del ciclo ('active', 'expiring_soon', 'expired', 'cancelled').
    - auto_renew / is_recurring: Habilita generación periódica automática de cuotas mensuales.
    """

    __tablename__ = "memberships"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clients.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    client: Mapped["Client"] = relationship("Client", lazy="joined")
    branch: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="Los Olivos", index=True
    )  # Los Olivos, Comas
    class_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # grupal_mensual (8 clases), clase_libre, particular_paquete
    plan_name: Mapped[str] = mapped_column(String(150), nullable=False)
    period_month: Mapped[str] = mapped_column(
        String(7), nullable=False, index=True
    )  # YYYY-MM (e.g. 2026-08)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    classes_total: Mapped[int] = mapped_column(Integer, nullable=False, default=8)
    classes_attended: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    discount_applied: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00"), server_default="0.00"
    )
    final_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    payment_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending", server_default="pending", index=True
    )  # paid, pending, partial
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="active", server_default="active", index=True
    )  # active, expiring_soon, expired, cancelled
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_recurring: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    auto_renew: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
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
