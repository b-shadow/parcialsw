class AiProviderError(RuntimeError):
    code = "provider_error"


class ProviderUnavailableError(AiProviderError):
    code = "provider_unavailable"


class ModelNotInstalledError(AiProviderError):
    code = "model_not_installed"


class ProviderTimeoutError(AiProviderError):
    code = "provider_timeout"


class InvalidStructuredOutputError(AiProviderError):
    code = "invalid_structured_output"


class ProviderProtocolError(AiProviderError):
    code = "provider_protocol_error"


class ContextTooLargeError(AiProviderError):
    code = "context_too_large"
