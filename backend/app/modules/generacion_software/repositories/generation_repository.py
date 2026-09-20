from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.modules.generacion_software.models import (
    GeneratedArtifact,
    GeneratedBackend,
    GeneratedFrontend,
    UmlTransformation,
)


class GenerationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add_transformation(self, transformation: UmlTransformation) -> UmlTransformation:
        self.db.add(transformation)
        self.db.flush()
        self.db.refresh(transformation)
        return transformation

    def get_transformation(self, transformation_id: UUID) -> UmlTransformation | None:
        return self.db.get(UmlTransformation, transformation_id)

    def add_backend(self, generated_backend: GeneratedBackend) -> GeneratedBackend:
        self.db.add(generated_backend)
        self.db.flush()
        self.db.refresh(generated_backend)
        return generated_backend

    def get_backend(self, backend_id: UUID) -> GeneratedBackend | None:
        return self.db.get(GeneratedBackend, backend_id)

    def add_frontend(self, generated_frontend: GeneratedFrontend) -> GeneratedFrontend:
        self.db.add(generated_frontend)
        self.db.flush()
        self.db.refresh(generated_frontend)
        return generated_frontend

    def get_frontend(self, frontend_id: UUID) -> GeneratedFrontend | None:
        return self.db.get(GeneratedFrontend, frontend_id)

    def add_artifact(self, artifact: GeneratedArtifact) -> GeneratedArtifact:
        self.db.add(artifact)
        self.db.flush()
        self.db.refresh(artifact)
        return artifact

    def delete_generation_tree_by_diagram(self, diagram_id: UUID) -> None:
        transformation_ids = list(
            self.db.scalars(
                select(UmlTransformation.id).where(UmlTransformation.diagram_id == diagram_id)
            )
        )
        if not transformation_ids:
            return

        backend_ids = list(
            self.db.scalars(
                select(GeneratedBackend.id).where(
                    GeneratedBackend.transformation_id.in_(transformation_ids)
                )
            )
        )
        frontend_ids = list(
            self.db.scalars(
                select(GeneratedFrontend.id).where(
                    GeneratedFrontend.transformation_id.in_(transformation_ids)
                )
            )
        )

        if frontend_ids:
            self.db.execute(
                delete(GeneratedArtifact).where(
                    GeneratedArtifact.generated_frontend_id.in_(frontend_ids)
                )
            )
            self.db.execute(delete(GeneratedFrontend).where(GeneratedFrontend.id.in_(frontend_ids)))
        if backend_ids:
            self.db.execute(
                delete(GeneratedArtifact).where(
                    GeneratedArtifact.generated_backend_id.in_(backend_ids)
                )
            )
            self.db.execute(delete(GeneratedBackend).where(GeneratedBackend.id.in_(backend_ids)))
        self.db.execute(delete(UmlTransformation).where(UmlTransformation.id.in_(transformation_ids)))
