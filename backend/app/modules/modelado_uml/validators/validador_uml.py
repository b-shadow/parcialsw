from uuid import UUID

from fastapi import HTTPException, status

from app.modules.modelado_uml.models import ClaseUML, DiagramaUML


def asegurar_diagrama_existente(diagram: DiagramaUML | None) -> DiagramaUML:
    if diagram is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagrama no encontrado")
    return diagram


def asegurar_clase_existente(uml_class: ClaseUML | None) -> ClaseUML:
    if uml_class is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clase UML no encontrada")
    return uml_class


def asegurar_clase_en_diagrama(uml_class: ClaseUML, diagram_id: UUID) -> None:
    if uml_class.diagram_id != diagram_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La clase no pertenece al diagrama indicado",
        )

