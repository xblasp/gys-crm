import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ClassType(str, Enum):
    GROUP = "group"
    PRIVATE = "private"
    FREE = "free"


class EnrollmentStatus(str, Enum):
    BOOKED = "booked"
    ATTENDED = "attended"
    CANCELLED = "cancelled"


class ClassSessionCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=150)
    class_type: ClassType
    branch: str = Field(default="Los Olivos", max_length=50)  # Los Olivos, Comas
    level: str = Field(default="intermedio", max_length=50)  # inicial, intermedio, avanzado, campeones
    age_group: str = Field(default="todas las edades", max_length=50)  # infantil, juvenil, adultos
    shift_time: str | None = Field(default=None, max_length=50)  # e.g. "Lunes y Miércoles 7-8pm", "Sábados 4-6pm"
    starts_at: datetime
    ends_at: datetime | None = None
    capacity: int = Field(ge=1, le=100)
    price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    instructor_name: str | None = Field(default=None, min_length=1, max_length=200)
    notes: str | None = Field(default=None, max_length=5_000)

    @model_validator(mode="after")
    def validate_class_details(self) -> "ClassSessionCreate":
        validate_class_details(
            class_type=self.class_type,
            capacity=self.capacity,
            starts_at=self.starts_at,
            ends_at=self.ends_at,
        )
        return self


class ClassSessionUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=150)
    class_type: ClassType | None = None
    branch: str | None = Field(default=None, max_length=50)
    level: str | None = Field(default=None, max_length=50)
    age_group: str | None = Field(default=None, max_length=50)
    shift_time: str | None = Field(default=None, max_length=50)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    capacity: int | None = Field(default=None, ge=1, le=100)
    price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    instructor_name: str | None = Field(default=None, min_length=1, max_length=200)
    notes: str | None = Field(default=None, max_length=5_000)

    @model_validator(mode="after")
    def must_include_a_field_to_update(self) -> "ClassSessionUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided to update a class session.")
        return self


class ClassSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    class_type: ClassType
    branch: str
    level: str
    age_group: str
    shift_time: str | None
    starts_at: datetime
    ends_at: datetime | None
    capacity: int
    price: Decimal | None
    instructor_name: str | None
    notes: str | None
    is_cancelled: bool
    created_at: datetime
    updated_at: datetime


class EnrollmentCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    client_id: uuid.UUID
    notes: str | None = Field(default=None, max_length=5_000)


class EnrollmentUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    status: EnrollmentStatus | None = None
    notes: str | None = Field(default=None, max_length=5_000)

    @model_validator(mode="after")
    def must_include_a_field_to_update(self) -> "EnrollmentUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided to update an enrollment.")
        return self


class EnrollmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    class_session_id: uuid.UUID
    status: EnrollmentStatus
    notes: str | None
    created_at: datetime
    updated_at: datetime


def validate_class_details(
    *,
    class_type: ClassType | str,
    capacity: int,
    starts_at: datetime,
    ends_at: datetime | None,
) -> None:
    if class_type == ClassType.PRIVATE and capacity != 1:
        raise ValueError("A private class must have a capacity of 1.")
    if class_type == ClassType.GROUP and capacity < 2:
        raise ValueError("A group class must have a capacity of at least 2.")
    if ends_at is not None and ends_at <= starts_at:
        raise ValueError("The end time must be after the start time.")
