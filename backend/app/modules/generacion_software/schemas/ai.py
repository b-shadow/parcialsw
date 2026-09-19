from typing import Literal

from pydantic import BaseModel, Field


class AiUmlAttribute(BaseModel):
    name: str
    data_type: str = "String"
    visibility: str = "private"
    is_required: bool = False


class AiUmlMethod(BaseModel):
    name: str
    return_type: str = "void"
    visibility: str = "public"


class AiUmlClass(BaseModel):
    name: str
    stereotype: str | None = None
    attributes: list[AiUmlAttribute] = Field(default_factory=list)
    methods: list[AiUmlMethod] = Field(default_factory=list)


class AiUmlRelationship(BaseModel):
    source: str
    target: str
    relationship_type: str = "association"
    label: str | None = None
    source_cardinality: str | None = None
    target_cardinality: str | None = None


class AiTextRequest(BaseModel):
    prompt: str = Field(min_length=1)
    language: str = "es"
    source_type: Literal["text", "voice", "image"] = "text"
    use_rag: bool = True


class AiVoiceRequest(BaseModel):
    transcript: str | None = None
    audio_base64: str | None = None
    language: str = "es"


class AiImageRequest(BaseModel):
    description: str | None = None
    image_base64: str | None = None
    file_name: str | None = None
    language: str = "es"


class AiUmlResponse(BaseModel):
    classes: list[AiUmlClass]
    relationships: list[AiUmlRelationship]
    confidence: float
    observations: list[str]
    knowledge_context: list[str] = Field(default_factory=list)
    engine: str


class AiValidationRequest(BaseModel):
    classes: list[AiUmlClass]
    relationships: list[AiUmlRelationship] = Field(default_factory=list)


class AiValidationResponse(BaseModel):
    errors: list[str]
    warnings: list[str]
    recommendations: list[str]
    score: float
    engine: str


class AiSoftwarePlanRequest(BaseModel):
    classes: list[AiUmlClass]
    relationships: list[AiUmlRelationship] = Field(default_factory=list)
    target: Literal["spring_boot", "flutter"]


class AiSoftwarePlanResponse(BaseModel):
    target: Literal["spring_boot", "flutter"]
    files: list[str]
    components: list[str]
    recommendations: list[str]
    engine: str


class AiModificationRequest(BaseModel):
    instruction: str = Field(min_length=1)
    classes: list[AiUmlClass]
    relationships: list[AiUmlRelationship] = Field(default_factory=list)


class AiModificationResponse(BaseModel):
    classes: list[AiUmlClass]
    relationships: list[AiUmlRelationship]
    changes: list[str]
    confidence: float
    engine: str


class AiCodeGenerationRequest(BaseModel):
    classes: list[AiUmlClass]
    relationships: list[AiUmlRelationship] = Field(default_factory=list)
    target: Literal["spring_boot", "flutter"]


class AiCodeGenerationResponse(BaseModel):
    target: Literal["spring_boot", "flutter"]
    architecture: list[str]
    files: list[str]
    recommendations: list[str]
    validation_notes: list[str]
    engine: str


class AiKnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=3, ge=1, le=10)


class AiKnowledgeItemResponse(BaseModel):
    topic: str
    content: str
    tags: list[str]


class AiDatasetSummaryResponse(BaseModel):
    records: int
    intents: list[str]
    targets: list[str]
    offline: bool = True


class AiTrainingPlanResponse(BaseModel):
    base_models: list[str]
    selected_primary_model: str
    selected_small_model: str
    runtime: str
    techniques: list[str]
    dataset_records: int
    stages: list[str]
    metrics: list[str]
    offline_policy: str


class AiEvaluationResponse(BaseModel):
    dataset_size: int
    class_precision: float
    relationship_precision: float
    average_score: float
    offline: bool = True


class AiModelProfileResponse(BaseModel):
    selected_model: str
    runtime: str
    offline: bool
    memory_profile: str
    license_policy: str
    supported_tasks: list[str]
