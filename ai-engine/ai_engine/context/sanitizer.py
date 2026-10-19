import re

SENSITIVE_PARTS = (
    "authorization",
    "database_url",
    "password",
    "private_key",
    "secret",
    "token",
    "vapid",
)


def sanitize_context_data(value: object) -> object:
    if isinstance(value, dict):
        return {
            str(key): sanitize_context_data(child)
            for key, child in value.items()
            if not any(part in str(key).casefold() for part in SENSITIVE_PARTS)
        }
    if isinstance(value, list):
        return [sanitize_context_data(child) for child in value]
    if isinstance(value, str):
        return sanitize_untrusted_text(value)
    return value


def sanitize_untrusted_text(value: str, max_length: int = 12000) -> str:
    text = value.replace("\x00", " ").strip()[:max_length]
    text = re.sub(r"(?i)bearer\s+[a-z0-9._~-]+", "[REDACTED_TOKEN]", text)
    text = re.sub(
        r"(?i)(password|secret|token|private[_ -]?key)\s*[:=]\s*\S+",
        r"\1=[REDACTED]",
        text,
    )
    return text
