from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.acceso_usuarios.services.audit_service import AuditService
from app.modules.modelado_uml.engine.internal_model import (
    UmlAttributeModel,
    UmlClassModel,
    UmlDiagramModel,
    UmlMethodModel,
    UmlParameterModel,
    UmlRelationshipModel,
    UmlVisualModel,
)
from app.modules.modelado_uml.engine.text_parser import build_uml_from_text
from app.modules.modelado_uml.engine.validator import validate_internal_model
from app.modules.modelado_uml.engine.xmi import export_xmi, import_xmi
from app.modules.modelado_uml.models import (
    UmlAttribute,
    UmlClass,
    UmlDiagram,
    UmlMethod,
    UmlParameter,
    UmlRelationship,
    UmlVisualElement,
    XmiExchange,
)
from app.modules.modelado_uml.repositories.uml_repository import UmlRepository
from app.modules.modelado_uml.schemas.uml import (
    DiagramCreateRequest,
    DiagramModelResponse,
    MoveElementRequest,
    TextToUmlRequest,
    UmlAttributeCreateRequest,
    UmlAttributeUpdateRequest,
    UmlClassCreateRequest,
    UmlClassDetailResponse,
    UmlClassUpdateRequest,
    UmlMethodCreateRequest,
    UmlMethodUpdateRequest,
    UmlParameterCreateRequest,
    UmlRelationshipCreateRequest,
    UmlRelationshipUpdateRequest,
    UmlValidationResponse,
    XmiExportResponse,
    XmiImportRequest,
)
from app.modules.modelado_uml.validators.uml_validator import (
    ensure_class_belongs_to_diagram,
    ensure_class_exists,
    ensure_diagram_exists,
)
from app.modules.proyectos_colaboracion.repositories.member_repository import MemberRepository
from app.modules.proyectos_colaboracion.validators.project_validator import ensure_membership


class UmlService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.uml = UmlRepository(db)
        self.members = MemberRepository(db)
        self.audit = AuditService(db)

    def create_diagram(self, payload: DiagramCreateRequest, user_id: UUID) -> UmlDiagram:
        ensure_membership(self.members.get_membership(payload.project_id, user_id))
        diagram = self.uml.add_diagram(
            UmlDiagram(
                project_id=payload.project_id,
                created_by_user_id=user_id,
                name=payload.name,
                diagram_type="class",
                description=payload.description,
                metadata_json=payload.metadata_json,
            )
        )
        self.audit.record(
            module="modelado_uml",
            action="CREATE_DIAGRAM",
            user_id=user_id,
            project_id=payload.project_id,
            metadata={"diagram_id": str(diagram.id)},
        )
        self.db.commit()
        self.db.refresh(diagram)
        return diagram

    def list_diagrams(self, project_id: UUID, user_id: UUID) -> list[UmlDiagram]:
        ensure_membership(self.members.get_membership(project_id, user_id))
        return self.uml.list_diagrams_by_project(project_id)

    def delete_diagram(self, diagram_id: UUID, user_id: UUID) -> None:
        diagram = ensure_diagram_exists(self.uml.get_diagram(diagram_id))
        ensure_membership(self.members.get_membership(diagram.project_id, user_id))
        self.uml.delete_visual_elements_by_diagram(diagram_id)
        self.uml.delete_xmi_exchanges_by_diagram(diagram_id)
        self.uml.delete_diagram(diagram)
        self.audit.record(
            module="modelado_uml",
            action="DELETE_DIAGRAM",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"diagram_id": str(diagram_id)},
        )
        self.db.commit()

    def create_class(
        self, diagram_id: UUID, payload: UmlClassCreateRequest, user_id: UUID
    ) -> UmlClass:
        diagram = ensure_diagram_exists(self.uml.get_diagram(diagram_id))
        ensure_membership(self.members.get_membership(diagram.project_id, user_id))
        uml_class = self.uml.add_class(
            UmlClass(
                diagram_id=diagram_id,
                name=payload.name,
                visibility=payload.visibility,
                element_type=payload.element_type,
                stereotype=payload.stereotype,
                description=payload.description,
                metadata_json=payload.metadata_json,
            )
        )
        self.uml.add_visual_element(
            UmlVisualElement(
                diagram_id=diagram_id,
                element_type="class",
                element_id=uml_class.id,
                position_x=payload.position_x,
                position_y=payload.position_y,
            )
        )
        self.audit.record(
            module="modelado_uml",
            action="CREATE_CLASS",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"diagram_id": str(diagram_id), "class_id": str(uml_class.id)},
        )
        self.db.commit()
        self.db.refresh(uml_class)
        return uml_class

    def list_classes(self, diagram_id: UUID, user_id: UUID) -> list[UmlClass]:
        diagram = ensure_diagram_exists(self.uml.get_diagram(diagram_id))
        ensure_membership(self.members.get_membership(diagram.project_id, user_id))
        return self.uml.list_classes(diagram_id)

    def get_diagram_model(self, diagram_id: UUID, user_id: UUID) -> DiagramModelResponse:
        diagram = ensure_diagram_exists(self.uml.get_diagram(diagram_id))
        ensure_membership(self.members.get_membership(diagram.project_id, user_id))
        classes = self.uml.list_classes(diagram_id)
        visuals = {
            visual.element_id: visual for visual in self.uml.list_visual_elements(diagram_id)
        }
        class_details = [
            UmlClassDetailResponse.model_validate(uml_class).model_copy(
                update={"visual": visuals.get(uml_class.id)}
            )
            for uml_class in classes
        ]
        return DiagramModelResponse(
            diagram=diagram,
            classes=class_details,
            relationships=self.uml.list_relationships(diagram_id),
        )

    def update_class(
        self, class_id: UUID, payload: UmlClassUpdateRequest, user_id: UUID
    ) -> UmlClass:
        uml_class = ensure_class_exists(self.uml.get_class(class_id))
        diagram = ensure_diagram_exists(self.uml.get_diagram(uml_class.diagram_id))
        ensure_membership(self.members.get_membership(diagram.project_id, user_id))
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(uml_class, field, value)
        self.audit.record(
            module="modelado_uml",
            action="UPDATE_CLASS",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"class_id": str(class_id)},
        )
        self.db.commit()
        self.db.refresh(uml_class)
        return uml_class

    def delete_class(self, class_id: UUID, user_id: UUID) -> None:
        uml_class = ensure_class_exists(self.uml.get_class(class_id))
        diagram = ensure_diagram_exists(self.uml.get_diagram(uml_class.diagram_id))
        ensure_membership(self.members.get_membership(diagram.project_id, user_id))
        for relationship in self.uml.list_relationships_for_class(class_id):
            self.uml.delete_visual_element(diagram.id, "relationship", relationship.id)
            self.uml.delete_relationship(relationship)
        self.db.flush()
        self.uml.delete_visual_element(diagram.id, "class", class_id)
        self.uml.delete_class(uml_class)
        self.audit.record(
            module="modelado_uml",
            action="DELETE_CLASS",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"class_id": str(class_id)},
        )
        self.db.commit()

    def add_attribute(
        self, class_id: UUID, payload: UmlAttributeCreateRequest, user_id: UUID
    ) -> UmlAttribute:
        uml_class = ensure_class_exists(self.uml.get_class(class_id))
        diagram = ensure_diagram_exists(self.uml.get_diagram(uml_class.diagram_id))
        ensure_membership(self.members.get_membership(diagram.project_id, user_id))
        attribute = self.uml.add_attribute(UmlAttribute(class_id=class_id, **payload.model_dump()))
        self.audit.record(
            module="modelado_uml",
            action="CREATE_ATTRIBUTE",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"class_id": str(class_id), "attribute_id": str(attribute.id)},
        )
        self.db.commit()
        self.db.refresh(attribute)
        return attribute

    def update_attribute(
        self, attribute_id: UUID, payload: UmlAttributeUpdateRequest, user_id: UUID
    ) -> UmlAttribute:
        from fastapi import HTTPException, status

        attribute = self.uml.get_attribute(attribute_id)
        if attribute is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Atributo UML no encontrado")
        uml_class = ensure_class_exists(self.uml.get_class(attribute.class_id))
        diagram = ensure_diagram_exists(self.uml.get_diagram(uml_class.diagram_id))
        ensure_membership(self.members.get_membership(diagram.project_id, user_id))
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(attribute, field, value)
        self.audit.record(
            module="modelado_uml",
            action="UPDATE_ATTRIBUTE",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"attribute_id": str(attribute_id), "class_id": str(attribute.class_id)},
        )
        self.db.commit()
        self.db.refresh(attribute)
        return attribute

    def delete_attribute(self, attribute_id: UUID, user_id: UUID) -> None:
        from fastapi import HTTPException, status

        attribute = self.uml.get_attribute(attribute_id)
        if attribute is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Atributo UML no encontrado")
        uml_class = ensure_class_exists(self.uml.get_class(attribute.class_id))
        diagram = ensure_diagram_exists(self.uml.get_diagram(uml_class.diagram_id))
        ensure_membership(self.members.get_membership(diagram.project_id, user_id))
        self.uml.delete_attribute(attribute)
        self.audit.record(
            module="modelado_uml",
            action="DELETE_ATTRIBUTE",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"attribute_id": str(attribute_id), "class_id": str(uml_class.id)},
        )
        self.db.commit()

    def add_method(
        self, class_id: UUID, payload: UmlMethodCreateRequest, user_id: UUID
    ) -> UmlMethod:
        uml_class = ensure_class_exists(self.uml.get_class(class_id))
        diagram = ensure_diagram_exists(self.uml.get_diagram(uml_class.diagram_id))
        ensure_membership(self.members.get_membership(diagram.project_id, user_id))
        method = self.uml.add_method(UmlMethod(class_id=class_id, **payload.model_dump()))
        self.audit.record(
            module="modelado_uml",
            action="CREATE_METHOD",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"class_id": str(class_id), "method_id": str(method.id)},
        )
        self.db.commit()
        self.db.refresh(method)
        return method

    def update_method(
        self, method_id: UUID, payload: UmlMethodUpdateRequest, user_id: UUID
    ) -> UmlMethod:
        from fastapi import HTTPException, status

        method = self.uml.get_method(method_id)
        if method is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metodo UML no encontrado")
        uml_class = ensure_class_exists(self.uml.get_class(method.class_id))
        diagram = ensure_diagram_exists(self.uml.get_diagram(uml_class.diagram_id))
        ensure_membership(self.members.get_membership(diagram.project_id, user_id))
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(method, field, value)
        self.audit.record(
            module="modelado_uml",
            action="UPDATE_METHOD",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"method_id": str(method_id), "class_id": str(method.class_id)},
        )
        self.db.commit()
        self.db.refresh(method)
        return method

    def delete_method(self, method_id: UUID, user_id: UUID) -> None:
        from fastapi import HTTPException, status

        method = self.uml.get_method(method_id)
        if method is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metodo UML no encontrado")
        uml_class = ensure_class_exists(self.uml.get_class(method.class_id))
        diagram = ensure_diagram_exists(self.uml.get_diagram(uml_class.diagram_id))
        ensure_membership(self.members.get_membership(diagram.project_id, user_id))
        self.uml.delete_method(method)
        self.audit.record(
            module="modelado_uml",
            action="DELETE_METHOD",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"method_id": str(method_id), "class_id": str(uml_class.id)},
        )
        self.db.commit()

    def add_parameter(
        self, method_id: UUID, payload: UmlParameterCreateRequest, user_id: UUID
    ) -> UmlParameter:
        method = self.uml.get_method(method_id)
        if method is None:
            from fastapi import HTTPException, status

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metodo UML no encontrado")
        uml_class = ensure_class_exists(self.uml.get_class(method.class_id))
        diagram = ensure_diagram_exists(self.uml.get_diagram(uml_class.diagram_id))
        ensure_membership(self.members.get_membership(diagram.project_id, user_id))
        parameter = self.uml.add_parameter(UmlParameter(method_id=method_id, **payload.model_dump()))
        self.audit.record(
            module="modelado_uml",
            action="CREATE_PARAMETER",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"method_id": str(method_id), "parameter_id": str(parameter.id)},
        )
        self.db.commit()
        self.db.refresh(parameter)
        return parameter

    def create_relationship(
        self, diagram_id: UUID, payload: UmlRelationshipCreateRequest, user_id: UUID
    ) -> UmlRelationship:
        diagram = ensure_diagram_exists(self.uml.get_diagram(diagram_id))
        ensure_membership(self.members.get_membership(diagram.project_id, user_id))
        source = ensure_class_exists(self.uml.get_class(payload.source_class_id))
        target = ensure_class_exists(self.uml.get_class(payload.target_class_id))
        ensure_class_belongs_to_diagram(source, diagram_id)
        ensure_class_belongs_to_diagram(target, diagram_id)
        relationship = self.uml.add_relationship(
            UmlRelationship(diagram_id=diagram_id, **payload.model_dump())
        )
        self.audit.record(
            module="modelado_uml",
            action="CREATE_RELATION",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"relationship_id": str(relationship.id)},
        )
        self.db.commit()
        self.db.refresh(relationship)
        return relationship

    def update_relationship(
        self, relationship_id: UUID, payload: UmlRelationshipUpdateRequest, user_id: UUID
    ) -> UmlRelationship:
        relationship = self.uml.get_relationship(relationship_id)
        if relationship is None:
            from fastapi import HTTPException, status

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relacion UML no encontrada")
        diagram = ensure_diagram_exists(self.uml.get_diagram(relationship.diagram_id))
        ensure_membership(self.members.get_membership(diagram.project_id, user_id))
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(relationship, field, value)
        self.audit.record(
            module="modelado_uml",
            action="UPDATE_RELATION",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"relationship_id": str(relationship_id)},
        )
        self.db.commit()
        self.db.refresh(relationship)
        return relationship

    def delete_relationship(self, relationship_id: UUID, user_id: UUID) -> None:
        relationship = self.uml.get_relationship(relationship_id)
        if relationship is None:
            from fastapi import HTTPException, status

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relacion UML no encontrada")
        diagram = ensure_diagram_exists(self.uml.get_diagram(relationship.diagram_id))
        ensure_membership(self.members.get_membership(diagram.project_id, user_id))
        self.uml.delete_visual_element(diagram.id, "relationship", relationship_id)
        self.uml.delete_relationship(relationship)
        self.audit.record(
            module="modelado_uml",
            action="DELETE_RELATION",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"relationship_id": str(relationship_id)},
        )
        self.db.commit()

    def move_element(
        self, diagram_id: UUID, payload: MoveElementRequest, user_id: UUID
    ) -> UmlVisualElement:
        diagram = ensure_diagram_exists(self.uml.get_diagram(diagram_id))
        ensure_membership(self.members.get_membership(diagram.project_id, user_id))
        visual = self.uml.get_visual_element(diagram_id, payload.element_type, payload.element_id)
        if visual is None:
            visual = self.uml.add_visual_element(
                UmlVisualElement(
                    diagram_id=diagram_id,
                    element_type=payload.element_type,
                    element_id=payload.element_id,
                    position_x=payload.position_x,
                    position_y=payload.position_y,
                    width=payload.width,
                    height=payload.height,
                    style=payload.style,
                )
            )
        else:
            visual.position_x = payload.position_x
            visual.position_y = payload.position_y
            visual.width = payload.width
            visual.height = payload.height
            visual.style = payload.style
        self.audit.record(
            module="modelado_uml",
            action="MOVE_ELEMENT",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"element_type": payload.element_type, "element_id": str(payload.element_id)},
        )
        self.db.commit()
        self.db.refresh(visual)
        return visual

    def validate_diagram(self, diagram_id: UUID, user_id: UUID) -> UmlValidationResponse:
        diagram = ensure_diagram_exists(self.uml.get_diagram(diagram_id))
        ensure_membership(self.members.get_membership(diagram.project_id, user_id))
        model = self._build_internal_model(diagram)
        errors, warnings, recommendations = validate_internal_model(model)
        return UmlValidationResponse(
            diagram_id=diagram_id,
            errors=errors,
            warnings=warnings,
            recommendations=recommendations,
        )

    def export_diagram_xmi(self, diagram_id: UUID, user_id: UUID) -> XmiExportResponse:
        diagram = ensure_diagram_exists(self.uml.get_diagram(diagram_id))
        ensure_membership(self.members.get_membership(diagram.project_id, user_id))
        content = export_xmi(self._build_internal_model(diagram))
        file_name = f"{diagram.name.lower().replace(' ', '-')}.xml"
        self.uml.add_xmi_exchange(
            XmiExchange(
                diagram_id=diagram_id,
                user_id=user_id,
                exchange_type="export",
                tool_name="Enterprise Architect",
                file_name=file_name,
                status="completed",
                metadata_json={"format": "xmi"},
            )
        )
        self.audit.record(
            module="modelado_uml",
            action="EXPORT_XMI",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"diagram_id": str(diagram_id), "file_name": file_name},
        )
        self.db.commit()
        return XmiExportResponse(diagram_id=diagram_id, file_name=file_name, content=content)

    def import_diagram_xmi(self, payload: XmiImportRequest, user_id: UUID) -> UmlDiagram:
        ensure_membership(self.members.get_membership(payload.project_id, user_id))
        model = import_xmi(payload.content, payload.name)
        diagram = self._persist_internal_model(model, payload.project_id, user_id)
        self.uml.add_xmi_exchange(
            XmiExchange(
                diagram_id=diagram.id,
                user_id=user_id,
                exchange_type="import",
                tool_name=payload.tool_name,
                file_name=payload.file_name,
                status="completed",
                metadata_json={"class_count": len(model.classes)},
            )
        )
        self.audit.record(
            module="modelado_uml",
            action="IMPORT_XMI",
            user_id=user_id,
            project_id=payload.project_id,
            metadata={"diagram_id": str(diagram.id), "file_name": payload.file_name},
        )
        self.db.commit()
        self.db.refresh(diagram)
        return diagram

    def import_diagram_xmi_into_existing(
        self, diagram_id: UUID, payload: XmiImportRequest, user_id: UUID
    ) -> UmlDiagram:
        diagram = ensure_diagram_exists(self.uml.get_diagram(diagram_id))
        ensure_membership(self.members.get_membership(diagram.project_id, user_id))
        model = import_xmi(payload.content, payload.name)

        self.uml.delete_visual_elements_by_diagram(diagram_id)
        self.uml.delete_relationships_by_diagram(diagram_id)
        self.uml.delete_classes_by_diagram(diagram_id)
        self.db.flush()

        diagram.name = model.name or payload.name
        diagram.diagram_type = model.diagram_type
        diagram.status = model.status
        diagram.current_version = model.current_version
        diagram.description = model.description
        diagram.metadata_json = {
            **diagram.metadata_json,
            **model.metadata_json,
            "imported_file_name": payload.file_name,
        }
        self._populate_existing_diagram_from_model(diagram, model)
        self.uml.add_xmi_exchange(
            XmiExchange(
                diagram_id=diagram.id,
                user_id=user_id,
                exchange_type="import",
                tool_name=payload.tool_name,
                file_name=payload.file_name,
                status="completed",
                metadata_json={"class_count": len(model.classes), "mode": "replace"},
            )
        )
        self.audit.record(
            module="modelado_uml",
            action="IMPORT_XMI_REPLACE_DIAGRAM",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"diagram_id": str(diagram.id), "file_name": payload.file_name},
        )
        self.db.commit()
        self.db.refresh(diagram)
        return diagram

    def generate_from_prompt(self, payload: TextToUmlRequest, user_id: UUID) -> UmlDiagram:
        ensure_membership(self.members.get_membership(payload.project_id, user_id))
        model = build_uml_from_text(payload.prompt, payload.name)
        diagram = self._persist_internal_model(
            model,
            payload.project_id,
            user_id,
            metadata={"source_type": payload.source_type, "source_prompt": payload.prompt},
        )
        self.audit.record(
            module="modelado_uml",
            action="GENERATE_UML_FROM_SOURCE",
            user_id=user_id,
            project_id=payload.project_id,
            metadata={"diagram_id": str(diagram.id), "source_type": payload.source_type},
        )
        self.db.commit()
        self.db.refresh(diagram)
        return diagram

    def _build_internal_model(self, diagram: UmlDiagram) -> UmlDiagramModel:
        visuals = {
            visual.element_id: visual for visual in self.uml.list_visual_elements(diagram.id)
        }
        classes = []
        for uml_class in self.uml.list_classes(diagram.id):
            visual = visuals.get(uml_class.id)
            classes.append(
                UmlClassModel(
                    id=str(uml_class.id),
                    name=uml_class.name,
                    visibility=uml_class.visibility,
                    element_type=uml_class.element_type,
                    stereotype=uml_class.stereotype,
                    description=uml_class.description,
                    attributes=[
                        UmlAttributeModel(
                            id=str(attribute.id),
                            name=attribute.name,
                            data_type=attribute.data_type,
                            visibility=attribute.visibility,
                            initial_value=attribute.initial_value,
                            multiplicity=attribute.multiplicity,
                            is_required=attribute.is_required,
                            order_index=attribute.order_index,
                            constraints=attribute.constraints,
                        )
                        for attribute in uml_class.attributes
                    ],
                    methods=[
                        UmlMethodModel(
                            id=str(method.id),
                            name=method.name,
                            return_type=method.return_type,
                            visibility=method.visibility,
                            order_index=method.order_index,
                            metadata_json=method.metadata_json,
                            parameters=[
                                UmlParameterModel(
                                    id=str(parameter.id),
                                    name=parameter.name,
                                    data_type=parameter.data_type,
                                    default_value=parameter.default_value,
                                    order_index=parameter.order_index,
                                )
                                for parameter in method.parameters
                            ],
                        )
                        for method in uml_class.methods
                    ],
                    visual=UmlVisualModel(
                        x=visual.position_x if visual else 0,
                        y=visual.position_y if visual else 0,
                        width=visual.width if visual else None,
                        height=visual.height if visual else None,
                        style=visual.style if visual else {},
                    ),
                    metadata_json=uml_class.metadata_json,
                )
            )
        relationships = [
            UmlRelationshipModel(
                id=str(relationship.id),
                source_class_id=str(relationship.source_class_id),
                target_class_id=str(relationship.target_class_id),
                relationship_type=relationship.relationship_type,
                source_cardinality=relationship.source_cardinality,
                target_cardinality=relationship.target_cardinality,
                direction=relationship.direction,
                label=relationship.label,
                metadata_json=relationship.metadata_json,
            )
            for relationship in self.uml.list_relationships(diagram.id)
        ]
        return UmlDiagramModel(
            id=str(diagram.id),
            project_id=str(diagram.project_id),
            name=diagram.name,
            diagram_type=diagram.diagram_type,
            status=diagram.status,
            current_version=diagram.current_version,
            description=diagram.description,
            classes=classes,
            relationships=relationships,
            metadata_json=diagram.metadata_json,
        )

    def _persist_internal_model(
        self,
        model: UmlDiagramModel,
        project_id: UUID,
        user_id: UUID,
        metadata: dict | None = None,
    ) -> UmlDiagram:
        diagram = self.uml.add_diagram(
            UmlDiagram(
                project_id=project_id,
                created_by_user_id=user_id,
                name=model.name,
                diagram_type=model.diagram_type,
                status=model.status,
                current_version=model.current_version,
                description=model.description,
                metadata_json={**model.metadata_json, **(metadata or {})},
            )
        )
        self._populate_existing_diagram_from_model(diagram, model)
        return diagram

    def _populate_existing_diagram_from_model(
        self, diagram: UmlDiagram, model: UmlDiagramModel
    ) -> None:
        id_by_external_ref: dict[str, UUID] = {}
        for uml_class_model in model.classes:
            uml_class = self.uml.add_class(
                UmlClass(
                    diagram_id=diagram.id,
                    name=uml_class_model.name,
                    visibility=uml_class_model.visibility,
                    element_type=uml_class_model.element_type,
                    stereotype=uml_class_model.stereotype,
                    description=uml_class_model.description,
                    metadata_json=uml_class_model.metadata_json,
                )
            )
            if uml_class_model.id:
                id_by_external_ref[uml_class_model.id] = uml_class.id
            id_by_external_ref[uml_class_model.name] = uml_class.id
            self.uml.add_visual_element(
                UmlVisualElement(
                    diagram_id=diagram.id,
                    element_type="class",
                    element_id=uml_class.id,
                    position_x=uml_class_model.visual.x,
                    position_y=uml_class_model.visual.y,
                    width=uml_class_model.visual.width,
                    height=uml_class_model.visual.height,
                    style=uml_class_model.visual.style,
                )
            )
            for attribute_model in uml_class_model.attributes:
                self.uml.add_attribute(UmlAttribute(class_id=uml_class.id, **attribute_model.model_dump(exclude={"id"})))
            for method_model in uml_class_model.methods:
                method = self.uml.add_method(
                    UmlMethod(class_id=uml_class.id, **method_model.model_dump(exclude={"id", "parameters"}))
                )
                for parameter_model in method_model.parameters:
                    self.uml.add_parameter(
                        UmlParameter(method_id=method.id, **parameter_model.model_dump(exclude={"id"}))
                    )
        for relationship_model in model.relationships:
            source_id = id_by_external_ref.get(relationship_model.source_class_id)
            target_id = id_by_external_ref.get(relationship_model.target_class_id)
            if source_id and target_id:
                metadata_json = dict(relationship_model.metadata_json)
                association_class_id = metadata_json.get("association_class_id")
                if association_class_id in id_by_external_ref:
                    metadata_json["association_class_id"] = str(id_by_external_ref[association_class_id])
                self.uml.add_relationship(
                    UmlRelationship(
                        diagram_id=diagram.id,
                        source_class_id=source_id,
                        target_class_id=target_id,
                        relationship_type=relationship_model.relationship_type,
                        source_cardinality=relationship_model.source_cardinality,
                        target_cardinality=relationship_model.target_cardinality,
                        direction=relationship_model.direction,
                        label=relationship_model.label,
                        metadata_json=metadata_json,
                    )
                )
