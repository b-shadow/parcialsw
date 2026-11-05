from collections import defaultdict
from uuid import UUID

from pydantic import BaseModel, Field, ValidationError, model_validator

from ai_engine.context.contratos import ContextoIAProyecto
from ai_engine.orchestration.contratos import AccionPlanificada
from ai_engine.providers.errores import ErrorSalidaEstructuradaInvalida


class CargaCreacionClase(BaseModel):
    model_config = {"extra": "forbid"}

    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    stereotype: str | None = Field(default=None, max_length=80)
    visibility: str = Field(default="public", max_length=20)
    element_type: str = Field(default="class", max_length=40)
    position_x: float = 0
    position_y: float = 0


class CargaActualizacionClase(BaseModel):
    model_config = {"extra": "forbid"}

    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    stereotype: str | None = Field(default=None, max_length=80)
    visibility: str | None = Field(default=None, max_length=20)
    element_type: str | None = Field(default=None, max_length=40)


class CargaCreacionAtributo(BaseModel):
    model_config = {"extra": "forbid"}

    class_id: UUID | None = None
    class_name: str | None = Field(default=None, max_length=120)
    name: str = Field(min_length=1, max_length=120)
    data_type: str = Field(min_length=1, max_length=120)
    visibility: str = Field(default="private", max_length=20)
    initial_value: str | None = Field(default=None, max_length=255)
    multiplicity: str | None = Field(default=None, max_length=40)
    is_required: bool = False
    order_index: int = 0
    constraints: dict = Field(default_factory=dict)


class CargaActualizacionAtributo(BaseModel):
    model_config = {"extra": "forbid"}

    name: str | None = Field(default=None, min_length=1, max_length=120)
    data_type: str | None = Field(default=None, min_length=1, max_length=120)
    visibility: str | None = Field(default=None, max_length=20)
    initial_value: str | None = Field(default=None, max_length=255)
    multiplicity: str | None = Field(default=None, max_length=40)
    is_required: bool | None = None
    order_index: int | None = None
    constraints: dict | None = None


class CargaCreacionMetodo(BaseModel):
    model_config = {"extra": "forbid"}

    class_id: UUID | None = None
    class_name: str | None = Field(default=None, max_length=120)
    name: str = Field(min_length=1, max_length=120)
    return_type: str | None = Field(default=None, max_length=120)
    visibility: str = Field(default="public", max_length=20)
    order_index: int = 0


class CargaActualizacionMetodo(BaseModel):
    model_config = {"extra": "forbid"}

    name: str | None = Field(default=None, min_length=1, max_length=120)
    return_type: str | None = Field(default=None, max_length=120)
    visibility: str | None = Field(default=None, max_length=20)
    order_index: int | None = None


class CargaCreacionRelacion(BaseModel):
    model_config = {"extra": "forbid"}

    source_class_id: UUID | None = None
    source_class_name: str | None = Field(default=None, max_length=120)
    target_class_id: UUID | None = None
    target_class_name: str | None = Field(default=None, max_length=120)
    relationship_type: str = Field(pattern="^(association|inheritance|implementation|dependency|aggregation|composition)$")
    source_cardinality: str | None = Field(default=None, max_length=40)
    target_cardinality: str | None = Field(default=None, max_length=40)
    label: str | None = Field(default=None, max_length=120)
    direction: str = Field(default="source_to_target", max_length=40)


class CargaActualizacionRelacion(BaseModel):
    model_config = {"extra": "forbid"}

    relationship_type: str | None = Field(
        default=None,
        pattern="^(association|inheritance|implementation|dependency|aggregation|composition)$",
    )
    source_cardinality: str | None = Field(default=None, max_length=40)
    target_cardinality: str | None = Field(default=None, max_length=40)
    direction: str | None = Field(default=None, max_length=40)
    label: str | None = Field(default=None, max_length=120)


class CargaEspecificacionMetodo(BaseModel):
    model_config = {"extra": "forbid"}

    description: str | None = Field(default=None, max_length=4000)
    operation_kind: str = Field(default="custom", max_length=40)
    exposure: str = Field(default="internal", max_length=40)
    preconditions: list = Field(default_factory=list)
    postconditions: list = Field(default_factory=list)
    business_rules: list = Field(default_factory=list)
    validations: list = Field(default_factory=list)
    side_effects: list = Field(default_factory=list)
    required_permissions: list[str] = Field(default_factory=list)
    related_entities: list[dict] = Field(default_factory=list)
    backend_contract: dict | None = None
    frontend_contract: dict | None = None
    schema_version: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def contratos_visibles_completos(self):
        if self.exposure in {"api", "user_action"} and self.backend_contract is None:
            raise ValueError("Una operacion visible requiere contrato backend")
        if self.exposure == "user_action" and self.frontend_contract is None:
            raise ValueError("Una accion de usuario requiere contrato Flutter")
        return self


class CargaGuardadoVersion(BaseModel):
    model_config = {"extra": "forbid"}

    name: str = Field(default="Version guardada por IA", min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)


class CargaVacia(BaseModel):
    model_config = {"extra": "forbid"}


PAYLOAD_MODELS: dict[str, type[BaseModel]] = {
    "create_class": CargaCreacionClase,
    "update_class": CargaActualizacionClase,
    "delete_class": CargaVacia,
    "create_attribute": CargaCreacionAtributo,
    "update_attribute": CargaActualizacionAtributo,
    "delete_attribute": CargaVacia,
    "create_method": CargaCreacionMetodo,
    "update_method": CargaActualizacionMetodo,
    "delete_method": CargaVacia,
    "create_relationship": CargaCreacionRelacion,
    "update_relationship": CargaActualizacionRelacion,
    "delete_relationship": CargaVacia,
    "update_method_specification": CargaEspecificacionMetodo,
    "save_version": CargaGuardadoVersion,
    "prepare_backend_generation": CargaVacia,
    "prepare_flutter_generation": CargaVacia,
}

HIGH_RISK = {"delete_class", "delete_attribute", "delete_method", "delete_relationship"}
MEDIUM_RISK = {
    "create_class",
    "update_class",
    "create_attribute",
    "update_attribute",
    "create_method",
    "update_method",
    "create_relationship",
    "update_relationship",
    "update_method_specification",
}


class PoliticaAcciones:
    def validar_plan(
        self,
        actions: list[AccionPlanificada],
        context: ContextoIAProyecto,
    ) -> list[AccionPlanificada]:
        action_by_id = {action.id: action for action in actions}
        if len(action_by_id) != len(actions):
            raise ErrorSalidaEstructuradaInvalida("El plan contiene IDs de accion duplicados")
        for action in actions:
            missing = [dependency for dependency in action.depends_on if dependency not in action_by_id]
            if missing:
                raise ErrorSalidaEstructuradaInvalida("El plan contiene una dependencia inexistente")
            self._validar_carga(action)
            self._validar_referencias(action, context, actions)
            self._aplicar_riesgo(action, context)
        self._asegurar_sin_ciclos(action_by_id)
        return sorted(actions, key=lambda item: item.order)

    @staticmethod
    def _validar_carga(action: AccionPlanificada) -> None:
        payload_model = PAYLOAD_MODELS.get(action.action_type)
        if payload_model is None:
            if not isinstance(action.payload, dict):
                raise ErrorSalidaEstructuradaInvalida("Payload de accion invalido")
            return
        try:
            validated = payload_model.model_validate(action.payload)
            action.payload = validated.model_dump(mode="json", exclude_none=True)
        except ValidationError as exc:
            raise ErrorSalidaEstructuradaInvalida(
                f"Payload invalido para {action.action_type}: {exc.errors()[0]['msg']}"
            ) from exc

    @staticmethod
    def _aplicar_riesgo(action: AccionPlanificada, context: ContextoIAProyecto) -> None:
        if action.action_type in HIGH_RISK:
            action.risk_level = "high"
            action.requires_confirmation = True
        elif action.action_type in MEDIUM_RISK:
            action.risk_level = "medium"
            action.requires_confirmation = context.constraints.require_confirmation
        else:
            action.risk_level = "low"
            action.requires_confirmation = context.constraints.require_confirmation

    @staticmethod
    def _validar_referencias(
        action: AccionPlanificada,
        context: ContextoIAProyecto,
        actions: list[AccionPlanificada],
    ) -> None:
        uml_actions = {
            "create_class",
            "update_class",
            "delete_class",
            "create_attribute",
            "update_attribute",
            "delete_attribute",
            "create_method",
            "update_method",
            "delete_method",
            "create_relationship",
            "update_relationship",
            "delete_relationship",
            "update_method_specification",
        }
        if action.action_type not in uml_actions:
            return
        diagram = context.active_diagram
        if diagram is None:
            raise ErrorSalidaEstructuradaInvalida("Una accion UML requiere un diagrama activo")
        if action.diagram_id is not None and action.diagram_id != diagram.id:
            raise ErrorSalidaEstructuradaInvalida("La accion referencia un diagrama externo")
        known_ids: set[str] = set()
        known_names: set[str] = set()
        for uml_class in diagram.classes:
            known_ids.add(str(uml_class.get("id")))
            known_names.add(str(uml_class.get("name", "")).casefold())
            for key in ("attributes", "methods"):
                for member in uml_class.get(key, []):
                    if isinstance(member, dict):
                        known_ids.add(str(member.get("id")))
        for relationship in diagram.relationships:
            known_ids.add(str(relationship.get("id")))
        if action.target_id is not None and str(action.target_id) not in known_ids:
            raise ErrorSalidaEstructuradaInvalida("La accion referencia un elemento externo")
        created_names = {
            str(item.payload.get("name", "")).casefold()
            for item in actions
            if item.action_type == "create_class"
        }
        allowed_names = known_names | created_names
        for key in ("class_name", "source_class_name", "target_class_name"):
            name = action.payload.get(key)
            if name and str(name).casefold() not in allowed_names:
                raise ErrorSalidaEstructuradaInvalida(
                    f"La accion referencia una clase inexistente: {name}"
                )
        for key in ("class_id", "source_class_id", "target_class_id"):
            reference = action.payload.get(key)
            if reference and str(reference) not in known_ids:
                raise ErrorSalidaEstructuradaInvalida("La accion referencia una clase externa")
    @staticmethod
    def _asegurar_sin_ciclos(action_by_id: dict[UUID, AccionPlanificada]) -> None:
        graph: dict[UUID, list[UUID]] = defaultdict(list)
        for action in action_by_id.values():
            graph[action.id].extend(action.depends_on)
        visiting: set[UUID] = set()
        visited: set[UUID] = set()

        def visit(node: UUID) -> None:
            if node in visiting:
                raise ErrorSalidaEstructuradaInvalida("El plan de acciones contiene un ciclo")
            if node in visited:
                return
            visiting.add(node)
            for dependency in graph[node]:
                visit(dependency)
            visiting.remove(node)
            visited.add(node)

        for action_id in action_by_id:
            visit(action_id)
