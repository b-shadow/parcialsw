from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.modelado_uml.engine.internal_model import (
    UmlAttributeModel,
    UmlClassModel,
    UmlDiagramModel,
    UmlMethodModel,
    UmlParameterModel,
    UmlRelationshipModel,
    UmlVisualModel,
)
from app.modules.modelado_uml.models import (
    UmlAttribute,
    UmlClass,
    UmlDiagram,
    UmlMethod,
    UmlMethodSpecification,
    UmlParameter,
    UmlRelationship,
    UmlVisualElement,
    XmiExchange,
)
from app.modules.modelado_uml.services.active_diagram_store import ActiveUmlDocumentStore

CACHE_KEY = "mongo_uml_repository"
DIRTY_KEY = "mongo_uml_dirty_diagrams"


class MongoUmlRepository:
    """Compatibility repository whose UML aggregate is stored only in MongoDB.

    SQL keeps the diagram registry and operational records. Transient SQLAlchemy
    objects are used as adapters so the existing application services retain
    their public contracts while no UML content row is read or written.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.documents = ActiveUmlDocumentStore()
        self.cache: dict[UUID, dict] = db.info.setdefault(CACHE_KEY, {})

    def add_diagram(self, diagram: UmlDiagram) -> UmlDiagram:
        self.db.add(diagram)
        self.db.flush()
        self.db.refresh(diagram)
        self._empty(diagram)
        self._dirty(diagram.id)
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

    def delete_diagram(self, diagram: UmlDiagram) -> None:
        self.cache.pop(diagram.id, None)
        self.db.delete(diagram)

    def add_class(self, item: UmlClass) -> UmlClass:
        self._identity(item)
        state = self._state(item.diagram_id)
        item.attributes = list(item.attributes or [])
        item.methods = list(item.methods or [])
        state["classes"][item.id] = item
        self._dirty(item.diagram_id)
        return item

    def get_class(self, class_id: UUID) -> UmlClass | None:
        return self._find("classes", class_id)

    def list_classes(self, diagram_id: UUID) -> list[UmlClass]:
        return sorted(self._state(diagram_id)["classes"].values(), key=lambda item: item.name)

    def delete_class(self, item: UmlClass) -> None:
        state = self._state(item.diagram_id)
        state["classes"].pop(item.id, None)
        for relationship in list(state["relationships"].values()):
            if item.id in {relationship.source_class_id, relationship.target_class_id}:
                state["relationships"].pop(relationship.id, None)
        state["visuals"].pop(("class", item.id), None)
        self._dirty(item.diagram_id)

    def delete_classes_by_diagram(self, diagram_id: UUID) -> None:
        state = self._state(diagram_id)
        state["classes"].clear()
        state["relationships"].clear()
        state["visuals"].clear()
        self._dirty(diagram_id)

    def add_attribute(self, item: UmlAttribute) -> UmlAttribute:
        self._identity(item)
        owner = self.get_class(item.class_id)
        if owner is None:
            raise ValueError("UML class does not exist")
        owner.attributes.append(item)
        self._dirty(owner.diagram_id)
        return item

    def get_attribute(self, attribute_id: UUID) -> UmlAttribute | None:
        for state in self.cache.values():
            for owner in state["classes"].values():
                for item in owner.attributes:
                    if item.id == attribute_id:
                        return item
        if self._all_loaded():
            return None
        self._load_all_registry_diagrams()
        return self.get_attribute(attribute_id)

    def delete_attribute(self, item: UmlAttribute) -> None:
        owner = self.get_class(item.class_id)
        if owner:
            owner.attributes = [value for value in owner.attributes if value.id != item.id]
            self._dirty(owner.diagram_id)

    def add_method(self, item: UmlMethod) -> UmlMethod:
        self._identity(item)
        owner = self.get_class(item.class_id)
        if owner is None:
            raise ValueError("UML class does not exist")
        item.parameters = list(item.parameters or [])
        owner.methods.append(item)
        self._dirty(owner.diagram_id)
        return item

    def get_method(self, method_id: UUID) -> UmlMethod | None:
        for state in self.cache.values():
            for owner in state["classes"].values():
                for item in owner.methods:
                    if item.id == method_id:
                        return item
        if self._all_loaded():
            return None
        self._load_all_registry_diagrams()
        return self.get_method(method_id)

    def get_method_specification(self, method_id: UUID):
        method = self.get_method(method_id)
        return method.specification if method else None

    def get_method_specification_for_update(self, method_id: UUID):
        return self.get_method_specification(method_id)

    def add_method_specification(self, item: UmlMethodSpecification):
        self._identity(item)
        method = self.get_method(item.method_id)
        if method is None:
            raise ValueError("UML method does not exist")
        method.specification = item
        owner = self.get_class(method.class_id)
        self._dirty(owner.diagram_id)
        return item

    def delete_method_specification(self, item: UmlMethodSpecification) -> None:
        method = self.get_method(item.method_id)
        if method:
            method.specification = None
            owner = self.get_class(method.class_id)
            self._dirty(owner.diagram_id)

    def delete_method(self, item: UmlMethod) -> None:
        owner = self.get_class(item.class_id)
        if owner:
            owner.methods = [value for value in owner.methods if value.id != item.id]
            self._dirty(owner.diagram_id)

    def add_parameter(self, item: UmlParameter) -> UmlParameter:
        self._identity(item)
        method = self.get_method(item.method_id)
        if method is None:
            raise ValueError("UML method does not exist")
        method.parameters.append(item)
        owner = self.get_class(method.class_id)
        self._dirty(owner.diagram_id)
        return item

    def get_parameter(self, parameter_id: UUID) -> UmlParameter | None:
        for state in self.cache.values():
            for owner in state["classes"].values():
                for method in owner.methods:
                    for item in method.parameters:
                        if item.id == parameter_id:
                            return item
        if self._all_loaded():
            return None
        self._load_all_registry_diagrams()
        return self.get_parameter(parameter_id)

    def delete_parameter(self, item: UmlParameter) -> None:
        method = self.get_method(item.method_id)
        if method:
            method.parameters = [value for value in method.parameters if value.id != item.id]
            owner = self.get_class(method.class_id)
            self._dirty(owner.diagram_id)

    def add_relationship(self, item: UmlRelationship) -> UmlRelationship:
        self._identity(item)
        self._state(item.diagram_id)["relationships"][item.id] = item
        self._dirty(item.diagram_id)
        return item

    def list_relationships(self, diagram_id: UUID) -> list[UmlRelationship]:
        return list(self._state(diagram_id)["relationships"].values())

    def list_relationships_for_class(self, class_id: UUID) -> list[UmlRelationship]:
        owner = self.get_class(class_id)
        if owner is None:
            return []
        return [
            item
            for item in self.list_relationships(owner.diagram_id)
            if (
                class_id in {item.source_class_id, item.target_class_id}
                or str(item.metadata_json.get("association_class_id")) == str(class_id)
            )
        ]

    def get_relationship(self, relationship_id: UUID) -> UmlRelationship | None:
        return self._find("relationships", relationship_id)

    def delete_relationship(self, item: UmlRelationship) -> None:
        state = self._state(item.diagram_id)
        state["relationships"].pop(item.id, None)
        state["visuals"].pop(("relationship", item.id), None)
        self._dirty(item.diagram_id)

    def delete_relationships_by_diagram(self, diagram_id: UUID) -> None:
        state = self._state(diagram_id)
        state["relationships"].clear()
        for key in [key for key in state["visuals"] if key[0] == "relationship"]:
            state["visuals"].pop(key)
        self._dirty(diagram_id)

    def add_visual_element(self, item: UmlVisualElement) -> UmlVisualElement:
        self._identity(item)
        self._state(item.diagram_id)["visuals"][(item.element_type, item.element_id)] = item
        self._dirty(item.diagram_id)
        return item

    def get_visual_element(self, diagram_id, element_type, element_id):
        return self._state(diagram_id)["visuals"].get((element_type, element_id))

    def list_visual_elements(self, diagram_id: UUID) -> list[UmlVisualElement]:
        return list(self._state(diagram_id)["visuals"].values())

    def delete_visual_elements_by_diagram(self, diagram_id: UUID) -> None:
        self._state(diagram_id)["visuals"].clear()
        self._dirty(diagram_id)

    def delete_visual_element(self, diagram_id, element_type, element_id) -> None:
        self._state(diagram_id)["visuals"].pop((element_type, element_id), None)
        self._dirty(diagram_id)

    def add_xmi_exchange(self, exchange: XmiExchange) -> XmiExchange:
        self.db.add(exchange)
        self.db.flush()
        self.db.refresh(exchange)
        return exchange

    def delete_xmi_exchanges_by_diagram(self, diagram_id: UUID) -> None:
        for item in self.db.scalars(
            select(XmiExchange).where(XmiExchange.diagram_id == diagram_id)
        ):
            self.db.delete(item)

    def model(self, diagram: UmlDiagram) -> UmlDiagramModel:
        state = self._state(diagram.id)
        visuals = state["visuals"]
        return UmlDiagramModel(
            id=str(diagram.id),
            project_id=str(diagram.project_id),
            name=diagram.name,
            diagram_type=diagram.diagram_type,
            status=diagram.status,
            current_version=diagram.current_version,
            description=diagram.description,
            metadata_json=diagram.metadata_json,
            classes=[
                self._class_model(item, visuals.get(("class", item.id)))
                for item in state["classes"].values()
            ],
            relationships=[
                UmlRelationshipModel(
                    id=str(item.id),
                    source_class_id=str(item.source_class_id),
                    target_class_id=str(item.target_class_id),
                    relationship_type=item.relationship_type,
                    source_cardinality=item.source_cardinality,
                    target_cardinality=item.target_cardinality,
                    direction=item.direction,
                    label=item.label,
                    metadata_json=item.metadata_json,
                )
                for item in state["relationships"].values()
            ],
        )

    def _state(self, diagram_id: UUID) -> dict:
        if diagram_id not in self.cache:
            diagram = self.get_diagram(diagram_id)
            if diagram is None:
                raise ValueError("UML diagram does not exist")
            document = self.documents.get(diagram_id)
            self.cache[diagram_id] = self._inflate(
                UmlDiagramModel.model_validate(document.content) if document else None,
                diagram,
            )
        return self.cache[diagram_id]

    def _empty(self, diagram: UmlDiagram) -> dict:
        state = {"diagram": diagram, "classes": {}, "relationships": {}, "visuals": {}}
        self.cache[diagram.id] = state
        return state

    def _inflate(self, model: UmlDiagramModel | None, diagram: UmlDiagram) -> dict:
        state = self._empty(diagram)
        if model is None:
            return state
        for source in model.classes:
            owner = UmlClass(
                id=UUID(source.id),
                diagram_id=diagram.id,
                name=source.name,
                visibility=source.visibility,
                element_type=source.element_type,
                stereotype=source.stereotype,
                description=source.description,
                metadata_json=source.metadata_json,
            )
            owner.attributes = [
                UmlAttribute(
                    id=UUID(item.id),
                    class_id=owner.id,
                    name=item.name,
                    data_type=item.data_type,
                    visibility=item.visibility,
                    initial_value=item.initial_value,
                    multiplicity=item.multiplicity,
                    is_required=item.is_required,
                    order_index=item.order_index,
                    constraints=item.constraints,
                )
                for item in source.attributes
            ]
            owner.methods = []
            for item in source.methods:
                method = UmlMethod(
                    id=UUID(item.id),
                    class_id=owner.id,
                    name=item.name,
                    return_type=item.return_type,
                    visibility=item.visibility,
                    order_index=item.order_index,
                    metadata_json=item.metadata_json,
                )
                method.parameters = [
                    UmlParameter(
                        id=UUID(value.id),
                        method_id=method.id,
                        name=value.name,
                        data_type=value.data_type,
                        default_value=value.default_value,
                        order_index=value.order_index,
                    )
                    for value in item.parameters
                ]
                method.specification = self._inflate_specification(method.id, item.specification)
                owner.methods.append(method)
            state["classes"][owner.id] = owner
            state["visuals"][("class", owner.id)] = UmlVisualElement(
                id=UUID(source.visual.id) if source.visual.id else uuid4(),
                diagram_id=diagram.id,
                element_type="class",
                element_id=owner.id,
                position_x=source.visual.x,
                position_y=source.visual.y,
                width=source.visual.width,
                height=source.visual.height,
                style=source.visual.style,
            )
        for source in model.relationships:
            item = UmlRelationship(
                id=UUID(source.id),
                diagram_id=diagram.id,
                source_class_id=UUID(source.source_class_id),
                target_class_id=UUID(source.target_class_id),
                relationship_type=source.relationship_type,
                source_cardinality=source.source_cardinality,
                target_cardinality=source.target_cardinality,
                direction=source.direction,
                label=source.label,
                metadata_json=source.metadata_json,
            )
            state["relationships"][item.id] = item
        return state

    @staticmethod
    def _inflate_specification(method_id: UUID, values: dict | None):
        if not values:
            return None
        fields = {
            key: value
            for key, value in values.items()
            if key in UmlMethodSpecification.__table__.columns
            and key not in {"id", "method_id", "created_at", "updated_at"}
        }
        return UmlMethodSpecification(
            id=UUID(values["id"]) if values.get("id") else uuid4(),
            method_id=method_id,
            **fields,
        )

    @staticmethod
    def _class_model(item: UmlClass, visual: UmlVisualElement | None) -> UmlClassModel:
        return UmlClassModel(
            id=str(item.id),
            name=item.name,
            visibility=item.visibility,
            element_type=item.element_type,
            stereotype=item.stereotype,
            description=item.description,
            metadata_json=item.metadata_json,
            attributes=[
                UmlAttributeModel(
                    id=str(value.id),
                    name=value.name,
                    data_type=value.data_type,
                    visibility=value.visibility,
                    initial_value=value.initial_value,
                    multiplicity=value.multiplicity,
                    is_required=value.is_required,
                    order_index=value.order_index,
                    constraints=value.constraints,
                )
                for value in item.attributes
            ],
            methods=[
                UmlMethodModel(
                    id=str(value.id),
                    name=value.name,
                    return_type=value.return_type,
                    visibility=value.visibility,
                    order_index=value.order_index,
                    metadata_json=value.metadata_json,
                    parameters=[
                        UmlParameterModel(
                            id=str(parameter.id),
                            name=parameter.name,
                            data_type=parameter.data_type,
                            default_value=parameter.default_value,
                            order_index=parameter.order_index,
                        )
                        for parameter in value.parameters
                    ],
                    specification=(
                    {
                            key: getattr(value.specification, key)
                            for key in (
                                "description",
                                "operation_kind",
                                "exposure",
                                "preconditions",
                                "postconditions",
                                "business_rules",
                                "validations",
                                "side_effects",
                                "required_permissions",
                                "related_entities",
                                "backend_contract",
                                "frontend_contract",
                                "schema_version",
                                "revision",
                            )
                    }
                        if value.specification
                        else None
                    ),
                )
                for value in item.methods
            ],
            visual=UmlVisualModel(
                id=str(visual.id) if visual else None,
                x=visual.position_x if visual else 0,
                y=visual.position_y if visual else 0,
                width=visual.width if visual else None,
                height=visual.height if visual else None,
                style=visual.style if visual else {},
            ),
        )

    def _find(self, bucket: str, item_id: UUID):
        for state in self.cache.values():
            item = state[bucket].get(item_id)
            if item is not None:
                return item
        self._load_all_registry_diagrams()
        for state in self.cache.values():
            item = state[bucket].get(item_id)
            if item is not None:
                return item
        return None

    def _load_all_registry_diagrams(self) -> None:
        for diagram in self.db.scalars(select(UmlDiagram)):
            if diagram.id not in self.cache:
                self._state(diagram.id)
        self.db.info["mongo_uml_all_loaded"] = True

    def _all_loaded(self) -> bool:
        return bool(self.db.info.get("mongo_uml_all_loaded"))

    def _dirty(self, diagram_id: UUID) -> None:
        self.db.info.setdefault(DIRTY_KEY, set()).add(diagram_id)

    @staticmethod
    def _identity(item) -> None:
        if item.id is None:
            item.id = uuid4()
        if getattr(item, "created_at", None) is None:
            item.created_at = datetime.now(UTC)
        item.updated_at = datetime.now(UTC)
