from app.modules.generacion_software.flutter_generator.uml_analyzer.model_analyzer import (
    FlutterProject,
)


def validate_project(project: FlutterProject) -> list[str]:
    errors: list[str] = []
    if len(project.package_name) < 2:
        errors.append("El paquete Flutter debe tener al menos dos caracteres")
    if not project.entities:
        errors.append("El modelo UML debe contener al menos una clase para generar Flutter")
    for entity in project.entities:
        if not entity.fields:
            errors.append(f"La entidad {entity.name} no contiene campos generables")
        repeated = {field.name for field in entity.fields if [item.name for item in entity.fields].count(field.name) > 1}
        if repeated:
            errors.append(f"La entidad {entity.name} contiene campos duplicados: {', '.join(sorted(repeated))}")
    return errors
