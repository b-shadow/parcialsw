from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.main import app
from app.modules.generacion_software.services.intermediate_model import (
    require_supported_intermediate_model,
)
from app.modules.modelado_uml.engine.internal_model import (
    UmlClassModel,
    UmlDiagramModel,
    UmlMethodModel,
    UmlParameterModel,
)
from app.modules.modelado_uml.engine.xmi import export_xmi, import_xmi
from app.modules.modelado_uml.schemas.method_specification import (
    BackendMethodContract,
    MethodGenerationRule,
    RequiredPermission,
    UmlMethodSpecificationCreate,
)
from app.modules.modelado_uml.services.method_specification_service import (
    MethodContext,
    MethodSpecificationService,
)


class _UmlCatalog:
    def __init__(self, classes: list[object]) -> None:
        self.classes = classes

    def list_classes(self, _diagram_id):
        return self.classes


def _context(*, private: bool = False):
    diagram_id = uuid4()
    parameter = SimpleNamespace(
        id=uuid4(), name="fecha", data_type="LocalDate", default_value=None
    )
    uml_class = SimpleNamespace(
        id=uuid4(),
        name="Inscripcion",
        diagram_id=diagram_id,
        attributes=[SimpleNamespace(id=uuid4(), name="estado")],
    )
    method = SimpleNamespace(
        id=uuid4(),
        class_id=uml_class.id,
        name="registrar",
        visibility="private" if private else "public",
        parameters=[parameter],
    )
    diagram = SimpleNamespace(id=diagram_id, project_id=uuid4())
    return MethodContext(method, uml_class, diagram, SimpleNamespace(project_role="EDITOR"))


def _service(context: MethodContext) -> MethodSpecificationService:
    service = object.__new__(MethodSpecificationService)
    service.uml = _UmlCatalog([context.uml_class])
    return service


def _ready_specification(context: MethodContext) -> UmlMethodSpecificationCreate:
    parameter = context.method.parameters[0]
    return UmlMethodSpecificationCreate(
        description="Registra una inscripcion con su fecha.",
        operation_kind="create",
        exposure="user_action",
        validations=[
            {
                "code": "fecha_requerida",
                "description": "La fecha es obligatoria",
                "target": {
                    "kind": "parameter",
                    "id": parameter.id,
                    "name": parameter.name,
                },
                "generation": {"kind": "required"},
            }
        ],
        backend_contract={
            "http_method": "POST",
            "path": "/inscripciones",
            "transactional": True,
            "authorization": ["inscripcion.crear"],
            "status_codes": {"success": 201},
        },
        frontend_contract={
            "interaction": "form",
            "label": "Registrar inscripcion",
            "success_message": "Inscripcion registrada",
            "fields": [
                {
                    "parameter_id": parameter.id,
                    "parameter": parameter.name,
                    "control": "date_picker",
                }
            ],
        },
    )


def test_phase4_closed_contracts_normalize_domain_codes() -> None:
    permission = RequiredPermission(code=" Inscripcion.Crear ")
    rule = MethodGenerationRule(kind="range", minimum=0, maximum=100)
    backend = BackendMethodContract(
        http_method="POST",
        path="/inscripciones",
        authorization=["EDITOR", "editor"],
        error_codes=["registro duplicado", "REGISTRO_DUPLICADO"],
    )

    assert permission.code == "inscripcion.crear"
    assert rule.maximum == 100
    assert backend.authorization == ["editor"]
    assert backend.error_codes == ["REGISTRO_DUPLICADO"]
    with pytest.raises(ValidationError):
        BackendMethodContract(http_method="GET", path="https://host/recurso")
    with pytest.raises(ValidationError):
        UmlMethodSpecificationCreate(unknown_contract=True)


def test_phase4_draft_is_permitted_but_strict_validation_blocks_generation() -> None:
    context = _context()
    service = _service(context)
    draft = UmlMethodSpecificationCreate(
        description="Registra la operacion", exposure="user_action"
    )

    relaxed = service.validate_model(context, draft, strict=False)
    strict = service.validate_model(context, draft, strict=True)

    assert relaxed.status == "draft"
    assert not relaxed.errors
    assert strict.status == "invalid"
    assert {item.code for item in strict.errors} == {
        "missing_backend_contract",
        "missing_flutter_contract",
    }


def test_phase4_valid_specification_is_ready_and_localdate_uses_picker() -> None:
    context = _context()
    result = _service(context).validate_model(
        context, _ready_specification(context), strict=True
    )

    assert result.status == "ready"
    assert result.ready_for_generation is True
    assert result.errors == []


def test_phase4_detects_private_exposure_unsafe_get_and_unknown_references() -> None:
    context = _context(private=True)
    payload = _ready_specification(context).model_copy(
        update={
            "operation_kind": "delete",
            "backend_contract": BackendMethodContract(
                http_method="GET", path="/inscripciones/{desconocido}"
            ),
        }
    )

    result = _service(context).validate_model(context, payload, strict=True)
    codes = {item.code for item in result.errors}

    assert "private_method_exposed" in codes
    assert "unknown_path_parameter" in codes
    assert "unsafe_get_operation" in codes
    assert "delete_requires_confirmation" in codes


def test_phase4_stale_revision_returns_machine_readable_conflict() -> None:
    with pytest.raises(HTTPException) as captured:
        MethodSpecificationService._conflict(7)

    assert captured.value.status_code == 409
    assert captured.value.detail == {"code": "stale_revision", "current_revision": 7}


def test_phase4_xmi_roundtrip_preserves_parameters_and_specification() -> None:
    parameter_id = str(uuid4())
    method_id = str(uuid4())
    source = UmlDiagramModel(
        name="Academico",
        classes=[
            UmlClassModel(
                id=str(uuid4()),
                name="Inscripcion",
                methods=[
                    UmlMethodModel(
                        id=method_id,
                        name="registrar",
                        return_type="void",
                        parameters=[
                            UmlParameterModel(
                                id=parameter_id,
                                name="fecha",
                                data_type="LocalDate",
                                order_index=0,
                            )
                        ],
                        specification=_ready_specification(_context()).model_dump(
                            mode="json"
                        ),
                    )
                ],
            )
        ],
    )

    xml = export_xmi(source)
    imported = import_xmi(xml)
    method = imported.classes[0].methods[0]

    assert "case_method_specification_v1" in xml
    assert [(item.name, item.data_type) for item in method.parameters] == [
        ("fecha", "LocalDate")
    ]
    assert method.specification is not None
    assert method.specification["operation_kind"] == "create"


def test_phase4_intermediate_model_v1_adapter_is_immutable_and_rejects_future() -> None:
    legacy = {"classes": [{"name": "Curso", "methods": [{"name": "crear"}]}]}
    adapted = require_supported_intermediate_model(legacy)

    assert "schema_version" not in legacy
    assert adapted["schema_version"] == 2
    assert adapted["classes"][0]["methods"][0]["parameters"] == []
    assert adapted["classes"][0]["methods"][0]["readiness"]["status"] == "legacy"
    with pytest.raises(ValueError, match="no soportada"):
        require_supported_intermediate_model({"schema_version": 3})


def test_phase4_openapi_exposes_signature_specification_and_refinement_contracts() -> None:
    paths = app.openapi()["paths"]
    expected = {
        "/api/v1/uml/parameters/{parameter_id}": {"patch", "delete"},
        "/api/v1/uml/methods/{method_id}/specification": {
            "get",
            "put",
            "patch",
            "delete",
        },
        "/api/v1/uml/methods/{method_id}/specification/validate": {"post"},
        "/api/v1/uml/methods/{method_id}/specification/refine": {"post"},
    }

    for path, verbs in expected.items():
        assert path in paths
        assert verbs.issubset(paths[path])
    put_parameters = paths[
        "/api/v1/uml/methods/{method_id}/specification"
    ]["put"]["parameters"]
    assert {item["name"] for item in put_parameters} >= {"If-Match", "If-None-Match"}
