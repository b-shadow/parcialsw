from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class PlanDiagnostic(FrozenModel):
    code: str
    severity: Literal["warning", "error"]
    message: str
    suggestion: str | None = None
    method_id: str | None = None
    class_id: str | None = None
    path: str | None = None


class LogicalTypePlan(FrozenModel):
    logical: str
    source: str
    java: str
    dart: str
    json_type: str
    json_format: str | None = None
    nullable: bool = True
    entity_id: str | None = None


class EntityFieldPlan(FrozenModel):
    id: str | None = None
    source_name: str
    json_name: str
    logical_type: LogicalTypePlan
    required: bool = False


class EntityPlan(FrozenModel):
    id: str
    source_name: str
    name: str
    module_name: str
    fields: tuple[EntityFieldPlan, ...] = ()


class ParameterPlan(FrozenModel):
    id: str
    source_name: str
    name: str
    logical_type: LogicalTypePlan
    required: bool = True
    location: Literal["path", "query", "body", "context"] = "body"
    order_index: int = 0


class OperationRulePlan(FrozenModel):
    code: str
    kind: str
    error_code: str
    fields: tuple[str, ...] = ()
    minimum: float | None = None
    maximum: float | None = None
    pattern: str | None = None
    entity_id: str | None = None
    severity: str = "error"


class RoutePlan(FrozenModel):
    operation_id: str
    http_method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
    contractual_path: str
    effective_path: str
    path_parameters: tuple[str, ...] = ()
    query_parameters: tuple[str, ...] = ()
    body_fields: tuple[str, ...] = ()
    success_status: int = 200
    permissions: tuple[str, ...] = ()


class DtoFieldPlan(FrozenModel):
    source_parameter_id: str
    json_name: str
    logical_type: LogicalTypePlan
    required: bool = True
    constraints: tuple[OperationRulePlan, ...] = ()


class DtoPlan(FrozenModel):
    name: str
    direction: Literal["request", "response"]
    operation_id: str
    fields: tuple[DtoFieldPlan, ...] = ()


class UiFieldPlan(FrozenModel):
    parameter_id: str
    json_name: str
    label: str
    control: str
    logical_type: LogicalTypePlan
    required: bool = True
    hidden: bool = False
    source_entity_id: str | None = None
    source_entity: str | None = None
    source_module: str | None = None
    display_fields: tuple[str, ...] = ()


class UiActionPlan(FrozenModel):
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
    fields: tuple[UiFieldPlan, ...] = ()


class OperationPlan(FrozenModel):
    id: str
    owner_entity_id: str
    owner_entity: str
    owner_module: str
    source_name: str
    java_name: str
    dart_name: str
    operation_kind: str
    exposure: Literal["internal", "api", "user_action"]
    return_type: LogicalTypePlan
    parameters: tuple[ParameterPlan, ...] = ()
    route: RoutePlan | None = None
    request_dto: DtoPlan | None = None
    response_dto: DtoPlan | None = None
    ui_action: UiActionPlan | None = None
    rules: tuple[OperationRulePlan, ...] = ()
    permissions: tuple[str, ...] = ()
    side_effects: tuple[dict, ...] = ()
    description: str | None = None


class ProjectPlan(FrozenModel):
    name: str
    artifact_id: str
    package_name: str
    base_package: str
    api_prefix: str = "/api"


class GenerationPlan(FrozenModel):
    schema_version: Literal[1] = 1
    source_transformation_id: str | None = None
    source_model_version: int
    mode: Literal["coordinated", "legacy_only"] = "coordinated"
    project: ProjectPlan
    entities: tuple[EntityPlan, ...] = ()
    relationships: tuple[dict, ...] = ()
    operations: tuple[OperationPlan, ...] = ()
    routes: tuple[RoutePlan, ...] = ()
    dtos: tuple[DtoPlan, ...] = ()
    ui_actions: tuple[UiActionPlan, ...] = ()
    theme: dict = Field(default_factory=dict)
    diagnostics: tuple[PlanDiagnostic, ...] = ()
    canonical_hash: str

    @property
    def errors(self) -> tuple[PlanDiagnostic, ...]:
        return tuple(item for item in self.diagnostics if item.severity == "error")

    @property
    def ready(self) -> bool:
        return not self.errors
