from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.modules.modelado_uml.schemas.uml import (
    RespuestaDetalleClaseUML,
    RespuestaDiagrama,
    RespuestaRelacionUML,
)


class ResumenProyectoMovil(BaseModel):
    id: UUID
    name: str
    description: str | None
    project_role: str
    status: str
    diagram_count: int
    member_count: int
    unread_notification_count: int
    updated_at: datetime


class ResumenDiagramaMovil(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    diagram_type: str
    class_count: int
    relationship_count: int
    updated_at: datetime
    updated_by_display_name: str | None


class DetalleDiagramaMovil(BaseModel):
    diagram: RespuestaDiagrama
    classes: list[RespuestaDetalleClaseUML]
    relationships: list[RespuestaRelacionUML]
    logical_version: int
    can_read: bool = True
    can_edit: bool = False


class ResumenGeneracionMovil(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    status: str
    stage: str
    error_detail: str | None
    created_at: datetime
    updated_at: datetime

