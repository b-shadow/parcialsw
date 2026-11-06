from ai_engine.inference.motor_local import engine
from ai_engine.services.contratos import (
    PerfilModelo,
    RespuestaElementoConocimiento,
    RespuestaEvaluacion,
    RespuestaGeneracionCodigo,
    RespuestaGeneracionUML,
    RespuestaModificacionUML,
    RespuestaPlanEntrenamiento,
    RespuestaPlanSoftware,
    RespuestaResumenDatos,
    RespuestaValidacionUMLMotor,
    SolicitudBusquedaConocimiento,
    SolicitudGeneracionCodigo,
    SolicitudGeneracionUML,
    SolicitudModificacionUML,
    SolicitudPlanSoftware,
    SolicitudProcesamientoImagen,
    SolicitudProcesamientoVoz,
    SolicitudValidacionUML,
)


class ServicioIALocal:
    def profile(self) -> PerfilModelo:
        return engine.profile()

    def texto_a_uml(self, request: SolicitudGeneracionUML) -> RespuestaGeneracionUML:
        return engine.generar_uml(request)

    def voz_a_uml(self, request: SolicitudProcesamientoVoz) -> RespuestaGeneracionUML:
        return engine.generar_uml_desde_voz(request)

    def imagen_a_uml(
        self, request: SolicitudProcesamientoImagen,
        *, ollama_base_url: str | None = None, vision_enabled: bool | None = None,
    ) -> RespuestaGeneracionUML:
        return engine.generar_uml_desde_imagen(
            request, ollama_base_url=ollama_base_url, vision_enabled=vision_enabled
        )

    def validar_uml(self, request: SolicitudValidacionUML) -> RespuestaValidacionUMLMotor:
        return engine.validar_uml(request)

    def plan_software(self, request: SolicitudPlanSoftware) -> RespuestaPlanSoftware:
        return engine.planificar_software(request)

    def modificar_uml(self, request: SolicitudModificacionUML) -> RespuestaModificacionUML:
        return engine.modificar_uml(request)

    def generar_orientacion_codigo(self, request: SolicitudGeneracionCodigo) -> RespuestaGeneracionCodigo:
        return engine.generar_orientacion_codigo(request)

    def buscar_conocimiento(self, request: SolicitudBusquedaConocimiento) -> list[RespuestaElementoConocimiento]:
        return engine.buscar_conocimiento(request)

    def resumen_datos(self) -> RespuestaResumenDatos:
        return engine.resumen_datos()

    def plan_entrenamiento(self) -> RespuestaPlanEntrenamiento:
        return engine.plan_entrenamiento()

    def evaluar_sin_conexion(self) -> RespuestaEvaluacion:
        return engine.evaluar_sin_conexion()
