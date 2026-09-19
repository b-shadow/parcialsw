from uuid import UUID

from fastapi import HTTPException, status

from app.modules.modelado_uml.models import UmlClass, UmlDiagram


def ensure_diagram_exists(diagram: UmlDiagram | None) -> UmlDiagram:
    if diagram is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagrama no encontrado")
    return diagram


def ensure_class_exists(uml_class: UmlClass | None) -> UmlClass:
    if uml_class is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clase UML no encontrada")
    return uml_class


def ensure_class_belongs_to_diagram(uml_class: UmlClass, diagram_id: UUID) -> None:
    if uml_class.diagram_id != diagram_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La clase no pertenece al diagrama indicado",
        )

