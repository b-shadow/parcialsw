from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ModeloInmutable(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class DiagnosticoPlan(ModeloInmutable):
    code: str
    severity: Literal["warning", "error"]
    message: str
    suggestion: str | None = None
    method_id: str | None = None
    class_id: str | None = None
    path: str | None = None


class PlanTipoLogico(ModeloInmutable):
    logical: str
    source: str
    java: str
    dart: str
    json_type: str
    json_format: str | None = None
    nullable: bool = True
    entity_id: str | None = None


class PlanCampoEntidad(ModeloInmutable):
    id: str | None = None
    source_name: str
    json_name: str
    logical_type: PlanTipoLogico
    required: bool = False


class PlanEntidad(ModeloInmutable):
    id: str
    source_name: str
    name: str
    module_name: str
    fields: tuple[PlanCampoEntidad, ...] = ()


class PlanParametro(ModeloInmutable):
    id: str
    source_name: str
    name: str
    logical_type: PlanTipoLogico
    required: bool = True
    location: Literal["path", "query", "body", "context"] = "body"
    order_index: int = 0


class PlanReglaOperacion(ModeloInmutable):
    code: str
    kind: str
    error_code: str
    fields: tuple[str, ...] = ()
    minimum: float | None = None
    maximum: float | None = None
    pattern: str | None = None
    entity_id: str | None = None
    severity: str = "error"


class PlanRuta(ModeloInmutable):
    operation_id: str
    http_method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
    contractual_path: str
    effective_path: str
    path_parameters: tuple[str, ...] = ()
    query_parameters: tuple[str, ...] = ()
    body_fields: tuple[str, ...] = ()
    success_status: int = 200
    permissions: tuple[str, ...] = ()


class PlanCampoDTO(ModeloInmutable):
    source_parameter_id: str
    json_name: str
    logical_type: PlanTipoLogico
    required: bool = True
    constraints: tuple[PlanReglaOperacion, ...] = ()


class PlanDTO(ModeloInmutable):
    name: str
    direction: Literal["request", "response"]
    operation_id: str
    fields: tuple[PlanCampoDTO, ...] = ()


class PlanCampoUI(ModeloInmutable):
    parameter_id: str
    json_name: str
    label: str
    control: str
    logical_type: PlanTipoLogico
    required: bool = True
    hidden: bool = False
    source_entity_id: str | None = None
    source_entity: str | None = None
    source_module: str | None = None
    display_fields: tuple[str, ...] = ()


class PlanAccionUI(ModeloInmutable):
    operation_id: str
    owner_entity: str
    owner_module: str
    dart_name: str
    label: str
    interaction: str
    placement: str | None = None
    confirmation_required: bool = False
    success_message: str | None = None
    refresh_targets: tuple[str, ...] = ()
    fields: tuple[PlanCampoUI, ...] = ()


class PlanOperacion(ModeloInmutable):
    id: str
    owner_entity_id: str
    owner_entity: str
    owner_module: str
    source_name: str
    java_name: str
    dart_name: str
    operation_kind: str
    exposure: Literal["internal", "api", "user_action"]
    return_type: PlanTipoLogico
    parameters: tuple[PlanParametro, ...] = ()
    route: PlanRuta | None = None
    request_dto: PlanDTO | None = None
    response_dto: PlanDTO | None = None
    ui_action: PlanAccionUI | None = None
    rules: tuple[PlanReglaOperacion, ...] = ()
    permissions: tuple[str, ...] = ()
    side_effects: tuple[dict, ...] = ()
    description: str | None = None


class PlanProyecto(ModeloInmutable):
    name: str
    artifact_id: str
    package_name: str
    base_package: str
    api_prefix: str = "/api"


class PlanGeneracion(ModeloInmutable):
    schema_version: Literal[1] = 1
    source_transformation_id: str | None = None
    source_model_version: int
    mode: Literal["coordinated", "legacy_only"] = "coordinated"
    project: PlanProyecto
    entities: tuple[PlanEntidad, ...] = ()
    relationships: tuple[dict, ...] = ()
    operations: tuple[PlanOperacion, ...] = ()
    routes: tuple[PlanRuta, ...] = ()
    dtos: tuple[PlanDTO, ...] = ()
    ui_actions: tuple[PlanAccionUI, ...] = ()
    theme: dict = Field(default_factory=dict)
    diagnostics: tuple[DiagnosticoPlan, ...] = ()
    canonical_hash: str

    @property
    def errors(self) -> tuple[DiagnosticoPlan, ...]:
        return tuple(item for item in self.diagnostics if item.severity == "error")

    @property
    def ready(self) -> bool:
        return not self.errors
