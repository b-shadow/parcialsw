import hashlib
import json
import re
from typing import Literal

from app.modules.generacion_software.coordinated_generator.compiler.nombres import (
    camel,
    is_reserved,
    kebab,
    pascal,
    safe_route,
    snake,
)
from app.modules.generacion_software.coordinated_generator.compiler.registro_tipos import (
    resolver_tipo_logico,
)
from app.modules.generacion_software.coordinated_generator.contracts import (
    DiagnosticoPlan,
    PlanAccionUI,
    PlanCampoDTO,
    PlanCampoEntidad,
    PlanCampoUI,
    PlanDTO,
    PlanEntidad,
    PlanGeneracion,
    PlanOperacion,
    PlanParametro,
    PlanProyecto,
    PlanReglaOperacion,
    PlanRuta,
)
from app.modules.generacion_software.services.modelo_intermedio import (
    requerir_modelo_intermedio_admitido,
)

SUPPORTED_CONTROLS = {
    "text_input", "multiline_text", "number_input", "decimal_input", "switch",
    "date_picker", "date_time_picker", "single_select", "entity_selector", "multi_select",
}
SUPPORTED_RULES = {
    "required", "range", "length", "pattern", "exists_by_id",
    "unique_by_fields", "state_transition", "calculation",
}
MUTATING_OPERATIONS = {"create", "update", "delete", "business_action"}


def compilar_plan_generacion(
    intermediate_model: dict,
    project_name: str,
    *,
    source_transformation_id: str | None = None,
    mode: Literal["coordinated", "legacy_only"] = "coordinated",
    theme: dict | None = None,
) -> PlanGeneracion:
    original_version = int(intermediate_model.get("schema_version", 1))
    model = requerir_modelo_intermedio_admitido(intermediate_model)
    diagnostics: list[DiagnosticoPlan] = []
    entities = _compilar_entidades(model, diagnostics)
    entity_by_id = {item.id: item for item in entities}
    entity_by_name = {
        item.source_name.casefold(): (item.id, item.name) for item in entities
    }
    operations: list[PlanOperacion] = []
    routes: list[PlanRuta] = []
    dtos: list[PlanDTO] = []
    ui_actions: list[PlanAccionUI] = []
    occupied_routes = _rutas_heredadas(entities)

    if mode == "coordinated":
        for raw_class in model.get("classes", []):
            owner = entity_by_id.get(str(raw_class.get("id")))
            if owner is None:
                continue
            for raw_method in raw_class.get("methods", []) or []:
                operation = _compilar_operacion(
                    raw_method,
                    owner,
                    entity_by_id,
                    entity_by_name,
                    diagnostics,
                )
                if operation is None:
                    continue
                if operation.route:
                    key = (operation.route.http_method, operation.route.effective_path.rstrip("/"))
                    if key in occupied_routes:
                        diagnostics.append(_diagnostico(
                            "route_collision", "error",
                            f"La ruta {key[0]} {key[1]} colisiona con otra operacion.",
                            operation.id, owner.id, "backend_contract.path",
                            "Cambie la ruta o el metodo HTTP de la especificacion.",
                        ))
                    occupied_routes.add(key)
                    routes.append(operation.route)
                operations.append(operation)
                if operation.request_dto:
                    dtos.append(operation.request_dto)
                if operation.response_dto:
                    dtos.append(operation.response_dto)
                if operation.ui_action:
                    ui_actions.append(operation.ui_action)

    project = PlanProyecto(
        name=pascal(project_name) or "AplicacionGenerada",
        artifact_id=kebab(project_name) or "aplicacion-generada",
        package_name=snake(project_name) or "aplicacion_generada",
        base_package=f"com.caseinteligente.generated.{(camel(project_name) or 'app').lower()}",
    )
    payload = {
        "schema_version": 1,
        "source_transformation_id": source_transformation_id,
        "source_model_version": original_version,
        "mode": mode,
        "project": project.model_dump(mode="json"),
        "entities": [item.model_dump(mode="json") for item in entities],
        "relationships": model.get("relationships", []),
        "operations": [item.model_dump(mode="json") for item in operations],
        "routes": [item.model_dump(mode="json") for item in routes],
        "dtos": [item.model_dump(mode="json") for item in dtos],
        "ui_actions": [item.model_dump(mode="json") for item in ui_actions],
        "theme": theme or {},
        "diagnostics": [item.model_dump(mode="json") for item in diagnostics],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return PlanGeneracion(**payload, canonical_hash=hashlib.sha256(canonical.encode()).hexdigest())


def _compilar_entidades(model: dict, diagnostics: list[DiagnosticoPlan]) -> tuple[PlanEntidad, ...]:
    result: list[PlanEntidad] = []
    normalized: set[str] = set()
    for index, raw in enumerate(model.get("classes", [])):
        source_name = str(raw.get("name") or "").strip()
        name = pascal(source_name)
        class_id = str(raw.get("id") or "")
        if not class_id or not name:
            diagnostics.append(DiagnosticoPlan(
                code="invalid_entity", severity="error",
                message=f"La clase en posicion {index} no tiene identidad y nombre validos.",
                path=f"classes[{index}]",
            ))
            continue
        if name.casefold() in normalized or is_reserved(name):
            diagnostics.append(DiagnosticoPlan(
                code="entity_name_collision", severity="error", class_id=class_id,
                message=f"El nombre normalizado {name} es duplicado o reservado.",
                path=f"classes[{index}].name",
            ))
        normalized.add(name.casefold())
        fields: list[PlanCampoEntidad] = []
        for raw_field in raw.get("attributes", []) or []:
            source_field = str(raw_field.get("name") or "").strip()
            if source_field.casefold() == "id":
                continue
            logical = resolver_tipo_logico(
                str(raw_field.get("data_type") or "String"),
                nullable=not bool(raw_field.get("is_required", False)),
            )
            if logical is None:
                diagnostics.append(_diagnostico(
                    "unknown_type", "error",
                    f"El tipo {raw_field.get('data_type')} no esta soportado.",
                    None, class_id, f"attributes.{source_field}.data_type",
                    "Use un tipo del registro comun.",
                ))
                continue
            fields.append(PlanCampoEntidad(
                id=str(raw_field.get("id")) if raw_field.get("id") else None,
                source_name=source_field,
                json_name=camel(source_field),
                logical_type=logical,
                required=bool(raw_field.get("is_required", False)),
            ))
        result.append(PlanEntidad(
            id=class_id,
            source_name=source_name,
            name=name,
            module_name=snake(name),
            fields=tuple(fields),
        ))
    return tuple(result)


def _compilar_operacion(raw, owner, entity_by_id, entity_by_name, diagnostics):
    method_id = str(raw.get("id") or "")
    specification = raw.get("specification")
    readiness = raw.get("readiness") or {}
    status = str(readiness.get("status") or "legacy")
    if not specification or status in {"legacy", "empty"}:
        return None
    if status != "ready" or not readiness.get("ready_for_generation"):
        diagnostics.append(_diagnostico(
            "method_not_ready", "error",
            f"El metodo {raw.get('name')} esta en estado {status}.", method_id,
            owner.id, "readiness", "Complete y valide estrictamente su especificacion.",
        ))
        return None
    source_name = str(raw.get("name") or "").strip()
    java_name = camel(source_name)
    if not method_id or not java_name or is_reserved(java_name):
        diagnostics.append(_diagnostico(
            "reserved_operation_name", "error", f"El nombre {source_name} no es generable.",
            method_id, owner.id, "name", "Use un nombre no reservado.",
        ))
        return None
    parameters = _compilar_parametros(
        raw.get("parameters", []), method_id, owner.id, entity_by_name, diagnostics
    )
    return_type = resolver_tipo_logico(
        raw.get("return_type") or "void", entity_by_name=entity_by_name
    )
    if return_type is None:
        diagnostics.append(_diagnostico(
            "unknown_type", "error", f"El retorno {raw.get('return_type')} no esta soportado.",
            method_id, owner.id, "return_type", "Use un tipo del registro comun.",
        ))
        return None
    operation_kind = str(specification.get("operation_kind") or "custom")
    exposure = str(specification.get("exposure") or "internal")
    backend = specification.get("backend_contract")
    frontend = specification.get("frontend_contract")
    if operation_kind == "custom":
        diagnostics.append(_diagnostico(
            "unsupported_operation_kind", "error", "Una operacion custom no define estrategia ejecutable.",
            method_id, owner.id, "operation_kind", "Seleccione una operacion soportada.",
        ))
    route = _compilar_ruta(method_id, backend, parameters, specification, diagnostics, owner.id)
    if exposure == "internal":
        route = None
    elif route is None:
        diagnostics.append(_diagnostico(
            "missing_backend_contract", "error", "La operacion expuesta no tiene ruta backend.",
            method_id, owner.id, "backend_contract", "Defina el contrato backend.",
        ))
    if route:
        parameters = tuple(
            item.model_copy(
                update={
                    "location": (
                        "path"
                        if item.name in route.path_parameters
                        else "query"
                        if item.name in route.query_parameters
                        else "body"
                    )
                }
            )
            for item in parameters
        )
    rules = _compilar_reglas(specification, method_id, owner.id, diagnostics)
    request_dto = _solicitud_dto(owner, java_name, method_id, parameters, rules)
    response_dto = _respuesta_dto(owner, java_name, method_id, return_type)
    ui_action = _compilar_accion_ui(
        method_id, owner, java_name, exposure, frontend, parameters,
        entity_by_id, diagnostics,
    )
    permissions = tuple(dict.fromkeys(
        str(item.get("code")) if isinstance(item, dict) else str(item)
        for item in [
            *specification.get("required_permissions", []),
            *((backend or {}).get("authorization", [])),
        ]
    ))
    if route:
        route = route.model_copy(update={"permissions": permissions})
    return PlanOperacion(
        id=method_id,
        owner_entity_id=owner.id,
        owner_entity=owner.name,
        owner_module=owner.module_name,
        source_name=source_name,
        java_name=java_name,
        dart_name=java_name,
        operation_kind=operation_kind,
        exposure=exposure,
        return_type=return_type,
        parameters=parameters,
        route=route,
        request_dto=request_dto,
        response_dto=response_dto,
        ui_action=ui_action,
        rules=rules,
        permissions=permissions,
        side_effects=tuple(specification.get("side_effects", [])),
        description=specification.get("description"),
    )


def _compilar_parametros(raw_parameters, method_id, class_id, entity_by_name, diagnostics):
    result = []
    seen: set[str] = set()
    for index, raw in enumerate(sorted(raw_parameters, key=lambda item: item.get("order_index", 0))):
        source_name = str(raw.get("name") or "")
        name = camel(source_name)
        if not name or name in seen or is_reserved(name):
            diagnostics.append(_diagnostico(
                "parameter_name_collision", "error", f"El parametro {source_name} es duplicado o reservado.",
                method_id, class_id, f"parameters[{index}].name", "Cambie el nombre del parametro.",
            ))
            continue
        seen.add(name)
        logical = resolver_tipo_logico(raw.get("data_type"), entity_by_name=entity_by_name)
        if logical is None:
            diagnostics.append(_diagnostico(
                "unknown_type", "error", f"El tipo {raw.get('data_type')} no esta soportado.",
                method_id, class_id, f"parameters[{index}].data_type", "Use un tipo del registro comun.",
            ))
            continue
        result.append(PlanParametro(
            id=str(raw.get("id") or f"{method_id}-parameter-{index}"),
            source_name=source_name,
            name=name,
            logical_type=logical,
            required=raw.get("default_value") is None,
            order_index=index,
        ))
    return tuple(result)


def _compilar_ruta(method_id, backend, parameters, specification, diagnostics, class_id):
    if not backend:
        return None
    contractual = safe_route(str(backend.get("path") or ""))
    effective = safe_route(f"/api/{contractual.lstrip('/')}")
    path_names = tuple(re.findall(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", contractual))
    parameter_names = {item.name for item in parameters}
    if set(path_names) - parameter_names:
        diagnostics.append(_diagnostico(
            "unresolved_path_parameter", "error", "La ruta contiene parametros ausentes en la firma.",
            method_id, class_id, "backend_contract.path", "Alinee ruta y parametros.",
        ))
    http_method = str(backend.get("http_method") or "POST").upper()
    if http_method == "GET" and specification.get("operation_kind") in MUTATING_OPERATIONS:
        diagnostics.append(_diagnostico(
            "unsafe_get_operation", "error", "GET no puede ejecutar una operacion mutante.",
            method_id, class_id, "backend_contract.http_method", "Use POST, PUT, PATCH o DELETE.",
        ))
    query = tuple(item.name for item in parameters if http_method == "GET" and item.name not in path_names)
    body = tuple(item.name for item in parameters if http_method != "GET" and item.name not in path_names)
    status_codes = backend.get("status_codes") or {}
    return PlanRuta(
        operation_id=method_id,
        http_method=http_method,
        contractual_path=contractual,
        effective_path=effective,
        path_parameters=path_names,
        query_parameters=query,
        body_fields=body,
        success_status=int(status_codes.get("success", 200)),
    )


def _compilar_reglas(specification, method_id, class_id, diagnostics):
    result = []
    for collection in ("preconditions", "business_rules", "validations"):
        for index, raw in enumerate(specification.get(collection, [])):
            generation = raw.get("generation") if isinstance(raw, dict) else None
            severity = str(raw.get("severity", "error")) if isinstance(raw, dict) else "error"
            if not generation:
                if severity == "error":
                    diagnostics.append(_diagnostico(
                        "unsupported_rule_for_generation", "error",
                        f"La regla {raw.get('code', index)} no tiene bloque generation.",
                        method_id, class_id, f"{collection}[{index}].generation",
                        "Seleccione una estrategia de regla estructurada.",
                    ))
                continue
            kind = str(generation.get("kind"))
            if kind not in SUPPORTED_RULES:
                diagnostics.append(_diagnostico(
                    "unsupported_rule_for_generation", "error", f"La regla {kind} no esta soportada.",
                    method_id, class_id, f"{collection}[{index}].generation.kind",
                    "Use una regla del catalogo soportado.",
                ))
                continue
            fields = tuple(camel(str(item)) for item in generation.get("fields", []))
            target = raw.get("target") if isinstance(raw, dict) else None
            if not fields and isinstance(target, dict) and target.get("name"):
                fields = (camel(str(target["name"])),)
            if kind in {"unique_by_fields", "calculation"} and not fields:
                diagnostics.append(_diagnostico(
                    "unsupported_rule_for_generation", "error", f"La regla {kind} requiere fields.",
                    method_id, class_id, f"{collection}[{index}].generation.fields",
                    "Seleccione al menos un campo.",
                ))
                continue
            result.append(PlanReglaOperacion(
                code=str(raw.get("code")), kind=kind,
                error_code=str(raw.get("error_code") or str(raw.get("code", "RULE_ERROR")).upper()),
                fields=fields, minimum=generation.get("minimum"), maximum=generation.get("maximum"),
                pattern=generation.get("pattern"), entity_id=(str(generation.get("entity_id")) if generation.get("entity_id") else None),
                severity=severity,
            ))
    return tuple(result)


def _solicitud_dto(owner, java_name, method_id, parameters, rules):
    constraints_by_field: dict[str, list] = {}
    for rule in rules:
        for field in rule.fields:
            constraints_by_field.setdefault(field, []).append(rule)
    return PlanDTO(
        name=f"{owner.name}{pascal(java_name)}Request", direction="request", operation_id=method_id,
        fields=tuple(PlanCampoDTO(
            source_parameter_id=item.id, json_name=item.name, logical_type=item.logical_type,
            required=item.required, constraints=tuple(constraints_by_field.get(item.name, [])),
        ) for item in parameters if item.location == "body"),
    )


def _respuesta_dto(owner, java_name, method_id, return_type):
    if return_type.logical == "void":
        return None
    return PlanDTO(
        name=f"{owner.name}{pascal(java_name)}Response", direction="response", operation_id=method_id,
        fields=(),
    )


def _compilar_accion_ui(method_id, owner, java_name, exposure, frontend, parameters, entity_by_id, diagnostics):
    if exposure != "user_action":
        return None
    if not frontend:
        diagnostics.append(_diagnostico(
            "missing_flutter_action", "error", "La accion visible no tiene contrato Flutter.",
            method_id, owner.id, "frontend_contract", "Defina interaccion y campos.",
        ))
        return None
    parameters_by_id = {item.id: item for item in parameters}
    fields = []
    mapped_parameter_ids: set[str] = set()
    for index, raw in enumerate(frontend.get("fields", [])):
        parameter = parameters_by_id.get(str(raw.get("parameter_id")))
        if parameter is None:
            diagnostics.append(_diagnostico(
                "backend_flutter_mismatch", "error", "El campo Flutter no corresponde a un parametro.",
                method_id, owner.id, f"frontend_contract.fields[{index}]", "Seleccione un parametro real.",
            ))
            continue
        control = str(raw.get("control"))
        if control not in SUPPORTED_CONTROLS:
            diagnostics.append(_diagnostico(
                "unknown_ui_control", "error", f"El control {control} no esta soportado.",
                method_id, owner.id, f"frontend_contract.fields[{index}].control", "Use un control soportado.",
            ))
            continue
        source = entity_by_id.get(str(raw.get("source_entity_id")))
        if control == "entity_selector" and source is None:
            diagnostics.append(_diagnostico(
                "unresolved_entity_reference", "error", "El selector no tiene entidad fuente valida.",
                method_id, owner.id, f"frontend_contract.fields[{index}].source_entity_id",
                "Seleccione una clase del diagrama.",
            ))
        fields.append(PlanCampoUI(
            parameter_id=parameter.id, json_name=parameter.name,
            label=parameter.source_name, control=control, logical_type=parameter.logical_type,
            required=parameter.required, hidden=bool(raw.get("hidden", False)),
            source_entity_id=source.id if source else None,
            source_entity=source.name if source else None,
            source_module=source.module_name if source else None,
            display_fields=tuple(raw.get("display_fields", [])),
        ))
        mapped_parameter_ids.add(parameter.id)
        if bool(raw.get("hidden", False)) and parameter.required:
            diagnostics.append(_diagnostico(
                "required_ui_parameter_hidden", "error",
                f"El parametro obligatorio {parameter.name} no puede quedar oculto.",
                method_id, owner.id, f"frontend_contract.fields[{index}].hidden",
                "Muestre un control o cambie el parametro a contexto interno.",
            ))
    for parameter in parameters:
        if parameter.required and parameter.id not in mapped_parameter_ids:
            diagnostics.append(_diagnostico(
                "missing_ui_parameter", "error",
                f"El parametro obligatorio {parameter.name} no tiene control Flutter.",
                method_id, owner.id, "frontend_contract.fields",
                "Agregue el parametro al formulario de la accion.",
            ))
    refresh = []
    for raw_id in frontend.get("refresh_targets", []):
        target = entity_by_id.get(str(raw_id))
        if target is None:
            diagnostics.append(_diagnostico(
                "unknown_refresh_target", "error", "El objetivo de refresco no existe.",
                method_id, owner.id, "frontend_contract.refresh_targets", "Seleccione una clase real.",
            ))
        else:
            refresh.append(target.module_name)
    return PlanAccionUI(
        operation_id=method_id, owner_entity=owner.name, owner_module=owner.module_name,
        dart_name=java_name, label=str(frontend.get("label") or java_name),
        interaction=str(frontend.get("interaction") or "form"), placement=frontend.get("placement"),
        confirmation_required=bool(frontend.get("confirmation_required", False)),
        success_message=frontend.get("success_message"), refresh_targets=tuple(refresh), fields=tuple(fields),
    )


def _rutas_heredadas(entities):
    routes = set()
    for entity in entities:
        base = f"/api/{camel(entity.name).lower()}s"
        routes.update({("GET", base), ("POST", base), ("GET", f"{base}/{{id}}"), ("PUT", f"{base}/{{id}}"), ("DELETE", f"{base}/{{id}}")})
    return routes


def _diagnostico(code, severity, message, method_id, class_id, path, suggestion=None):
    return DiagnosticoPlan(
        code=code, severity=severity, message=message, suggestion=suggestion,
        method_id=method_id or None, class_id=class_id or None, path=path,
    )
