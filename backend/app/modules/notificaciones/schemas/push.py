from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class ClavesPush(BaseModel):
    p256dh: str = Field(min_length=16, max_length=512)
    auth: str = Field(min_length=8, max_length=256)


class CreacionSuscripcionPush(BaseModel):
    endpoint: HttpUrl
    expiration_time: datetime | None = None
    keys: ClavesPush


class EliminacionSuscripcionPush(BaseModel):
    endpoint: HttpUrl


class RespuestaSuscripcionPush(BaseModel):
    id: UUID
    endpoint: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class RespuestaConfiguracionPush(BaseModel):
    enabled: bool
    public_key: str | None = None


class RegistroDispositivoMovil(BaseModel):
    endpoint: str = Field(min_length=10, max_length=2048)
