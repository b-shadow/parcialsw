from pydantic import BaseModel, Field


class UmlVisualModel(BaseModel):
    x: float = 0
    y: float = 0
    width: float | None = None
    height: float | None = None
    style: dict = Field(default_factory=dict)


class UmlParameterModel(BaseModel):
    id: str | None = None
    name: str
    data_type: str
    default_value: str | None = None
    order_index: int = 0


class UmlAttributeModel(BaseModel):
    id: str | None = None
    name: str
    data_type: str
    visibility: str = "private"
    initial_value: str | None = None
    multiplicity: str | None = None
    is_required: bool = False
    order_index: int = 0
    constraints: dict = Field(default_factory=dict)


class UmlMethodModel(BaseModel):
    id: str | None = None
    name: str
    return_type: str | None = None
    visibility: str = "public"
    order_index: int = 0
    parameters: list[UmlParameterModel] = Field(default_factory=list)
    metadata_json: dict = Field(default_factory=dict)


class UmlClassModel(BaseModel):
    id: str | None = None
    name: str
    visibility: str = "public"
    element_type: str = "class"
    stereotype: str | None = None
    description: str | None = None
    attributes: list[UmlAttributeModel] = Field(default_factory=list)
    methods: list[UmlMethodModel] = Field(default_factory=list)
    visual: UmlVisualModel = Field(default_factory=UmlVisualModel)
    metadata_json: dict = Field(default_factory=dict)


class UmlRelationshipModel(BaseModel):
    id: str | None = None
    source_class_id: str
    target_class_id: str
    relationship_type: str
    source_cardinality: str | None = None
    target_cardinality: str | None = None
    direction: str = "source_to_target"
    label: str | None = None
    metadata_json: dict = Field(default_factory=dict)


class UmlDiagramModel(BaseModel):
    id: str | None = None
    project_id: str | None = None
    name: str
    diagram_type: str = "class"
    status: str = "active"
    current_version: int = 1
    description: str | None = None
    classes: list[UmlClassModel] = Field(default_factory=list)
    relationships: list[UmlRelationshipModel] = Field(default_factory=list)
    metadata_json: dict = Field(default_factory=dict)
