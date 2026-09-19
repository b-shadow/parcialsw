from typing import Literal

from pydantic import BaseModel, Field


class UmlGenerationRequest(BaseModel):
    prompt: str = Field(min_length=1)
    language: str = "es"
    source_type: Literal["text", "voice", "image"] = "text"
    use_rag: bool = True


class UmlAttribute(BaseModel):
    name: str
    data_type: str = "String"
    visibility: str = "private"
    is_required: bool = False


class UmlMethod(BaseModel):
    name: str
    return_type: str = "void"
    visibility: str = "public"


class UmlClass(BaseModel):
    name: str
    stereotype: str | None = None
    attributes: list[UmlAttribute] = Field(default_factory=list)
    methods: list[UmlMethod] = Field(default_factory=list)


class UmlRelationship(BaseModel):
    source: str
    target: str
    relationship_type: str = "association"
    label: str | None = None
    source_cardinality: str | None = None
    target_cardinality: str | None = None


class UmlGenerationResponse(BaseModel):
    classes: list[UmlClass]
    relationships: list[UmlRelationship]
    confidence: float = Field(ge=0, le=1)
    observations: list[str] = Field(default_factory=list)
    knowledge_context: list[str] = Field(default_factory=list)
    engine: str = "local-offline"


class VoiceProcessingRequest(BaseModel):
    transcript: str | None = None
    audio_base64: str | None = None
    language: str = "es"


class ImageProcessingRequest(BaseModel):
    description: str | None = None
    image_base64: str | None = None
    file_name: str | None = None
    language: str = "es"


class UmlValidationRequest(BaseModel):
    classes: list[UmlClass]
    relationships: list[UmlRelationship] = Field(default_factory=list)


class UmlValidationResponse(BaseModel):
    errors: list[str]
    warnings: list[str]
    recommendations: list[str]
    score: float = Field(ge=0, le=1)
    engine: str = "local-offline"


class SoftwarePlanRequest(BaseModel):
    classes: list[UmlClass]
    relationships: list[UmlRelationship] = Field(default_factory=list)
    target: Literal["spring_boot", "flutter"]


class SoftwarePlanResponse(BaseModel):
    target: Literal["spring_boot", "flutter"]
    files: list[str]
    components: list[str]
    recommendations: list[str]
    engine: str = "local-offline"


class UmlModificationRequest(BaseModel):
    instruction: str = Field(min_length=1)
    classes: list[UmlClass]
    relationships: list[UmlRelationship] = Field(default_factory=list)


class UmlModificationResponse(BaseModel):
    classes: list[UmlClass]
    relationships: list[UmlRelationship]
    changes: list[str]
    confidence: float = Field(ge=0, le=1)
    engine: str = "local-offline"


class CodeGenerationRequest(BaseModel):
    classes: list[UmlClass]
    relationships: list[UmlRelationship] = Field(default_factory=list)
    target: Literal["spring_boot", "flutter"]


class CodeGenerationResponse(BaseModel):
    target: Literal["spring_boot", "flutter"]
    architecture: list[str]
    files: list[str]
    recommendations: list[str]
    validation_notes: list[str]
    engine: str = "local-offline"


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=3, ge=1, le=10)


class KnowledgeItemResponse(BaseModel):
    topic: str
    content: str
    tags: list[str]


class DatasetSummaryResponse(BaseModel):
    records: int
    intents: list[str]
    targets: list[str]
    offline: bool = True


class TrainingPlanResponse(BaseModel):
    base_models: list[str]
    selected_primary_model: str
    selected_small_model: str
    runtime: str
    techniques: list[str]
    dataset_records: int
    stages: list[str]
    metrics: list[str]
    offline_policy: str


class EvaluationResponse(BaseModel):
    dataset_size: int
    class_precision: float
    relationship_precision: float
    average_score: float
    offline: bool = True


class ModelProfile(BaseModel):
    selected_model: str
    runtime: str
    offline: bool
    memory_profile: str
    license_policy: str
    supported_tasks: list[str]
