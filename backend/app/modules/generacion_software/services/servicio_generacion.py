from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.acceso_usuarios.services.servicio_auditoria import ServicioAuditoria
from app.modules.generacion_software.backend_generator import ServicioGeneradorSpringBoot
from app.modules.generacion_software.coordinated_generator.services import (
    ServicioGeneradorCoordinado,
)
from app.modules.generacion_software.coordinated_generator.validators.verificacion_previa import (
    ErrorVerificacionPreviaGeneracion,
)
from app.modules.generacion_software.flutter_generator import ServicioGeneradorFlutter
from app.modules.generacion_software.models import (
    ArtefactoGenerado,
    BackendGenerado,
    FrontendGenerado,
    GeneracionCoordinada,
    TransformacionUML,
)
from app.modules.generacion_software.repositories.repositorio_generacion import (
    RepositorioGeneracion,
)
from app.modules.generacion_software.schemas.generacion import (
    SolicitudGeneracionBackend,
    SolicitudGeneracionCoordinada,
    SolicitudGeneracionFrontend,
    SolicitudTransformacion,
    SolicitudVerificacionPreviaCoordinada,
)
from app.modules.generacion_software.services.modelo_intermedio import (
    requerir_modelo_intermedio_admitido,
)
from app.modules.generacion_software.validators.validador_generacion import (
    asegurar_transformacion_existente,
)
from app.modules.modelado_uml.schemas.especificacion_metodo import BaseEspecificacionMetodoUML
from app.modules.modelado_uml.services.servicio_especificacion_metodo import (
    ContextoMetodo,
    ServicioEspecificacionMetodo,
)
from app.modules.modelado_uml.services.servicio_uml import ServicioUML
from app.modules.modelado_uml.validators.validador_uml import asegurar_diagrama_existente
from app.modules.proyectos_colaboracion.repositories.repositorio_integrantes import (
    RepositorioIntegrantes,
)
from app.modules.proyectos_colaboracion.repositories.repositorio_proyectos import (
    RepositorioProyectos,
)
from app.modules.proyectos_colaboracion.validators.validador_proyecto import (
    asegurar_participacion,
    asegurar_permiso_proyecto,
)


class ServicioGeneracion:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.generations = RepositorioGeneracion(db)
        self.uml_service = ServicioUML(db)
        self.uml = self.uml_service.uml
        self.members = RepositorioIntegrantes(db)
        self.projects = RepositorioProyectos(db)
        self.audit = ServicioAuditoria(db)

    def transform(self, payload: SolicitudTransformacion, user_id: UUID) -> TransformacionUML:
        diagram = asegurar_diagrama_existente(self.uml.obtener_diagrama(payload.diagram_id))
        member = asegurar_permiso_proyecto(self.db, diagram.project_id, user_id, "generation.run")
        document_model = self.uml_service._construir_modelo_interno(diagram)
        classes = document_model.classes
        relationships = document_model.relationships
        intermediate_model = {
            "schema_version": 2,
            "diagram": {
                "id": str(diagram.id),
                "name": document_model.name,
                "type": document_model.diagram_type,
            },
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
                                dict(method.specification) if method.specification else None
                            ),
                            "readiness": self._preparacion_metodo(method, uml_class, diagram, member),
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
        transformation = self.generations.agregar_transformacion(
            TransformacionUML(
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

    def _preparacion_metodo(self, method, uml_class, diagram, member) -> dict:
        specification = None
        if method.specification:
            raw = dict(method.specification)
            raw.pop("revision", None)
            specification = BaseEspecificacionMetodoUML.model_validate(raw)
        validation = ServicioEspecificacionMetodo(self.db).validar_modelo(
            ContextoMetodo(
                method=method,
                uml_class=uml_class,
                diagram=diagram,
                member=member,
            ),
            specification,
            strict=True,
        )
        return {
            "status": validation.status,
            "ready_for_generation": validation.ready_for_generation,
            "diagnostics": [
                item.model_dump(mode="json") for item in [*validation.errors, *validation.warnings]
            ],
        }

    def generar_backend(
        self, payload: SolicitudGeneracionBackend, user_id: UUID
    ) -> BackendGenerado:
        transformation = asegurar_transformacion_existente(
            self.generations.obtener_transformacion(payload.transformation_id)
        )
        asegurar_permiso_proyecto(self.db, transformation.project_id, user_id, "generation.run")
        if not transformation.intermediate_model.get("classes"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El diagrama no contiene clases para generar el backend.",
            )
        project = self.projects.obtener_para_actualizar(transformation.project_id)
        version_label = f"v{len(self.generations.listar_backends(transformation.project_id)) + 1}"
        generated_name = f"{project.name}_{version_label}"
        generated = self.generations.agregar_backend(
            BackendGenerado(
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
            generation_result = ServicioGeneradorSpringBoot().generate(
                requerir_modelo_intermedio_admitido(transformation.intermediate_model),
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
            self.generations.agregar_artefacto(
                ArtefactoGenerado(
                    project_id=transformation.project_id,
                    generated_backend_id=generated.id,
                    artifact_type="spring_boot_source",
                    file_name=file_path.name,
                    file_path=str(file_path),
                    checksum=generation_result.manifest["checksums"][relative_path],
                    metadata_json={"relative_path": relative_path},
                )
            )
        self.generations.agregar_artefacto(
            ArtefactoGenerado(
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

    def listar_backends(self, project_id: UUID, user_id: UUID) -> list[BackendGenerado]:
        asegurar_participacion(self.members.obtener_participacion(project_id, user_id))
        return self.generations.listar_backends(project_id)

    def obtener_ruta_artefacto_backend(self, backend_id: UUID, user_id: UUID) -> str:
        generated = self.generations.obtener_backend(backend_id)
        if generated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Backend generado no encontrado"
            )
        asegurar_permiso_proyecto(self.db, generated.project_id, user_id, "generation.run")
        zip_path = generated.manifest.get("zip_path") if generated.manifest else None
        if not zip_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="ZIP de backend no encontrado"
            )
        return str(zip_path)

    def generar_frontend(
        self, payload: SolicitudGeneracionFrontend, user_id: UUID
    ) -> FrontendGenerado:
        transformation = asegurar_transformacion_existente(
            self.generations.obtener_transformacion(payload.transformation_id)
        )
        asegurar_permiso_proyecto(self.db, transformation.project_id, user_id, "generation.run")
        project = self.projects.obtener_para_actualizar(transformation.project_id)
        backend = None
        if payload.backend_id is not None:
            backend = self.generations.obtener_backend(payload.backend_id)
            if backend is None or backend.project_id != transformation.project_id:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="El backend seleccionado no pertenece al proyecto",
                )
        version_label = f"v{len(self.generations.listar_frontends(transformation.project_id)) + 1}"
        generated_name = f"{project.name}_{version_label}"
        generated = self.generations.agregar_frontend(
            FrontendGenerado(
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
            api_base_url = payload.api_base_url or (
                "http://10.0.2.2:8080" if payload.backend_id else "http://localhost:8080"
            )
            theme_config = self._tema_efectivo(transformation.project_id, payload.theme_config)
            generation_result = ServicioGeneradorFlutter().generate(
                requerir_modelo_intermedio_admitido(transformation.intermediate_model),
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
            self.generations.agregar_artefacto(
                ArtefactoGenerado(
                    project_id=transformation.project_id,
                    generated_frontend_id=generated.id,
                    artifact_type="flutter_source",
                    file_name=file_path.name,
                    file_path=str(file_path),
                    checksum=generation_result.manifest["checksums"][relative_path],
                    metadata_json={"relative_path": relative_path},
                )
            )
        self.generations.agregar_artefacto(
            ArtefactoGenerado(
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

    def listar_frontends(self, project_id: UUID, user_id: UUID) -> list[FrontendGenerado]:
        asegurar_participacion(self.members.obtener_participacion(project_id, user_id))
        return self.generations.listar_frontends(project_id)

    def obtener_ruta_artefacto_frontend(self, frontend_id: UUID, user_id: UUID) -> str:
        generated = self.generations.obtener_frontend(frontend_id)
        if generated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Frontend generado no encontrado"
            )
        asegurar_permiso_proyecto(self.db, generated.project_id, user_id, "generation.run")
        zip_path = generated.manifest.get("zip_path") if generated.manifest else None
        if not zip_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="ZIP de Flutter no encontrado"
            )
        return str(zip_path)

    def verificar_coordinada(self, payload: SolicitudVerificacionPreviaCoordinada, user_id: UUID) -> dict:
        transformation = asegurar_transformacion_existente(
            self.generations.obtener_transformacion(payload.transformation_id)
        )
        asegurar_permiso_proyecto(self.db, transformation.project_id, user_id, "generation.run")
        plan = ServicioGeneradorCoordinado().preflight(
            transformation.intermediate_model,
            payload.name,
            source_transformation_id=str(transformation.id),
            theme=self._tema_efectivo(transformation.project_id, payload.theme_config),
        )
        return {
            "schema_version": plan.schema_version,
            "canonical_hash": plan.canonical_hash,
            "ready": plan.ready,
            "errors": [item.model_dump(mode="json") for item in plan.errors],
            "plan": plan.model_dump(mode="json"),
            "ui_manifest": self._manifiesto_ui(plan),
        }

    def generar_coordinada(
        self, payload: SolicitudGeneracionCoordinada, user_id: UUID
    ) -> GeneracionCoordinada:
        transformation = asegurar_transformacion_existente(
            self.generations.obtener_transformacion(payload.transformation_id)
        )
        asegurar_permiso_proyecto(self.db, transformation.project_id, user_id, "generation.run")
        existing = self.generations.obtener_coordinada_por_solicitud(
            transformation.id, user_id, payload.client_request_id
        )
        if existing is not None:
            return existing
        generated = self.generations.agregar_coordinada(
            GeneracionCoordinada(
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
            result = ServicioGeneradorCoordinado().generate(
                transformation.intermediate_model,
                payload.name,
                str(generated.id),
                api_base_url=payload.api_base_url,
                theme=self._tema_efectivo(transformation.project_id, payload.theme_config),
                verify=payload.verify,
                allow_unverified=payload.allow_unverified,
                source_transformation_id=str(transformation.id),
            )
        except ErrorVerificacionPreviaGeneracion as exc:
            generated.status = "failed"
            generated.stage = "preflight_failed"
            generated.plan_hash = exc.plan.canonical_hash
            generated.plan_json = exc.plan.model_dump(mode="json")
            generated.diagnostics = [item.model_dump(mode="json") for item in exc.plan.errors]
            generated.error_detail = str(exc)
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "generation_preflight_failed",
                    "diagnostics": generated.diagnostics,
                },
            ) from exc
        except ValueError as exc:
            generated.status = "failed"
            generated.stage = "verification_failed"
            generated.error_detail = str(exc)
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "coordinated_generation_failed",
                    "message": str(exc),
                },
            ) from exc
        generated.plan_hash = result.plan.canonical_hash
        generated.plan_json = result.plan.model_dump(mode="json")
        generated.diagnostics = [item.model_dump(mode="json") for item in result.plan.diagnostics]
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

    def obtener_coordinada(self, generation_id: UUID, user_id: UUID) -> GeneracionCoordinada:
        generated = self.generations.obtener_coordinada(generation_id)
        if generated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Generacion coordinada no encontrada",
            )
        asegurar_permiso_proyecto(self.db, generated.project_id, user_id, "generation.run")
        return generated

    def obtener_ruta_artefacto_coordinado(self, generation_id: UUID, user_id: UUID) -> str:
        generated = self.obtener_coordinada(generation_id, user_id)
        if not generated.artifact_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bundle coordinado no disponible",
            )
        return generated.artifact_path

    def _tema_efectivo(self, project_id: UUID, override: dict | None) -> dict:
        from app.modules.generacion_software.repositories.repositorio_temas import RepositorioTemas
        from app.modules.generacion_software.schemas.contrato_temas import normalizar_tema

        source = override
        if source is None:
            stored = RepositorioTemas(self.db).get(project_id)
            source = stored.config_json if stored else None
        theme, diagnostics, _ = normalizar_tema(source)
        errors = [item for item in diagnostics if item.severity == "error"]
        if errors:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "invalid_flutter_theme",
                    "diagnostics": [item.model_dump(mode="json") for item in errors],
                },
            )
        return theme.model_dump(mode="json")

    @staticmethod
    def _manifiesto_ui(plan) -> dict:
        from app.modules.generacion_software.coordinated_generator.contracts import (
            construir_manifiesto_ui,
        )

        return construir_manifiesto_ui(plan).model_dump(mode="json")

    def obtener_manifiesto_ui(
        self, transformation_id: UUID, user_id: UUID, name: str = "Preview"
    ) -> dict:
        transformation = asegurar_transformacion_existente(
            self.generations.obtener_transformacion(transformation_id)
        )
        asegurar_permiso_proyecto(self.db, transformation.project_id, user_id, "generation.run")
        plan = ServicioGeneradorCoordinado().preflight(
            transformation.intermediate_model,
            name,
            source_transformation_id=str(transformation.id),
            theme=self._tema_efectivo(transformation.project_id, None),
        )
        return self._manifiesto_ui(plan)
