from typing import Literal

from pydantic import BaseModel, Field


class SolicitudGeneracionUML(BaseModel):
    prompt: str = Field(min_length=1)
    language: str = "es"
    source_type: Literal["text", "voice", "image"] = "text"
    use_rag: bool = True


class AtributoUMLMotor(BaseModel):
    name: str
    data_type: str = "String"
    visibility: str = "private"
    is_required: bool = False


class MetodoUMLMotor(BaseModel):
    name: str
    return_type: str = "void"
    visibility: str = "public"


class ClaseUMLMotor(BaseModel):
    name: str
    stereotype: str | None = None
    attributes: list[AtributoUMLMotor] = Field(default_factory=list)
    methods: list[MetodoUMLMotor] = Field(default_factory=list)


class RelacionUMLMotor(BaseModel):
    source: str
    target: str
    relationship_type: str = "association"
    label: str | None = None
    source_cardinality: str | None = None
    target_cardinality: str | None = None
    metadata_json: dict = Field(default_factory=dict)


class RespuestaGeneracionUML(BaseModel):
    classes: list[ClaseUMLMotor]
    relationships: list[RelacionUMLMotor]
    confidence: float = Field(ge=0, le=1)
    observations: list[str] = Field(default_factory=list)
    knowledge_context: list[str] = Field(default_factory=list)
    engine: str = "local-offline"


class SolicitudProcesamientoVoz(BaseModel):
    transcript: str | None = None
    audio_base64: str | None = None
    language: str = "es"


class SolicitudProcesamientoImagen(BaseModel):
    description: str | None = None
    image_base64: str | None = None
    file_name: str | None = None
    language: str = "es"


class SolicitudValidacionUML(BaseModel):
    classes: list[ClaseUMLMotor]
    relationships: list[RelacionUMLMotor] = Field(default_factory=list)


class RespuestaValidacionUMLMotor(BaseModel):
    errors: list[str]
    warnings: list[str]
    recommendations: list[str]
    score: float = Field(ge=0, le=1)
    engine: str = "local-offline"


class SolicitudPlanSoftware(BaseModel):
    classes: list[ClaseUMLMotor]
    relationships: list[RelacionUMLMotor] = Field(default_factory=list)
    target: Literal["spring_boot", "flutter"]


class RespuestaPlanSoftware(BaseModel):
    target: Literal["spring_boot", "flutter"]
    files: list[str]
    components: list[str]
    recommendations: list[str]
    engine: str = "local-offline"


class SolicitudModificacionUML(BaseModel):
    instruction: str = Field(min_length=1)
    classes: list[ClaseUMLMotor]
    relationships: list[RelacionUMLMotor] = Field(default_factory=list)
    selected_class_name: str | None = None


class RespuestaModificacionUML(BaseModel):
    classes: list[ClaseUMLMotor]
    relationships: list[RelacionUMLMotor]
    changes: list[str]
    confidence: float = Field(ge=0, le=1)
    engine: str = "local-offline"


class SolicitudGeneracionCodigo(BaseModel):
    classes: list[ClaseUMLMotor]
    relationships: list[RelacionUMLMotor] = Field(default_factory=list)
    target: Literal["spring_boot", "flutter"]


class RespuestaGeneracionCodigo(BaseModel):
    target: Literal["spring_boot", "flutter"]
    architecture: list[str]
    files: list[str]
    recommendations: list[str]
    validation_notes: list[str]
    engine: str = "local-offline"


class SolicitudBusquedaConocimiento(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=3, ge=1, le=10)


class RespuestaElementoConocimiento(BaseModel):
    topic: str
    content: str
    tags: list[str]


class RespuestaResumenDatos(BaseModel):
    records: int
    intents: list[str]
    targets: list[str]
    offline: bool = True


class RespuestaPlanEntrenamiento(BaseModel):
    base_models: list[str]
    selected_primary_model: str
    selected_small_model: str
    runtime: str
    techniques: list[str]
    dataset_records: int
    stages: list[str]
    metrics: list[str]
    offline_policy: str


class RespuestaEvaluacion(BaseModel):
    dataset_size: int
    class_precision: float
    relationship_precision: float
    average_score: float
    offline: bool = True


class PerfilModelo(BaseModel):
    selected_model: str
    runtime: str
    offline: bool
    memory_profile: str
    license_policy: str
    supported_tasks: list[str]
