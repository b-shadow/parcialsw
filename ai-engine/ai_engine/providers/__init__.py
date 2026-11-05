from ai_engine.providers.base import (
    EstadoProveedor,
    MensajeProveedor,
    ProveedorIA,
    RespuestaProveedor,
    SolicitudProveedor,
)
from ai_engine.providers.errores import (
    ErrorContextoDemasiadoGrande,
    ErrorModeloNoInstalado,
    ErrorProtocoloProveedor,
    ErrorProveedorIA,
    ErrorProveedorNoDisponible,
    ErrorSalidaEstructuradaInvalida,
    ErrorTiempoEsperaProveedor,
)

__all__ = [
    "ErrorContextoDemasiadoGrande",
    "ErrorModeloNoInstalado",
    "ErrorProtocoloProveedor",
    "ErrorProveedorIA",
    "ErrorProveedorNoDisponible",
    "ErrorSalidaEstructuradaInvalida",
    "ErrorTiempoEsperaProveedor",
    "EstadoProveedor",
    "MensajeProveedor",
    "ProveedorGemini",
    "ProveedorIA",
    "ProveedorOllama",
    "RespuestaProveedor",
    "SolicitudProveedor",
]


def __getattr__(name: str):
    if name == "ProveedorOllama":
        from ai_engine.providers.proveedor_ollama import ProveedorOllama

        return ProveedorOllama
    if name == "ProveedorGemini":
        from ai_engine.providers.proveedor_gemini import ProveedorGemini

        return ProveedorGemini
    raise AttributeError(name)
