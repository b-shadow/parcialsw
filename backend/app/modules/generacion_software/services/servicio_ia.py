from ai_engine.services import ServicioIALocal
from ai_engine.services.contratos import (
    SolicitudBusquedaConocimiento,
    SolicitudGeneracionCodigo,
    SolicitudGeneracionUML,
    SolicitudModificacionUML,
    SolicitudPlanSoftware,
    SolicitudProcesamientoImagen,
    SolicitudProcesamientoVoz,
    SolicitudValidacionUML,
)

from app.modules.generacion_software.schemas.ai import (
    SolicitudBusquedaConocimientoIA,
    SolicitudGeneracionCodigoIA,
    SolicitudImagenIA,
    SolicitudModificacionIA,
    SolicitudPlanSoftwareIA,
    SolicitudTextoIA,
    SolicitudValidacionIA,
    SolicitudVozIA,
)


class ServicioIA:
    def __init__(self) -> None:
        self.local_ai = ServicioIALocal()

    def profile(self):
        return self.local_ai.profile()

    def texto_a_uml(self, payload: SolicitudTextoIA):
        return self.local_ai.texto_a_uml(SolicitudGeneracionUML(**payload.model_dump()))

    def voz_a_uml(self, payload: SolicitudVozIA):
        return self.local_ai.voz_a_uml(SolicitudProcesamientoVoz(**payload.model_dump()))

    def imagen_a_uml(self, payload: SolicitudImagenIA):
        return self.local_ai.imagen_a_uml(SolicitudProcesamientoImagen(**payload.model_dump()))

    def validar_uml(self, payload: SolicitudValidacionIA):
        return self.local_ai.validar_uml(SolicitudValidacionUML(**payload.model_dump()))

    def plan_software(self, payload: SolicitudPlanSoftwareIA):
        return self.local_ai.plan_software(SolicitudPlanSoftware(**payload.model_dump()))

    def modificar_uml(self, payload: SolicitudModificacionIA):
        return self.local_ai.modificar_uml(SolicitudModificacionUML(**payload.model_dump()))

    def generar_orientacion_codigo(self, payload: SolicitudGeneracionCodigoIA):
        return self.local_ai.generar_orientacion_codigo(SolicitudGeneracionCodigo(**payload.model_dump()))

    def buscar_conocimiento(self, payload: SolicitudBusquedaConocimientoIA):
        return self.local_ai.buscar_conocimiento(SolicitudBusquedaConocimiento(**payload.model_dump()))

    def resumen_datos(self):
        return self.local_ai.resumen_datos()

    def plan_entrenamiento(self):
        return self.local_ai.plan_entrenamiento()

    def evaluar_sin_conexion(self):
        return self.local_ai.evaluar_sin_conexion()
