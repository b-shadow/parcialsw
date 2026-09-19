from app.core.database.session import Base
from app.modules.acceso_usuarios.models import AuditLog, Role, User, UserRole, UserSession
from app.modules.generacion_software.models import (
    AiProcess,
    GeneratedArtifact,
    GeneratedBackend,
    GeneratedFrontend,
    UmlTransformation,
)
from app.modules.modelado_uml.models import (
    UmlAttribute,
    UmlClass,
    UmlDiagram,
    UmlMethod,
    UmlParameter,
    UmlRelationship,
    UmlVisualElement,
    XmiExchange,
)
from app.modules.proyectos_colaboracion.models import (
    CollaborationEvent,
    Project,
    ProjectInvitation,
    ProjectMember,
    ProjectPermission,
    ProjectVersion,
)

__all__ = [
    "AiProcess",
    "AuditLog",
    "Base",
    "CollaborationEvent",
    "GeneratedArtifact",
    "GeneratedBackend",
    "GeneratedFrontend",
    "Project",
    "ProjectInvitation",
    "ProjectMember",
    "ProjectPermission",
    "ProjectVersion",
    "Role",
    "UmlAttribute",
    "UmlClass",
    "UmlDiagram",
    "UmlMethod",
    "UmlParameter",
    "UmlRelationship",
    "UmlTransformation",
    "UmlVisualElement",
    "User",
    "UserRole",
    "UserSession",
    "XmiExchange",
]

