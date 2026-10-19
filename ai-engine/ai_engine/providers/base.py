from __future__ import annotations

from typing import Generic, Literal, Protocol, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)


class ProviderMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1, max_length=60000)


class ProviderRequest(BaseModel):
    model: str = Field(min_length=1, max_length=160)
    messages: list[ProviderMessage] = Field(min_length=1, max_length=100)
    temperature: float = Field(default=0, ge=0, le=2)
    correlation_id: UUID
    max_output_tokens: int = Field(default=4096, ge=128, le=32768)
    think: bool | None = False


class ProviderHealth(BaseModel):
    provider: str
    available: bool
    installed_models: list[str] = Field(default_factory=list)
    requested_model: str | None = None
    requested_model_available: bool | None = None
    latency_ms: int = 0
    error_code: str | None = None
    error_message: str | None = None
    cached: bool = False


class ProviderResponse(BaseModel, Generic[T]):  # noqa: UP046 - compatible con Python 3.11
    provider: str
    model: str
    content: T
    duration_ms: int
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    finish_reason: str | None = None
    retries: int = 0
    fallback_used: bool = False


class AiProvider(Protocol):
    async def health(self, requested_model: str | None = None) -> ProviderHealth: ...

    async def complete_structured(
        self,
        request: ProviderRequest,
        response_model: type[T],
    ) -> ProviderResponse[T]: ...
