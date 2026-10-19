from app.modules.generacion_software.coordinated_generator.contracts import (
    GenerationPlan,
    PlanDiagnostic,
)


def validate_cross_contract(
    plan: GenerationPlan,
    backend_manifest: dict,
    frontend_manifest: dict,
) -> tuple[PlanDiagnostic, ...]:
    """Compare emitted inventories without reparsing Java or Dart source."""
    diagnostics: list[PlanDiagnostic] = []
    expected = {
        (route.operation_id, route.http_method, route.effective_path)
        for route in plan.routes
    }
    backend = {
        (item["operation_id"], item["http_method"], item["path"])
        for item in backend_manifest.get("functional_routes", [])
    }
    frontend = {
        (item["operation_id"], item["http_method"], item["path"])
        for item in frontend_manifest.get("functional_routes", [])
    }
    for target, actual in (("Spring Boot", backend), ("Flutter", frontend)):
        for operation_id, method, path in sorted(expected - actual):
            diagnostics.append(
                PlanDiagnostic(
                    code="cross_contract_missing_route",
                    severity="error",
                    message=f"{target} no emitio {method} {path}.",
                    method_id=operation_id,
                    path="routes",
                )
            )
        for operation_id, method, path in sorted(actual - expected):
            diagnostics.append(
                PlanDiagnostic(
                    code="cross_contract_unplanned_route",
                    severity="error",
                    message=f"{target} emitio una ruta no planificada: {method} {path}.",
                    method_id=operation_id,
                    path="routes",
                )
            )
    backend_dtos = backend_manifest.get("functional_dtos", {})
    frontend_dtos = frontend_manifest.get("functional_dtos", {})
    for operation in plan.operations:
        if operation.route is None:
            continue
        expected_fields = [item.name for item in operation.parameters if item.location == "body"]
        for target, inventory in (("Spring Boot", backend_dtos), ("Flutter", frontend_dtos)):
            actual_fields = inventory.get(operation.id)
            if actual_fields != expected_fields:
                diagnostics.append(
                    PlanDiagnostic(
                        code="cross_contract_dto_mismatch",
                        severity="error",
                        message=(
                            f"{target} usa {actual_fields or []} y el plan exige "
                            f"{expected_fields}."
                        ),
                        method_id=operation.id,
                        path="dtos",
                    )
                )
    return tuple(diagnostics)
