from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.acceso_usuarios.models import User
from app.modules.generacion_software.models import CoordinatedGeneration
from app.modules.modelado_uml.models import UmlClass, UmlDiagram, UmlRelationship
from app.modules.modelado_uml.services.uml_service import UmlService
from app.modules.notificaciones.models import Notification
from app.modules.proyectos_colaboracion.models import ProjectMember
from app.modules.proyectos_colaboracion.repositories.member_repository import MemberRepository
from app.modules.proyectos_colaboracion.repositories.project_repository import ProjectRepository
from app.modules.proyectos_colaboracion.schemas.mobile import (
    MobileDiagramDetail,
    MobileDiagramSummary,
    MobileGenerationSummary,
    MobileProjectSummary,
)
from app.modules.proyectos_colaboracion.validators.project_validator import ensure_membership


class MobileReadService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.members = MemberRepository(db)

    def list_projects(self, user_id: UUID) -> list[MobileProjectSummary]:
        summaries: list[MobileProjectSummary] = []
        for project in self.projects.list_for_user(user_id):
            membership = ensure_membership(
                self.members.get_membership(project.id, user_id)
            )
            diagram_count = self.db.scalar(
                select(func.count(UmlDiagram.id)).where(UmlDiagram.project_id == project.id)
            ) or 0
            member_count = self.db.scalar(
                select(func.count(ProjectMember.id)).where(
                    ProjectMember.project_id == project.id
                )
            ) or 0
            unread_notification_count = self.db.scalar(
                select(func.count(Notification.id)).where(
                    Notification.project_id == project.id,
                    Notification.recipient_user_id == user_id,
                    Notification.read_at.is_(None),
                    Notification.archived_at.is_(None),
                )
            ) or 0
            summaries.append(
                MobileProjectSummary(
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

    def list_diagrams(self, project_id: UUID, user_id: UUID) -> list[MobileDiagramSummary]:
        ensure_membership(self.members.get_membership(project_id, user_id))
        rows = self.db.execute(
            select(
                UmlDiagram,
                func.count(func.distinct(UmlClass.id)),
                func.count(func.distinct(UmlRelationship.id)),
                User.full_name,
            )
            .outerjoin(UmlClass, UmlClass.diagram_id == UmlDiagram.id)
            .outerjoin(UmlRelationship, UmlRelationship.diagram_id == UmlDiagram.id)
            .outerjoin(User, User.id == UmlDiagram.created_by_user_id)
            .where(UmlDiagram.project_id == project_id)
            .group_by(UmlDiagram.id, User.full_name)
            .order_by(UmlDiagram.updated_at.desc())
        ).all()
        return [
            MobileDiagramSummary(
                id=diagram.id,
                project_id=diagram.project_id,
                name=diagram.name,
                diagram_type=diagram.diagram_type,
                class_count=class_count,
                relationship_count=relationship_count,
                updated_at=diagram.updated_at,
                updated_by_display_name=display_name,
            )
            for diagram, class_count, relationship_count, display_name in rows
        ]

    def get_diagram(self, diagram_id: UUID, user_id: UUID) -> MobileDiagramDetail:
        diagram = self.db.get(UmlDiagram, diagram_id)
        if diagram is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagrama no encontrado")
        ensure_membership(self.members.get_membership(diagram.project_id, user_id))
        model = UmlService(self.db).get_diagram_model(diagram_id, user_id)
        return MobileDiagramDetail(
            diagram=model.diagram,
            classes=model.classes,
            relationships=model.relationships,
            logical_version=diagram.current_version,
            can_read=True,
            can_edit=False,
        )

    def list_generations(
        self, project_id: UUID, user_id: UUID, limit: int = 30
    ) -> list[MobileGenerationSummary]:
        ensure_membership(self.members.get_membership(project_id, user_id))
        generations = self.db.scalars(
            select(CoordinatedGeneration)
            .where(CoordinatedGeneration.project_id == project_id)
            .order_by(CoordinatedGeneration.created_at.desc())
            .limit(limit)
        )
        return [
            MobileGenerationSummary(
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

