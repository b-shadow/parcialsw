from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

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


class UmlRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add_diagram(self, diagram: UmlDiagram) -> UmlDiagram:
        self.db.add(diagram)
        self.db.flush()
        self.db.refresh(diagram)
        return diagram

    def get_diagram(self, diagram_id: UUID) -> UmlDiagram | None:
        return self.db.get(UmlDiagram, diagram_id)

    def list_diagrams_by_project(self, project_id: UUID) -> list[UmlDiagram]:
        return list(
            self.db.scalars(
                select(UmlDiagram)
                .where(UmlDiagram.project_id == project_id)
                .order_by(UmlDiagram.created_at.desc())
            )
        )

    def add_class(self, uml_class: UmlClass) -> UmlClass:
        self.db.add(uml_class)
        self.db.flush()
        self.db.refresh(uml_class)
        return uml_class

    def get_class(self, class_id: UUID) -> UmlClass | None:
        return self.db.get(UmlClass, class_id)

    def list_classes(self, diagram_id: UUID) -> list[UmlClass]:
        return list(
            self.db.scalars(
                select(UmlClass).where(UmlClass.diagram_id == diagram_id).order_by(UmlClass.name)
            )
        )

    def delete_class(self, uml_class: UmlClass) -> None:
        self.db.delete(uml_class)

    def add_attribute(self, attribute: UmlAttribute) -> UmlAttribute:
        self.db.add(attribute)
        self.db.flush()
        self.db.refresh(attribute)
        return attribute

    def add_method(self, method: UmlMethod) -> UmlMethod:
        self.db.add(method)
        self.db.flush()
        self.db.refresh(method)
        return method

    def get_method(self, method_id: UUID) -> UmlMethod | None:
        return self.db.get(UmlMethod, method_id)

    def add_parameter(self, parameter: UmlParameter) -> UmlParameter:
        self.db.add(parameter)
        self.db.flush()
        self.db.refresh(parameter)
        return parameter

    def add_relationship(self, relationship: UmlRelationship) -> UmlRelationship:
        self.db.add(relationship)
        self.db.flush()
        self.db.refresh(relationship)
        return relationship

    def list_relationships(self, diagram_id: UUID) -> list[UmlRelationship]:
        return list(
            self.db.scalars(
                select(UmlRelationship).where(UmlRelationship.diagram_id == diagram_id)
            )
        )

    def list_relationships_for_class(self, class_id: UUID) -> list[UmlRelationship]:
        return list(
            self.db.scalars(
                select(UmlRelationship).where(
                    or_(
                        UmlRelationship.source_class_id == class_id,
                        UmlRelationship.target_class_id == class_id,
                    )
                )
            )
        )

    def get_relationship(self, relationship_id: UUID) -> UmlRelationship | None:
        return self.db.get(UmlRelationship, relationship_id)

    def delete_relationship(self, relationship: UmlRelationship) -> None:
        self.db.delete(relationship)

    def add_visual_element(self, visual: UmlVisualElement) -> UmlVisualElement:
        self.db.add(visual)
        self.db.flush()
        self.db.refresh(visual)
        return visual

    def get_visual_element(
        self, diagram_id: UUID, element_type: str, element_id: UUID
    ) -> UmlVisualElement | None:
        return self.db.scalar(
            select(UmlVisualElement).where(
                UmlVisualElement.diagram_id == diagram_id,
                UmlVisualElement.element_type == element_type,
                UmlVisualElement.element_id == element_id,
            )
        )

    def list_visual_elements(self, diagram_id: UUID) -> list[UmlVisualElement]:
        return list(
            self.db.scalars(select(UmlVisualElement).where(UmlVisualElement.diagram_id == diagram_id))
        )

    def add_xmi_exchange(self, exchange: XmiExchange) -> XmiExchange:
        self.db.add(exchange)
        self.db.flush()
        self.db.refresh(exchange)
        return exchange
