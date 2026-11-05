from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ContextoProyecto(BaseModel):
    id: UUID
    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)


class ContextoActor(BaseModel):
    id: UUID
    display_name: str = Field(min_length=1, max_length=160)
    project_role: str = Field(min_length=1, max_length=40)
    permissions: list[str] = Field(default_factory=list, max_length=100)


class ContextoDiagrama(BaseModel):
    id: UUID
    name: str
    current_version: int = Field(ge=0)
    classes: list[dict] = Field(default_factory=list, max_length=500)
    relationships: list[dict] = Field(default_factory=list, max_length=1000)


class ContextoMensajeReciente(BaseModel):
    sequence_number: int = Field(ge=1)
    role: Literal["user", "assistant", "system", "tool"]
    content: str = Field(max_length=4000)
    author_display_name: str | None = Field(default=None, max_length=160)


class ElementoActividadEquipo(BaseModel):
    user_id: UUID | None = None
    display_name: str
    actions: list[str] = Field(default_factory=list, max_length=10)
    last_at: datetime


class RestriccionesContexto(BaseModel):
    language: str = "es"
    offline: bool = True
    require_confirmation: bool = True
    surface: Literal["desktop", "mobile_readonly"] = "desktop"


class ContextoIAProyecto(BaseModel):
    project: ContextoProyecto
    actor: ContextoActor
    active_diagram: ContextoDiagrama | None = None
    recent_messages: list[ContextoMensajeReciente] = Field(default_factory=list, max_length=200)
    conversation_summary: str | None = Field(default=None, max_length=10000)
    available_versions: list[dict] = Field(default_factory=list, max_length=100)
    generation_state: dict = Field(default_factory=dict)
    team_activity: list[ElementoActividadEquipo] = Field(default_factory=list, max_length=30)
    constraints: RestriccionesContexto = Field(default_factory=RestriccionesContexto)
    context_reduced: bool = False
