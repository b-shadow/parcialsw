from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.proyectos_colaboracion.models import IntegranteProyecto


class RepositorioIntegrantes:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, member: IntegranteProyecto) -> IntegranteProyecto:
        self.db.add(member)
        self.db.flush()
        self.db.refresh(member)
        return member

    def get(self, member_id: UUID) -> IntegranteProyecto | None:
        return self.db.get(IntegranteProyecto, member_id)

    def obtener_participacion(self, project_id: UUID, user_id: UUID) -> IntegranteProyecto | None:
        return self.db.scalar(
            select(IntegranteProyecto).where(
                IntegranteProyecto.project_id == project_id,
                IntegranteProyecto.user_id == user_id,
            )
        )

    def listar_por_proyecto(self, project_id: UUID) -> list[IntegranteProyecto]:
        return list(
            self.db.scalars(
                select(IntegranteProyecto)
                .where(IntegranteProyecto.project_id == project_id)
                .order_by(IntegranteProyecto.created_at)
            )
        )

    def delete(self, member: IntegranteProyecto) -> None:
        self.db.delete(member)
