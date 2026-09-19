from collections import Counter

from ai_engine.services.contracts import UmlClass, UmlRelationship, UmlValidationResponse


def validate_uml_quality(classes: list[UmlClass], relationships: list[UmlRelationship]) -> UmlValidationResponse:
    errors: list[str] = []
    warnings: list[str] = []
    recommendations: list[str] = []

    if not classes:
        errors.append("El modelo no contiene clases.")

    names = [uml_class.name for uml_class in classes]
    duplicates = [name for name, count in Counter(names).items() if count > 1]
    if duplicates:
        warnings.append(f"Clases duplicadas: {', '.join(sorted(duplicates))}.")

    for uml_class in classes:
        if not uml_class.attributes:
            recommendations.append(f"Agregar atributos a {uml_class.name}.")
        if not uml_class.methods:
            recommendations.append(f"Agregar metodos a {uml_class.name}.")

    valid_names = set(names)
    for relationship in relationships:
        if relationship.source not in valid_names:
            errors.append(f"Relacion con origen inexistente: {relationship.source}.")
        if relationship.target not in valid_names:
            errors.append(f"Relacion con destino inexistente: {relationship.target}.")

    score = 1.0
    score -= min(len(errors) * 0.25, 0.75)
    score -= min(len(warnings) * 0.1, 0.2)
    score -= min(len(recommendations) * 0.03, 0.2)
    return UmlValidationResponse(
        errors=errors,
        warnings=warnings,
        recommendations=recommendations,
        score=max(score, 0),
    )
