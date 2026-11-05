from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.acceso_usuarios.models import Usuario
from app.modules.generacion_software.models import GeneracionCoordinada
from app.modules.modelado_uml.models import DiagramaUML
from app.modules.modelado_uml.services.servicio_uml import ServicioUML
from app.modules.notificaciones.models import Notificacion
from app.modules.proyectos_colaboracion.models import IntegranteProyecto
from app.modules.proyectos_colaboracion.repositories.repositorio_integrantes import (
    RepositorioIntegrantes,
)
from app.modules.proyectos_colaboracion.repositories.repositorio_proyectos import (
    RepositorioProyectos,
)
from app.modules.proyectos_colaboracion.schemas.movil import (
    DetalleDiagramaMovil,
    ResumenDiagramaMovil,
    ResumenGeneracionMovil,
    ResumenProyectoMovil,
)
from app.modules.proyectos_colaboracion.validators.validador_proyecto import asegurar_participacion


class ServicioLecturaMovil:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = RepositorioProyectos(db)
        self.members = RepositorioIntegrantes(db)

    def listar_proyectos(self, user_id: UUID) -> list[ResumenProyectoMovil]:
        summaries: list[ResumenProyectoMovil] = []
        for project in self.projects.listar_por_usuario(user_id):
            membership = asegurar_participacion(self.members.obtener_participacion(project.id, user_id))
            diagram_count = (
                self.db.scalar(
                    select(func.count(DiagramaUML.id)).where(DiagramaUML.project_id == project.id)
                )
                or 0
            )
            member_count = (
                self.db.scalar(
                    select(func.count(IntegranteProyecto.id)).where(
                        IntegranteProyecto.project_id == project.id
                    )
                )
                or 0
            )
            unread_notification_count = (
                self.db.scalar(
                    select(func.count(Notificacion.id)).where(
                        Notificacion.project_id == project.id,
                        Notificacion.recipient_user_id == user_id,
                        Notificacion.read_at.is_(None),
                        Notificacion.archived_at.is_(None),
                    )
                )
                or 0
            )
            summaries.append(
                ResumenProyectoMovil(
                    id=project.id,
                    name=project.name,
                    description=project.description,
                    project_role=membership.project_role,
                    status=project.status,
                    diagram_count=diagram_count,
                    member_count=member_count,
                    unread_notification_count=unread_notification_count,
                    updated_at=project.updated_at,
                )
            )
        return summaries

    def listar_diagramas(self, project_id: UUID, user_id: UUID) -> list[ResumenDiagramaMovil]:
        asegurar_participacion(self.members.obtener_participacion(project_id, user_id))
        rows = self.db.execute(
            select(
                DiagramaUML,
                Usuario.full_name,
            )
            .outerjoin(Usuario, Usuario.id == DiagramaUML.created_by_user_id)
            .where(DiagramaUML.project_id == project_id)
            .order_by(DiagramaUML.updated_at.desc())
        ).all()
        summaries = []
        uml_service = ServicioUML(self.db)
        for diagram, display_name in rows:
            model = uml_service.obtener_modelo_diagrama(diagram.id, user_id)
            summaries.append(
                ResumenDiagramaMovil(
                    id=diagram.id,
                    project_id=diagram.project_id,
                    name=diagram.name,
                    diagram_type=diagram.diagram_type,
                    class_count=len(model.classes),
                    relationship_count=len(model.relationships),
                    updated_at=diagram.updated_at,
                    updated_by_display_name=display_name,
                )
            )
        return summaries

    def obtener_diagrama(self, diagram_id: UUID, user_id: UUID) -> DetalleDiagramaMovil:
        diagram = self.db.get(DiagramaUML, diagram_id)
        if diagram is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Diagrama no encontrado"
            )
        asegurar_participacion(self.members.obtener_participacion(diagram.project_id, user_id))
        model = ServicioUML(self.db).obtener_modelo_diagrama(diagram_id, user_id)
        return DetalleDiagramaMovil(
            diagram=model.diagram,
            classes=model.classes,
            relationships=model.relationships,
            logical_version=diagram.current_version,
            can_read=True,
            can_edit=False,
        )

    def listar_generaciones(
        self, project_id: UUID, user_id: UUID, limit: int = 30
    ) -> list[ResumenGeneracionMovil]:
        asegurar_participacion(self.members.obtener_participacion(project_id, user_id))
        generations = self.db.scalars(
            select(GeneracionCoordinada)
            .where(GeneracionCoordinada.project_id == project_id)
            .order_by(GeneracionCoordinada.created_at.desc())
            .limit(limit)
        )
        return [
            ResumenGeneracionMovil(
                id=item.id,
                project_id=item.project_id,
                name=item.name,
                status=item.status,
                stage=item.stage,
                error_detail=item.error_detail,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            for item in generations
        ]
