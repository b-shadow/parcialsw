__all__ = [
    "ServicioAplicacionIAProyecto",
    "ServicioContratoAsistente",
    "ServicioEjecucionAccionesIA",
]


def __getattr__(name: str):
    if name == "ServicioEjecucionAccionesIA":
        from app.modules.asistente_proyecto.services.servicio_ejecucion_acciones import (
            ServicioEjecucionAccionesIA,
        )

        return ServicioEjecucionAccionesIA
    if name == "ServicioContratoAsistente":
        from app.modules.asistente_proyecto.services.servicio_asistente import (
            ServicioContratoAsistente,
        )

        return ServicioContratoAsistente
    if name == "ServicioAplicacionIAProyecto":
        from app.modules.asistente_proyecto.services.servicio_aplicacion_ia_proyecto import (
            ServicioAplicacionIAProyecto,
        )

        return ServicioAplicacionIAProyecto
    raise AttributeError(name)
