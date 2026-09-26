from typing import Any
import calendar
import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MembershipClassType(str, Enum):
    GRUPAL_MENSUAL = "grupal_mensual"
    CLASE_LIBRE = "clase_libre"
    PARTICULAR_PAQUETE = "particular_paquete"


class MembershipPaymentStatus(str, Enum):
    PAID = "paid"
    PENDING = "pending"
    PARTIAL = "partial"


class MembershipStatus(str, Enum):
    ACTIVE = "active"
    EXPIRING_SOON = "expiring_soon"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class MembershipCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    client_id: uuid.UUID
    branch: str = Field(default="Los Olivos", max_length=50)
    class_type: MembershipClassType = MembershipClassType.GRUPAL_MENSUAL
    plan_name: str = Field(default="Mensualidad Marinera (8 clases)", min_length=1, max_length=150)
    period_month: str = Field(pattern=r"^\d{4}-\d{2}$")  # YYYY-MM
    start_date: date | None = None
    end_date: date | None = None
    classes_total: int = Field(default=8, ge=1, le=100)
    price: Decimal = Field(default=Decimal("150.00"), gt=0, max_digits=10, decimal_places=2)
    discount_applied: Decimal = Field(default=Decimal("0.00"), ge=0, max_digits=10, decimal_places=2)
    payment_status: MembershipPaymentStatus = MembershipPaymentStatus.PENDING
    is_recurring: bool = True
    auto_renew: bool = True
    notes: str | None = Field(default=None, max_length=5000)

    @model_validator(mode="after")
    def validate_dates_and_price(self) -> "MembershipCreate":
        if not self.start_date or not self.end_date:
            try:
                year, month = map(int, self.period_month.split("-"))
                _, last_day = calendar.monthrange(year, month)
                if not self.start_date:
                    self.start_date = date(year, month, 1)
                if not self.end_date:
                    self.end_date = date(year, month, last_day)
            except Exception:
                pass

        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("The end date cannot be earlier than the start date.")
        if self.discount_applied > self.price:
            raise ValueError("Discount cannot exceed membership base price.")
        return self


class MembershipUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    branch: str | None = Field(default=None, max_length=50)
    plan_name: str | None = Field(default=None, max_length=150)
    start_date: date | None = None
    end_date: date | None = None
    classes_total: int | None = Field(default=None, ge=1, le=100)
    classes_attended: int | None = Field(default=None, ge=0, le=100)
    payment_status: MembershipPaymentStatus | None = None
    status: MembershipStatus | None = None
    is_recurring: bool | None = None
    auto_renew: bool | None = None
    notes: str | None = Field(default=None, max_length=5000)


class MembershipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    client_name: str | None = None
    client_dni: str | None = None
    branch: str
    class_type: str
    plan_name: str
    period_month: str
    start_date: date
    end_date: date
    classes_total: int
    classes_attended: int
    price: Decimal
    discount_applied: Decimal
    final_price: Decimal
    payment_status: str
    status: str
    is_recurring: bool = True
    auto_renew: bool = True
    notes: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    is_expiring_within_5_days: bool | None = None

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
