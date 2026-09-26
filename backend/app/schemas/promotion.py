import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DiscountType(str, Enum):
    FIXED_AMOUNT = "fixed_amount"
    PERCENTAGE = "percentage"
    ENROLLMENT_FEE_WAIVER = "enrollment_fee_waiver"


class DiscountAppliesTo(str, Enum):
    ENROLLMENT = "enrollment"
    MEMBERSHIP = "membership"
    OTHER = "other"


def validate_discount_value(discount_type: DiscountType | str, value: Decimal) -> None:
    if discount_type == DiscountType.ENROLLMENT_FEE_WAIVER:
        if value != 0:
            raise ValueError("An enrollment fee waiver must have a discount value of 0.")
        return

    if value <= 0:
        raise ValueError("The discount value must be greater than 0.")
    if discount_type == DiscountType.PERCENTAGE and value > 100:
        raise ValueError("A percentage discount cannot exceed 100.")


class PromotionCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=5_000)
    discount_type: DiscountType
    discount_value: Decimal = Field(ge=0, max_digits=10, decimal_places=2)

    @model_validator(mode="after")
    def has_valid_discount_value(self) -> "PromotionCreate":
        validate_discount_value(self.discount_type, self.discount_value)
        return self


class PromotionUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=5_000)
    discount_type: DiscountType | None = None
    discount_value: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    is_active: bool | None = None

    @model_validator(mode="after")
    def must_include_a_field_to_update(self) -> "PromotionUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided to update a promotion.")
        return self


class PromotionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    discount_type: DiscountType
    discount_value: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ClientDiscountCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    promotion_id: uuid.UUID | None = None
    promotion_name: str | None = Field(default=None, min_length=1, max_length=150)
    discount_type: DiscountType | None = None
    discount_value: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    applies_to: DiscountAppliesTo = DiscountAppliesTo.ENROLLMENT
    reason: str = Field(min_length=1, max_length=5_000)
    applied_by: str = Field(min_length=1, max_length=150)

    @model_validator(mode="after")
    def uses_a_promotion_or_a_complete_manual_discount(self) -> "ClientDiscountCreate":
        if self.promotion_id is not None:
            if any(
                value is not None
                for value in (self.promotion_name, self.discount_type, self.discount_value)
            ):
                raise ValueError(
                    "Do not send manual discount fields when applying a saved promotion."
                )
            return self

        if None in (self.promotion_name, self.discount_type, self.discount_value):
            raise ValueError(
                "A manual discount requires promotion_name, discount_type, and discount_value."
            )
        validate_discount_value(self.discount_type, self.discount_value)
        return self


class ClientDiscountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    promotion_id: uuid.UUID | None
    promotion_name: str
    discount_type: DiscountType
    discount_value: Decimal
    applies_to: DiscountAppliesTo
    reason: str
    applied_by: str
    applied_at: datetime
