from fastapi import HTTPException, status

from app.modules.acceso_usuarios.models import Usuario


def asegurar_correo_disponible(existing_user: Usuario | None) -> None:
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo ya esta registrado",
        )


def asegurar_usuario_existente(user: Usuario | None) -> Usuario:
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return user

