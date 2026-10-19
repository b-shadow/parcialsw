from typing import TypeVar

from pydantic import BaseModel, ValidationError

from ai_engine.providers.errors import InvalidStructuredOutputError

T = TypeVar("T", bound=BaseModel)


class StructuredOutputValidator:
    """Valida JSON del proveedor sin permitir objetos parcialmente confiables."""

    def validate(self, raw_content: str, response_model: type[T]) -> T:
        try:
            return response_model.model_validate_json(raw_content)
        except ValidationError as exc:
            raise InvalidStructuredOutputError(self.validation_summary(exc)) from exc
        except ValueError as exc:
            raise InvalidStructuredOutputError("JSON invalido") from exc

    @staticmethod
    def validation_summary(exc: ValidationError) -> str:
        return "; ".join(
            f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
            for error in exc.errors()[:8]
        )
