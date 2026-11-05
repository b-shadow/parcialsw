from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.acceso_usuarios.models import Usuario
from app.modules.proyectos_colaboracion.models import (
    EventoColaboracion,
    IntegranteProyecto,
    Proyecto,
    VersionProyecto,
)


class RepositorioProyectos:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, project: Proyecto) -> Proyecto:
        self.db.add(project)
        self.db.flush()
        self.db.refresh(project)
        return project

    def get(self, project_id: UUID) -> Proyecto | None:
        return self.db.get(Proyecto, project_id)

    def obtener_para_actualizar(self, project_id: UUID) -> Proyecto | None:
        return self.db.scalar(
            select(Proyecto).where(Proyecto.id == project_id).with_for_update()
        )

    def listar_por_usuario(self, user_id: UUID) -> list[Proyecto]:
        statement = (
            select(Proyecto)
            .join(IntegranteProyecto, IntegranteProyecto.project_id == Proyecto.id)
            .where(IntegranteProyecto.user_id == user_id)
            .order_by(Proyecto.created_at.desc())
        )
        return list(self.db.scalars(statement))

    def siguiente_numero_version(self, project_id: UUID) -> int:
        versions = self.db.scalars(
            select(VersionProyecto.version_number)
            .where(VersionProyecto.project_id == project_id)
            .order_by(VersionProyecto.version_number.desc())
            .limit(1)
        ).first()
        return (versions or 0) + 1

    def obtener_version(self, version_id: UUID) -> VersionProyecto | None:
        return self.db.get(VersionProyecto, version_id)

    def listar_versiones(self, project_id: UUID) -> list[tuple[VersionProyecto, str]]:
        statement = (
            select(VersionProyecto, Usuario.full_name)
            .join(Usuario, Usuario.id == VersionProyecto.created_by_user_id)
            .where(VersionProyecto.project_id == project_id)
            .order_by(VersionProyecto.version_number.desc())
        )
        return list(self.db.execute(statement).tuples())

    def listar_cambios(
        self, project_id: UUID, limit: int = 100
    ) -> list[tuple[EventoColaboracion, str]]:
        statement = (
            select(EventoColaboracion, Usuario.full_name)
            .join(Usuario, Usuario.id == EventoColaboracion.user_id)
            .where(EventoColaboracion.project_id == project_id)
            .order_by(EventoColaboracion.sequence_number.desc())
            .limit(max(1, min(limit, 250)))
        )
        return list(self.db.execute(statement).tuples())

    def listar_cambios_posteriores(
        self, project_id: UUID, after_sequence: int, limit: int = 250
    ) -> list[tuple[EventoColaboracion, str]]:
        statement = (
            select(EventoColaboracion, Usuario.full_name)
            .join(Usuario, Usuario.id == EventoColaboracion.user_id)
            .where(
                EventoColaboracion.project_id == project_id,
                EventoColaboracion.sequence_number > after_sequence,
            )
            .order_by(EventoColaboracion.sequence_number)
            .limit(max(1, min(limit, 250)))
        )
        return list(self.db.execute(statement).tuples())

    def listar_actividad_anterior(
        self, project_id: UUID, before_sequence: int | None, limit: int,
        event_types: set[str] | None = None,
    ) -> list[tuple[EventoColaboracion, str]]:
        statement = (
            select(EventoColaboracion, Usuario.full_name)
            .join(Usuario, Usuario.id == EventoColaboracion.user_id)
            .where(EventoColaboracion.project_id == project_id)
        )
        if before_sequence is not None:
            statement = statement.where(EventoColaboracion.sequence_number < before_sequence)
        if event_types:
            statement = statement.where(EventoColaboracion.event_type.in_(event_types))
        return list(self.db.execute(
            statement.order_by(EventoColaboracion.sequence_number.desc())
            .limit(max(1, min(limit, 100)) + 1)
        ).tuples())

    def secuencia_evento_actual(self, project_id: UUID) -> int:
        current = self.db.scalar(
            select(func.max(EventoColaboracion.sequence_number)).where(
                EventoColaboracion.project_id == project_id
            )
        )
        return current or 0

    def obtener_evento_por_id_cliente(
        self, project_id: UUID, user_id: UUID, client_event_id: UUID
    ) -> EventoColaboracion | None:
        return self.db.scalar(
            select(EventoColaboracion).where(
                EventoColaboracion.project_id == project_id,
                EventoColaboracion.user_id == user_id,
                EventoColaboracion.client_event_id == client_event_id,
            )
        )

    def siguiente_secuencia_evento(self, project_id: UUID) -> int:
        return self.secuencia_evento_actual(project_id) + 1
