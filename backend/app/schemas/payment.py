from typing import Any
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PaymentMethod(str, Enum):
    EFECTIVO = "efectivo"
    YAPE = "yape"
    PLIN = "plin"
    TRANSFERENCIA = "transferencia"


class PaymentConcept(str, Enum):
    MENSUALIDAD = "mensualidad"
    MATRICULA = "matricula"
    CLASE_LIBRE = "clase_libre"
    PAQUETE_PARTICULAR = "paquete_particular"
    OTRO = "otro"


class PaymentStatus(str, Enum):
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    client_id: uuid.UUID
    membership_id: uuid.UUID | None = None
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    payment_date: datetime | None = None
    period_month: str = Field(pattern=r"^\d{4}-\d{2}$")  # YYYY-MM
    concept: PaymentConcept = PaymentConcept.MENSUALIDAD
    shift_detail: str | None = Field(default=None, max_length=100)
    payment_method: PaymentMethod = PaymentMethod.YAPE
    transaction_reference: str | None = Field(default=None, max_length=100)
    branch: str = Field(default="Los Olivos", max_length=50)
    registered_by: str = Field(min_length=1, max_length=150)
    notes: str | None = Field(default=None, max_length=5000)


class PaymentCancel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    cancellation_reason: str = Field(min_length=3, max_length=5000)
    cancelled_by: str = Field(min_length=1, max_length=150)  # Must be Admin General


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    client_name: str | None = None
    client_dni: str | None = None
    membership_id: uuid.UUID | None
    amount: Decimal
    payment_date: datetime
    period_month: str
    concept: str
    shift_detail: str | None
    payment_method: str
    transaction_reference: str | None
    branch: str
    registered_by: str
    status: str
    cancellation_reason: str | None
    cancelled_by: str | None
    cancelled_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def populate_client_details(cls, data: Any) -> Any:
        if hasattr(data, "client") and data.client:
            name = f"{data.client.first_name} {data.client.last_name}"
            dni = getattr(data.client, "dni", None)
            if hasattr(data, "__dict__"):
                data.__dict__["client_name"] = name
                data.__dict__["client_dni"] = dni
        elif isinstance(data, dict):
            if "client" in data and data["client"]:
                c = data["client"]
                if hasattr(c, "first_name"):
                    data["client_name"] = f"{c.first_name} {c.last_name}"
                    data["client_dni"] = getattr(c, "dni", None)
                elif isinstance(c, dict):
                    data["client_name"] = f"{c.get('first_name', '')} {c.get('last_name', '')}".strip()
                    data["client_dni"] = c.get("dni")
        return data
