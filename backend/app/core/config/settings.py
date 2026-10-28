from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Plataforma CASE Inteligente"
    app_env: str = "development"
    api_prefix: str = "/api/v1"
    database_url: str = (
        "postgresql+psycopg://case_user:case_password@localhost:5433/case_inteligente"
    )
    mongodb_uri: str = "mongodb://case_user:case_password@localhost:27018/?authSource=admin"
    mongodb_database: str = Field(default="case_inteligente_nosql", min_length=1)
    mongodb_enabled: bool = True
    mongodb_required: bool = True
    mongodb_connect_timeout_ms: int = Field(default=3000, ge=100, le=60000)
    mongodb_server_selection_timeout_ms: int = Field(default=3000, ge=100, le=60000)
    mongodb_outbox_batch_size: int = Field(default=50, ge=1, le=500)
    mongodb_outbox_max_attempts: int = Field(default=8, ge=1, le=100)
    ai_messages_mongodb_read_enabled: bool = True
    ai_messages_sql_fallback_enabled: bool = False
    ai_messages_compare_reads: bool = False
    ai_messages_migration_batch_size: int = Field(default=200, ge=10, le=2000)
    ai_messages_migration_required: bool = False
    uml_versions_mongodb_read_enabled: bool = True
    uml_versions_sql_fallback_enabled: bool = False
    uml_versions_compare_reads: bool = False
    uml_versions_migration_batch_size: int = Field(default=200, ge=10, le=2000)
    uml_versions_migration_required: bool = False
    uml_diagrams_mongodb_read_enabled: bool = True
    uml_diagrams_sql_fallback_enabled: bool = False
    uml_diagrams_compare_reads: bool = False
    uml_diagrams_dual_write_enabled: bool = False
    uml_diagrams_migration_batch_size: int = Field(default=100, ge=10, le=1000)
    uml_diagrams_migration_required: bool = False
    nosql_reconciliation_interval_seconds: int = Field(default=300, ge=30, le=86400)
    nosql_reconciliation_required: bool = False
    nosql_reconciliation_max_age_seconds: int = Field(default=900, ge=60, le=86400)
    nosql_alert_pending_outbox: int = Field(default=100, ge=0)
    nosql_alert_dead_outbox: int = Field(default=1, ge=0)
    nosql_alert_max_document_bytes: int = Field(default=12_000_000, ge=1024)
    nosql_alert_max_revision_lag: int = Field(default=0, ge=0)
    nosql_backup_path: str = "../storage/backups"
    phase14_consolidation_required: bool = False
    nosql_consolidated_mode: bool = True
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

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]

    @property
    def allowed_hosts(self) -> list[str]:
        return [host.strip() for host in self.allowed_hosts_raw.split(",") if host.strip()]


settings = Settings()
