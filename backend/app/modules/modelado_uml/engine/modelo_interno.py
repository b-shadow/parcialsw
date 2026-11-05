from pydantic import BaseModel, Field


class ModeloVisualUML(BaseModel):
    id: str | None = None
    x: float = 0
    y: float = 0
    width: float | None = None
    height: float | None = None
    style: dict = Field(default_factory=dict)


class ModeloParametroUML(BaseModel):
    id: str | None = None
    name: str
    data_type: str
    default_value: str | None = None
    order_index: int = 0


class ModeloAtributoUML(BaseModel):
    id: str | None = None
    name: str
    data_type: str
    visibility: str = "private"
    initial_value: str | None = None
    multiplicity: str | None = None
    is_required: bool = False
    order_index: int = 0
    constraints: dict = Field(default_factory=dict)


class ModeloMetodoUML(BaseModel):
    id: str | None = None
    name: str
    return_type: str | None = None
    visibility: str = "public"
    order_index: int = 0
    parameters: list[ModeloParametroUML] = Field(default_factory=list)
    metadata_json: dict = Field(default_factory=dict)
    specification: dict | None = None
    readiness: dict | None = None


class ModeloClaseUML(BaseModel):
    id: str | None = None
    name: str
    visibility: str = "public"
    element_type: str = "class"
    stereotype: str | None = None
    description: str | None = None
    attributes: list[ModeloAtributoUML] = Field(default_factory=list)
    methods: list[ModeloMetodoUML] = Field(default_factory=list)
    visual: ModeloVisualUML = Field(default_factory=ModeloVisualUML)
    metadata_json: dict = Field(default_factory=dict)


class ModeloRelacionUML(BaseModel):
    id: str | None = None
    source_class_id: str
    target_class_id: str
    relationship_type: str
    source_cardinality: str | None = None
    target_cardinality: str | None = None
    direction: str = "source_to_target"
    label: str | None = None
    metadata_json: dict = Field(default_factory=dict)


class ModeloDiagramaUML(BaseModel):
    id: str | None = None
    project_id: str | None = None
    name: str
    diagram_type: str = "class"
    status: str = "active"
    current_version: int = 1
    description: str | None = None
    classes: list[ModeloClaseUML] = Field(default_factory=list)
    relationships: list[ModeloRelacionUML] = Field(default_factory=list)
    metadata_json: dict = Field(default_factory=dict)
