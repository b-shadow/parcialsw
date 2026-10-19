from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

WsEventTypeV2 = Literal[
    "AI_MESSAGE_CREATED",
    "AI_MESSAGE_STATUS_CHANGED",
    "AI_ACTION_PROPOSED",
    "AI_ACTION_STATUS_CHANGED",
    "AI_RECOMMENDATION_CREATED",
    "AI_RECOMMENDATION_STATUS_CHANGED",
    "AI_CONVERSATION_SUMMARY_UPDATED",
    "AI_PROCESSING_STARTED",
    "AI_PROCESSING_FINISHED",
    "AI_PROCESSING_FAILED",
    "PRESENCE_JOINED",
    "PRESENCE_LEFT",
    "PRESENCE_SNAPSHOT",
    "SYNC_REQUIRED",
    "FLUTTER_THEME_UPDATED",
    "PROJECT_VERSION_CREATED",
    "PROJECT_VERSION_RESTORED",
    "METHOD_SIGNATURE_UPDATED",
    "METHOD_SPECIFICATION_CREATED",
    "METHOD_SPECIFICATION_UPDATED",
    "METHOD_SPECIFICATION_DELETED",
    "METHOD_SPECIFICATION_REFINED",
]


class WebSocketActorV2(BaseModel):
    user_id: UUID | None = None
    display_name: str = Field(min_length=1, max_length=160)


class WebSocketEventV2(BaseModel):
    protocol_version: Literal[2] = 2
    type: WsEventTypeV2
    event_id: UUID
    project_id: UUID
    diagram_id: UUID | None = None
    sequence_number: int = Field(ge=0)
    conversation_sequence: int | None = Field(default=None, ge=0)
    persistent: bool = True
    correlation_id: UUID
    occurred_at: datetime
    actor: WebSocketActorV2
    payload: dict = Field(default_factory=dict)
