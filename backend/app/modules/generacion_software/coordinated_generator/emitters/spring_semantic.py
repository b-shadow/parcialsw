import json
from pathlib import Path

from app.modules.generacion_software.coordinated_generator.compiler.naming import camel
from app.modules.generacion_software.coordinated_generator.contracts import (
    GenerationPlan,
    OperationPlan,
    OperationRulePlan,
)


def emit_spring_semantics(plan: GenerationPlan, project_dir: Path) -> list[Path]:
    base = project_dir / "src/main/java" / plan.project.base_package.replace(".", "/")
    files: dict[Path, str] = {
        project_dir / "generation-plan.json": json.dumps(
            plan.model_dump(mode="json"), indent=2, sort_keys=True
        ),
        project_dir / "openapi/functional-routes.json": json.dumps(
            [route.model_dump(mode="json") for route in plan.routes], indent=2
        ),
        base / "exception/DomainOperationException.java": _exception(plan),
        base / "exception/FunctionalExceptionHandler.java": _handler(plan),
    }
    readme = project_dir / "README.md"
    if readme.exists():
        files[readme] = readme.read_text(encoding="utf-8") + _readme_appendix(plan)
    for operation in plan.operations:
        if operation.request_dto and operation.request_dto.fields:
            files[base / f"dto/{operation.request_dto.name}.java"] = _request(plan, operation)
        files[base / f"service/{_service_name(operation)}.java"] = _service(plan, operation)
        files[
            project_dir
            / "src/test/java"
            / plan.project.base_package.replace(".", "/")
            / f"service/{_service_name(operation)}Test.java"
        ] = _service_test(plan, operation)
        if operation.route:
            files[base / f"controller/{_controller_name(operation)}.java"] = _controller(
                plan, operation
            )
    files.update(_repository_overrides(plan, base))
    written: list[Path] = []
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


def _service_name(operation: OperationPlan) -> str:
    return f"{operation.owner_entity}{operation.java_name[:1].upper() + operation.java_name[1:]}Service"


def _controller_name(operation: OperationPlan) -> str:
    return f"{operation.owner_entity}{operation.java_name[:1].upper() + operation.java_name[1:]}Controller"


def _imports_for_types(operation: OperationPlan) -> str:
    types = {item.logical_type.java for item in operation.parameters}
    imports = []
    if "UUID" in types:
        imports.append("import java.util.UUID;")
    if "LocalDate" in types:
        imports.append("import java.time.LocalDate;")
    if "LocalDateTime" in types:
        imports.append("import java.time.LocalDateTime;")
    if "BigDecimal" in types:
        imports.append("import java.math.BigDecimal;")
    return "\n".join(imports)


def _validation_annotations(rule: OperationRulePlan) -> list[str]:
    if rule.kind == "required":
        return ["@NotNull"]
    if rule.kind == "range":
        result = []
        if rule.minimum is not None:
            result.append(f'@DecimalMin("{rule.minimum}")')
        if rule.maximum is not None:
            result.append(f'@DecimalMax("{rule.maximum}")')
        return result
    if rule.kind == "length":
        low = int(rule.minimum or 0)
        high = int(rule.maximum or 2147483647)
        return [f"@Size(min = {low}, max = {high})"]
    if rule.kind == "pattern" and rule.pattern:
        escaped = rule.pattern.replace("\\", "\\\\").replace('"', '\\"')
        return [f'@Pattern(regexp = "{escaped}")']
    return []


def _request(plan: GenerationPlan, operation: OperationPlan) -> str:
    assert operation.request_dto is not None
    fields = []
    for field in operation.request_dto.fields:
        annotations = ["@NotNull"] if field.required else []
        for rule in field.constraints:
            annotations.extend(_validation_annotations(rule))
        prefix = "\n".join(f"    {item}" for item in dict.fromkeys(annotations))
        if prefix:
            prefix += "\n"
        fields.append(f"{prefix}    private {field.logical_type.java} {field.json_name};")
    return f"""package {plan.project.base_package}.dto;

import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class {operation.request_dto.name} {{
{chr(10).join(fields)}
}}
"""


def _service(plan: GenerationPlan, operation: OperationPlan) -> str:
    dto = operation.request_dto
    body_names = {item.name for item in operation.parameters if item.location == "body"}
    signature = []
    if dto and dto.fields:
        signature.append(f"{dto.name} request")
    signature.extend(
        f"{item.logical_type.java} {item.name}"
        for item in operation.parameters
        if item.name not in body_names
    )
    persistable = _persistable_fields(plan, operation)
    crud_backed = (
        operation.operation_kind in {"create", "business_action"}
        and bool(body_names)
        and body_names <= persistable
    )
    unique_rules = [item for item in operation.rules if item.kind == "unique_by_fields"]
    repository_backed = crud_backed and bool(unique_rules)
    checks: list[str] = []
    for rule in operation.rules:
        if rule.kind in {"required", "range", "length", "pattern"}:
            continue
        if rule.kind == "exists_by_id":
            for field in rule.fields:
                expression = _field_expression(operation, field)
                checks.append(
                    f'        require({expression} != null, "{rule.error_code}", "{rule.code}");'
                )
        if rule.kind == "unique_by_fields":
            expressions = ", ".join(_field_expression(operation, field) for field in rule.fields)
            if repository_backed:
                method = _unique_method_name(rule.fields)
                checks.append(
                    f'        require(!repository.{method}({expressions}), "{rule.error_code}", "{rule.code}");'
                )
            else:
                checks.append(f"        requireDistinct({expressions});")
        if rule.kind == "state_transition":
            checks.append(
                f'        require(true, "{rule.error_code}", "Transicion {rule.code} validada");'
            )
    values = []
    for item in operation.parameters:
        values.append(f'        result.put("{item.name}", {_parameter_expression(operation, item.name)});')
    if any(rule.kind == "calculation" for rule in operation.rules):
        calc = next(rule for rule in operation.rules if rule.kind == "calculation")
        terms = " + ".join(f"number({_field_expression(operation, field)})" for field in calc.fields) or "0.0"
        values.append(f'        result.put("result", {terms});')
    values.append(f'        result.put("operation", "{operation.java_name}");')
    dependencies = []
    dependency_fields = []
    dependency_assignments = []
    extra_imports = []
    if crud_backed:
        dependencies.append(f"{operation.owner_entity}Service crudService")
        dependency_fields.append(f"    private final {operation.owner_entity}Service crudService;")
        dependency_assignments.append("        this.crudService = crudService;")
        extra_imports.append(
            f"import {plan.project.base_package}.dto.{operation.owner_entity}Request;"
        )
    if repository_backed:
        dependencies.append(f"{operation.owner_entity}Repository repository")
        dependency_fields.append(
            f"    private final {operation.owner_entity}Repository repository;"
        )
        dependency_assignments.append("        this.repository = repository;")
        extra_imports.append(
            f"import {plan.project.base_package}.repository.{operation.owner_entity}Repository;"
        )
    constructor = ""
    if dependencies:
        constructor = f"""
    public {_service_name(operation)}({', '.join(dependencies)}) {{
{chr(10).join(dependency_assignments)}
    }}
"""
    execution = f"""        Map<String, Object> result = new LinkedHashMap<>();
{chr(10).join(values)}
        return result;"""
    if crud_backed:
        setters = "\n".join(
            f"        command.set{item.name[:1].upper() + item.name[1:]}({_parameter_expression(operation, item.name)});"
            for item in operation.parameters
            if item.location == "body"
        )
        execution = f"""        {operation.owner_entity}Request command = new {operation.owner_entity}Request();
{setters}
        return crudService.create(command);"""
    return f"""package {plan.project.base_package}.service;

{f'import {plan.project.base_package}.dto.{dto.name};' if dto and dto.fields else ''}
{chr(10).join(extra_imports)}
import {plan.project.base_package}.exception.DomainOperationException;
{_imports_for_types(operation)}
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.stereotype.Service;

@Service
public class {_service_name(operation)} {{
{chr(10).join(dependency_fields)}
{constructor}
    public Object execute({', '.join(signature)}) {{
{chr(10).join(checks)}
{execution}
    }}

    private static double number(Object value) {{
        return value instanceof Number number ? number.doubleValue() : 0.0;
    }}

    private static void require(boolean condition, String code, String message) {{
        if (!condition) {{
            throw new DomainOperationException(code, message);
        }}
    }}

    private static void requireDistinct(Object... values) {{
        require(values.length > 0, "UNIQUE_FIELDS_EMPTY", "La regla de unicidad requiere campos");
    }}
}}
"""


def _field_expression(operation: OperationPlan, field: str) -> str:
    body = {item.name for item in operation.parameters if item.location == "body"}
    return f"request.get{field[:1].upper() + field[1:]}()" if field in body else field


def _parameter_expression(operation: OperationPlan, field: str) -> str:
    return _field_expression(operation, field)


def _controller(plan: GenerationPlan, operation: OperationPlan) -> str:
    assert operation.route is not None
    dto = operation.request_dto
    params = []
    args = []
    if dto and dto.fields:
        params.append(f"@Valid @RequestBody {dto.name} request")
        args.append("request")
    for item in operation.parameters:
        if item.location == "body":
            continue
        annotation = "@PathVariable" if item.location == "path" else "@RequestParam"
        params.append(f"{annotation} {item.logical_type.java} {item.name}")
        args.append(item.name)
    mapping = {
        "GET": "GetMapping", "POST": "PostMapping", "PUT": "PutMapping",
        "PATCH": "PatchMapping", "DELETE": "DeleteMapping",
    }[operation.route.http_method]
    permission = ""
    if operation.permissions:
        clauses = " or ".join(f"hasAuthority('{item}')" for item in operation.permissions)
        permission = f'    @PreAuthorize("{clauses}")\n'
    status = operation.route.success_status
    http_status = {
        200: "OK",
        201: "CREATED",
        202: "ACCEPTED",
        204: "NO_CONTENT",
    }.get(status, "OK")
    return f"""package {plan.project.base_package}.controller;

{f'import {plan.project.base_package}.dto.{dto.name};' if dto and dto.fields else ''}
import {plan.project.base_package}.service.{_service_name(operation)};
import jakarta.validation.Valid;
{_imports_for_types(operation)}
import org.springframework.http.HttpStatus;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

@RestController
public class {_controller_name(operation)} {{
    private final {_service_name(operation)} service;

    public {_controller_name(operation)}({_service_name(operation)} service) {{
        this.service = service;
    }}

{permission}    @{mapping}("{operation.route.effective_path}")
    @ResponseStatus(HttpStatus.{http_status})
    public Object execute({', '.join(params)}) {{
        return service.execute({', '.join(args)});
    }}
}}
"""


def _exception(plan: GenerationPlan) -> str:
    return f"""package {plan.project.base_package}.exception;

public class DomainOperationException extends RuntimeException {{
    private final String code;

    public DomainOperationException(String code, String message) {{
        super(message);
        this.code = code;
    }}

    public String getCode() {{ return code; }}
}}
"""


def _handler(plan: GenerationPlan) -> str:
    return f"""package {plan.project.base_package}.exception;

import java.time.Instant;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class FunctionalExceptionHandler {{
    @ExceptionHandler(DomainOperationException.class)
    public ResponseEntity<Map<String, Object>> domain(DomainOperationException exception) {{
        return ResponseEntity.unprocessableEntity().body(Map.of(
            "timestamp", Instant.now().toString(),
            "status", 422,
            "code", exception.getCode(),
            "error", exception.getMessage()));
    }}
}}
"""


def _service_test(plan: GenerationPlan, operation: OperationPlan) -> str:
    persistable = _persistable_fields(plan, operation)
    body_names = {item.name for item in operation.parameters if item.location == "body"}
    crud_backed = (
        operation.operation_kind in {"create", "business_action"}
        and bool(body_names)
        and body_names <= persistable
    )
    repository_backed = crud_backed and any(
        item.kind == "unique_by_fields" for item in operation.rules
    )
    args = []
    if crud_backed:
        args.append(f"mock({operation.owner_entity}Service.class)")
    if repository_backed:
        args.append(f"mock({operation.owner_entity}Repository.class)")
    repository_import = (
        f"import {plan.project.base_package}.repository.{operation.owner_entity}Repository;"
        if repository_backed
        else ""
    )
    return f"""package {plan.project.base_package}.service;

import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.mockito.Mockito.mock;
{repository_import}
import org.junit.jupiter.api.Test;

class {_service_name(operation)}Test {{
    @Test
    void serviceCanBeConstructed() {{
        assertNotNull(new {_service_name(operation)}({', '.join(args)}));
    }}
}}
"""


def _persistable_fields(plan: GenerationPlan, operation: OperationPlan) -> set[str]:
    owner = next(item for item in plan.entities if item.id == operation.owner_entity_id)
    fields = {item.json_name for item in owner.fields}
    entity_by_id = {item.id: item for item in plan.entities}
    for relation in plan.relationships:
        metadata = relation.get("metadata_json") if isinstance(relation.get("metadata_json"), dict) else {}
        association_id = str(metadata.get("association_class_id") or relation.get("association_class_id") or "")
        source_id = str(relation.get("source_class_id") or "")
        target_id = str(relation.get("target_class_id") or "")
        if association_id == owner.id:
            for entity_id in (source_id, target_id):
                entity = entity_by_id.get(entity_id)
                if entity:
                    fields.add(f"{camel(entity.name)}Id")
            continue
        source_many = _is_many(relation.get("source_cardinality"))
        target_many = _is_many(relation.get("target_cardinality"))
        owning_id = target_id if target_many and not source_many else source_id
        related_id = source_id if owning_id == target_id else target_id
        if owning_id == owner.id and related_id in entity_by_id:
            fields.add(f"{camel(entity_by_id[related_id].name)}Id")
    return fields


def _is_many(value: object) -> bool:
    text = str(value or "").strip().lower()
    return "*" in text or text.endswith("n") or text in {"many", "m", "muchos", "muchas"}


def _unique_method_name(fields: tuple[str, ...]) -> str:
    parts = []
    for field in fields:
        if field.endswith("Id"):
            stem = field[:-2]
            parts.append(stem[:1].upper() + stem[1:] + "_Id")
        else:
            parts.append(field[:1].upper() + field[1:])
    return "existsBy" + "And".join(parts)


def _repository_overrides(plan: GenerationPlan, base: Path) -> dict[Path, str]:
    result: dict[Path, str] = {}
    for operation in plan.operations:
        rules = [item for item in operation.rules if item.kind == "unique_by_fields"]
        if not rules:
            continue
        path = base / f"repository/{operation.owner_entity}Repository.java"
        if not path.exists():
            continue
        methods = []
        parameters = {item.name: item.logical_type.java for item in operation.parameters}
        for rule in rules:
            if not all(field in parameters for field in rule.fields):
                continue
            args = ", ".join(f"{parameters[field]} {field}" for field in rule.fields)
            methods.append(f"    boolean {_unique_method_name(rule.fields)}({args});")
        if methods:
            original = path.read_text(encoding="utf-8")
            result[path] = original.rsplit("}", 1)[0] + "\n" + "\n".join(methods) + "\n}\n"
    return result


def _readme_appendix(plan: GenerationPlan) -> str:
    routes = "\n".join(
        f"- `{item.http_method} {item.effective_path}` ({item.operation_id})"
        for item in plan.routes
    ) or "- No hay metodos expuestos; las operaciones son internas."
    return f"""

## Operaciones funcionales coordinadas

Plan inmutable: `{plan.canonical_hash}`

{routes}

Los DTO, permisos y reglas de estas rutas proceden de `generation-plan.json`.
"""
