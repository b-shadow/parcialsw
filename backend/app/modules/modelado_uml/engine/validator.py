from collections import Counter

from app.modules.modelado_uml.engine.internal_model import UmlDiagramModel


def validate_internal_model(diagram: UmlDiagramModel) -> tuple[list[str], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    recommendations: list[str] = []

    if not diagram.classes:
        errors.append("El diagrama no contiene clases UML.")

    names = [uml_class.name.strip() for uml_class in diagram.classes]
    if any(not name for name in names):
        errors.append("Existen clases sin nombre.")

    duplicate_names = sorted(name for name, count in Counter(names).items() if count > 1)
    if duplicate_names:
        warnings.append(f"Clases con nombres duplicados: {', '.join(duplicate_names)}.")

    class_ids = {uml_class.id or uml_class.name for uml_class in diagram.classes}
    for relationship in diagram.relationships:
        if not relationship.source_class_id or not relationship.target_class_id:
            errors.append("Existen relaciones incompletas.")
        if relationship.source_class_id not in class_ids and relationship.source_class_id not in names:
            errors.append(f"Relacion con origen inexistente: {relationship.source_class_id}.")
        if relationship.target_class_id not in class_ids and relationship.target_class_id not in names:
            errors.append(f"Relacion con destino inexistente: {relationship.target_class_id}.")
        if relationship.source_class_id == relationship.target_class_id:
            warnings.append("Existe una relacion reflexiva; revisar si es intencional.")

    for uml_class in diagram.classes:
        if not uml_class.attributes:
            recommendations.append(f"Agregar atributos a {uml_class.name}.")
        if not uml_class.methods:
            recommendations.append(f"Agregar metodos a {uml_class.name}.")

    if len(diagram.classes) > 1 and not diagram.relationships:
        recommendations.append("Agregar relaciones para expresar colaboracion entre clases.")

    return errors, warnings, recommendations
