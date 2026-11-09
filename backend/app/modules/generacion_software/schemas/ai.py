from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class AtributoUMLIA(BaseModel):
    name: str
    data_type: str = "String"
    visibility: str = "private"
    is_required: bool = False


class MetodoUMLIA(BaseModel):
    name: str
    return_type: str = "void"
    visibility: str = "public"


class ClaseUMLIA(BaseModel):
    name: str
    stereotype: str | None = None
    attributes: list[AtributoUMLIA] = Field(default_factory=list)
    methods: list[MetodoUMLIA] = Field(default_factory=list)


class RelacionUMLIA(BaseModel):
    source: str
    target: str
    relationship_type: str = "association"
    label: str | None = None
    source_cardinality: str | None = None
    target_cardinality: str | None = None
    metadata_json: dict = Field(default_factory=dict)


class SolicitudTextoIA(BaseModel):
    prompt: str = Field(min_length=1)
    language: str = "es"
    source_type: Literal["text", "voice", "image"] = "text"
    use_rag: bool = True


class SolicitudVozIA(BaseModel):
    transcript: str | None = None
    audio_base64: str | None = None
    language: str = "es"


class SolicitudImagenIA(BaseModel):
    project_id: UUID | None = None
    description: str | None = None
    image_base64: str | None = None
    file_name: str | None = None
    language: str = "es"


class RespuestaUMLIA(BaseModel):
    classes: list[ClaseUMLIA]
    relationships: list[RelacionUMLIA]
    confidence: float
    observations: list[str]
    knowledge_context: list[str] = Field(default_factory=list)
    engine: str


class SolicitudValidacionIA(BaseModel):
    classes: list[ClaseUMLIA]
    relationships: list[RelacionUMLIA] = Field(default_factory=list)


class RespuestaValidacionIA(BaseModel):
    errors: list[str]
    warnings: list[str]
    recommendations: list[str]
    score: float
    engine: str


class SolicitudPlanSoftwareIA(BaseModel):
    classes: list[ClaseUMLIA]
    relationships: list[RelacionUMLIA] = Field(default_factory=list)
    target: Literal["spring_boot", "flutter"]


class RespuestaPlanSoftwareIA(BaseModel):
    target: Literal["spring_boot", "flutter"]
    files: list[str]
    components: list[str]
    recommendations: list[str]
    engine: str


class SolicitudModificacionIA(BaseModel):
    instruction: str = Field(min_length=1)
    classes: list[ClaseUMLIA]
    relationships: list[RelacionUMLIA] = Field(default_factory=list)
    selected_class_name: str | None = None


class RespuestaModificacionIA(BaseModel):
    classes: list[ClaseUMLIA]
    relationships: list[RelacionUMLIA]
    changes: list[str]
    confidence: float
    engine: str


class SolicitudGeneracionCodigoIA(BaseModel):
    classes: list[ClaseUMLIA]
    relationships: list[RelacionUMLIA] = Field(default_factory=list)
    target: Literal["spring_boot", "flutter"]


class RespuestaGeneracionCodigoIA(BaseModel):
    target: Literal["spring_boot", "flutter"]
    architecture: list[str]
    files: list[str]
    recommendations: list[str]
    validation_notes: list[str]
    engine: str


class SolicitudBusquedaConocimientoIA(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=3, ge=1, le=10)


class RespuestaElementoConocimientoIA(BaseModel):
    topic: str
    content: str
    tags: list[str]


class RespuestaResumenDatosIA(BaseModel):
    records: int
    intents: list[str]
    targets: list[str]
    offline: bool = True


class RespuestaPlanEntrenamientoIA(BaseModel):
    base_models: list[str]
    selected_primary_model: str
    selected_small_model: str
    runtime: str
    techniques: list[str]
    dataset_records: int
    stages: list[str]
    metrics: list[str]
    offline_policy: str


class RespuestaEvaluacionIA(BaseModel):
    dataset_size: int
    class_precision: float
    relationship_precision: float
    average_score: float
    offline: bool = True


class RespuestaPerfilModeloIA(BaseModel):
    selected_model: str
    runtime: str
    offline: bool
    memory_profile: str
    license_policy: str
    supported_tasks: list[str]
