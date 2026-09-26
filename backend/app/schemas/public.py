import uuid
from pydantic import BaseModel, ConfigDict, Field


class PublicLeadCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=30)
    whatsapp: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=255)
    birth_year: int | None = Field(default=None, ge=1900, le=2100)
    is_minor: bool = False
    guardian_name: str | None = Field(default=None, max_length=200)
    guardian_phone: str | None = Field(default=None, max_length=30)
    preferred_branch: str = Field(default="Los Olivos", max_length=50)  # Los Olivos, Comas
    class_interest: str = Field(default="grupal", max_length=50)  # grupal, libre, particular, prueba
    message: str | None = Field(default=None, max_length=2000)


class PublicLeadResponse(BaseModel):
    client_id: uuid.UUID
    interaction_id: uuid.UUID
    message: str
    preferred_branch: str
