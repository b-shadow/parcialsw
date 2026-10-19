from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

IntentName = Literal[
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

ActionType = Literal[
    "create_class",
    "update_class",
    "delete_class",
    "create_attribute",
    "update_attribute",
    "delete_attribute",
    "create_method",
    "update_method",
    "delete_method",
    "create_relationship",
    "update_relationship",
    "delete_relationship",
    "update_method_specification",
    "save_version",
    "prepare_backend_generation",
    "prepare_flutter_generation",
]


class DetectedIntent(BaseModel):
    name: IntentName
    confidence: float = Field(ge=0, le=1)
    evidence: str = Field(min_length=1, max_length=240)
    order: int = Field(ge=1)


class PlannedAction(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    order: int = Field(ge=1)
    action_type: ActionType
    target_type: str | None = Field(default=None, max_length=80)
    target_id: UUID | None = None
    target_name: str | None = Field(default=None, max_length=160)
    diagram_id: UUID | None = None
    base_diagram_version: int | None = Field(default=None, ge=0)
    payload: dict = Field(default_factory=dict)
    depends_on: list[UUID] = Field(default_factory=list, max_length=50)
    risk_level: Literal["low", "medium", "high"] = "low"
    requires_confirmation: bool = True
    explanation: str = Field(min_length=1, max_length=500)
    confidence: float = Field(default=0.8, ge=0, le=1)


class PlannedRecommendation(BaseModel):
    category: Literal[
        "uml_quality",
        "architecture",
        "method_specification",
        "generation",
        "collaboration",
        "security",
        "usability",
    ]
    severity: Literal["info", "warning", "critical"] = "info"
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=2000)
    references: list[dict] = Field(default_factory=list, max_length=50)


class UnifiedAiResult(BaseModel):
    answer: str = Field(min_length=1, max_length=20000)
    detected_intents: list[DetectedIntent] = Field(default_factory=list, max_length=20)
    actions: list[PlannedAction] = Field(default_factory=list, max_length=100)
    recommendations: list[PlannedRecommendation] = Field(default_factory=list, max_length=100)
    references: list[dict] = Field(default_factory=list, max_length=100)
    requires_user_input: bool = False
    clarification_question: str | None = Field(default=None, max_length=1000)
    warnings: list[str] = Field(default_factory=list, max_length=100)
    provider: str = Field(default="unknown", max_length=40)
    model: str = Field(default="unknown", max_length=160)
    fallback_used: bool = False


class OrchestrationResult(BaseModel):
    result: UnifiedAiResult
    duration_ms: int
    provider_duration_ms: int | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    retries: int = 0
    context_reduced: bool = False
    error_code: str | None = None
