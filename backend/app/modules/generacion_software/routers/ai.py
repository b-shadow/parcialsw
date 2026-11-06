from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config.configuracion import settings
from app.core.database.sesion import obtener_sesion_bd
from app.core.security.dependencias import obtener_usuario_actual
from app.modules.acceso_usuarios.models import Usuario
from app.modules.asistente_proyecto.services.fabrica_proveedores import obtener_url_ollama
from app.modules.asistente_proyecto.services.servicio_asistente import ServicioContratoAsistente
from app.modules.generacion_software.schemas.ai import (
    RespuestaElementoConocimientoIA,
    RespuestaEvaluacionIA,
    RespuestaGeneracionCodigoIA,
    RespuestaModificacionIA,
    RespuestaPerfilModeloIA,
    RespuestaPlanEntrenamientoIA,
    RespuestaPlanSoftwareIA,
    RespuestaResumenDatosIA,
    RespuestaUMLIA,
    RespuestaValidacionIA,
    SolicitudBusquedaConocimientoIA,
    SolicitudGeneracionCodigoIA,
    SolicitudImagenIA,
    SolicitudModificacionIA,
    SolicitudPlanSoftwareIA,
    SolicitudTextoIA,
    SolicitudValidacionIA,
    SolicitudVozIA,
)
from app.modules.generacion_software.services.servicio_ia import ServicioIA

router = APIRouter(prefix="/ai", tags=["ia-local-offline"])


@router.get("/profile", response_model=RespuestaPerfilModeloIA)
def profile(_: Annotated[Usuario, Depends(obtener_usuario_actual)]) -> RespuestaPerfilModeloIA:
    return ServicioIA().profile()


@router.post("/uml/text", response_model=RespuestaUMLIA)
def texto_a_uml(
    payload: SolicitudTextoIA,
    _: Annotated[Usuario, Depends(obtener_usuario_actual)],
) -> RespuestaUMLIA:
    return ServicioIA().texto_a_uml(payload)


@router.post("/generate-uml", response_model=RespuestaUMLIA)
def alias_generar_uml(
    payload: SolicitudTextoIA,
    _: Annotated[Usuario, Depends(obtener_usuario_actual)],
) -> RespuestaUMLIA:
    return ServicioIA().texto_a_uml(payload)


@router.post("/uml/voice", response_model=RespuestaUMLIA)
def voz_a_uml(
    payload: SolicitudVozIA,
    _: Annotated[Usuario, Depends(obtener_usuario_actual)],
) -> RespuestaUMLIA:
    return ServicioIA().voz_a_uml(payload)


@router.post("/uml/image", response_model=RespuestaUMLIA)
def imagen_a_uml(
    payload: SolicitudImagenIA,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> RespuestaUMLIA:
    origen = settings.ollama_default_source
    if payload.project_id is not None:
        configuracion = ServicioContratoAsistente(db).obtener_configuracion(payload.project_id, current_user.id)
        origen = configuracion.settings_json.get("origen_ollama", origen)
    url = obtener_url_ollama(origen)
    return ServicioIA().imagen_a_uml(payload, ollama_base_url=url, vision_enabled=bool(url))


@router.post("/analyze-image", response_model=RespuestaUMLIA)
def alias_analizar_imagen(
    payload: SolicitudImagenIA,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> RespuestaUMLIA:
    return imagen_a_uml(payload, current_user, db)


@router.post("/uml/validate", response_model=RespuestaValidacionIA)
def validar_uml(
    payload: SolicitudValidacionIA,
    _: Annotated[Usuario, Depends(obtener_usuario_actual)],
) -> RespuestaValidacionIA:
    return ServicioIA().validar_uml(payload)


@router.post("/validate-model", response_model=RespuestaValidacionIA)
def alias_validar_modelo(
    payload: SolicitudValidacionIA,
    _: Annotated[Usuario, Depends(obtener_usuario_actual)],
) -> RespuestaValidacionIA:
    return ServicioIA().validar_uml(payload)


@router.post("/software/plan", response_model=RespuestaPlanSoftwareIA)
def plan_software(
    payload: SolicitudPlanSoftwareIA,
    _: Annotated[Usuario, Depends(obtener_usuario_actual)],
) -> RespuestaPlanSoftwareIA:
    return ServicioIA().plan_software(payload)


@router.post("/uml/modify", response_model=RespuestaModificacionIA)
def modificar_uml(
    payload: SolicitudModificacionIA,
    _: Annotated[Usuario, Depends(obtener_usuario_actual)],
) -> RespuestaModificacionIA:
    return ServicioIA().modificar_uml(payload)


@router.post("/generate-code", response_model=RespuestaGeneracionCodigoIA)
def generar_codigo(
    payload: SolicitudGeneracionCodigoIA,
    _: Annotated[Usuario, Depends(obtener_usuario_actual)],
) -> RespuestaGeneracionCodigoIA:
    return ServicioIA().generar_orientacion_codigo(payload)


@router.post("/knowledge/search", response_model=list[RespuestaElementoConocimientoIA])
def buscar_conocimiento(
    payload: SolicitudBusquedaConocimientoIA,
    _: Annotated[Usuario, Depends(obtener_usuario_actual)],
) -> list[RespuestaElementoConocimientoIA]:
    return ServicioIA().buscar_conocimiento(payload)


@router.get("/dataset/summary", response_model=RespuestaResumenDatosIA)
def resumen_datos(_: Annotated[Usuario, Depends(obtener_usuario_actual)]) -> RespuestaResumenDatosIA:
    return ServicioIA().resumen_datos()


@router.get("/training/plan", response_model=RespuestaPlanEntrenamientoIA)
def plan_entrenamiento(_: Annotated[Usuario, Depends(obtener_usuario_actual)]) -> RespuestaPlanEntrenamientoIA:
    return ServicioIA().plan_entrenamiento()


@router.get("/evaluation/offline", response_model=RespuestaEvaluacionIA)
def evaluar_sin_conexion(_: Annotated[Usuario, Depends(obtener_usuario_actual)]) -> RespuestaEvaluacionIA:
    return ServicioIA().evaluar_sin_conexion()
