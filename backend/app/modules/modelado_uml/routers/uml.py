import logging
import re
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database.sesion import obtener_sesion_bd
from app.core.security.dependencias import obtener_usuario_actual
from app.modules.acceso_usuarios.models import Usuario
from app.modules.asistente_proyecto.schemas import RespuestaAccionIA
from app.modules.asistente_proyecto.services.publicador_eventos import PublicadorEventosIAProyecto
from app.modules.modelado_uml.models import ClaseUML, DiagramaUML, RelacionUML
from app.modules.modelado_uml.schemas.especificacion_metodo import (
    CreacionEspecificacionMetodoUML,
    EnvolturaEspecificacionMetodo,
    ParcheEspecificacionMetodoUML,
    RespuestaEspecificacionMetodoUML,
    RespuestaPropuestaEspecificacionMetodo,
    RespuestaValidacionEspecificacionMetodo,
    SolicitudRefinamientoEspecificacionMetodo,
)
from app.modules.modelado_uml.schemas.uml import (
    RespuestaAtributoUML,
    RespuestaClaseUML,
    RespuestaDiagrama,
    RespuestaElementoVisualUML,
    RespuestaExportacionXMI,
    RespuestaMetodoUML,
    RespuestaModeloDiagrama,
    RespuestaParametroUML,
    RespuestaRelacionUML,
    RespuestaValidacionUML,
    SolicitudActualizacionAtributoUML,
    SolicitudActualizacionClaseUML,
    SolicitudActualizacionMetodoUML,
    SolicitudActualizacionParametroUML,
    SolicitudActualizacionRelacionUML,
    SolicitudCreacionAtributoUML,
    SolicitudCreacionClaseUML,
    SolicitudCreacionDiagrama,
    SolicitudCreacionMetodoUML,
    SolicitudCreacionParametroUML,
    SolicitudCreacionRelacionUML,
    SolicitudImportacionXMI,
    SolicitudMoverElemento,
    SolicitudTextoAUML,
)
from app.modules.modelado_uml.services.servicio_especificacion_metodo import (
    ServicioEspecificacionMetodo,
)
from app.modules.modelado_uml.services.servicio_uml import ServicioUML

router = APIRouter(prefix="/uml", tags=["modelado-uml"])
logger = logging.getLogger(__name__)


@router.get(
    "/methods/{method_id}/specification",
    response_model=EnvolturaEspecificacionMetodo,
)
def obtener_especificacion_metodo(
    method_id: UUID,
    response: Response,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> object:
    result = ServicioEspecificacionMetodo(db).get(method_id, current_user.id)
    if result.specification:
        response.headers["ETag"] = f'"revision-{result.specification.revision}"'
    return result


@router.put(
    "/methods/{method_id}/specification",
    response_model=RespuestaEspecificacionMetodoUML,
)
async def put_method_specification(
    method_id: UUID,
    payload: CreacionEspecificacionMetodoUML,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
    response: Response,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    if_none_match: Annotated[str | None, Header(alias="If-None-Match")] = None,
) -> object:
    service = ServicioEspecificacionMetodo(db)
    expected = _parse_revision(if_match) if if_match else None
    if if_none_match != "*" and expected is None:
        raise HTTPException(status_code=428, detail="Use If-Match o If-None-Match")
    item = service.put(
        method_id,
        payload,
        current_user.id,
        expected_revision=expected,
        create_only=if_none_match == "*",
    )
    context = service.contexto_evento(method_id, current_user.id)
    event_type = "METHOD_SPECIFICATION_CREATED" if item.revision == 1 else "METHOD_SPECIFICATION_UPDATED"
    await _publish_method_event(context, current_user, event_type, item.revision, list(payload.model_fields_set))
    response.headers["ETag"] = f'"revision-{item.revision}"'
    return item


@router.patch(
    "/methods/{method_id}/specification",
    response_model=RespuestaEspecificacionMetodoUML,
)
async def patch_method_specification(
    method_id: UUID,
    payload: ParcheEspecificacionMetodoUML,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
    response: Response,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> object:
    if if_match is None:
        raise HTTPException(status_code=428, detail="Use If-Match con la revision observada")
    service = ServicioEspecificacionMetodo(db)
    item = service.patch(
        method_id, payload, current_user.id, expected_revision=_parse_revision(if_match)
    )
    context = service.contexto_evento(method_id, current_user.id)
    await _publish_method_event(
        context,
        current_user,
        "METHOD_SPECIFICATION_UPDATED",
        item.revision,
        list(payload.model_fields_set),
    )
    response.headers["ETag"] = f'"revision-{item.revision}"'
    return item


@router.delete("/methods/{method_id}/specification", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_especificacion_metodo(
    method_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> None:
    if if_match is None:
        raise HTTPException(status_code=428, detail="Use If-Match con la revision observada")
    service = ServicioEspecificacionMetodo(db)
    context = service.delete(
        method_id, current_user.id, expected_revision=_parse_revision(if_match)
    )
    await _publish_method_event(
        context, current_user, "METHOD_SPECIFICATION_DELETED", 0, ["specification"]
    )


@router.post(
    "/methods/{method_id}/specification/validate",
    response_model=RespuestaValidacionEspecificacionMetodo,
)
def validar_especificacion_metodo(
    method_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
    strict: bool = Query(default=False),
) -> object:
    return ServicioEspecificacionMetodo(db).validate(
        method_id, current_user.id, strict=strict
    )


@router.post(
    "/methods/{method_id}/specification/refine",
    response_model=RespuestaPropuestaEspecificacionMetodo,
)
async def refine_method_specification(
    method_id: UUID,
    payload: SolicitudRefinamientoEspecificacionMetodo,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> object:
    proposal, action, context = ServicioEspecificacionMetodo(db).refine(
        method_id, payload, current_user.id
    )
    try:
        publisher = PublicadorEventosIAProyecto()
        await publisher.publicar_persistido(
            project_id=context.diagram.project_id,
            actor_user_id=current_user.id,
            event_type="METHOD_SPECIFICATION_REFINED",
            payload={
                "diagram_id": str(context.diagram.id),
                "class_id": str(context.uml_class.id),
                "method_id": str(method_id),
                "revision": payload.base_revision,
                "changed_fields": proposal.changed_fields,
            },
            correlation_id=uuid4(),
            diagram_id=context.diagram.id,
        )
        await publisher.publicar_persistido(
            project_id=context.diagram.project_id,
            actor_user_id=current_user.id,
            event_type="AI_ACTION_PROPOSED",
            payload=RespuestaAccionIA.model_validate(action).model_dump(mode="json"),
            correlation_id=uuid4(),
            diagram_id=context.diagram.id,
        )
    except Exception:
        logger.exception("No se pudo publicar el refinamiento de metodo ya confirmado")
    return proposal


def _parse_revision(value: str) -> int:
    match = re.fullmatch(r'(?:W/)?"revision-(\d+)"', value.strip())
    if match is None:
        raise HTTPException(status_code=400, detail="ETag de revision invalido")
    return int(match.group(1))


async def _publish_method_event(context, user, event_type, revision, changed_fields):
    try:
        await PublicadorEventosIAProyecto().publicar_persistido(
            project_id=context.diagram.project_id,
            actor_user_id=user.id,
            event_type=event_type,
            payload={
                "diagram_id": str(context.diagram.id),
                "class_id": str(context.uml_class.id),
                "method_id": str(context.method.id),
                "revision": revision,
                "changed_fields": changed_fields,
            },
            correlation_id=uuid4(),
            diagram_id=context.diagram.id,
        )
    except Exception:
        logger.exception("No se pudo publicar el evento de especificacion ya confirmada")


@router.post("/diagrams", response_model=RespuestaDiagrama, status_code=status.HTTP_201_CREATED)
def crear_diagrama(
    payload: SolicitudCreacionDiagrama,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> DiagramaUML:
    return ServicioUML(db).crear_diagrama(payload, current_user.id)


@router.get("/projects/{project_id}/diagrams", response_model=list[RespuestaDiagrama])
def listar_diagramas(
    project_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> list[DiagramaUML]:
    return ServicioUML(db).listar_diagramas(project_id, current_user.id)


@router.delete("/diagrams/{diagram_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_diagrama(
    diagram_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> None:
    ServicioUML(db).eliminar_diagrama(diagram_id, current_user.id)


@router.post(
    "/diagrams/{diagram_id}/classes",
    response_model=RespuestaClaseUML,
    status_code=status.HTTP_201_CREATED,
)
def crear_clase(
    diagram_id: UUID,
    payload: SolicitudCreacionClaseUML,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> ClaseUML:
    return ServicioUML(db).crear_clase(diagram_id, payload, current_user.id)


@router.get("/diagrams/{diagram_id}/classes", response_model=list[RespuestaClaseUML])
def listar_clases(
    diagram_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> list[ClaseUML]:
    return ServicioUML(db).listar_clases(diagram_id, current_user.id)


@router.get("/diagrams/{diagram_id}/model", response_model=RespuestaModeloDiagrama)
def obtener_modelo_diagrama(
    diagram_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> RespuestaModeloDiagrama:
    return ServicioUML(db).obtener_modelo_diagrama(diagram_id, current_user.id)


@router.patch("/classes/{class_id}", response_model=RespuestaClaseUML)
def actualizar_clase(
    class_id: UUID,
    payload: SolicitudActualizacionClaseUML,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> ClaseUML:
    return ServicioUML(db).actualizar_clase(class_id, payload, current_user.id)


@router.delete("/classes/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_clase(
    class_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> None:
    ServicioUML(db).eliminar_clase(class_id, current_user.id)


@router.post("/classes/{class_id}/attributes", response_model=RespuestaAtributoUML, status_code=status.HTTP_201_CREATED)
def agregar_atributo(
    class_id: UUID,
    payload: SolicitudCreacionAtributoUML,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> RespuestaAtributoUML:
    return ServicioUML(db).agregar_atributo(class_id, payload, current_user.id)


@router.patch("/attributes/{attribute_id}", response_model=RespuestaAtributoUML)
def actualizar_atributo(
    attribute_id: UUID,
    payload: SolicitudActualizacionAtributoUML,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> RespuestaAtributoUML:
    return ServicioUML(db).actualizar_atributo(attribute_id, payload, current_user.id)


@router.delete("/attributes/{attribute_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_atributo(
    attribute_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> None:
    ServicioUML(db).eliminar_atributo(attribute_id, current_user.id)


@router.post("/classes/{class_id}/methods", response_model=RespuestaMetodoUML, status_code=status.HTTP_201_CREATED)
def agregar_metodo(
    class_id: UUID,
    payload: SolicitudCreacionMetodoUML,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> RespuestaMetodoUML:
    return ServicioUML(db).agregar_metodo(class_id, payload, current_user.id)


@router.patch("/methods/{method_id}", response_model=RespuestaMetodoUML)
def actualizar_metodo(
    method_id: UUID,
    payload: SolicitudActualizacionMetodoUML,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> RespuestaMetodoUML:
    return ServicioUML(db).actualizar_metodo(method_id, payload, current_user.id)


@router.delete("/methods/{method_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_metodo(
    method_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> None:
    ServicioUML(db).eliminar_metodo(method_id, current_user.id)


@router.post("/methods/{method_id}/parameters", response_model=RespuestaParametroUML, status_code=status.HTTP_201_CREATED)
def agregar_parametro(
    method_id: UUID,
    payload: SolicitudCreacionParametroUML,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> RespuestaParametroUML:
    return ServicioUML(db).agregar_parametro(method_id, payload, current_user.id)


@router.patch("/parameters/{parameter_id}", response_model=RespuestaParametroUML)
def actualizar_parametro(
    parameter_id: UUID,
    payload: SolicitudActualizacionParametroUML,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> RespuestaParametroUML:
    return ServicioUML(db).actualizar_parametro(parameter_id, payload, current_user.id)


@router.delete("/parameters/{parameter_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_parametro(
    parameter_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> None:
    ServicioUML(db).eliminar_parametro(parameter_id, current_user.id)


@router.post(
    "/diagrams/{diagram_id}/relationships",
    response_model=RespuestaRelacionUML,
    status_code=status.HTTP_201_CREATED,
)
def crear_relacion(
    diagram_id: UUID,
    payload: SolicitudCreacionRelacionUML,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> RelacionUML:
    return ServicioUML(db).crear_relacion(diagram_id, payload, current_user.id)


@router.patch("/relationships/{relationship_id}", response_model=RespuestaRelacionUML)
def actualizar_relacion(
    relationship_id: UUID,
    payload: SolicitudActualizacionRelacionUML,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> RelacionUML:
    return ServicioUML(db).actualizar_relacion(relationship_id, payload, current_user.id)


@router.delete("/relationships/{relationship_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_relacion(
    relationship_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> None:
    ServicioUML(db).eliminar_relacion(relationship_id, current_user.id)


@router.patch("/diagrams/{diagram_id}/visual-elements", response_model=RespuestaElementoVisualUML)
def mover_elemento(
    diagram_id: UUID,
    payload: SolicitudMoverElemento,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> RespuestaElementoVisualUML:
    return ServicioUML(db).mover_elemento(diagram_id, payload, current_user.id)


@router.post("/diagrams/{diagram_id}/validate", response_model=RespuestaValidacionUML)
def validar_diagrama(
    diagram_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> RespuestaValidacionUML:
    return ServicioUML(db).validar_diagrama(diagram_id, current_user.id)


@router.post("/generate", response_model=RespuestaDiagrama, status_code=status.HTTP_201_CREATED)
def generar_desde_instruccion(
    payload: SolicitudTextoAUML,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> DiagramaUML:
    return ServicioUML(db).generar_desde_instruccion(payload, current_user.id)


@router.post("/xmi/import", response_model=RespuestaDiagrama, status_code=status.HTTP_201_CREATED)
def importar_diagrama_xmi(
    payload: SolicitudImportacionXMI,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> DiagramaUML:
    return ServicioUML(db).importar_diagrama_xmi(payload, current_user.id)


@router.post("/diagrams/{diagram_id}/xmi/import", response_model=RespuestaDiagrama)
def importar_xmi_en_diagrama(
    diagram_id: UUID,
    payload: SolicitudImportacionXMI,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> DiagramaUML:
    return ServicioUML(db).importar_diagrama_xmi_en_existente(diagram_id, payload, current_user.id)


@router.get("/diagrams/{diagram_id}/xmi", response_model=RespuestaExportacionXMI)
def exportar_diagrama_xmi(
    diagram_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> RespuestaExportacionXMI:
    return ServicioUML(db).exportar_diagrama_xmi(diagram_id, current_user.id)
