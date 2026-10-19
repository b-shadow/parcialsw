from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

ALLOWED_ROUTES = {
    "projects", "project_management", "project_collaborative", "project_diagram",
    "project_ai", "generation", "profile",
}


class NotificationDeepLink(BaseModel):
    model_config = ConfigDict(extra="forbid")
    route_name: str
    params: dict[str, str] = Field(default_factory=dict)
    query: dict[str, str] = Field(default_factory=dict)

    @field_validator("route_name")
    @classmethod
    def route_is_internal(cls, value: str) -> str:
        if value not in ALLOWED_ROUTES:
            raise ValueError("Destino interno no permitido")
        return value


class NotificationResponse(BaseModel):
    id: UUID
    project_id: UUID | None
    actor_user_id: UUID | None
    type: str
    severity: Literal["info", "success", "warning", "error"]
    title: str
    body: str
    resource_type: str | None
    resource_id: UUID | None
    deep_link: dict
    occurred_at: datetime
    read_at: datetime | None
    clicked_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class NotificationPageResponse(BaseModel):
    items: list[NotificationResponse]
    next_cursor: str | None
    has_more: bool


class UnreadCountResponse(BaseModel):
    count: int


class NotificationPreferenceItem(BaseModel):
    category: str = Field(min_length=1, max_length=80)
    project_id: UUID | None = None
    in_app_enabled: bool = True
    push_enabled: bool = True
    muted_until: datetime | None = None


class NotificationPreferencesUpdate(BaseModel):
    items: list[NotificationPreferenceItem] = Field(max_length=100)
