from ai_engine.providers.base import (
    AiProvider,
    ProviderHealth,
    ProviderMessage,
    ProviderRequest,
    ProviderResponse,
)
from ai_engine.providers.errors import (
    AiProviderError,
    ContextTooLargeError,
    InvalidStructuredOutputError,
    ModelNotInstalledError,
    ProviderProtocolError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)

__all__ = [
    "AiProvider",
    "AiProviderError",
    "ContextTooLargeError",
    "InvalidStructuredOutputError",
    "ModelNotInstalledError",
    "OllamaProvider",
    "ProviderHealth",
    "ProviderMessage",
    "ProviderProtocolError",
    "ProviderRequest",
    "ProviderResponse",
    "ProviderTimeoutError",
    "ProviderUnavailableError",
]


def __getattr__(name: str):
    if name == "OllamaProvider":
        from ai_engine.providers.ollama_provider import OllamaProvider

        return OllamaProvider
    raise AttributeError(name)
