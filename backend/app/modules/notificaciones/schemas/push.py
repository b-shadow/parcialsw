from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class PushKeys(BaseModel):
    p256dh: str = Field(min_length=16, max_length=512)
    auth: str = Field(min_length=8, max_length=256)


class PushSubscriptionCreate(BaseModel):
    endpoint: HttpUrl
    expiration_time: datetime | None = None
    keys: PushKeys


class PushSubscriptionDelete(BaseModel):
    endpoint: HttpUrl


class PushSubscriptionResponse(BaseModel):
    id: UUID
    endpoint: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PushConfigResponse(BaseModel):
    enabled: bool
    public_key: str | None = None
