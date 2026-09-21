from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.acceso_usuarios.services.audit_service import AuditService
from app.modules.generacion_software.backend_generator import SpringBootGeneratorService
from app.modules.generacion_software.flutter_generator import FlutterGeneratorService
from app.modules.generacion_software.models import (
    GeneratedArtifact,
    GeneratedBackend,
    GeneratedFrontend,
    UmlTransformation,
)
from app.modules.generacion_software.repositories.generation_repository import GenerationRepository
from app.modules.generacion_software.schemas.generation import (
    BackendGenerationRequest,
    FrontendGenerationRequest,
    TransformationRequest,
)
from app.modules.generacion_software.validators.generation_validator import (
    ensure_transformation_exists,
)
from app.modules.modelado_uml.repositories.uml_repository import UmlRepository
from app.modules.modelado_uml.validators.uml_validator import ensure_diagram_exists
from app.modules.proyectos_colaboracion.repositories.member_repository import MemberRepository
from app.modules.proyectos_colaboracion.validators.project_validator import ensure_membership


class GenerationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.generations = GenerationRepository(db)
        self.uml = UmlRepository(db)
        self.members = MemberRepository(db)
        self.audit = AuditService(db)

    def transform(self, payload: TransformationRequest, user_id: UUID) -> UmlTransformation:
        diagram = ensure_diagram_exists(self.uml.get_diagram(payload.diagram_id))
        ensure_membership(self.members.get_membership(diagram.project_id, user_id))
        classes = self.uml.list_classes(diagram.id)
        relationships = self.uml.list_relationships(diagram.id)
        intermediate_model = {
            "diagram": {"id": str(diagram.id), "name": diagram.name, "type": diagram.diagram_type},
            "classes": [
                {
                    "id": str(uml_class.id),
                    "name": uml_class.name,
                    "type": uml_class.element_type,
                    "visibility": uml_class.visibility,
                    "attributes": [
                        {
                            "id": str(attribute.id),
                            "name": attribute.name,
                            "data_type": attribute.data_type,
                            "visibility": attribute.visibility,
                            "is_required": attribute.is_required,
                            "multiplicity": attribute.multiplicity,
                        }
                        for attribute in uml_class.attributes
                    ],
                    "methods": [
                        {
                            "id": str(method.id),
                            "name": method.name,
                            "return_type": method.return_type,
                            "visibility": method.visibility,
                        }
                        for method in uml_class.methods
                    ],
                }
                for uml_class in classes
            ],
            "relationships": [
                {
                    "id": str(relation.id),
                    "source_class_id": str(relation.source_class_id),
                    "target_class_id": str(relation.target_class_id),
                    "type": relation.relationship_type,
                    "source_cardinality": relation.source_cardinality,
                    "target_cardinality": relation.target_cardinality,
                    "label": relation.label,
                    "metadata_json": relation.metadata_json,
                }
                for relation in relationships
            ],
        }
        transformation = self.generations.add_transformation(
            UmlTransformation(
                project_id=diagram.project_id,
                diagram_id=diagram.id,
                requested_by_user_id=user_id,
                source_version=payload.source_version,
                target_platform=payload.target_platform,
                intermediate_model=intermediate_model,
                status="completed",
            )
        )
        self.audit.record(
            module="generacion_software",
            action="TRANSFORM_UML",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"transformation_id": str(transformation.id)},
        )
        self.db.commit()
        self.db.refresh(transformation)
        return transformation

    def generate_backend(
        self, payload: BackendGenerationRequest, user_id: UUID
    ) -> GeneratedBackend:
        transformation = ensure_transformation_exists(
            self.generations.get_transformation(payload.transformation_id)
        )
        ensure_membership(self.members.get_membership(transformation.project_id, user_id))
        generated = self.generations.add_backend(
            GeneratedBackend(
                project_id=transformation.project_id,
                transformation_id=transformation.id,
                generated_by_user_id=user_id,
                name=payload.name,
                version_label=payload.version_label,
                status="generating",
                artifact_path=None,
                manifest={},
            )
        )
        try:
            generation_result = SpringBootGeneratorService().generate(
                transformation.intermediate_model,
                payload.name,
                str(generated.id),
            )
        except ValueError as exc:
            generated.status = "failed"
            generated.error_detail = str(exc)
            self.db.commit()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        generated.status = "generated"
        generated.artifact_path = str(generation_result.project_dir)
        generated.manifest = generation_result.manifest
        for file_path in generation_result.files:
            relative_path = file_path.relative_to(generation_result.project_dir).as_posix()
            self.generations.add_artifact(
                GeneratedArtifact(
                    project_id=transformation.project_id,
                    generated_backend_id=generated.id,
                    artifact_type="spring_boot_source",
                    file_name=file_path.name,
                    file_path=str(file_path),
                    checksum=generation_result.manifest["checksums"][
                        relative_path
                    ],
                    metadata_json={"relative_path": relative_path},
                )
            )
        self.generations.add_artifact(
            GeneratedArtifact(
                project_id=transformation.project_id,
                generated_backend_id=generated.id,
                artifact_type="spring_boot_zip",
                file_name=generation_result.zip_path.name,
                file_path=str(generation_result.zip_path),
                checksum=None,
                metadata_json={"relative_path": generation_result.zip_path.name},
            )
        )
        self.audit.record(
            module="generacion_software",
            action="GENERATE_BACKEND",
            user_id=user_id,
            project_id=transformation.project_id,
            metadata={"generated_backend_id": str(generated.id)},
        )
        self.db.commit()
        self.db.refresh(generated)
        return generated

    def get_backend_artifact_path(self, backend_id: UUID, user_id: UUID) -> str:
        generated = self.generations.get_backend(backend_id)
        if generated is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backend generado no encontrado")
        ensure_membership(self.members.get_membership(generated.project_id, user_id))
        zip_path = generated.manifest.get("zip_path") if generated.manifest else None
        if not zip_path:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ZIP de backend no encontrado")
        return str(zip_path)

    def generate_frontend(
        self, payload: FrontendGenerationRequest, user_id: UUID
    ) -> GeneratedFrontend:
        transformation = ensure_transformation_exists(
            self.generations.get_transformation(payload.transformation_id)
        )
        ensure_membership(self.members.get_membership(transformation.project_id, user_id))
        generated = self.generations.add_frontend(
            GeneratedFrontend(
                project_id=transformation.project_id,
                transformation_id=transformation.id,
                generated_by_user_id=user_id,
                backend_id=payload.backend_id,
                name=payload.name,
                version_label=payload.version_label,
                status="generating",
                artifact_path=None,
                manifest={},
            )
        )
        try:
            api_base_url = payload.api_base_url or ("http://10.0.2.2:8080" if payload.backend_id else "http://localhost:8080")
            generation_result = FlutterGeneratorService().generate(
                transformation.intermediate_model,
                payload.name,
                str(generated.id),
                api_base_url=api_base_url,
            )
        except ValueError as exc:
            generated.status = "failed"
            generated.error_detail = str(exc)
            self.db.commit()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        generated.status = "generated"
        generated.artifact_path = str(generation_result.project_dir)
        generated.manifest = generation_result.manifest
        for file_path in generation_result.files:
            relative_path = file_path.relative_to(generation_result.project_dir).as_posix()
            self.generations.add_artifact(
                GeneratedArtifact(
                    project_id=transformation.project_id,
                    generated_frontend_id=generated.id,
                    artifact_type="flutter_source",
                    file_name=file_path.name,
                    file_path=str(file_path),
                    checksum=generation_result.manifest["checksums"][relative_path],
                    metadata_json={"relative_path": relative_path},
                )
            )
        self.generations.add_artifact(
            GeneratedArtifact(
                project_id=transformation.project_id,
                generated_frontend_id=generated.id,
                artifact_type="flutter_zip",
                file_name=generation_result.zip_path.name,
                file_path=str(generation_result.zip_path),
                checksum=None,
                metadata_json={"relative_path": generation_result.zip_path.name},
            )
        )
        self.audit.record(
            module="generacion_software",
            action="GENERATE_FRONTEND",
            user_id=user_id,
            project_id=transformation.project_id,
            metadata={"generated_frontend_id": str(generated.id)},
        )
        self.db.commit()
        self.db.refresh(generated)
        return generated

    def get_frontend_artifact_path(self, frontend_id: UUID, user_id: UUID) -> str:
        generated = self.generations.get_frontend(frontend_id)
        if generated is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Frontend generado no encontrado")
        ensure_membership(self.members.get_membership(generated.project_id, user_id))
        zip_path = generated.manifest.get("zip_path") if generated.manifest else None
        if not zip_path:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ZIP de Flutter no encontrado")
        return str(zip_path)
