class ErrorProveedorIA(RuntimeError):
    code = "provider_error"


class ErrorProveedorNoDisponible(ErrorProveedorIA):
    code = "provider_unavailable"


class ErrorModeloNoInstalado(ErrorProveedorIA):
    code = "model_not_installed"


class ErrorTiempoEsperaProveedor(ErrorProveedorIA):
    code = "provider_timeout"


class ErrorSalidaEstructuradaInvalida(ErrorProveedorIA):
    code = "invalid_structured_output"


class ErrorProtocoloProveedor(ErrorProveedorIA):
    code = "provider_protocol_error"


class ErrorContextoDemasiadoGrande(ErrorProveedorIA):
    code = "context_too_large"
