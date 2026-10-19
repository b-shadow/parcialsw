import re
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

OperationKind = Literal[
    "create", "read", "search", "update", "delete", "calculate", "business_action", "custom"
]
Exposure = Literal["internal", "api", "user_action"]
ReadinessStatus = Literal["empty", "draft", "needs_review", "invalid", "ready", "legacy"]

SNAKE_CASE = re.compile(r"^[a-z][a-z0-9_]*$")
UPPER_SNAKE_CASE = re.compile(r"^[A-Z][A-Z0-9_]*$")
PERMISSION_CODE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$")


class StrictModel(BaseModel):
    model_config = {"extra": "forbid"}


def _snake(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    return normalized


class MethodTargetReference(StrictModel):
    kind: Literal["parameter", "attribute", "class", "relationship"]
    id: UUID | None = None
    name: str = Field(min_length=1, max_length=120)


class MethodGenerationRule(StrictModel):
    kind: Literal[
        "required",
        "range",
        "length",
        "pattern",
        "exists_by_id",
        "unique_by_fields",
        "state_transition",
        "calculation",
    ]
    entity_id: UUID | None = None
    fields: list[str] = Field(default_factory=list, max_length=20)
    minimum: float | None = None
    maximum: float | None = None
    pattern: str | None = Field(default=None, max_length=200)
    from_states: list[str] = Field(default_factory=list, max_length=20)
    to_state: str | None = Field(default=None, max_length=80)

    @field_validator("pattern")
    @classmethod
    def reject_unsafe_pattern(cls, value: str | None) -> str | None:
        if value and len(value) > 200:
            raise ValueError("El patron excede el limite permitido")
        return value


class MethodRuleItem(StrictModel):
    code: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=500)
    severity: Literal["info", "warning", "error"] = "error"
    target: MethodTargetReference | None = None
    error_code: str | None = Field(default=None, max_length=80)
    generation: MethodGenerationRule | None = None

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        normalized = _snake(value)
        if not SNAKE_CASE.fullmatch(normalized):
            raise ValueError("El codigo debe usar snake_case")
        return normalized

    @field_validator("error_code")
    @classmethod
    def validate_error_code(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = re.sub(r"[^A-Z0-9]+", "_", value.strip().upper()).strip("_")
        if not UPPER_SNAKE_CASE.fullmatch(normalized):
            raise ValueError("El codigo de error debe usar UPPER_SNAKE_CASE")
        return normalized


class MethodSideEffect(StrictModel):
    code: str = Field(min_length=1, max_length=80)
    kind: Literal[
        "data_change", "status_change", "notification", "audit_event", "refresh_required"
    ]
    description: str = Field(min_length=1, max_length=500)
    target_entity_id: UUID | None = None
    target_entity_name: str | None = Field(default=None, max_length=120)

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        normalized = _snake(value)
        if not SNAKE_CASE.fullmatch(normalized):
            raise ValueError("El codigo debe usar snake_case")
        return normalized


class RequiredPermission(StrictModel):
    code: str = Field(min_length=3, max_length=120)
    description: str | None = Field(default=None, max_length=300)

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not PERMISSION_CODE.fullmatch(normalized):
            raise ValueError("El permiso debe usar el formato recurso.accion")
        return normalized


class RelatedEntityReference(StrictModel):
    class_id: UUID | None = None
    class_name: str = Field(min_length=1, max_length=120)
    relation: Literal[
        "owner", "input_reference", "output", "reads", "creates", "updates", "deletes", "refresh_target"
    ]
    required: bool = False
    source_parameter_id: UUID | None = None


class BackendStatusCodes(StrictModel):
    success: int = Field(default=200, ge=100, le=599)
    validation_error: int = Field(default=400, ge=400, le=499)
    not_found: int = Field(default=404, ge=400, le=499)
    conflict: int = Field(default=409, ge=400, le=499)


class BackendMethodContract(StrictModel):
    http_method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
    path: str = Field(min_length=1, max_length=255)
    request_dto: str | None = Field(default=None, max_length=160)
    response_dto: str | None = Field(default=None, max_length=160)
    transactional: bool = False
    authorization: list[str] = Field(default_factory=list, max_length=50)
    error_codes: list[str] = Field(default_factory=list, max_length=50)
    status_codes: BackendStatusCodes = Field(default_factory=BackendStatusCodes)

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        value = value.strip()
        if (
            not value.startswith("/")
            or ".." in value
            or "?" in value
            or "#" in value
            or "://" in value
            or re.search(r"\s", value)
        ):
            raise ValueError("La ruta debe ser relativa, segura y sin query fija")
        return value

    @field_validator("authorization")
    @classmethod
    def normalize_authorization(cls, values: list[str]) -> list[str]:
        return list(dict.fromkeys(value.strip().lower() for value in values if value.strip()))

    @field_validator("error_codes")
    @classmethod
    def normalize_errors(cls, values: list[str]) -> list[str]:
        normalized = [re.sub(r"[^A-Z0-9]+", "_", value.upper()).strip("_") for value in values]
        if any(not UPPER_SNAKE_CASE.fullmatch(value) for value in normalized):
            raise ValueError("Los errores deben usar UPPER_SNAKE_CASE")
        return list(dict.fromkeys(normalized))


class FlutterFieldContract(StrictModel):
    parameter_id: UUID | None = None
    parameter: str = Field(min_length=1, max_length=120)
    control: Literal[
        "text_input", "multiline_text", "number_input", "decimal_input", "switch",
        "date_picker", "date_time_picker", "single_select", "entity_selector", "multi_select",
    ]
    source_entity_id: UUID | None = None
    source_entity: str | None = Field(default=None, max_length=120)
    display_fields: list[str] = Field(default_factory=list, max_length=10)
    hidden: bool = False

    @model_validator(mode="before")
    @classmethod
    def adapt_legacy_controls(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        aliases = {
            "text": "text_input", "textarea": "multiline_text", "number": "number_input",
            "date": "date_picker", "select": "single_select",
        }
        adapted = dict(value)
        adapted["control"] = aliases.get(str(adapted.get("control")), adapted.get("control"))
        return adapted


class FlutterMethodContract(StrictModel):
    interaction: Literal["form", "button", "menu_action", "background", "filter"]
    label: str = Field(min_length=1, max_length=160)
    placement: str | None = Field(default=None, max_length=100)
    confirmation_required: bool = False
    refresh_targets: list[UUID] = Field(default_factory=list, max_length=30)
    success_message: str | None = Field(default=None, max_length=300)
    fields: list[FlutterFieldContract] = Field(default_factory=list, max_length=50)


def _normalize_rules(values: list[MethodRuleItem | str]) -> list[MethodRuleItem]:
    result: list[MethodRuleItem] = []
    for index, value in enumerate(values):
        if isinstance(value, str):
            result.append(MethodRuleItem(code=_snake(value)[:70] or f"rule_{index + 1}", description=value.strip()))
        else:
            result.append(value)
    return result


def _normalize_permissions(values: list[RequiredPermission | str]) -> list[RequiredPermission]:
    result = []
    for value in values:
        if isinstance(value, str):
            result.append(RequiredPermission(code=value))
        else:
            result.append(value)
    return result


class UmlMethodSpecificationBase(StrictModel):
    description: str | None = Field(default=None, max_length=4000)
    operation_kind: OperationKind = "custom"
    exposure: Exposure = "internal"
    preconditions: list[MethodRuleItem | str] = Field(default_factory=list, max_length=100)
    postconditions: list[MethodRuleItem | str] = Field(default_factory=list, max_length=100)
    business_rules: list[MethodRuleItem | str] = Field(default_factory=list, max_length=100)
    validations: list[MethodRuleItem | str] = Field(default_factory=list, max_length=100)
    side_effects: list[MethodSideEffect] = Field(default_factory=list, max_length=100)
    required_permissions: list[RequiredPermission | str] = Field(default_factory=list, max_length=50)
    related_entities: list[RelatedEntityReference] = Field(default_factory=list, max_length=50)
    backend_contract: BackendMethodContract | None = None
    frontend_contract: FlutterMethodContract | None = None
    schema_version: Literal[1] = 1

    @field_validator("backend_contract", "frontend_contract", mode="before")
    @classmethod
    def empty_contract_is_absent(cls, value: object) -> object:
        return None if value == {} else value

    @field_validator("preconditions", "postconditions", "business_rules", "validations")
    @classmethod
    def normalize_rules(cls, value: list[MethodRuleItem | str]) -> list[MethodRuleItem]:
        return _normalize_rules(value)

    @field_validator("required_permissions")
    @classmethod
    def normalize_permissions(
        cls, value: list[RequiredPermission | str]
    ) -> list[RequiredPermission]:
        return _normalize_permissions(value)


class UmlMethodSpecificationCreate(UmlMethodSpecificationBase):
    pass


class UmlMethodSpecificationPatch(StrictModel):
    description: str | None = Field(default=None, max_length=4000)
    operation_kind: OperationKind | None = None
    exposure: Exposure | None = None
    preconditions: list[MethodRuleItem | str] | None = Field(default=None, max_length=100)
    postconditions: list[MethodRuleItem | str] | None = Field(default=None, max_length=100)
    business_rules: list[MethodRuleItem | str] | None = Field(default=None, max_length=100)
    validations: list[MethodRuleItem | str] | None = Field(default=None, max_length=100)
    side_effects: list[MethodSideEffect] | None = Field(default=None, max_length=100)
    required_permissions: list[RequiredPermission | str] | None = Field(default=None, max_length=50)
    related_entities: list[RelatedEntityReference] | None = Field(default=None, max_length=50)
    backend_contract: BackendMethodContract | None = None
    frontend_contract: FlutterMethodContract | None = None
    schema_version: Literal[1] | None = None

    @field_validator("preconditions", "postconditions", "business_rules", "validations")
    @classmethod
    def normalize_optional_rules(
        cls, value: list[MethodRuleItem | str] | None
    ) -> list[MethodRuleItem] | None:
        return _normalize_rules(value) if value is not None else None

    @field_validator("required_permissions")
    @classmethod
    def normalize_optional_permissions(
        cls, value: list[RequiredPermission | str] | None
    ) -> list[RequiredPermission] | None:
        return _normalize_permissions(value) if value is not None else None


class MethodDiagnostic(StrictModel):
    code: str
    severity: Literal["info", "warning", "error"]
    path: str
    message: str
    suggestion: str | None = None
    related_element_id: UUID | None = None


class MethodSpecificationValidationResponse(StrictModel):
    status: ReadinessStatus
    ready_for_generation: bool
    errors: list[MethodDiagnostic] = Field(default_factory=list)
    warnings: list[MethodDiagnostic] = Field(default_factory=list)
    inferred_fields: list[str] = Field(default_factory=list)


class UmlMethodSpecificationResponse(UmlMethodSpecificationBase):
    id: UUID
    method_id: UUID
    revision: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "extra": "forbid"}


class MethodSpecificationEnvelope(StrictModel):
    specification: UmlMethodSpecificationResponse | None
    readiness: MethodSpecificationValidationResponse


class MethodSpecificationRefineRequest(StrictModel):
    instruction: str = Field(min_length=3, max_length=8000)
    base_revision: int = Field(ge=0)
    client_message_id: UUID


class MethodSpecificationProposalResponse(StrictModel):
    action_id: UUID
    method_id: UUID
    base_revision: int
    summary: str
    patch: UmlMethodSpecificationPatch
    changed_fields: list[str]
    unresolved_references: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    validation: MethodSpecificationValidationResponse
    provider: str
    fallback_used: bool = False


# Aliases retained for imports created in the first two phases.
SpecificationRule = MethodRuleItem
RelatedEntity = RelatedEntityReference
BackendContract = BackendMethodContract
FrontendContract = FlutterMethodContract
