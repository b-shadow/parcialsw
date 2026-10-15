import re
from collections import Counter

from app.modules.modelado_uml.engine.internal_model import UmlDiagramModel

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


def _has_inheritance_cycle(diagram: UmlDiagramModel) -> bool:
    graph: dict[str, set[str]] = {}
    for relationship in diagram.relationships:
        if relationship.relationship_type == "inheritance":
            graph.setdefault(relationship.source_class_id, set()).add(relationship.target_class_id)

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(visit(target) for target in graph.get(node, set())):
            return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in graph)


def validate_internal_model(diagram: UmlDiagramModel) -> tuple[list[str], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    recommendations: list[str] = []

    if not diagram.classes:
        errors.append("El diagrama no contiene clases UML.")

    names = [uml_class.name.strip() for uml_class in diagram.classes]
    if any(not name for name in names):
        errors.append("Existen clases sin nombre.")

    normalized_names = [name.casefold() for name in names]
    duplicate_names = sorted(
        names[index]
        for index, normalized in enumerate(normalized_names)
        if normalized_names.count(normalized) > 1
    )
    if duplicate_names:
        warnings.append(
            f"Clases con nombres duplicados: {', '.join(sorted(set(duplicate_names)))}."
        )

    for uml_class in diagram.classes:
        if uml_class.visibility not in ALLOWED_VISIBILITIES:
            warnings.append(
                f"Visibilidad no reconocida en {uml_class.name}: {uml_class.visibility}."
            )

        attribute_names = [attribute.name.strip().casefold() for attribute in uml_class.attributes]
        duplicated_attributes = sorted(
            name for name, count in Counter(attribute_names).items() if name and count > 1
        )
        if duplicated_attributes:
            warnings.append(
                f"Atributos duplicados en {uml_class.name}: {', '.join(duplicated_attributes)}."
            )
        for attribute in uml_class.attributes:
            if not attribute.name.strip():
                errors.append(f"Existe un atributo sin nombre en {uml_class.name}.")
            if not attribute.data_type.strip():
                errors.append(f"El atributo {attribute.name or '(sin nombre)'} no tiene tipo.")
            if attribute.visibility not in ALLOWED_VISIBILITIES:
                warnings.append(
                    f"Visibilidad no reconocida en {uml_class.name}.{attribute.name}: "
                    f"{attribute.visibility}."
                )
            if not _valid_multiplicity(attribute.multiplicity):
                errors.append(
                    f"Multiplicidad invalida en {uml_class.name}.{attribute.name}: "
                    f"{attribute.multiplicity}."
                )

        method_names = [method.name.strip().casefold() for method in uml_class.methods]
        duplicated_methods = sorted(
            name for name, count in Counter(method_names).items() if name and count > 1
        )
        if duplicated_methods:
            warnings.append(
                f"Metodos duplicados en {uml_class.name}: {', '.join(duplicated_methods)}."
            )
        for method in uml_class.methods:
            if not method.name.strip():
                errors.append(f"Existe un metodo sin nombre en {uml_class.name}.")
            if method.return_type is not None and not method.return_type.strip():
                errors.append(f"El metodo {uml_class.name}.{method.name} tiene retorno vacio.")
            if method.visibility not in ALLOWED_VISIBILITIES:
                warnings.append(
                    f"Visibilidad no reconocida en {uml_class.name}.{method.name}: "
                    f"{method.visibility}."
                )
            parameter_names = [parameter.name.strip().casefold() for parameter in method.parameters]
            if any(count > 1 for count in Counter(parameter_names).values()):
                warnings.append(
                    f"El metodo {uml_class.name}.{method.name} tiene parametros duplicados."
                )
            for parameter in method.parameters:
                if not parameter.name.strip() or not parameter.data_type.strip():
                    errors.append(
                        f"El metodo {uml_class.name}.{method.name} tiene un parametro incompleto."
                    )

    class_ids = {uml_class.id or uml_class.name for uml_class in diagram.classes}
    class_ids.update(names)
    relationship_keys: list[tuple[str, str, str]] = []
    for relationship in diagram.relationships:
        if not relationship.source_class_id or not relationship.target_class_id:
            errors.append("Existen relaciones incompletas.")
        if (
            relationship.source_class_id not in class_ids
            and relationship.source_class_id not in names
        ):
            errors.append(f"Relacion con origen inexistente: {relationship.source_class_id}.")
        if (
            relationship.target_class_id not in class_ids
            and relationship.target_class_id not in names
        ):
            errors.append(f"Relacion con destino inexistente: {relationship.target_class_id}.")
        if relationship.source_class_id == relationship.target_class_id:
            warnings.append("Existe una relacion reflexiva; revisar si es intencional.")
        if relationship.relationship_type not in ALLOWED_RELATIONSHIP_TYPES:
            errors.append(f"Tipo de relacion no soportado: {relationship.relationship_type}.")
        for side, cardinality in (
            ("origen", relationship.source_cardinality),
            ("destino", relationship.target_cardinality),
        ):
            if not _valid_multiplicity(cardinality):
                errors.append(
                    f"Multiplicidad invalida en {side} de la relacion "
                    f"{relationship.source_class_id} - {relationship.target_class_id}: {cardinality}."
                )
        relationship_keys.append(
            (
                relationship.source_class_id,
                relationship.target_class_id,
                relationship.relationship_type,
            )
        )

        association_class_id = relationship.metadata_json.get("association_class_id")
        if association_class_id is not None:
            association_class_id = str(association_class_id)
            if association_class_id not in class_ids:
                errors.append(f"Clase asociativa inexistente: {association_class_id}.")
            if association_class_id in {
                relationship.source_class_id,
                relationship.target_class_id,
            }:
                errors.append(
                    "La clase asociativa debe ser distinta de los extremos de la relacion."
                )

    duplicated_relationships = [
        key for key, count in Counter(relationship_keys).items() if count > 1
    ]
    if duplicated_relationships:
        warnings.append("Existen relaciones duplicadas entre las mismas clases.")

    if _has_inheritance_cycle(diagram):
        errors.append("La jerarquia de herencia contiene un ciclo.")

    for uml_class in diagram.classes:
        if not uml_class.attributes:
            recommendations.append(f"Agregar atributos a {uml_class.name}.")

    if len(diagram.classes) > 1 and not diagram.relationships:
        recommendations.append("Agregar relaciones para expresar colaboracion entre clases.")

    return errors, warnings, recommendations
