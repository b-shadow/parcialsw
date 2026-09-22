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
        default="http://localhost:5173,http://127.0.0.1:5173,https://case-inteligente.vercel.app",
        alias="CORS_ORIGINS",
    )
    allowed_hosts_raw: str = Field(default="*", alias="ALLOWED_HOSTS")
    generated_storage_path: str = "../storage/generated"
    s3_artifacts_bucket: str | None = None
    aws_region: str = "us-east-1"
    log_level: str = "INFO"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]

    @property
    def allowed_hosts(self) -> list[str]:
        return [host.strip() for host in self.allowed_hosts_raw.split(",") if host.strip()]


settings = Settings()
