__all__ = ["LocalAIService"]


def __getattr__(name: str):
    if name == "LocalAIService":
        from ai_engine.services.local_ai_service import LocalAIService

        return LocalAIService
    raise AttributeError(name)
