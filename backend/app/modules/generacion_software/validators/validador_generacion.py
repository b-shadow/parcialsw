from fastapi import HTTPException, status

from app.modules.generacion_software.models import TransformacionUML


def asegurar_transformacion_existente(
    transformation: TransformacionUML | None,
) -> TransformacionUML:
    if transformation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transformacion no encontrada",
        )
    return transformation

