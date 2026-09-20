from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DiagramCreateRequest(BaseModel):
    project_id: UUID
    name: str = Field(min_length=2, max_length=160)
    description: str | None = None
    metadata_json: dict = Field(default_factory=dict)


class DiagramResponse(BaseModel):
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


class UmlClassCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    visibility: str = "public"
    element_type: str = "class"
    stereotype: str | None = None
    description: str | None = None
    metadata_json: dict = Field(default_factory=dict)
    position_x: float = 0
    position_y: float = 0


class UmlClassUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    visibility: str | None = None
    element_type: str | None = None
    stereotype: str | None = None
    description: str | None = None
    metadata_json: dict | None = None


class UmlClassResponse(BaseModel):
    id: UUID
    diagram_id: UUID
    name: str
    visibility: str
    element_type: str
    stereotype: str | None
    description: str | None
    metadata_json: dict

    model_config = {"from_attributes": True}


class UmlClassDetailResponse(UmlClassResponse):
    attributes: list["UmlAttributeResponse"] = Field(default_factory=list)
    methods: list["UmlMethodResponse"] = Field(default_factory=list)
    visual: "UmlVisualElementResponse | None" = None


class UmlAttributeCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    data_type: str = Field(min_length=1, max_length=120)
    visibility: str = "private"
    initial_value: str | None = None
    multiplicity: str | None = None
    is_required: bool = False
    order_index: int = 0
    constraints: dict = Field(default_factory=dict)


class UmlAttributeUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    data_type: str | None = Field(default=None, min_length=1, max_length=120)
    visibility: str | None = None
    initial_value: str | None = None
    multiplicity: str | None = None
    is_required: bool | None = None
    order_index: int | None = None
    constraints: dict | None = None


class UmlAttributeResponse(BaseModel):
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


class UmlMethodCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    return_type: str | None = None
    visibility: str = "public"
    order_index: int = 0
    metadata_json: dict = Field(default_factory=dict)


class UmlMethodUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    return_type: str | None = None
    visibility: str | None = None
    order_index: int | None = None
    metadata_json: dict | None = None


class UmlParameterCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    data_type: str = Field(min_length=1, max_length=120)
    default_value: str | None = None
    order_index: int = 0


class UmlParameterResponse(BaseModel):
    id: UUID
    method_id: UUID
    name: str
    data_type: str
    default_value: str | None
    order_index: int

    model_config = {"from_attributes": True}


class UmlMethodResponse(BaseModel):
    id: UUID
    class_id: UUID
    name: str
    return_type: str | None
    visibility: str
    order_index: int
    metadata_json: dict
    parameters: list[UmlParameterResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class UmlRelationshipCreateRequest(BaseModel):
    source_class_id: UUID
    target_class_id: UUID
    relationship_type: str = Field(pattern="^(association|inheritance|implementation|dependency|aggregation|composition)$")
    source_cardinality: str | None = None
    target_cardinality: str | None = None
    direction: str = "source_to_target"
    label: str | None = None
    metadata_json: dict = Field(default_factory=dict)


class UmlRelationshipUpdateRequest(BaseModel):
    relationship_type: str | None = Field(
        default=None,
        pattern="^(association|inheritance|implementation|dependency|aggregation|composition)$",
    )
    source_cardinality: str | None = None
    target_cardinality: str | None = None
    direction: str | None = None
    label: str | None = None
    metadata_json: dict | None = None


class UmlRelationshipResponse(BaseModel):
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


class UmlValidationResponse(BaseModel):
    diagram_id: UUID
    errors: list[str]
    warnings: list[str]
    recommendations: list[str]


class UmlVisualElementResponse(BaseModel):
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


class MoveElementRequest(BaseModel):
    element_type: str = Field(pattern="^(class|relationship)$")
    element_id: UUID
    position_x: float
    position_y: float
    width: float | None = None
    height: float | None = None
    style: dict = Field(default_factory=dict)


class DiagramModelResponse(BaseModel):
    diagram: DiagramResponse
    classes: list[UmlClassDetailResponse]
    relationships: list[UmlRelationshipResponse]


class TextToUmlRequest(BaseModel):
    project_id: UUID
    name: str = Field(min_length=2, max_length=160)
    prompt: str = Field(min_length=5)
    source_type: str = Field(default="text", pattern="^(text|voice|image)$")


class XmiImportRequest(BaseModel):
    project_id: UUID
    name: str = Field(min_length=2, max_length=160)
    content: str = Field(min_length=10)
    tool_name: str | None = "Enterprise Architect"
    file_name: str = "modelo-importado.xml"


class XmiExportResponse(BaseModel):
    diagram_id: UUID
    file_name: str
    content: str


UmlClassDetailResponse.model_rebuild()
UmlMethodResponse.model_rebuild()
