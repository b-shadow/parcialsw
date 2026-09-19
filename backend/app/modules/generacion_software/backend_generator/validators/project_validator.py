from app.modules.generacion_software.backend_generator.analyzer.model_analyzer import (
    SpringBootProject,
)


def validate_project(project: SpringBootProject) -> list[str]:
    errors: list[str] = []
    if not project.entities:
        errors.append("El modelo UML no contiene entidades para generar.")
    names = [entity.name for entity in project.entities]
    if len(names) != len(set(names)):
        errors.append("Existen entidades duplicadas en el modelo generado.")
    for entity in project.entities:
        if not entity.fields:
            errors.append(f"La entidad {entity.name} no contiene campos generables.")
    return errors
