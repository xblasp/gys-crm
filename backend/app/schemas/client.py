import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ClientAcquisitionSource(str, Enum):
    REFERRAL = "referral"
    RECOMENDACION = "recomendacion"
    IN_PERSON = "in_person"
    PRESENCIAL = "presencial"
    WHATSAPP = "whatsapp"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    WEB = "web"

    # Legacy values are kept so existing records and API consumers remain valid.
    SOCIAL_MEDIA = "social_media"
    WEBSITE = "website"
    WALK_IN = "walk_in"
    OTHER = "other"


class ClientStatus(str, Enum):
    INTERESTED = "interested"
    ACTIVE = "active"
    RETIRED = "retired"


class BranchName(str, Enum):
    LOS_OLIVOS = "Los Olivos"
    COMAS = "Comas"
    TODAS = "Todas"


def _validate_referral_details(
    acquisition_source: ClientAcquisitionSource | str | None,
    referrer_name: str | None,
    referrer_phone: str | None,
) -> None:
    if acquisition_source in (ClientAcquisitionSource.REFERRAL, "referral", "recomendacion") and (
        not referrer_name or not referrer_phone
    ):
        raise ValueError(
            "A referral source requires the referrer's name and contact number."
        )


class ClientCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    dni: str | None = Field(default=None, pattern=r"^\d{8}$")
    phone: str | None = Field(default=None, min_length=1, max_length=30)
    whatsapp: str | None = Field(default=None, min_length=1, max_length=30)
    email: str | None = Field(default=None, min_length=3, max_length=255)
    birth_year: int | None = Field(default=None, ge=1900, le=2100)
    is_minor: bool = False
    guardian_name: str | None = Field(default=None, max_length=200)
    guardian_phone: str | None = Field(default=None, max_length=30)
    guardian_relationship: str | None = Field(default=None, max_length=50)  # Padre, Madre, Tutor
    guardian_dni: str | None = Field(default=None, pattern=r"^\d{8}$")
    preferred_branch: str | None = Field(default="Los Olivos", max_length=50)
    status: ClientStatus = ClientStatus.INTERESTED
    acquisition_source: ClientAcquisitionSource = ClientAcquisitionSource.OTHER
    referrer_name: str | None = Field(default=None, min_length=1, max_length=200)
    referrer_phone: str | None = Field(default=None, min_length=1, max_length=30)
    uninterested_reason: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=5_000)

    @model_validator(mode="after")
    def validate_rules(self) -> "ClientCreate":
        _validate_referral_details(
            self.acquisition_source, self.referrer_name, self.referrer_phone
        )
        if self.birth_year and (datetime.now().year - self.birth_year) < 18:
            self.is_minor = True
        return self


class ClientUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    dni: str | None = Field(default=None, pattern=r"^\d{8}$")
    phone: str | None = Field(default=None, min_length=1, max_length=30)
    whatsapp: str | None = Field(default=None, min_length=1, max_length=30)
    email: str | None = Field(default=None, min_length=3, max_length=255)
    birth_year: int | None = Field(default=None, ge=1900, le=2100)
    is_minor: bool | None = None
    guardian_name: str | None = Field(default=None, max_length=200)
    guardian_phone: str | None = Field(default=None, max_length=30)
    guardian_relationship: str | None = Field(default=None, max_length=50)
    guardian_dni: str | None = Field(default=None, pattern=r"^\d{8}$")
    preferred_branch: str | None = Field(default=None, max_length=50)
    status: ClientStatus | None = None
    acquisition_source: ClientAcquisitionSource | None = None
    referrer_name: str | None = Field(default=None, min_length=1, max_length=200)
    referrer_phone: str | None = Field(default=None, min_length=1, max_length=30)
    uninterested_reason: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=5_000)

    @model_validator(mode="after")
    def must_include_a_field_to_update(self) -> "ClientUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided to update a client.")
        return self


class ClientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_name: str
    last_name: str
    dni: str | None
    phone: str | None
    whatsapp: str | None
    email: str | None
    birth_year: int | None
    is_minor: bool
    guardian_name: str | None
    guardian_phone: str | None
    guardian_relationship: str | None
    guardian_dni: str | None
    preferred_branch: str | None
    status: ClientStatus
    acquisition_source: ClientAcquisitionSource
    referrer_name: str | None
    referrer_phone: str | None
    uninterested_reason: str | None
    retired_at: datetime | None = None
    notes: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RetirementReason(str, Enum):
    CRUCE_HORARIOS = "cruce_horarios"
    ECONOMICO_PRECIO = "economico_precio"
    DISTANCIA_MUDANZA = "distancia_mudanza"
    SALUD_LESION = "salud_lesion"
    VIAJE_TEMPORAL = "viaje_temporal"
    FIN_TEMPORADA = "fin_temporada"
    INSATISFACCION = "insatisfaccion"
    PERSONAL_FAMILIAR = "personal_familiar"
    OTRO = "otro"


RETIREMENT_REASON_LABELS: dict[str, str] = {
    "cruce_horarios": "Cruce de Horarios (Colegio / Universidad / Trabajo)",
    "economico_precio": "Precio / Situación Económica",
    "distancia_mudanza": "Distancia / Cambio de Domicilio",
    "salud_lesion": "Salud o Lesión",
    "viaje_temporal": "Viaje o Ausencia Temporal",
    "fin_temporada": "Culminó Temporada / Vacaciones",
    "insatisfaccion": "Insatisfacción con la Clase o Servicio",
    "personal_familiar": "Motivos Personales / Familiares",
    "otro": "Otro Motivo",
}


class ClientRetireRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    reason: str = Field(min_length=1, max_length=100)
    notes: str | None = Field(default=None, max_length=2000)
    retired_by: str = Field(default="Administrador", max_length=150)


class ClientReactivateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    reactivated_by: str = Field(default="Administrador", max_length=150)
    notes: str | None = Field(default=None, max_length=2000)

