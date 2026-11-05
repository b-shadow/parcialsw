import logging
from functools import lru_cache

from ai_engine.providers.base import ProveedorIA
from ai_engine.providers.proveedor_gemini import ProveedorGemini
from ai_engine.providers.proveedor_ollama import ProveedorOllama

from app.core.config.configuracion import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def obtener_proveedor_ollama() -> ProveedorOllama:
    return ProveedorOllama(
        base_url=settings.ollama_base_url,
        connect_timeout=settings.ollama_connect_timeout_seconds,
        read_timeout=settings.ollama_read_timeout_seconds,
        keep_alive=settings.ollama_keep_alive,
        max_retries=settings.ai_max_retries,
    )


@lru_cache(maxsize=1)
def obtener_proveedor_gemini() -> ProveedorGemini:
    return ProveedorGemini(
        api_key=settings.gemini_api_key,
        base_url=settings.gemini_base_url,
        model=settings.gemini_model or "gemini-2.5-flash",
        max_retries=settings.ai_max_retries,
    )


async def resolver_modelo_ollama(provider: ProveedorOllama, requested_model: str) -> str:
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
        if ProveedorOllama._modelo_disponible(candidate, installed):
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


async def seleccionar_proveedor(
    preferred: str, requested_model: str = ""
) -> tuple[ProveedorIA | None, str]:
    """Select the AI provider and resolve the model name.

    Returns (provider, model_name). If provider is None, caller should use RuleEngine.
    """
    if preferred == "gemini":
        if not settings.gemini_api_key:
            logger.warning("Gemini seleccionado pero GEMINI_API_KEY no está configurada")
            return None, ""
        provider = obtener_proveedor_gemini()
        model = requested_model or settings.gemini_model or "gemini-2.5-flash"
        return provider, model

    if preferred == "ollama":
        provider = obtener_proveedor_ollama()
        model = await resolver_modelo_ollama(
            provider, requested_model or settings.ollama_default_model
        )
        return provider, model

    # 'rule_engine' or default fallback
    return None, requested_model or "deterministic-v2"
