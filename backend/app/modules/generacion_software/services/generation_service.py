from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.acceso_usuarios.services.audit_service import AuditService
from app.modules.generacion_software.backend_generator import SpringBootGeneratorService
from app.modules.generacion_software.coordinated_generator.services import (
    CoordinatedGeneratorService,
)
from app.modules.generacion_software.coordinated_generator.validators.preflight import (
    GenerationPreflightError,
)
from app.modules.generacion_software.flutter_generator import FlutterGeneratorService
from app.modules.generacion_software.models import (
    CoordinatedGeneration,
    GeneratedArtifact,
    GeneratedBackend,
    GeneratedFrontend,
    UmlTransformation,
)
from app.modules.generacion_software.repositories.generation_repository import GenerationRepository
from app.modules.generacion_software.schemas.generation import (
    BackendGenerationRequest,
    CoordinatedGenerationRequest,
    CoordinatedPreflightRequest,
    FrontendGenerationRequest,
    TransformationRequest,
)
from app.modules.generacion_software.services.intermediate_model import (
    require_supported_intermediate_model,
)
from app.modules.generacion_software.validators.generation_validator import (
    ensure_transformation_exists,
)
from app.modules.modelado_uml.repositories.uml_repository import UmlRepository
from app.modules.modelado_uml.services.method_specification_service import (
    MethodContext,
    MethodSpecificationService,
)
from app.modules.modelado_uml.validators.uml_validator import ensure_diagram_exists
from app.modules.proyectos_colaboracion.repositories.member_repository import MemberRepository
from app.modules.proyectos_colaboracion.repositories.project_repository import ProjectRepository
from app.modules.proyectos_colaboracion.validators.project_validator import (
    ensure_membership,
    ensure_project_permission,
)


class GenerationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.generations = GenerationRepository(db)
        self.uml = UmlRepository(db)
        self.members = MemberRepository(db)
        self.projects = ProjectRepository(db)
        self.audit = AuditService(db)

    def transform(self, payload: TransformationRequest, user_id: UUID) -> UmlTransformation:
        diagram = ensure_diagram_exists(self.uml.get_diagram(payload.diagram_id))
        ensure_project_permission(self.db, diagram.project_id, user_id, "generation.run")
        classes = self.uml.list_classes(diagram.id)
        relationships = self.uml.list_relationships(diagram.id)
        intermediate_model = {
            "schema_version": 2,
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
                            "parameters": [
                                {
                                    "id": str(parameter.id),
                                    "name": parameter.name,
                                    "data_type": parameter.data_type,
                                    "default_value": parameter.default_value,
                                    "order_index": parameter.order_index,
                                }
                                for parameter in method.parameters
                            ],
                            "specification": (
                                {
                                    "schema_version": method.specification.schema_version,
                                    "revision": method.specification.revision,
                                    "description": method.specification.description,
                                    "operation_kind": method.specification.operation_kind,
                                    "exposure": method.specification.exposure,
                                    "preconditions": method.specification.preconditions,
                                    "postconditions": method.specification.postconditions,
                                    "business_rules": method.specification.business_rules,
                                    "validations": method.specification.validations,
                                    "side_effects": method.specification.side_effects,
                                    "required_permissions": method.specification.required_permissions,
                                    "related_entities": method.specification.related_entities,
                                    "backend_contract": method.specification.backend_contract or None,
                                    "frontend_contract": method.specification.frontend_contract or None,
                                }
                                if method.specification
                                else None
                            ),
                            "readiness": self._method_readiness(
                                method, uml_class, diagram, member
                            ),
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

    def _method_readiness(self, method, uml_class, diagram, member) -> dict:
        validation = MethodSpecificationService(self.db).validate_model(
            MethodContext(
                method=method,
                uml_class=uml_class,
                diagram=diagram,
                member=member,
            ),
            method.specification,
            strict=True,
        )
        return {
            "status": validation.status,
            "ready_for_generation": validation.ready_for_generation,
            "diagnostics": [
                item.model_dump(mode="json")
                for item in [*validation.errors, *validation.warnings]
            ],
        }

    def generate_backend(
        self, payload: BackendGenerationRequest, user_id: UUID
    ) -> GeneratedBackend:
        transformation = ensure_transformation_exists(
            self.generations.get_transformation(payload.transformation_id)
        )
        ensure_project_permission(self.db, transformation.project_id, user_id, "generation.run")
        project = self.projects.get_for_update(transformation.project_id)
        version_label = f"v{len(self.generations.list_backends(transformation.project_id)) + 1}"
        generated_name = f"{project.name}_{version_label}"
        generated = self.generations.add_backend(
            GeneratedBackend(
                project_id=transformation.project_id,
                transformation_id=transformation.id,
                generated_by_user_id=user_id,
                name=generated_name,
                version_label=version_label,
                status="generating",
                artifact_path=None,
                manifest={},
            )
        )
        try:
            generation_result = SpringBootGeneratorService().generate(
                require_supported_intermediate_model(transformation.intermediate_model),
                generated_name,
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

    def list_backends(self, project_id: UUID, user_id: UUID) -> list[GeneratedBackend]:
        ensure_membership(self.members.get_membership(project_id, user_id))
        return self.generations.list_backends(project_id)

    def get_backend_artifact_path(self, backend_id: UUID, user_id: UUID) -> str:
        generated = self.generations.get_backend(backend_id)
        if generated is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backend generado no encontrado")
        ensure_project_permission(self.db, generated.project_id, user_id, "generation.run")
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
        ensure_project_permission(self.db, transformation.project_id, user_id, "generation.run")
        project = self.projects.get_for_update(transformation.project_id)
        backend = None
        if payload.backend_id is not None:
            backend = self.generations.get_backend(payload.backend_id)
            if backend is None or backend.project_id != transformation.project_id:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="El backend seleccionado no pertenece al proyecto",
                )
        version_label = f"v{len(self.generations.list_frontends(transformation.project_id)) + 1}"
        generated_name = f"{project.name}_{version_label}"
        generated = self.generations.add_frontend(
            GeneratedFrontend(
                project_id=transformation.project_id,
                transformation_id=transformation.id,
                generated_by_user_id=user_id,
                backend_id=payload.backend_id,
                name=generated_name,
                version_label=version_label,
                status="generating",
                artifact_path=None,
                manifest={},
            )
        )
        try:
            api_base_url = payload.api_base_url or ("http://10.0.2.2:8080" if payload.backend_id else "http://localhost:8080")
            theme_config = self._effective_theme(transformation.project_id, payload.theme_config)
            generation_result = FlutterGeneratorService().generate(
                require_supported_intermediate_model(transformation.intermediate_model),
                generated_name,
                str(generated.id),
                api_base_url=api_base_url,
                theme_config=theme_config,
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

    def list_frontends(self, project_id: UUID, user_id: UUID) -> list[GeneratedFrontend]:
        ensure_membership(self.members.get_membership(project_id, user_id))
        return self.generations.list_frontends(project_id)

    def get_frontend_artifact_path(self, frontend_id: UUID, user_id: UUID) -> str:
        generated = self.generations.get_frontend(frontend_id)
        if generated is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Frontend generado no encontrado")
        ensure_project_permission(self.db, generated.project_id, user_id, "generation.run")
        zip_path = generated.manifest.get("zip_path") if generated.manifest else None
        if not zip_path:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ZIP de Flutter no encontrado")
        return str(zip_path)

    def preflight_coordinated(
        self, payload: CoordinatedPreflightRequest, user_id: UUID
    ) -> dict:
        transformation = ensure_transformation_exists(
            self.generations.get_transformation(payload.transformation_id)
        )
        ensure_project_permission(self.db, transformation.project_id, user_id, "generation.run")
        plan = CoordinatedGeneratorService().preflight(
            transformation.intermediate_model,
            payload.name,
            source_transformation_id=str(transformation.id),
            theme=self._effective_theme(transformation.project_id, payload.theme_config),
        )
        return {
            "schema_version": plan.schema_version,
            "canonical_hash": plan.canonical_hash,
            "ready": plan.ready,
            "errors": [item.model_dump(mode="json") for item in plan.errors],
            "plan": plan.model_dump(mode="json"),
            "ui_manifest": self._ui_manifest(plan),
        }

    def generate_coordinated(
        self, payload: CoordinatedGenerationRequest, user_id: UUID
    ) -> CoordinatedGeneration:
        transformation = ensure_transformation_exists(
            self.generations.get_transformation(payload.transformation_id)
        )
        ensure_project_permission(self.db, transformation.project_id, user_id, "generation.run")
        existing = self.generations.get_coordinated_by_request(
            transformation.id, user_id, payload.client_request_id
        )
        if existing is not None:
            return existing
        generated = self.generations.add_coordinated(
            CoordinatedGeneration(
                project_id=transformation.project_id,
                transformation_id=transformation.id,
                requested_by_user_id=user_id,
                client_request_id=payload.client_request_id,
                name=payload.name,
                status="generating",
                stage="preflight",
                plan_json={},
                diagnostics=[],
                manifest={},
            )
        )
        self.db.commit()
        try:
            generated.stage = "generating"
            result = CoordinatedGeneratorService().generate(
                transformation.intermediate_model,
                payload.name,
                str(generated.id),
                api_base_url=payload.api_base_url,
                theme=self._effective_theme(transformation.project_id, payload.theme_config),
                verify=payload.verify,
                allow_unverified=payload.allow_unverified,
                source_transformation_id=str(transformation.id),
            )
        except GenerationPreflightError as exc:
            generated.status = "failed"
            generated.stage = "preflight_failed"
            generated.plan_hash = exc.plan.canonical_hash
            generated.plan_json = exc.plan.model_dump(mode="json")
            generated.diagnostics = [item.model_dump(mode="json") for item in exc.plan.errors]
            generated.error_detail = str(exc)
            self.db.commit()
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={
                "code": "generation_preflight_failed",
                "diagnostics": generated.diagnostics,
            }) from exc
        except ValueError as exc:
            generated.status = "failed"
            generated.stage = "verification_failed"
            generated.error_detail = str(exc)
            self.db.commit()
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={
                "code": "coordinated_generation_failed",
                "message": str(exc),
            }) from exc
        generated.plan_hash = result.plan.canonical_hash
        generated.plan_json = result.plan.model_dump(mode="json")
        generated.diagnostics = [
            item.model_dump(mode="json") for item in result.plan.diagnostics
        ]
        generated.manifest = result.manifest
        generated.artifact_path = str(result.bundle_path)
        generated.status = result.manifest["status"]
        generated.stage = "published"
        self.audit.record(
            module="generacion_software",
            action="GENERATE_COORDINATED",
            user_id=user_id,
            project_id=transformation.project_id,
            metadata={
                "coordinated_generation_id": str(generated.id),
                "plan_hash": generated.plan_hash,
            },
        )
        self.db.commit()
        self.db.refresh(generated)
        return generated

    def get_coordinated(
        self, generation_id: UUID, user_id: UUID
    ) -> CoordinatedGeneration:
        generated = self.generations.get_coordinated(generation_id)
        if generated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Generacion coordinada no encontrada",
            )
        ensure_project_permission(self.db, generated.project_id, user_id, "generation.run")
        return generated

    def get_coordinated_artifact_path(self, generation_id: UUID, user_id: UUID) -> str:
        generated = self.get_coordinated(generation_id, user_id)
        if not generated.artifact_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bundle coordinado no disponible",
            )
        return generated.artifact_path

    def _effective_theme(self, project_id: UUID, override: dict | None) -> dict:
        from app.modules.generacion_software.repositories.theme_repository import ThemeRepository
        from app.modules.generacion_software.schemas.theme_contract import normalize_theme

        source = override
        if source is None:
            stored = ThemeRepository(self.db).get(project_id)
            source = stored.config_json if stored else None
        theme, diagnostics, _ = normalize_theme(source)
        errors = [item for item in diagnostics if item.severity == "error"]
        if errors:
            raise HTTPException(status_code=422, detail={
                "code": "invalid_flutter_theme",
                "diagnostics": [item.model_dump(mode="json") for item in errors],
            })
        return theme.model_dump(mode="json")

    @staticmethod
    def _ui_manifest(plan) -> dict:
        from app.modules.generacion_software.coordinated_generator.contracts import (
            build_ui_manifest,
        )
        return build_ui_manifest(plan).model_dump(mode="json")

    def get_ui_manifest(self, transformation_id: UUID, user_id: UUID, name: str = "Preview") -> dict:
        transformation = ensure_transformation_exists(self.generations.get_transformation(transformation_id))
        ensure_project_permission(self.db, transformation.project_id, user_id, "generation.run")
        plan = CoordinatedGeneratorService().preflight(
            transformation.intermediate_model, name,
            source_transformation_id=str(transformation.id),
            theme=self._effective_theme(transformation.project_id, None),
        )
        return self._ui_manifest(plan)
