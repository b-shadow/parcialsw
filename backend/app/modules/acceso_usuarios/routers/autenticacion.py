from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database.sesion import obtener_sesion_bd
from app.core.security.dependencias import obtener_usuario_actual
from app.modules.acceso_usuarios.models import Usuario
from app.modules.acceso_usuarios.schemas.autenticacion import (
    RespuestaToken,
    SolicitudIngreso,
    SolicitudRegistro,
)
from app.modules.acceso_usuarios.schemas.usuario import RespuestaUsuario
from app.modules.acceso_usuarios.services.servicio_autenticacion import ServicioAutenticacion

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RespuestaUsuario, status_code=status.HTTP_201_CREATED)
def registrar(payload: SolicitudRegistro, db: Annotated[Session, Depends(obtener_sesion_bd)]) -> Usuario:
    return ServicioAutenticacion(db).registrar(payload)


@router.post("/login", response_model=RespuestaToken)
def ingresar(payload: SolicitudIngreso, db: Annotated[Session, Depends(obtener_sesion_bd)]) -> RespuestaToken:
    return ServicioAutenticacion(db).ingresar(payload)


@router.get("/me", response_model=RespuestaUsuario)
def me(current_user: Annotated[Usuario, Depends(obtener_usuario_actual)]) -> Usuario:
    return current_user
