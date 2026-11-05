from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.modules.generacion_software.models import (
    ArtefactoGenerado,
    BackendGenerado,
    FrontendGenerado,
    GeneracionCoordinada,
    TransformacionUML,
)


class RepositorioGeneracion:
    def __init__(self, db: Session) -> None:
        self.db = db

    def agregar_transformacion(self, transformation: TransformacionUML) -> TransformacionUML:
        self.db.add(transformation)
        self.db.flush()
        self.db.refresh(transformation)
        return transformation

    def obtener_transformacion(self, transformation_id: UUID) -> TransformacionUML | None:
        return self.db.get(TransformacionUML, transformation_id)

    def agregar_backend(self, generated_backend: BackendGenerado) -> BackendGenerado:
        self.db.add(generated_backend)
        self.db.flush()
        self.db.refresh(generated_backend)
        return generated_backend

    def obtener_backend(self, backend_id: UUID) -> BackendGenerado | None:
        return self.db.get(BackendGenerado, backend_id)

    def listar_backends(self, project_id: UUID) -> list[BackendGenerado]:
        return list(
            self.db.scalars(
                select(BackendGenerado)
                .where(BackendGenerado.project_id == project_id)
                .order_by(BackendGenerado.created_at.desc())
            )
        )

    def agregar_frontend(self, generated_frontend: FrontendGenerado) -> FrontendGenerado:
        self.db.add(generated_frontend)
        self.db.flush()
        self.db.refresh(generated_frontend)
        return generated_frontend

    def obtener_frontend(self, frontend_id: UUID) -> FrontendGenerado | None:
        return self.db.get(FrontendGenerado, frontend_id)

    def listar_frontends(self, project_id: UUID) -> list[FrontendGenerado]:
        return list(
            self.db.scalars(
                select(FrontendGenerado)
                .where(FrontendGenerado.project_id == project_id)
                .order_by(FrontendGenerado.created_at.desc())
            )
        )

    def agregar_artefacto(self, artifact: ArtefactoGenerado) -> ArtefactoGenerado:
        self.db.add(artifact)
        self.db.flush()
        self.db.refresh(artifact)
        return artifact

    def agregar_coordinada(self, generated: GeneracionCoordinada) -> GeneracionCoordinada:
        self.db.add(generated)
        self.db.flush()
        self.db.refresh(generated)
        return generated

    def obtener_coordinada(self, generation_id: UUID) -> GeneracionCoordinada | None:
        return self.db.get(GeneracionCoordinada, generation_id)

    def obtener_coordinada_por_solicitud(
        self, transformation_id: UUID, user_id: UUID, client_request_id: str
    ) -> GeneracionCoordinada | None:
        return self.db.scalar(
            select(GeneracionCoordinada).where(
                GeneracionCoordinada.transformation_id == transformation_id,
                GeneracionCoordinada.requested_by_user_id == user_id,
                GeneracionCoordinada.client_request_id == client_request_id,
            )
        )

    def eliminar_arbol_generacion_por_diagrama(self, diagram_id: UUID) -> None:
        transformation_ids = list(
            self.db.scalars(
                select(TransformacionUML.id).where(TransformacionUML.diagram_id == diagram_id)
            )
        )
        if not transformation_ids:
            return

        self.db.execute(
            delete(GeneracionCoordinada).where(
                GeneracionCoordinada.transformation_id.in_(transformation_ids)
            )
        )

        backend_ids = list(
            self.db.scalars(
                select(BackendGenerado.id).where(
                    BackendGenerado.transformation_id.in_(transformation_ids)
                )
            )
        )
        frontend_ids = list(
            self.db.scalars(
                select(FrontendGenerado.id).where(
                    FrontendGenerado.transformation_id.in_(transformation_ids)
                )
            )
        )

        if frontend_ids:
            self.db.execute(
                delete(ArtefactoGenerado).where(
                    ArtefactoGenerado.generated_frontend_id.in_(frontend_ids)
                )
            )
            self.db.execute(delete(FrontendGenerado).where(FrontendGenerado.id.in_(frontend_ids)))
        if backend_ids:
            self.db.execute(
                delete(ArtefactoGenerado).where(
                    ArtefactoGenerado.generated_backend_id.in_(backend_ids)
                )
            )
            self.db.execute(delete(BackendGenerado).where(BackendGenerado.id.in_(backend_ids)))
        self.db.execute(delete(TransformacionUML).where(TransformacionUML.id.in_(transformation_ids)))
