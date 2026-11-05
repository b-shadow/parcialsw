from typing import TypeVar

from pydantic import BaseModel, ValidationError

from ai_engine.providers.errores import ErrorSalidaEstructuradaInvalida

T = TypeVar("T", bound=BaseModel)


class ValidadorSalidaEstructurada:
    """Valida JSON del proveedor sin permitir objetos parcialmente confiables."""

    def validar(self, raw_content: str, response_model: type[T]) -> T:
        try:
            return response_model.model_validate_json(raw_content)
        except ValidationError as exc:
            raise ErrorSalidaEstructuradaInvalida(self.resumen_validacion(exc)) from exc
        except ValueError as exc:
            raise ErrorSalidaEstructuradaInvalida("JSON invalido") from exc

    @staticmethod
    def resumen_validacion(exc: ValidationError) -> str:
        return "; ".join(
            f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
            for error in exc.errors()[:8]
        )
