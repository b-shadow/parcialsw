from __future__ import annotations

import json
import time
from typing import Any

import httpx

from ai_engine.orchestration.response_validator import StructuredOutputValidator
from ai_engine.providers.base import (
    ProviderHealth,
    ProviderRequest,
    ProviderResponse,
    T,
)
from ai_engine.providers.errors import (
    InvalidStructuredOutputError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com"


class GeminiProvider:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str = DEFAULT_GEMINI_BASE_URL,
        model: str = DEFAULT_GEMINI_MODEL,
        timeout: float = 60.0,
        max_retries: int = 2,
        transport: httpx.AsyncBaseTransport | None = None,
        validator: StructuredOutputValidator | None = None,
    ) -> None:
        self.api_key = api_key.strip() if api_key else None
        self.base_url = base_url.rstrip("/")
        self.model = model or DEFAULT_GEMINI_MODEL
        self.max_retries = max(0, min(max_retries, 3))
        self.validator = validator or StructuredOutputValidator()
        self._owns_client = True

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["x-goog-api-key"] = self.api_key

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=httpx.Timeout(timeout),
            transport=transport,
            follow_redirects=False,
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self.client.aclose()

    async def health(self, requested_model: str | None = None) -> ProviderHealth:
        started = time.perf_counter()
        target_model = (requested_model or self.model).removeprefix("models/")

        if not self.api_key:
            return ProviderHealth(
                provider="gemini",
                available=False,
                error_code="missing_api_key",
                error_message="Falta GEMINI_API_KEY",
                requested_model=target_model,
                requested_model_available=False,
                latency_ms=0,
            )

        try:
            response = await self.client.get(f"/v1beta/models/{target_model}")
            if response.status_code == 200:
                return ProviderHealth(
                    provider="gemini",
                    available=True,
                    installed_models=[target_model],
                    requested_model=target_model,
                    requested_model_available=True,
                    latency_ms=int((time.perf_counter() - started) * 1000),
                )
            if response.status_code == 404:
                return ProviderHealth(
                    provider="gemini",
                    available=False,
                    error_code="model_not_installed",
                    error_message=f"El modelo '{target_model}' no existe en Gemini",
                    requested_model=target_model,
                    requested_model_available=False,
                    latency_ms=int((time.perf_counter() - started) * 1000),
                )
            return ProviderHealth(
                provider="gemini",
                available=False,
                error_code="provider_unavailable",
                error_message=f"Gemini respondió HTTP {response.status_code}",
                requested_model=target_model,
                requested_model_available=False,
                latency_ms=int((time.perf_counter() - started) * 1000),
            )
        except httpx.TimeoutException:
            return ProviderHealth(
                provider="gemini",
                available=False,
                error_code="provider_timeout",
                error_message="Gemini no respondió a tiempo",
                requested_model=target_model,
                requested_model_available=False,
                latency_ms=int((time.perf_counter() - started) * 1000),
            )
        except httpx.RequestError:
            return ProviderHealth(
                provider="gemini",
                available=False,
                error_code="provider_unavailable",
                error_message="No se pudo comunicar con Google AI Studio",
                requested_model=target_model,
                requested_model_available=False,
                latency_ms=int((time.perf_counter() - started) * 1000),
            )

    async def complete_structured(
        self,
        request: ProviderRequest,
        response_model: type[T],
    ) -> ProviderResponse[T]:
        if not self.api_key:
            raise ProviderUnavailableError("Falta GEMINI_API_KEY")

        started = time.perf_counter()
        target_model = (request.model or self.model).removeprefix("models/")

        system_parts: list[dict[str, str]] = []
        raw_contents: list[dict[str, Any]] = []

        for msg in request.messages:
            if msg.role == "system":
                system_parts.append({"text": msg.content})
            else:
                role = "model" if msg.role == "assistant" else "user"
                # Coalesce consecutive turns with the same role
                if raw_contents and raw_contents[-1]["role"] == role:
                    raw_contents[-1]["parts"].append({"text": msg.content})
                else:
                    raw_contents.append({"role": role, "parts": [{"text": msg.content}]})

        if not raw_contents:
            raw_contents.append({"role": "user", "parts": [{"text": "Genera la respuesta solicitada."}]})

        generation_config: dict[str, Any] = {
            "temperature": request.temperature,
            "maxOutputTokens": request.max_output_tokens,
            "responseMimeType": "application/json",
        }

        last_error = "Salida estructurada inválida"

        for attempt in range(self.max_retries + 1):
            contents_payload = [dict(c) for c in raw_contents]
            if attempt > 0:
                contents_payload.append(
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": (
                                    "La respuesta anterior no cumplió el esquema JSON requerido. "
                                    f"Error: {last_error[:400]}. Responde únicamente con JSON válido."
                                )
                            }
                        ],
                    }
                )

            body: dict[str, Any] = {
                "contents": contents_payload,
                "generationConfig": generation_config,
            }
            if system_parts:
                body["systemInstruction"] = {"parts": system_parts}

            try:
                response = await self.client.post(
                    f"/v1beta/models/{target_model}:generateContent",
                    json=body,
                )
            except httpx.TimeoutException as exc:
                if attempt < self.max_retries:
                    continue
                raise ProviderTimeoutError("Gemini no respondió a tiempo") from exc
            except httpx.RequestError as exc:
                if attempt < self.max_retries:
                    continue
                raise ProviderUnavailableError("Error de conexión con Google AI Studio") from exc

            if response.status_code == 429:
                if attempt < self.max_retries:
                    continue
                raise ProviderUnavailableError("Gemini límite de tasa excedido (HTTP 429)")

            if response.status_code >= 500:
                if attempt < self.max_retries:
                    continue
                raise ProviderUnavailableError(f"Gemini respondió HTTP {response.status_code}")

            if response.status_code != 200:
                raise ProviderUnavailableError(f"Gemini respondió HTTP {response.status_code}")

            try:
                data = response.json()
            except (json.JSONDecodeError, ValueError):
                last_error = "Respuesta no es JSON válido"
                continue

            candidates = data.get("candidates")
            if not candidates or not isinstance(candidates, list):
                last_error = "Sin candidatos en la respuesta de Gemini"
                continue

            candidate = candidates[0]
            parts = candidate.get("content", {}).get("parts", [])
            if not parts:
                last_error = "Candidato sin contenido en Gemini"
                continue

            text_content = parts[0].get("text", "")
            try:
                validated = self.validator.validate(text_content, response_model)
            except InvalidStructuredOutputError as exc:
                last_error = str(exc)
                continue

            usage = data.get("usageMetadata", {})
            prompt_tokens = usage.get("promptTokenCount")
            completion_tokens = usage.get("candidatesTokenCount")
            finish_reason = candidate.get("finishReason")

            return ProviderResponse[T](
                provider="gemini",
                model=target_model,
                content=validated,
                duration_ms=int((time.perf_counter() - started) * 1000),
                prompt_tokens=prompt_tokens if isinstance(prompt_tokens, int) else None,
                completion_tokens=completion_tokens if isinstance(completion_tokens, int) else None,
                finish_reason=str(finish_reason) if finish_reason else None,
                retries=attempt,
            )

        raise InvalidStructuredOutputError(last_error)
