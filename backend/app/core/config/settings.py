from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Plataforma CASE Inteligente"
    app_env: str = "development"
    api_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://case_user:case_password@localhost:5433/case_inteligente"
    jwt_secret_key: str = "change-me-in-development"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins_raw: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173,https://case-inteligente.vercel.app,https://case-inteligente-v2.vercel.app",
        alias="CORS_ORIGINS",
    )
    allowed_hosts_raw: str = Field(default="*", alias="ALLOWED_HOSTS")
    generated_storage_path: str = "../storage/generated"
    s3_artifacts_bucket: str | None = None
    aws_region: str = "us-east-1"
    log_level: str = "INFO"
    vapid_public_key: str | None = None
    vapid_private_key: str | None = None
    vapid_subject: str = "mailto:admin@example.com"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_default_model: str = "qwen2.5-coder:7b"
    ollama_small_model: str = "qwen2.5-coder:1.5b"
    ollama_vision_model: str = "qwen3-vl:2b-instruct"
    ollama_vision_enabled: bool = True
    ollama_vision_timeout_seconds: float = 900
    ollama_connect_timeout_seconds: float = 3
    ollama_read_timeout_seconds: float = 120
    ollama_keep_alive: str = "10m"
    ai_max_retries: int = 2
    ai_max_input_chars: int = 12000
    ai_max_context_chars: int = 50000
    ai_temperature: float = 0
    ai_rule_fallback_enabled: bool = True
    ai_max_concurrent_requests: int = 2
    ai_messages_per_minute: int = 12
    ai_max_concurrent_per_user_project: int = 1
    project_snapshot_max_bytes: int = 8 * 1024 * 1024
    notification_outbox_batch_size: int = 50

    # Redis y NoSQL
    redis_enabled: bool = False
    redis_url: str = "redis://127.0.0.1:6379/0"
    redis_key_prefix: str = "case"
    redis_change_log_maxlen: int = 10000

    # Bloqueos e IA Proactiva
    element_lock_ttl_seconds: int = 60
    ai_proactive_enabled: bool = True
    ai_proactive_min_changes: int = 5
    ai_proactive_cooldown_seconds: int = 120

    # Gemini opcional
    gemini_api_key: str | None = None
    gemini_model: str = ""
    gemini_base_url: str = "https://generativelanguage.googleapis.com"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]

    @property
    def allowed_hosts(self) -> list[str]:
        return [host.strip() for host in self.allowed_hosts_raw.split(",") if host.strip()]


settings = Settings()
