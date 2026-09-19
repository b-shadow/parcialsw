from fastapi import HTTPException, status

from app.modules.generacion_software.models import UmlTransformation


def ensure_transformation_exists(
    transformation: UmlTransformation | None,
) -> UmlTransformation:
    if transformation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transformacion no encontrada",
        )
    return transformation

