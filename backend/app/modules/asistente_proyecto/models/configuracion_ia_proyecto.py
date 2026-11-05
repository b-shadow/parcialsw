"""Vista de la configuración de IA guardada en projects.settings.ai."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass
class ConfiguracionIAProyecto:
    id: UUID
    project_id: UUID
    created_by_user_id: UUID
    updated_by_user_id: UUID
    created_at: datetime
    updated_at: datetime
    enabled: bool = True
    preferred_provider: str = "ollama"
    model_name: str = "qwen2.5-coder:7b"
    fallback_enabled: bool = True
    require_confirmation: bool = True
    max_context_messages: int = 40
    summary_trigger_messages: int = 30
    settings_json: dict = field(default_factory=dict)
