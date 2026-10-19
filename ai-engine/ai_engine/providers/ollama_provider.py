from __future__ import annotations

import json
import time
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel

from ai_engine.orchestration.response_validator import StructuredOutputValidator
from ai_engine.providers.base import (
    ProviderHealth,
    ProviderRequest,
    ProviderResponse,
    T,
)
from ai_engine.providers.errors import (
    InvalidStructuredOutputError,
    ModelNotInstalledError,
    ProviderProtocolError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)

ALLOWED_OLLAMA_HOSTS = {"127.0.0.1", "localhost", "::1"}


def validate_ollama_base_url(value: str) -> str:
    parsed = urlparse(value.rstrip("/"))
    if (
        parsed.scheme != "http"
        or parsed.hostname not in ALLOWED_OLLAMA_HOSTS
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise ValueError("OLLAMA_BASE_URL debe ser una URL HTTP local sin credenciales ni ruta")
    return value.rstrip("/")


class OllamaProvider:
    def __init__(
        self,
        *,
        base_url: str = "http://127.0.0.1:11434",
        connect_timeout: float = 3,
        read_timeout: float = 120,
        keep_alive: str = "10m",
        max_retries: int = 2,
        health_cache_seconds: float = 5,
        max_response_bytes: int = 2_000_000,
        validator: StructuredOutputValidator | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = validate_ollama_base_url(base_url)
        self.keep_alive = keep_alive
        self.max_retries = max(0, min(max_retries, 2))
        self.health_cache_seconds = max(0, health_cache_seconds)
        self.max_response_bytes = max_response_bytes
        self.validator = validator or StructuredOutputValidator()
        self._health_cache: tuple[float, ProviderHealth] | None = None
        self._owns_client = client is None
        self.client = client or httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(read_timeout, connect=connect_timeout),
            follow_redirects=False,
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self.client.aclose()

    async def health(self, requested_model: str | None = None) -> ProviderHealth:
        now = time.monotonic()
        if self._health_cache and now - self._health_cache[0] <= self.health_cache_seconds:
            cached = self._health_cache[1].model_copy(deep=True)
            cached.cached = True
            cached.requested_model = requested_model
            cached.requested_model_available = (
                self._model_available(requested_model, cached.installed_models)
                if requested_model
                else None
            )
            return cached
        started = time.perf_counter()
        try:
            response = await self.client.get("/api/tags")
            self._reject_redirect(response)
            response.raise_for_status()
            payload = response.json()
            models = sorted(
                {
                    str(item.get("name") or item.get("model"))
                    for item in payload.get("models", [])
                    if item.get("name") or item.get("model")
                }
            )
            result = ProviderHealth(
                provider="ollama",
                available=True,
                installed_models=models,
                requested_model=requested_model,
                requested_model_available=(
                    self._model_available(requested_model, models) if requested_model else None
                ),
                latency_ms=int((time.perf_counter() - started) * 1000),
            )
        except httpx.TimeoutException:
            result = self._unavailable_health(started, "provider_timeout", "Ollama no respondio a tiempo")
        except (httpx.HTTPError, ProviderProtocolError, ValueError, json.JSONDecodeError):
            result = self._unavailable_health(started, "provider_unavailable", "Ollama no esta disponible")
        self._health_cache = (now, result.model_copy(deep=True))
        return result

    async def complete_structured(
        self,
        request: ProviderRequest,
        response_model: type[T],
    ) -> ProviderResponse[T]:
        health = await self.health(request.model)
        if not health.available:
            if health.error_code == "provider_timeout":
                raise ProviderTimeoutError(health.error_message)
            raise ProviderUnavailableError(health.error_message)
        if not health.requested_model_available:
            raise ModelNotInstalledError(f"El modelo '{request.model}' no esta instalado")

        started = time.perf_counter()
        messages = [message.model_dump() for message in request.messages]
        last_error = "Salida estructurada invalida"
        for attempt in range(self.max_retries + 1):
            if attempt:
                messages.append(
                    {
                        "role": "system",
                        "content": (
                            "La respuesta anterior no cumplio el esquema. Devuelve solo JSON valido. "
                            f"Error resumido: {last_error[:500]}"
                        ),
                    }
                )
            raw = await self._post_chat(request, response_model, messages)
            content = raw.get("message", {}).get("content")
            if not isinstance(content, str) or len(content.encode("utf-8")) > self.max_response_bytes:
                last_error = "Contenido ausente o demasiado grande"
                continue
            try:
                validated = self.validator.validate(content, response_model)
            except InvalidStructuredOutputError as exc:
                last_error = str(exc)
                continue
            return ProviderResponse[T](
                provider="ollama",
                model=str(raw.get("model") or request.model),
                content=validated,
                duration_ms=int((time.perf_counter() - started) * 1000),
                prompt_tokens=self._optional_int(raw.get("prompt_eval_count")),
                completion_tokens=self._optional_int(raw.get("eval_count")),
                finish_reason=str(raw.get("done_reason")) if raw.get("done_reason") else None,
                retries=attempt,
            )
        raise InvalidStructuredOutputError(last_error)

    async def _post_chat(
        self,
        request: ProviderRequest,
        response_model: type[BaseModel],
        messages: list[dict],
    ) -> dict:
        try:
            response = await self.client.post(
                "/api/chat",
                json={
                    "model": request.model,
                    "messages": messages,
                    "stream": False,
                    "format": response_model.model_json_schema(),
                    "options": {
                        "temperature": request.temperature,
                        "num_predict": request.max_output_tokens,
                    },
                    "keep_alive": self.keep_alive,
                    "think": request.think,
                },
            )
            self._reject_redirect(response)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ProviderProtocolError("Respuesta Ollama inesperada")
            return payload
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError("Ollama no respondio a tiempo") from exc
        except httpx.HTTPStatusError as exc:
            raise ProviderUnavailableError(
                f"Ollama respondio HTTP {exc.response.status_code}"
            ) from exc
        except (httpx.RequestError, json.JSONDecodeError) as exc:
            raise ProviderUnavailableError("No se pudo comunicar con Ollama") from exc

    @staticmethod
    def _reject_redirect(response: httpx.Response) -> None:
        if 300 <= response.status_code < 400:
            raise ProviderProtocolError("Ollama intento redirigir la solicitud")

    @staticmethod
    def _model_available(requested: str, models: list[str]) -> bool:
        requested_base = requested.split(":", 1)[0]
        return any(
            item == requested
            or (":" not in requested and item.split(":", 1)[0] == requested_base)
            for item in models
        )

    @staticmethod
    def _optional_int(value: object) -> int | None:
        return value if isinstance(value, int) else None

    @staticmethod
    def _unavailable_health(started: float, code: str, message: str) -> ProviderHealth:
        return ProviderHealth(
            provider="ollama",
            available=False,
            latency_ms=int((time.perf_counter() - started) * 1000),
            error_code=code,
            error_message=message,
        )
