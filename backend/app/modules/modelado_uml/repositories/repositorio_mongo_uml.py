from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException
from pydantic import ValidationError
from pymongo.errors import PyMongoError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.nosql.errores import ErrorMongoNoDisponible
from app.modules.modelado_uml.engine.modelo_interno import (
    ModeloAtributoUML,
    ModeloClaseUML,
    ModeloDiagramaUML,
    ModeloMetodoUML,
    ModeloParametroUML,
    ModeloRelacionUML,
    ModeloVisualUML,
)
from app.modules.modelado_uml.models import (
    AtributoUML,
    ClaseUML,
    DiagramaUML,
    ElementoVisualUML,
    EspecificacionMetodoUML,
    IntercambioXMI,
    MetodoUML,
    ParametroUML,
    RelacionUML,
)
from app.modules.modelado_uml.services.almacen_diagrama_activo import AlmacenDocumentosUMLActivo

CACHE_KEY = "mongo_uml_repository"
DIRTY_KEY = "mongo_uml_dirty_diagrams"


class RepositorioMongoUML:
    """Compatibility repository whose UML aggregate is stored only in MongoDB.

    SQL keeps the diagram registry and operational records. Transient SQLAlchemy
    objects are used as adapters so the existing application services retain
    their public contracts while no UML content row is read or written.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.documents = AlmacenDocumentosUMLActivo()
        self.cache: dict[UUID, dict] = db.info.setdefault(CACHE_KEY, {})

    def agregar_diagrama(self, diagram: DiagramaUML) -> DiagramaUML:
        self.db.add(diagram)
        self.db.flush()
        self.db.refresh(diagram)
        self._vacio(diagram)
        self._modificados(diagram.id)
        return diagram

    def obtener_diagrama(self, diagram_id: UUID) -> DiagramaUML | None:
        return self.db.get(DiagramaUML, diagram_id)

    def listar_diagramas_por_proyecto(self, project_id: UUID) -> list[DiagramaUML]:
        return list(
            self.db.scalars(
                select(DiagramaUML)
                .where(DiagramaUML.project_id == project_id)
                .order_by(DiagramaUML.created_at.desc())
            )
        )

    def eliminar_diagrama(self, diagram: DiagramaUML) -> None:
        self.cache.pop(diagram.id, None)
        self.db.delete(diagram)

    def agregar_clase(self, item: ClaseUML) -> ClaseUML:
        self._identidad(item)
        state = self._estado(item.diagram_id)
        item.attributes = list(item.attributes or [])
        item.methods = list(item.methods or [])
        state["classes"][item.id] = item
        self._modificados(item.diagram_id)
        return item

    def obtener_clase(self, class_id: UUID) -> ClaseUML | None:
        return self._buscar("classes", class_id)

    def listar_clases(self, diagram_id: UUID) -> list[ClaseUML]:
        return sorted(self._estado(diagram_id)["classes"].values(), key=lambda item: item.name)

    def eliminar_clase(self, item: ClaseUML) -> None:
        state = self._estado(item.diagram_id)
        state["classes"].pop(item.id, None)
        for relationship in list(state["relationships"].values()):
            if item.id in {relationship.source_class_id, relationship.target_class_id}:
                state["relationships"].pop(relationship.id, None)
        state["visuals"].pop(("class", item.id), None)
        self._modificados(item.diagram_id)

    def eliminar_clases_por_diagrama(self, diagram_id: UUID) -> None:
        state = self._estado(diagram_id)
        state["classes"].clear()
        state["relationships"].clear()
        state["visuals"].clear()
        self._modificados(diagram_id)

    def agregar_atributo(self, item: AtributoUML) -> AtributoUML:
        self._identidad(item)
        owner = self.obtener_clase(item.class_id)
        if owner is None:
            raise ValueError("UML class does not exist")
        owner.attributes.append(item)
        self._modificados(owner.diagram_id)
        return item

    def obtener_atributo(self, attribute_id: UUID) -> AtributoUML | None:
        for state in self.cache.values():
            for owner in state["classes"].values():
                for item in owner.attributes:
                    if item.id == attribute_id:
                        return item
        if self._todos_cargados():
            return None
        self._cargar_todos_diagramas_registro()
        return self.obtener_atributo(attribute_id)

    def eliminar_atributo(self, item: AtributoUML) -> None:
        owner = self.obtener_clase(item.class_id)
        if owner:
            owner.attributes = [value for value in owner.attributes if value.id != item.id]
            self._modificados(owner.diagram_id)

    def agregar_metodo(self, item: MetodoUML) -> MetodoUML:
        self._identidad(item)
        owner = self.obtener_clase(item.class_id)
        if owner is None:
            raise ValueError("UML class does not exist")
        item.parameters = list(item.parameters or [])
        owner.methods.append(item)
        self._modificados(owner.diagram_id)
        return item

    def obtener_metodo(self, method_id: UUID) -> MetodoUML | None:
        for state in self.cache.values():
            for owner in state["classes"].values():
                for item in owner.methods:
                    if item.id == method_id:
                        return item
        if self._todos_cargados():
            return None
        self._cargar_todos_diagramas_registro()
        return self.obtener_metodo(method_id)

    def obtener_especificacion_metodo(self, method_id: UUID):
        method = self.obtener_metodo(method_id)
        return method.specification if method else None

    def obtener_especificacion_metodo_para_actualizar(self, method_id: UUID):
        return self.obtener_especificacion_metodo(method_id)

    def agregar_especificacion_metodo(self, item: EspecificacionMetodoUML):
        self._identidad(item)
        method = self.obtener_metodo(item.method_id)
        if method is None:
            raise ValueError("UML method does not exist")
        method.specification = item
        owner = self.obtener_clase(method.class_id)
        self._modificados(owner.diagram_id)
        return item

    def eliminar_especificacion_metodo(self, item: EspecificacionMetodoUML) -> None:
        method = self.obtener_metodo(item.method_id)
        if method:
            method.specification = None
            owner = self.obtener_clase(method.class_id)
            self._modificados(owner.diagram_id)

    def eliminar_metodo(self, item: MetodoUML) -> None:
        owner = self.obtener_clase(item.class_id)
        if owner:
            owner.methods = [value for value in owner.methods if value.id != item.id]
            self._modificados(owner.diagram_id)

    def agregar_parametro(self, item: ParametroUML) -> ParametroUML:
        self._identidad(item)
        method = self.obtener_metodo(item.method_id)
        if method is None:
            raise ValueError("UML method does not exist")
        method.parameters.append(item)
        owner = self.obtener_clase(method.class_id)
        self._modificados(owner.diagram_id)
        return item

    def obtener_parametro(self, parameter_id: UUID) -> ParametroUML | None:
        for state in self.cache.values():
            for owner in state["classes"].values():
                for method in owner.methods:
                    for item in method.parameters:
                        if item.id == parameter_id:
                            return item
        if self._todos_cargados():
            return None
        self._cargar_todos_diagramas_registro()
        return self.obtener_parametro(parameter_id)

    def eliminar_parametro(self, item: ParametroUML) -> None:
        method = self.obtener_metodo(item.method_id)
        if method:
            method.parameters = [value for value in method.parameters if value.id != item.id]
            owner = self.obtener_clase(method.class_id)
            self._modificados(owner.diagram_id)

    def agregar_relacion(self, item: RelacionUML) -> RelacionUML:
        self._identidad(item)
        self._estado(item.diagram_id)["relationships"][item.id] = item
        self._modificados(item.diagram_id)
        return item

    def listar_relaciones(self, diagram_id: UUID) -> list[RelacionUML]:
        return list(self._estado(diagram_id)["relationships"].values())

    def listar_relaciones_clase(self, class_id: UUID) -> list[RelacionUML]:
        owner = self.obtener_clase(class_id)
        if owner is None:
            return []
        return [
            item
            for item in self.listar_relaciones(owner.diagram_id)
            if (
                class_id in {item.source_class_id, item.target_class_id}
                or str(item.metadata_json.get("association_class_id")) == str(class_id)
            )
        ]

    def obtener_relacion(self, relationship_id: UUID) -> RelacionUML | None:
        return self._buscar("relationships", relationship_id)

    def eliminar_relacion(self, item: RelacionUML) -> None:
        state = self._estado(item.diagram_id)
        state["relationships"].pop(item.id, None)
        state["visuals"].pop(("relationship", item.id), None)
        self._modificados(item.diagram_id)

    def eliminar_relaciones_por_diagrama(self, diagram_id: UUID) -> None:
        state = self._estado(diagram_id)
        state["relationships"].clear()
        for key in [key for key in state["visuals"] if key[0] == "relationship"]:
            state["visuals"].pop(key)
        self._modificados(diagram_id)

    def agregar_elemento_visual(self, item: ElementoVisualUML) -> ElementoVisualUML:
        self._identidad(item)
        self._estado(item.diagram_id)["visuals"][(item.element_type, item.element_id)] = item
        self._modificados(item.diagram_id)
        return item

    def obtener_elemento_visual(self, diagram_id, element_type, element_id):
        return self._estado(diagram_id)["visuals"].get((element_type, element_id))

    def listar_elementos_visuales(self, diagram_id: UUID) -> list[ElementoVisualUML]:
        return list(self._estado(diagram_id)["visuals"].values())

    def eliminar_elementos_visuales_por_diagrama(self, diagram_id: UUID) -> None:
        self._estado(diagram_id)["visuals"].clear()
        self._modificados(diagram_id)

    def eliminar_elemento_visual(self, diagram_id, element_type, element_id) -> None:
        self._estado(diagram_id)["visuals"].pop((element_type, element_id), None)
        self._modificados(diagram_id)

    def agregar_intercambio_xmi(self, exchange: IntercambioXMI) -> IntercambioXMI:
        self.db.add(exchange)
        self.db.flush()
        self.db.refresh(exchange)
        return exchange

    def eliminar_intercambios_xmi_por_diagrama(self, diagram_id: UUID) -> None:
        for item in self.db.scalars(
            select(IntercambioXMI).where(IntercambioXMI.diagram_id == diagram_id)
        ):
            self.db.delete(item)

    def model(self, diagram: DiagramaUML) -> ModeloDiagramaUML:
        state = self._estado(diagram.id)
        visuals = state["visuals"]
        return ModeloDiagramaUML(
            id=str(diagram.id),
            project_id=str(diagram.project_id),
            name=diagram.name,
            diagram_type=diagram.diagram_type,
            status=diagram.status,
            current_version=diagram.current_version,
            description=diagram.description,
            metadata_json=diagram.metadata_json,
            classes=[
                self._modelo_clase(item, visuals.get(("class", item.id)))
                for item in state["classes"].values()
            ],
            relationships=[
                ModeloRelacionUML(
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

    def _estado(self, diagram_id: UUID) -> dict:
        if diagram_id not in self.cache:
            diagram = self.obtener_diagrama(diagram_id)
            if diagram is None:
                raise ValueError("UML diagram does not exist")
            try:
                document = self.documents.get(diagram_id)
            except (ErrorMongoNoDisponible, PyMongoError) as exc:
                raise HTTPException(
                    status_code=503,
                    detail={
                        "code": "UML_DOCUMENT_UNAVAILABLE",
                        "message": "No se pudo consultar el contenido del diagrama en MongoDB",
                    },
                ) from exc
            if document is None:
                raise HTTPException(
                    status_code=503,
                    detail={
                        "code": "UML_DOCUMENT_MISSING",
                        "message": "El contenido del diagrama no esta disponible en MongoDB",
                    },
                )
            try:
                model = ModeloDiagramaUML.model_validate(document.content)
            except ValidationError as exc:
                raise HTTPException(
                    status_code=503,
                    detail={
                        "code": "UML_DOCUMENT_INVALID",
                        "message": "El contenido del diagrama en MongoDB no es valido",
                    },
                ) from exc
            self.cache[diagram_id] = self._reconstruir(model, diagram)
        return self.cache[diagram_id]

    def _vacio(self, diagram: DiagramaUML) -> dict:
        state = {"diagram": diagram, "classes": {}, "relationships": {}, "visuals": {}}
        self.cache[diagram.id] = state
        return state

    def _reconstruir(self, model: ModeloDiagramaUML | None, diagram: DiagramaUML) -> dict:
        state = self._vacio(diagram)
        if model is None:
            return state
        for source in model.classes:
            owner = ClaseUML(
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
                AtributoUML(
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
                method = MetodoUML(
                    id=UUID(item.id),
                    class_id=owner.id,
                    name=item.name,
                    return_type=item.return_type,
                    visibility=item.visibility,
                    order_index=item.order_index,
                    metadata_json=item.metadata_json,
                )
                method.parameters = [
                    ParametroUML(
                        id=UUID(value.id),
                        method_id=method.id,
                        name=value.name,
                        data_type=value.data_type,
                        default_value=value.default_value,
                        order_index=value.order_index,
                    )
                    for value in item.parameters
                ]
                method.specification = self._reconstruir_especificacion(method.id, item.specification)
                owner.methods.append(method)
            state["classes"][owner.id] = owner
            state["visuals"][("class", owner.id)] = ElementoVisualUML(
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
            item = RelacionUML(
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
    def _reconstruir_especificacion(method_id: UUID, values: dict | None):
        if not values:
            return None
        fields = {
            key: value
            for key, value in values.items()
            if key in EspecificacionMetodoUML.__table__.columns
            and key not in {"id", "method_id", "created_at", "updated_at"}
        }
        return EspecificacionMetodoUML(
            id=UUID(values["id"]) if values.get("id") else uuid4(),
            method_id=method_id,
            **fields,
        )

    @staticmethod
    def _modelo_clase(item: ClaseUML, visual: ElementoVisualUML | None) -> ModeloClaseUML:
        return ModeloClaseUML(
            id=str(item.id),
            name=item.name,
            visibility=item.visibility,
            element_type=item.element_type,
            stereotype=item.stereotype,
            description=item.description,
            metadata_json=item.metadata_json,
            attributes=[
                ModeloAtributoUML(
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
                ModeloMetodoUML(
                    id=str(value.id),
                    name=value.name,
                    return_type=value.return_type,
                    visibility=value.visibility,
                    order_index=value.order_index,
                    metadata_json=value.metadata_json,
                    parameters=[
                        ModeloParametroUML(
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
            visual=ModeloVisualUML(
                id=str(visual.id) if visual else None,
                x=visual.position_x if visual else 0,
                y=visual.position_y if visual else 0,
                width=visual.width if visual else None,
                height=visual.height if visual else None,
                style=(visual.style or {}) if visual else {},
            ),
        )

    def _buscar(self, bucket: str, item_id: UUID):
        for state in self.cache.values():
            item = state[bucket].get(item_id)
            if item is not None:
                return item
        self._cargar_todos_diagramas_registro()
        for state in self.cache.values():
            item = state[bucket].get(item_id)
            if item is not None:
                return item
        return None

    def _cargar_todos_diagramas_registro(self) -> None:
        for diagram in self.db.scalars(select(DiagramaUML)):
            if diagram.id not in self.cache:
                self._estado(diagram.id)
        self.db.info["mongo_uml_all_loaded"] = True

    def _todos_cargados(self) -> bool:
        return bool(self.db.info.get("mongo_uml_all_loaded"))

    def _modificados(self, diagram_id: UUID) -> None:
        self.db.info.setdefault(DIRTY_KEY, set()).add(diagram_id)

    @staticmethod
    def _identidad(item) -> None:
        if item.id is None:
            item.id = uuid4()
        if getattr(item, "created_at", None) is None:
            item.created_at = datetime.now(UTC)
        item.updated_at = datetime.now(UTC)
