from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

ACTION_LABELS: dict[str, str] = {
    "CREATE_CLASS": "Creó la clase",
    "UPDATE_CLASS": "Editó la clase",
    "DELETE_CLASS": "Eliminó la clase",
    "CREATE_ATTRIBUTE": "Agregó el atributo",
    "UPDATE_ATTRIBUTE": "Editó el atributo",
    "DELETE_ATTRIBUTE": "Eliminó el atributo",
    "CREATE_METHOD": "Agregó el método",
    "UPDATE_METHOD": "Editó el método",
    "DELETE_METHOD": "Eliminó el método",
    "CREATE_PARAMETER": "Agregó el parámetro",
    "UPDATE_PARAMETER": "Editó el parámetro",
    "DELETE_PARAMETER": "Eliminó el parámetro",
    "CREATE_RELATION": "Relacionó clases",
    "UPDATE_RELATION": "Editó la relación",
    "DELETE_RELATION": "Eliminó la relación",
    "MOVE_ELEMENT": "Movió elemento en el lienzo",
    "CREATE_DIAGRAM": "Creó el diagrama",
    "DELETE_DIAGRAM": "Eliminó el diagrama",
    "CREATE_PROJECT": "Creó el proyecto",
    "UPDATE_PROJECT": "Actualizó el proyecto",
    "DELETE_PROJECT": "Eliminó el proyecto",
    "ADD_PROJECT_MEMBER": "Agregó un integrante",
    "UPDATE_PROJECT_MEMBER": "Actualizó un integrante",
    "REMOVE_PROJECT_MEMBER": "Retiró un integrante",
    "SET_PROJECT_PERMISSION": "Modificó permisos de integrante",
    "CREATE_PROJECT_VERSION": "Guardó una versión",
    "RESTORE_PROJECT_VERSION": "Restauró una versión",
    "IMPORT_XMI": "Importó un XMI",
    "IMPORT_XMI_REPLACE_DIAGRAM": "Reemplazó diagrama desde XMI",
    "EXPORT_XMI": "Exportó a XMI",
    "TRANSFORM_UML": "Transformó el modelo UML",
    "GENERATE_BACKEND": "Generó backend Spring Boot",
    "GENERATE_FRONTEND": "Generó frontend Flutter",
    "GENERATE_COORDINATED": "Generó Spring Boot y Flutter",
    "GENERATE_UML_FROM_SOURCE": "Generó UML desde fuente",
    "FLUTTER_THEME_UPDATED": "Actualizó el tema Flutter",
    "FLUTTER_THEME_PRESET_CREATED": "Creó preset de tema Flutter",
    "FLUTTER_THEME_PRESET_UPDATED": "Actualizó preset de tema Flutter",
    "FLUTTER_THEME_PRESET_DELETED": "Eliminó preset de tema Flutter",
    "CREATE_METHOD_SPECIFICATION": "Especificó método funcional",
    "UPDATE_METHOD_SPECIFICATION": "Actualizó especificación de método",
    "REFINE_METHOD_SPECIFICATION": "Refinó especificación con IA",
    "LOGIN": "Inició sesión",
    "CHANGE_PASSWORD": "Cambió contraseña",
    "REGISTER_USER": "Registró usuario",
    "UPDATE_USER": "Actualizó usuario",
}

GLOBAL_STREAM: str = "changelog:all"


def project_stream_key(project_id: UUID | str) -> str:
    return f"changelog:project:{project_id}"


def build_summary(action: str, metadata: dict) -> str:
    label = ACTION_LABELS.get(action, action.replace("_", " ").capitalize())
    name = (
        metadata.get("name")
        or metadata.get("class_name")
        or metadata.get("target_name")
        or metadata.get("title")
        or ""
    )
    if name:
        summary = f"{label} {name}".strip()
    else:
        summary = label
    return summary[:200]


class PendingChange(BaseModel):
    project_id: UUID
    actor_user_id: UUID | None = None
    source: Literal["ui", "ai", "ws", "system"] = "ui"
    module: str
    action: str
    entity_type: str | None = None
    entity_id: str | None = None
    diagram_id: UUID | None = None
    metadata: dict = Field(default_factory=dict)


class ChangeLogEntry(BaseModel):
    id: str
    project_id: UUID
    occurred_at: datetime
    actor_user_id: UUID | None = None
    actor_display_name: str | None = None
    source: Literal["ui", "ai", "ws", "system"]
    module: str
    action: str
    entity_type: str | None = None
    entity_id: str | None = None
    diagram_id: UUID | None = None
    summary: str
    metadata: dict = Field(default_factory=dict)


class ChangeLogPage(BaseModel):
    items: list[ChangeLogEntry]
    next_cursor: str | None = None
    source: Literal["redis", "postgres_fallback"]
