from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database.sesion import obtener_sesion_bd
from app.core.security.jwt import decode_access_token
from app.modules.acceso_usuarios.models import Usuario
from app.modules.acceso_usuarios.repositories.repositorio_usuarios import RepositorioUsuarios

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def obtener_usuario_actual(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> Usuario:
    try:
        user_id = decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales invalidas",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = RepositorioUsuarios(db).obtener_por_id(user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no autorizado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_admin(current_user: Annotated[Usuario, Depends(obtener_usuario_actual)]) -> Usuario:
    if "ADMINISTRADOR" not in current_user.nombres_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol ADMINISTRADOR",
        )
    return current_user
