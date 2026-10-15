import re
from collections import Counter

from ai_engine.services.contracts import UmlClass, UmlRelationship, UmlValidationResponse

ALLOWED_RELATIONSHIP_TYPES = {
    "association",
    "inheritance",
    "implementation",
    "dependency",
    "aggregation",
    "composition",
}
ALLOWED_VISIBILITIES = {"public", "private", "protected", "package"}
MULTIPLICITY_PATTERN = re.compile(r"^(?:\*|\d+|\d+\.\.(?:\d+|\*))$")


def _valid_multiplicity(value: str | None) -> bool:
    if value is None or not value.strip():
        return True
    normalized = value.strip()
    if not MULTIPLICITY_PATTERN.fullmatch(normalized):
        return False
    if ".." not in normalized:
        return True
    lower, upper = normalized.split("..", maxsplit=1)
    return upper == "*" or int(lower) <= int(upper)


def validate_uml_quality(
    classes: list[UmlClass], relationships: list[UmlRelationship]
) -> UmlValidationResponse:
    errors: list[str] = []
    warnings: list[str] = []
    recommendations: list[str] = []

    if not classes:
        errors.append("El modelo no contiene clases.")

    names = [uml_class.name.strip() for uml_class in classes]
    if any(not name for name in names):
        errors.append("Existen clases sin nombre.")
    normalized_names = [name.casefold() for name in names]
    duplicates = sorted(
        names[index]
        for index, normalized in enumerate(normalized_names)
        if normalized_names.count(normalized) > 1
    )
    if duplicates:
        warnings.append(f"Clases duplicadas: {', '.join(sorted(set(duplicates)))}.")

    for uml_class in classes:
        attribute_names = [attribute.name.strip().casefold() for attribute in uml_class.attributes]
        duplicated_attributes = sorted(
            name for name, count in Counter(attribute_names).items() if name and count > 1
        )
        if duplicated_attributes:
            warnings.append(
                f"Atributos duplicados en {uml_class.name}: {', '.join(duplicated_attributes)}."
            )
        for attribute in uml_class.attributes:
            if not attribute.name.strip() or not attribute.data_type.strip():
                errors.append(f"Existe un atributo incompleto en {uml_class.name}.")
            if attribute.visibility not in ALLOWED_VISIBILITIES:
                warnings.append(f"Visibilidad no reconocida en {uml_class.name}.{attribute.name}.")
        method_names = [method.name.strip().casefold() for method in uml_class.methods]
        duplicated_methods = sorted(
            name for name, count in Counter(method_names).items() if name and count > 1
        )
        if duplicated_methods:
            warnings.append(
                f"Metodos duplicados en {uml_class.name}: {', '.join(duplicated_methods)}."
            )
        for method in uml_class.methods:
            if not method.name.strip() or not method.return_type.strip():
                errors.append(f"Existe un metodo incompleto en {uml_class.name}.")
            if method.visibility not in ALLOWED_VISIBILITIES:
                warnings.append(f"Visibilidad no reconocida en {uml_class.name}.{method.name}.")
        if not uml_class.attributes:
            recommendations.append(f"Agregar atributos a {uml_class.name}.")

    valid_names = set(names)
    relationship_keys: list[tuple[str, str, str]] = []
    for relationship in relationships:
        if relationship.source not in valid_names:
            errors.append(f"Relacion con origen inexistente: {relationship.source}.")
        if relationship.target not in valid_names:
            errors.append(f"Relacion con destino inexistente: {relationship.target}.")
        if relationship.relationship_type not in ALLOWED_RELATIONSHIP_TYPES:
            errors.append(f"Tipo de relacion no soportado: {relationship.relationship_type}.")
        if not _valid_multiplicity(relationship.source_cardinality):
            errors.append(
                f"Multiplicidad invalida en origen de {relationship.source} - "
                f"{relationship.target}: {relationship.source_cardinality}."
            )
        if not _valid_multiplicity(relationship.target_cardinality):
            errors.append(
                f"Multiplicidad invalida en destino de {relationship.source} - "
                f"{relationship.target}: {relationship.target_cardinality}."
            )
        association_class_name = relationship.metadata_json.get("association_class_name")
        if association_class_name and association_class_name not in valid_names:
            errors.append(f"Clase asociativa inexistente: {association_class_name}.")
        relationship_keys.append(
            (relationship.source, relationship.target, relationship.relationship_type)
        )

    if any(count > 1 for count in Counter(relationship_keys).values()):
        warnings.append("Existen relaciones duplicadas entre las mismas clases.")

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
