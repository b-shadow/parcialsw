from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

VALID_ELEMENT_TYPES = {"class", "interface", "enum", "abstract_class"}
VALID_VISIBILITIES = {"public", "private", "protected", "package"}
VALID_RELATIONSHIP_TYPES = {
    "association",
    "inheritance",
    "aggregation",
    "composition",
    "dependency",
    "realization",
    "implementation",
}
RELATIONSHIP_PATTERN = "^(association|inheritance|aggregation|composition|dependency|realization|implementation)$"


class SolicitudCreacionDiagrama(BaseModel):
    project_id: UUID
    name: str = Field(min_length=2, max_length=160)
    description: str | None = None
    metadata_json: dict = Field(default_factory=dict)


class RespuestaDiagrama(BaseModel):
    id: UUID
    project_id: UUID
    created_by_user_id: UUID
    name: str
    diagram_type: str
    status: str
    current_version: int
    description: str | None
    metadata_json: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class SolicitudCreacionClaseUML(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    visibility: str = "public"
    element_type: str = "class"
    stereotype: str | None = None
    description: str | None = None
    metadata_json: dict = Field(default_factory=dict)
    position_x: float = 0
    position_y: float = 0

    @field_validator("element_type")
    @classmethod
    def validar_tipo_elemento(cls, v: str) -> str:
        if v not in VALID_ELEMENT_TYPES:
            raise ValueError(
                f"El tipo de elemento debe ser uno de: {', '.join(sorted(VALID_ELEMENT_TYPES))}"
            )
        return v

    @field_validator("visibility")
    @classmethod
    def validar_visibilidad(cls, v: str) -> str:
        if v not in VALID_VISIBILITIES:
            raise ValueError(
                f"La visibilidad debe ser una de: {', '.join(sorted(VALID_VISIBILITIES))}"
            )
        return v


class SolicitudActualizacionClaseUML(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    visibility: str | None = None
    element_type: str | None = None
    stereotype: str | None = None
    description: str | None = None
    metadata_json: dict | None = None

    @field_validator("element_type")
    @classmethod
    def validar_tipo_elemento(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_ELEMENT_TYPES:
            raise ValueError(
                f"El tipo de elemento debe ser uno de: {', '.join(sorted(VALID_ELEMENT_TYPES))}"
            )
        return v

    @field_validator("visibility")
    @classmethod
    def validar_visibilidad(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_VISIBILITIES:
            raise ValueError(
                f"La visibilidad debe ser una de: {', '.join(sorted(VALID_VISIBILITIES))}"
            )
        return v


class RespuestaClaseUML(BaseModel):
    id: UUID
    diagram_id: UUID
    name: str
    visibility: str
    element_type: str
    stereotype: str | None
    description: str | None
    metadata_json: dict

    model_config = {"from_attributes": True}


class RespuestaDetalleClaseUML(RespuestaClaseUML):
    attributes: list["RespuestaAtributoUML"] = Field(default_factory=list)
    methods: list["RespuestaMetodoUML"] = Field(default_factory=list)
    visual: "RespuestaElementoVisualUML | None" = None


class SolicitudCreacionAtributoUML(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    data_type: str = Field(min_length=1, max_length=120)
    visibility: str = "private"
    initial_value: str | None = None
    multiplicity: str | None = None
    is_required: bool = False
    order_index: int = 0
    constraints: dict = Field(default_factory=dict)

    @field_validator("visibility")
    @classmethod
    def validar_visibilidad(cls, v: str) -> str:
        if v not in VALID_VISIBILITIES:
            raise ValueError(
                f"La visibilidad debe ser una de: {', '.join(sorted(VALID_VISIBILITIES))}"
            )
        return v


class SolicitudActualizacionAtributoUML(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    data_type: str | None = Field(default=None, min_length=1, max_length=120)
    visibility: str | None = None
    initial_value: str | None = None
    multiplicity: str | None = None
    is_required: bool | None = None
    order_index: int | None = None
    constraints: dict | None = None

    @field_validator("visibility")
    @classmethod
    def validar_visibilidad(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_VISIBILITIES:
            raise ValueError(
                f"La visibilidad debe ser una de: {', '.join(sorted(VALID_VISIBILITIES))}"
            )
        return v


class RespuestaAtributoUML(BaseModel):
    id: UUID
    class_id: UUID
    name: str
    data_type: str
    visibility: str
    initial_value: str | None
    multiplicity: str | None
    is_required: bool
    order_index: int
    constraints: dict

    model_config = {"from_attributes": True}


class SolicitudCreacionMetodoUML(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    return_type: str | None = None
    visibility: str = "public"
    order_index: int = 0
    metadata_json: dict = Field(default_factory=dict)

    @field_validator("visibility")
    @classmethod
    def validar_visibilidad(cls, v: str) -> str:
        if v not in VALID_VISIBILITIES:
            raise ValueError(
                f"La visibilidad debe ser una de: {', '.join(sorted(VALID_VISIBILITIES))}"
            )
        return v


class SolicitudActualizacionMetodoUML(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    return_type: str | None = None
    visibility: str | None = None
    order_index: int | None = None
    metadata_json: dict | None = None

    @field_validator("visibility")
    @classmethod
    def validar_visibilidad(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_VISIBILITIES:
            raise ValueError(
                f"La visibilidad debe ser una de: {', '.join(sorted(VALID_VISIBILITIES))}"
            )
        return v


class SolicitudCreacionParametroUML(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    data_type: str = Field(min_length=1, max_length=120)
    default_value: str | None = None
    order_index: int = 0


class SolicitudActualizacionParametroUML(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    data_type: str | None = Field(default=None, min_length=1, max_length=120)
    default_value: str | None = None
    order_index: int | None = Field(default=None, ge=0)


class RespuestaParametroUML(BaseModel):
    id: UUID
    method_id: UUID
    name: str
    data_type: str
    default_value: str | None
    order_index: int

    model_config = {"from_attributes": True}


class RespuestaMetodoUML(BaseModel):
    id: UUID
    class_id: UUID
    name: str
    return_type: str | None
    visibility: str
    order_index: int
    metadata_json: dict
    parameters: list[RespuestaParametroUML] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class SolicitudCreacionRelacionUML(BaseModel):
    source_class_id: UUID
    target_class_id: UUID
    relationship_type: str = Field(pattern=RELATIONSHIP_PATTERN)
    source_cardinality: str | None = None
    target_cardinality: str | None = None
    direction: str = "source_to_target"
    label: str | None = None
    metadata_json: dict = Field(default_factory=dict)

    @field_validator("relationship_type")
    @classmethod
    def validar_tipo_relacion(cls, v: str) -> str:
        if v not in VALID_RELATIONSHIP_TYPES:
            raise ValueError(
                f"El tipo de relación debe ser uno de: {', '.join(sorted(VALID_RELATIONSHIP_TYPES))}"
            )
        return v


class SolicitudActualizacionRelacionUML(BaseModel):
    relationship_type: str | None = Field(
        default=None,
        pattern=RELATIONSHIP_PATTERN,
    )
    source_cardinality: str | None = None
    target_cardinality: str | None = None
    direction: str | None = None
    label: str | None = None
    metadata_json: dict | None = None

    @field_validator("relationship_type")
    @classmethod
    def validar_tipo_relacion(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_RELATIONSHIP_TYPES:
            raise ValueError(
                f"El tipo de relación debe ser uno de: {', '.join(sorted(VALID_RELATIONSHIP_TYPES))}"
            )
        return v


class RespuestaRelacionUML(BaseModel):
    id: UUID
    diagram_id: UUID
    source_class_id: UUID
    target_class_id: UUID
    relationship_type: str
    source_cardinality: str | None
    target_cardinality: str | None
    direction: str
    label: str | None
    metadata_json: dict

    model_config = {"from_attributes": True}


class RespuestaValidacionUML(BaseModel):
    diagram_id: UUID
    errors: list[str]
    warnings: list[str]
    recommendations: list[str]


class RespuestaElementoVisualUML(BaseModel):
    id: UUID
    diagram_id: UUID
    element_type: str
    element_id: UUID
    position_x: float
    position_y: float
    width: float | None
    height: float | None
    style: dict

    model_config = {"from_attributes": True}


class SolicitudMoverElemento(BaseModel):
    element_type: str = Field(pattern="^(class|relationship)$")
    element_id: UUID
    position_x: float
    position_y: float
    width: float | None = None
    height: float | None = None
    style: dict = Field(default_factory=dict)


class RespuestaModeloDiagrama(BaseModel):
    diagram: RespuestaDiagrama
    classes: list[RespuestaDetalleClaseUML]
    relationships: list[RespuestaRelacionUML]


class SolicitudTextoAUML(BaseModel):
    project_id: UUID
    name: str = Field(min_length=2, max_length=160)
    prompt: str = Field(min_length=5)
    source_type: str = Field(default="text", pattern="^(text|voice|image)$")


class SolicitudImportacionXMI(BaseModel):
    project_id: UUID
    name: str = Field(min_length=2, max_length=160)
    content: str = Field(min_length=10)
    tool_name: str | None = "Enterprise Architect"
    file_name: str = "modelo-importado.xml"


class RespuestaExportacionXMI(BaseModel):
    diagram_id: UUID
    file_name: str
    content: str


RespuestaDetalleClaseUML.model_rebuild()
RespuestaMetodoUML.model_rebuild()
