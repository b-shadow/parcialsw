from functools import lru_cache

from ai_engine.providers.ollama_provider import OllamaProvider

from app.core.config.settings import settings


@lru_cache(maxsize=1)
def get_ollama_provider() -> OllamaProvider:
    return OllamaProvider(
        base_url=settings.ollama_base_url,
        connect_timeout=settings.ollama_connect_timeout_seconds,
        read_timeout=settings.ollama_read_timeout_seconds,
        keep_alive=settings.ollama_keep_alive,
        max_retries=settings.ai_max_retries,
    )


async def resolve_ollama_model(provider: OllamaProvider, requested_model: str) -> str:
    """Use the configured model when possible, otherwise choose a local Qwen model."""
    health = await provider.health(requested_model)
    if not health.available or health.requested_model_available:
        return requested_model

    installed = health.installed_models
    preferred = (
        settings.ollama_small_model,
        settings.ollama_default_model,
        settings.ollama_vision_model,
    )
    for candidate in preferred:
        if OllamaProvider._model_available(candidate, installed):
            return next(
                item
                for item in installed
                if item == candidate
                or (
                    ":" not in candidate
                    and item.split(":", 1)[0] == candidate.split(":", 1)[0]
                )
            )

    qwen_models = [item for item in installed if "qwen" in item.casefold()]
    return qwen_models[0] if qwen_models else requested_model
