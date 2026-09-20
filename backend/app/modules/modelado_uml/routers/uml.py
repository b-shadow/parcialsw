from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database.session import get_db
from app.core.security.dependencies import get_current_user
from app.modules.acceso_usuarios.models import User
from app.modules.modelado_uml.models import UmlClass, UmlDiagram, UmlRelationship
from app.modules.modelado_uml.schemas.uml import (
    DiagramCreateRequest,
    DiagramModelResponse,
    DiagramResponse,
    MoveElementRequest,
    TextToUmlRequest,
    UmlAttributeCreateRequest,
    UmlAttributeResponse,
    UmlAttributeUpdateRequest,
    UmlClassCreateRequest,
    UmlClassResponse,
    UmlClassUpdateRequest,
    UmlMethodCreateRequest,
    UmlMethodResponse,
    UmlMethodUpdateRequest,
    UmlParameterCreateRequest,
    UmlParameterResponse,
    UmlRelationshipCreateRequest,
    UmlRelationshipResponse,
    UmlRelationshipUpdateRequest,
    UmlValidationResponse,
    UmlVisualElementResponse,
    XmiExportResponse,
    XmiImportRequest,
)
from app.modules.modelado_uml.services.uml_service import UmlService

router = APIRouter(prefix="/uml", tags=["modelado-uml"])


@router.post("/diagrams", response_model=DiagramResponse, status_code=status.HTTP_201_CREATED)
def create_diagram(
    payload: DiagramCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UmlDiagram:
    return UmlService(db).create_diagram(payload, current_user.id)


@router.get("/projects/{project_id}/diagrams", response_model=list[DiagramResponse])
def list_diagrams(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[UmlDiagram]:
    return UmlService(db).list_diagrams(project_id, current_user.id)


@router.delete("/diagrams/{diagram_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_diagram(
    diagram_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    UmlService(db).delete_diagram(diagram_id, current_user.id)


@router.post(
    "/diagrams/{diagram_id}/classes",
    response_model=UmlClassResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_class(
    diagram_id: UUID,
    payload: UmlClassCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UmlClass:
    return UmlService(db).create_class(diagram_id, payload, current_user.id)


@router.get("/diagrams/{diagram_id}/classes", response_model=list[UmlClassResponse])
def list_classes(
    diagram_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[UmlClass]:
    return UmlService(db).list_classes(diagram_id, current_user.id)


@router.get("/diagrams/{diagram_id}/model", response_model=DiagramModelResponse)
def get_diagram_model(
    diagram_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DiagramModelResponse:
    return UmlService(db).get_diagram_model(diagram_id, current_user.id)


@router.patch("/classes/{class_id}", response_model=UmlClassResponse)
def update_class(
    class_id: UUID,
    payload: UmlClassUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UmlClass:
    return UmlService(db).update_class(class_id, payload, current_user.id)


@router.delete("/classes/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_class(
    class_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    UmlService(db).delete_class(class_id, current_user.id)


@router.post("/classes/{class_id}/attributes", response_model=UmlAttributeResponse, status_code=status.HTTP_201_CREATED)
def add_attribute(
    class_id: UUID,
    payload: UmlAttributeCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UmlAttributeResponse:
    return UmlService(db).add_attribute(class_id, payload, current_user.id)


@router.patch("/attributes/{attribute_id}", response_model=UmlAttributeResponse)
def update_attribute(
    attribute_id: UUID,
    payload: UmlAttributeUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UmlAttributeResponse:
    return UmlService(db).update_attribute(attribute_id, payload, current_user.id)


@router.delete("/attributes/{attribute_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attribute(
    attribute_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    UmlService(db).delete_attribute(attribute_id, current_user.id)


@router.post("/classes/{class_id}/methods", response_model=UmlMethodResponse, status_code=status.HTTP_201_CREATED)
def add_method(
    class_id: UUID,
    payload: UmlMethodCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UmlMethodResponse:
    return UmlService(db).add_method(class_id, payload, current_user.id)


@router.patch("/methods/{method_id}", response_model=UmlMethodResponse)
def update_method(
    method_id: UUID,
    payload: UmlMethodUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UmlMethodResponse:
    return UmlService(db).update_method(method_id, payload, current_user.id)


@router.delete("/methods/{method_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_method(
    method_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    UmlService(db).delete_method(method_id, current_user.id)


@router.post("/methods/{method_id}/parameters", response_model=UmlParameterResponse, status_code=status.HTTP_201_CREATED)
def add_parameter(
    method_id: UUID,
    payload: UmlParameterCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UmlParameterResponse:
    return UmlService(db).add_parameter(method_id, payload, current_user.id)


@router.post(
    "/diagrams/{diagram_id}/relationships",
    response_model=UmlRelationshipResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_relationship(
    diagram_id: UUID,
    payload: UmlRelationshipCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UmlRelationship:
    return UmlService(db).create_relationship(diagram_id, payload, current_user.id)


@router.patch("/relationships/{relationship_id}", response_model=UmlRelationshipResponse)
def update_relationship(
    relationship_id: UUID,
    payload: UmlRelationshipUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UmlRelationship:
    return UmlService(db).update_relationship(relationship_id, payload, current_user.id)


@router.delete("/relationships/{relationship_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_relationship(
    relationship_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    UmlService(db).delete_relationship(relationship_id, current_user.id)


@router.patch("/diagrams/{diagram_id}/visual-elements", response_model=UmlVisualElementResponse)
def move_element(
    diagram_id: UUID,
    payload: MoveElementRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UmlVisualElementResponse:
    return UmlService(db).move_element(diagram_id, payload, current_user.id)


@router.post("/diagrams/{diagram_id}/validate", response_model=UmlValidationResponse)
def validate_diagram(
    diagram_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UmlValidationResponse:
    return UmlService(db).validate_diagram(diagram_id, current_user.id)


@router.post("/generate", response_model=DiagramResponse, status_code=status.HTTP_201_CREATED)
def generate_from_prompt(
    payload: TextToUmlRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UmlDiagram:
    return UmlService(db).generate_from_prompt(payload, current_user.id)


@router.post("/xmi/import", response_model=DiagramResponse, status_code=status.HTTP_201_CREATED)
def import_xmi_diagram(
    payload: XmiImportRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UmlDiagram:
    return UmlService(db).import_diagram_xmi(payload, current_user.id)


@router.post("/diagrams/{diagram_id}/xmi/import", response_model=DiagramResponse)
def import_xmi_into_diagram(
    diagram_id: UUID,
    payload: XmiImportRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UmlDiagram:
    return UmlService(db).import_diagram_xmi_into_existing(diagram_id, payload, current_user.id)


@router.get("/diagrams/{diagram_id}/xmi", response_model=XmiExportResponse)
def export_xmi_diagram(
    diagram_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> XmiExportResponse:
    return UmlService(db).export_diagram_xmi(diagram_id, current_user.id)
