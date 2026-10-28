from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectContext(BaseModel):
    id: UUID
    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)


class ActorContext(BaseModel):
    id: UUID
    display_name: str = Field(min_length=1, max_length=160)
    project_role: str = Field(min_length=1, max_length=40)
    permissions: list[str] = Field(default_factory=list, max_length=100)


class DiagramContext(BaseModel):
    id: UUID
    name: str
    current_version: int = Field(ge=0)
    classes: list[dict] = Field(default_factory=list, max_length=500)
    relationships: list[dict] = Field(default_factory=list, max_length=1000)


class RecentMessageContext(BaseModel):
    sequence_number: int = Field(ge=1)
    role: Literal["user", "assistant", "system", "tool"]
    content: str = Field(max_length=4000)
    author_display_name: str | None = Field(default=None, max_length=160)


class TeamActivityItem(BaseModel):
    user_id: UUID | None = None
    display_name: str
    actions: list[str] = Field(default_factory=list, max_length=10)
    last_at: datetime


class ContextConstraints(BaseModel):
    language: str = "es"
    offline: bool = True
    require_confirmation: bool = True
    surface: Literal["desktop", "mobile_readonly"] = "desktop"


class AiProjectContext(BaseModel):
    project: ProjectContext
    actor: ActorContext
    active_diagram: DiagramContext | None = None
    recent_messages: list[RecentMessageContext] = Field(default_factory=list, max_length=200)
    conversation_summary: str | None = Field(default=None, max_length=10000)
    available_versions: list[dict] = Field(default_factory=list, max_length=100)
    generation_state: dict = Field(default_factory=dict)
    team_activity: list[TeamActivityItem] = Field(default_factory=list, max_length=30)
    constraints: ContextConstraints = Field(default_factory=ContextConstraints)
    context_reduced: bool = False
