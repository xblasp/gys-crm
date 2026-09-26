import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class InteractionChannel(str, Enum):
    WHATSAPP = "whatsapp"
    PRESENCIAL = "presencial"
    LLAMADA = "llamada"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    WEB = "web"


class InteractionMotive(str, Enum):
    PRECIOS_Y_HORARIOS = "precios_y_horarios"
    VISITA_LOCAL = "visita_local"
    PARTICULARES = "particulares"
    CLASE_PRUEBA = "clase_prueba"
    SEGUIMIENTO = "seguimiento"
    OTRO = "otro"


class InteractionResult(str, Enum):
    PIDIO_INFORMACION = "pidio_informacion"
    VINO_A_PROBARSE = "vino_a_probarse"
    SE_INSCRIBIO = "se_inscribio"
    LO_PENSARA = "lo_pensara"
    NO_RESPONDIO = "no_respondio"


class InteractionCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    client_id: uuid.UUID
    interaction_date: datetime | None = None
    channel: InteractionChannel
    motive: InteractionMotive
    summary: str = Field(min_length=1, max_length=5000)
    result: InteractionResult
    uninterested_reason: str | None = Field(default=None, max_length=100)
    attended_by: str = Field(min_length=1, max_length=150)
    next_followup_date: datetime | None = None
    reminder_active: bool = False

    @model_validator(mode="after")
    def auto_set_reminder(self) -> "InteractionCreate":
        if self.next_followup_date is not None or self.result in {
            InteractionResult.LO_PENSARA,
            InteractionResult.NO_RESPONDIO,
            InteractionResult.PIDIO_INFORMACION,
        }:
            self.reminder_active = True
        return self


class InteractionUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    channel: InteractionChannel | None = None
    motive: InteractionMotive | None = None
    summary: str | None = Field(default=None, max_length=5000)
    result: InteractionResult | None = None
    uninterested_reason: str | None = Field(default=None, max_length=100)
    attended_by: str | None = Field(default=None, max_length=150)
    next_followup_date: datetime | None = None
    reminder_active: bool | None = None


class InteractionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    interaction_date: datetime
    channel: InteractionChannel
    motive: InteractionMotive
    summary: str
    result: InteractionResult
    uninterested_reason: str | None
    attended_by: str
    next_followup_date: datetime | None
    reminder_active: bool
    created_at: datetime
    updated_at: datetime


class ClientTimelineItem(BaseModel):
    event_type: str  # interaction, enrollment, payment, discount
    title: str
    description: str
    timestamp: datetime
    author_or_channel: str
    status_or_result: str | None = None
    amount: float | None = None
