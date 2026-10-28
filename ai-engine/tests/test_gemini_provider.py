import asyncio
import json
from uuid import uuid4

import httpx
import pytest
from pydantic import BaseModel

from ai_engine.providers.base import ProviderMessage, ProviderRequest
from ai_engine.providers.errors import InvalidStructuredOutputError, ProviderUnavailableError
from ai_engine.providers.gemini_provider import GeminiProvider


class SampleOutput(BaseModel):
    message: str
    count: int


def _request() -> ProviderRequest:
    return ProviderRequest(
        model="gemini-2.5-flash",
        messages=[
            ProviderMessage(role="system", content="Responde en JSON."),
            ProviderMessage(role="user", content="Hola"),
        ],
        correlation_id=uuid4(),
    )


def test_gemini_health_without_api_key() -> None:
    provider = GeminiProvider(api_key=None)
    health = asyncio.run(provider.health())
    assert health.available is False
    assert health.error_code == "missing_api_key"
    assert health.provider == "gemini"
    asyncio.run(provider.aclose())


def test_gemini_valid_json_response_and_headers() -> None:
    recorded_headers: dict[str, str] = {}
    recorded_url: str = ""

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal recorded_headers, recorded_url
        recorded_headers = dict(request.headers)
        recorded_url = str(request.url)

        if "generateContent" in request.url.path:
            return httpx.Response(
                200,
                json={
                    "candidates": [
                        {
                            "content": {
                                "parts": [{"text": json.dumps({"message": "Éxito", "count": 42})}]
                            },
                            "finishReason": "STOP",
                        }
                    ],
                    "usageMetadata": {
                        "promptTokenCount": 15,
                        "candidatesTokenCount": 20,
                    },
                },
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    provider = GeminiProvider(api_key="secret-api-key-123", transport=transport)
    response = asyncio.run(provider.complete_structured(_request(), SampleOutput))
    asyncio.run(provider.aclose())

    assert response.provider == "gemini"
    assert response.content.message == "Éxito"
    assert response.content.count == 42
    assert response.retries == 0
    assert response.prompt_tokens == 15
    assert response.completion_tokens == 20

    # Verification: Key in header, not in URL
    assert recorded_headers.get("x-goog-api-key") == "secret-api-key-123"
    assert "secret-api-key-123" not in recorded_url


def test_gemini_retries_on_invalid_json_then_succeeds() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            # First attempt: invalid JSON
            return httpx.Response(
                200,
                json={
                    "candidates": [
                        {
                            "content": {
                                "parts": [{"text": "not a valid json"}]
                            }
                        }
                    ]
                },
            )
        # Second attempt: valid JSON
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [{"text": json.dumps({"message": "Recuperado", "count": 1})}]
                        }
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    provider = GeminiProvider(api_key="test-key", transport=transport, max_retries=2)
    response = asyncio.run(provider.complete_structured(_request(), SampleOutput))
    asyncio.run(provider.aclose())

    assert response.retries == 1
    assert response.content.message == "Recuperado"


def test_gemini_rate_limit_429_exhausts_retries_without_leaking_key() -> None:
    api_key_secret = "super-secret-key-xyz"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"error": {"message": "Resource has been exhausted"}})

    transport = httpx.MockTransport(handler)
    provider = GeminiProvider(api_key=api_key_secret, transport=transport, max_retries=1)

    with pytest.raises(ProviderUnavailableError) as exc_info:
        asyncio.run(provider.complete_structured(_request(), SampleOutput))
    asyncio.run(provider.aclose())

    err_msg = str(exc_info.value)
    assert "429" in err_msg or "límite" in err_msg.lower()
    assert api_key_secret not in err_msg
