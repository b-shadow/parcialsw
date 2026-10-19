import json
from pathlib import Path

import pytest

from app.main import app
from app.modules.generacion_software.coordinated_generator import compile_generation_plan
from app.modules.generacion_software.coordinated_generator.services import (
    CoordinatedGeneratorService,
)
from app.modules.generacion_software.coordinated_generator.validators import (
    validate_cross_contract,
)
from app.modules.generacion_software.coordinated_generator.validators.preflight import (
    GenerationPreflightError,
)


def _model(*, ready: bool = True) -> dict:
    method_id = "method-registrar"
    parameters = [
        {"id": "param-estudiante", "name": "estudianteId", "data_type": "UUID", "order_index": 0},
        {"id": "param-curso", "name": "cursoId", "data_type": "UUID", "order_index": 1},
        {"id": "param-fecha", "name": "fecha", "data_type": "LocalDate", "order_index": 2},
        {"id": "param-nota", "name": "notaFinal", "data_type": "Double", "order_index": 3},
    ]
    return {
        "schema_version": 2,
        "classes": [
            {
                "id": "estudiante",
                "name": "Estudiante",
                "attributes": [{"name": "nombre", "data_type": "String", "is_required": True}],
                "methods": [],
            },
            {
                "id": "curso",
                "name": "Curso",
                "attributes": [{"name": "nombre", "data_type": "String", "is_required": True}],
                "methods": [],
            },
            {
                "id": "inscripcion",
                "name": "Inscripcion",
                "attributes": [
                    {"name": "fecha", "data_type": "LocalDate", "is_required": True},
                    {"name": "notaFinal", "data_type": "Double", "is_required": False},
                ],
                "methods": [
                    {
                        "id": method_id,
                        "name": "registrarInscripcion",
                        "return_type": "void",
                        "parameters": parameters,
                        "readiness": {
                            "status": "ready" if ready else "draft",
                            "ready_for_generation": ready,
                        },
                        "specification": {
                            "description": "Registra una inscripcion.",
                            "operation_kind": "business_action",
                            "exposure": "user_action",
                            "required_permissions": [{"code": "inscripcion.crear"}],
                            "validations": [
                                {
                                    "code": "fecha_requerida",
                                    "severity": "error",
                                    "target": {"kind": "parameter", "name": "fecha"},
                                    "generation": {"kind": "required"},
                                },
                                {
                                    "code": "nota_valida",
                                    "severity": "error",
                                    "target": {"kind": "parameter", "name": "notaFinal"},
                                    "generation": {"kind": "range", "minimum": 0, "maximum": 100},
                                },
                            ],
                            "business_rules": [
                                {
                                    "code": "inscripcion_unica",
                                    "severity": "error",
                                    "generation": {
                                        "kind": "unique_by_fields",
                                        "fields": ["estudianteId", "cursoId"],
                                    },
                                }
                            ],
                            "backend_contract": {
                                "http_method": "POST",
                                "path": "/inscripciones/registrar",
                                "authorization": ["inscripcion.crear"],
                                "status_codes": {"success": 201},
                            },
                            "frontend_contract": {
                                "interaction": "form",
                                "label": "Registrar inscripcion",
                                "confirmation_required": True,
                                "success_message": "Inscripcion registrada",
                                "refresh_targets": ["inscripcion"],
                                "fields": [
                                    {
                                        "parameter_id": "param-estudiante",
                                        "control": "entity_selector",
                                        "source_entity_id": "estudiante",
                                        "display_fields": ["nombre"],
                                    },
                                    {
                                        "parameter_id": "param-curso",
                                        "control": "entity_selector",
                                        "source_entity_id": "curso",
                                        "display_fields": ["nombre"],
                                    },
                                    {"parameter_id": "param-fecha", "control": "date_picker"},
                                    {"parameter_id": "param-nota", "control": "decimal_input"},
                                ],
                            },
                        },
                    }
                ],
            },
        ],
        "relationships": [
            {
                "source_class_id": "estudiante",
                "target_class_id": "curso",
                "type": "association",
                "source_cardinality": "*",
                "target_cardinality": "*",
                "metadata_json": {"association_class_id": "inscripcion"},
            }
        ],
    }


def test_phase5_plan_is_deterministic_and_shared() -> None:
    first = compile_generation_plan(_model(), "Academico")
    second = compile_generation_plan(_model(), "Academico")

    assert first.ready
    assert first.canonical_hash == second.canonical_hash
    assert len(first.operations) == 1
    operation = first.operations[0]
    assert operation.route.effective_path == "/api/inscripciones/registrar"
    assert [item.name for item in operation.parameters] == [
        "estudianteId", "cursoId", "fecha", "notaFinal"
    ]
    assert {item.kind for item in operation.rules} == {
        "required", "range", "unique_by_fields"
    }
    assert operation.ui_action is not None
    assert operation.permissions == ("inscripcion.crear",)


def test_phase5_preflight_blocks_draft_before_writing(tmp_path: Path) -> None:
    service = CoordinatedGeneratorService(tmp_path)
    with pytest.raises(GenerationPreflightError):
        service.generate(
            _model(ready=False), "Academico", "blocked", verify=False,
            allow_unverified=True,
        )
    assert not (tmp_path / "blocked").exists()


def test_phase5_generates_both_projects_and_atomic_bundle(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.modules.generacion_software.flutter_generator.generator.project_writer.which",
        lambda _: None,
    )
    result = CoordinatedGeneratorService(tmp_path).generate(
        _model(), "Academico", "generation-1", verify=False, allow_unverified=True
    )

    assert result.bundle_path.exists()
    assert result.manifest["status"] == "generated_unverified"
    assert result.manifest["cross_validation"]["status"] == "passed"
    backend_controller = next(result.backend_dir.rglob("*RegistrarInscripcionController.java"))
    backend_service = next(result.backend_dir.rglob("*RegistrarInscripcionService.java"))
    backend_repository = next(result.backend_dir.rglob("InscripcionRepository.java"))
    frontend_screen = next(result.frontend_dir.rglob("actions/registrar_inscripcion_screen.dart"))
    frontend_router = result.frontend_dir / "lib/core/routes/app_router.dart"
    assert '@PostMapping("/api/inscripciones/registrar")' in backend_controller.read_text(encoding="utf-8")
    assert "return crudService.create(command);" in backend_service.read_text(encoding="utf-8")
    assert "existsByEstudiante_IdAndCurso_Id" in backend_repository.read_text(encoding="utf-8")
    assert "Registrar inscripcion" in frontend_screen.read_text(encoding="utf-8")
    assert "NavigationBar(" in frontend_router.read_text(encoding="utf-8")
    assert json.loads((result.backend_dir / "generation-plan.json").read_text())["canonical_hash"] == result.plan.canonical_hash
    assert json.loads((result.frontend_dir / "generation-plan.json").read_text())["canonical_hash"] == result.plan.canonical_hash


def test_phase5_cross_validation_detects_route_drift() -> None:
    plan = compile_generation_plan(_model(), "Academico")
    good = {
        "functional_routes": [
            {"operation_id": route.operation_id, "http_method": route.http_method, "path": route.effective_path}
            for route in plan.routes
        ],
        "functional_dtos": {
            operation.id: [item.name for item in operation.parameters if item.location == "body"]
            for operation in plan.operations
        },
    }
    broken = {**good, "functional_routes": []}
    diagnostics = validate_cross_contract(plan, good, broken)
    assert {item.code for item in diagnostics} == {"cross_contract_missing_route"}


def test_phase5_openapi_exposes_coordinated_lifecycle() -> None:
    paths = app.openapi()["paths"]
    assert "/api/v1/generation/coordinated/preflight" in paths
    assert "/api/v1/generation/coordinated" in paths
    assert "/api/v1/generation/coordinated/{generation_id}" in paths
    assert "/api/v1/generation/coordinated/{generation_id}/download" in paths
