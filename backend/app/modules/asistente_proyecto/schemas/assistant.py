from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

AiIntent = Literal[
    "answer_question",
    "explain_system",
    "explain_uml",
    "recommend",
    "review_uml",
    "validate_uml",
    "modify_uml",
    "generate_uml",
    "specify_method",
    "prepare_generation",
    "summarize_conversation",
    "summarize_project",
    "coordinate_team",
    "unknown",
]

SENSITIVE_KEYS = {
    "api_key",
    "apikey",
    "authorization",
    "aws_secret_access_key",
    "database_url",
    "password",
    "private_key",
    "secret",
    "token",
    "vapid_private_key",
}


def reject_sensitive_keys(value: object, path: str = "settings_json") -> object:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).strip().lower()
            if normalized in SENSITIVE_KEYS or any(part in normalized for part in ("password", "secret", "token", "private_key")):
                raise ValueError(f"{path} no admite el campo sensible '{key}'")
            reject_sensitive_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_sensitive_keys(child, f"{path}[{index}]")
    return value


class AiProjectSettingsUpdate(BaseModel):
    model_config = {"extra": "forbid"}

    enabled: bool = True
    preferred_provider: Literal["ollama", "rule_engine"] = "ollama"
    model_name: str = Field(default="qwen2.5-coder:7b", min_length=1, max_length=120)
    fallback_enabled: bool = True
    require_confirmation: bool = True
    max_context_messages: int = Field(default=40, ge=5, le=200)
    summary_trigger_messages: int = Field(default=30, ge=5, le=200)
    settings_json: dict = Field(default_factory=dict)

    @field_validator("model_name")
    @classmethod
    def normalize_model_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("El modelo es obligatorio")
        return normalized

    @field_validator("settings_json")
    @classmethod
    def validate_settings_json(cls, value: dict) -> dict:
        reject_sensitive_keys(value)
        return value


class AiProjectSettingsResponse(AiProjectSettingsUpdate):
    id: UUID
    project_id: UUID
    created_by_user_id: UUID
    updated_by_user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AiReference(BaseModel):
    type: Literal[
        "project",
        "diagram",
        "uml_class",
        "uml_attribute",
        "uml_method",
        "uml_relationship",
        "project_version",
        "generation",
        "message",
    ]
    id: UUID
    label: str = Field(min_length=1, max_length=200)


class AiConversationResponse(BaseModel):
    id: UUID
    project_id: UUID
    title: str
    created_by_user_id: UUID | None
    status: Literal["active", "archived"]
    summary: str | None
    summary_until_sequence: int
    last_message_sequence: int
    schema_version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AiConversationCreate(BaseModel):
    title: str = Field(default="Nuevo chat", min_length=1, max_length=160)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        return value.strip()


class AiConversationUpdate(AiConversationCreate):
    pass


class AiMessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    project_id: UUID
    author_user_id: UUID | None
    author_display_name: str | None = None
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    sequence_number: int
    client_message_id: UUID | None
    correlation_id: UUID
    status: Literal["pending", "streaming", "completed", "failed", "cancelled"]
    detected_intents: list[AiIntent]
    references_json: list[AiReference]
    metadata_json: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AiMessagePage(BaseModel):
    items: list[AiMessageResponse]
    previous_cursor: int | None = None
    next_cursor: int | None = None
    has_more_before: bool = False
    has_more_after: bool = False
    min_sequence: int | None = None
    max_sequence: int | None = None


class RequestedContext(BaseModel):
    include_diagram: bool = True
    include_recent_messages: bool = True
    include_project_versions: bool = False
    surface: Literal["desktop", "mobile_readonly"] = "desktop"


class AiInteractionRequest(BaseModel):
    client_message_id: UUID
    content: str = Field(min_length=1, max_length=20000)
    conversation_id: UUID | None = None
    diagram_id: UUID | None = None
    base_diagram_version: int | None = Field(default=None, ge=0)
    requested_context: RequestedContext = Field(default_factory=RequestedContext)

    @field_validator("content")
    @classmethod
    def normalize_content(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("El mensaje no puede estar vacio")
        return normalized


class AiInteractionResponse(BaseModel):
    message_id: UUID
    correlation_id: UUID
    status: Literal["pending", "streaming", "completed", "failed", "cancelled"]
    detected_intents: list[AiIntent] = Field(default_factory=list)
    answer: str = ""
    actions: list[dict] = Field(default_factory=list)
    recommendations: list[dict] = Field(default_factory=list)
    conversation_sequence: int
    provider: str = "unknown"
    model: str = "unknown"
    fallback_used: bool = False
    warnings: list[str] = Field(default_factory=list)
    requires_user_input: bool = False
    clarification_question: str | None = None
    duration_ms: int = 0
    context_reduced: bool = False


class AiProviderHealthResponse(BaseModel):
    provider: str
    available: bool
    models: list[str] = Field(default_factory=list)
    selected_model: str
    selected_model_available: bool
    latency_ms: int | None = None
    error_code: str | None = None
    error_message: str | None = None


class AiActionResponse(BaseModel):
    id: UUID
    project_id: UUID
    conversation_id: UUID
    source_message_id: UUID
    requested_by_user_id: UUID
    action_type: str
    target_type: str | None
    target_id: UUID | None
    payload: dict
    risk_level: Literal["low", "medium", "high"]
    requires_confirmation: bool
    status: Literal["proposed", "confirmed", "executing", "applied", "rejected", "failed", "cancelled"]
    confirmed_by_user_id: UUID | None
    confirmed_at: datetime | None
    executed_at: datetime | None
    result_json: dict
    error_message: str | None
    idempotency_key: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AiActionDecisionResponse(BaseModel):
    action: AiActionResponse
    idempotent: bool = False


class AiRecommendationResponse(BaseModel):
    id: UUID
    project_id: UUID
    conversation_id: UUID
    source_message_id: UUID
    category: str
    severity: Literal["info", "warning", "critical"]
    title: str
    description: str
    references_json: list[AiReference]
    status: Literal["open", "accepted", "dismissed", "resolved"]
    resolved_by_user_id: UUID | None
    resolved_at: datetime | None
    resolution_note: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AiRecommendationStatusUpdate(BaseModel):
    status: Literal["accepted", "dismissed", "resolved"]
    resolution_note: str | None = Field(default=None, max_length=1000)


class AiActionQuery(BaseModel):
    status: str | None = None
    limit: int = Field(default=50, ge=1, le=200)


class AiRecommendationQuery(BaseModel):
    status: str | None = None
    severity: str | None = None
    limit: int = Field(default=50, ge=1, le=200)


class AiMessageCreateInternal(BaseModel):
    role: Literal["user", "assistant", "system", "tool"]
    content: str = Field(min_length=1, max_length=20000)
    client_message_id: UUID | None = None
    correlation_id: UUID
    detected_intents: list[AiIntent] = Field(default_factory=list)
    references: list[AiReference] = Field(default_factory=list)
    metadata_json: dict = Field(default_factory=dict)
    status: Literal["pending", "streaming", "completed", "failed", "cancelled"] = "completed"

    @model_validator(mode="after")
    def require_client_id_for_user(self) -> "AiMessageCreateInternal":
        if self.role == "user" and self.client_message_id is None:
            raise ValueError("Los mensajes de usuario requieren client_message_id")
        return self
