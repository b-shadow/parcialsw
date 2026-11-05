from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

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


class RepositorioUML:
    def __init__(self, db: Session) -> None:
        self.db = db

    def agregar_diagrama(self, diagram: DiagramaUML) -> DiagramaUML:
        self.db.add(diagram)
        self.db.flush()
        self.db.refresh(diagram)
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
        self.db.delete(diagram)

    def agregar_clase(self, uml_class: ClaseUML) -> ClaseUML:
        self.db.add(uml_class)
        self.db.flush()
        self.db.refresh(uml_class)
        return uml_class

    def obtener_clase(self, class_id: UUID) -> ClaseUML | None:
        return self.db.get(ClaseUML, class_id)

    def listar_clases(self, diagram_id: UUID) -> list[ClaseUML]:
        return list(
            self.db.scalars(
                select(ClaseUML).where(ClaseUML.diagram_id == diagram_id).order_by(ClaseUML.name)
            )
        )

    def eliminar_clase(self, uml_class: ClaseUML) -> None:
        self.db.delete(uml_class)

    def eliminar_clases_por_diagrama(self, diagram_id: UUID) -> None:
        for uml_class in self.listar_clases(diagram_id):
            self.db.delete(uml_class)

    def agregar_atributo(self, attribute: AtributoUML) -> AtributoUML:
        self.db.add(attribute)
        self.db.flush()
        self.db.refresh(attribute)
        return attribute

    def obtener_atributo(self, attribute_id: UUID) -> AtributoUML | None:
        return self.db.get(AtributoUML, attribute_id)

    def eliminar_atributo(self, attribute: AtributoUML) -> None:
        self.db.delete(attribute)

    def agregar_metodo(self, method: MetodoUML) -> MetodoUML:
        self.db.add(method)
        self.db.flush()
        self.db.refresh(method)
        return method

    def obtener_metodo(self, method_id: UUID) -> MetodoUML | None:
        return self.db.get(MetodoUML, method_id)

    def obtener_especificacion_metodo(self, method_id: UUID) -> EspecificacionMetodoUML | None:
        return self.db.scalar(
            select(EspecificacionMetodoUML).where(
                EspecificacionMetodoUML.method_id == method_id
            )
        )

    def obtener_especificacion_metodo_para_actualizar(
        self, method_id: UUID
    ) -> EspecificacionMetodoUML | None:
        return self.db.scalar(
            select(EspecificacionMetodoUML)
            .where(EspecificacionMetodoUML.method_id == method_id)
            .with_for_update()
        )

    def agregar_especificacion_metodo(
        self, specification: EspecificacionMetodoUML
    ) -> EspecificacionMetodoUML:
        self.db.add(specification)
        self.db.flush()
        self.db.refresh(specification)
        return specification

    def eliminar_especificacion_metodo(self, specification: EspecificacionMetodoUML) -> None:
        self.db.delete(specification)

    def eliminar_metodo(self, method: MetodoUML) -> None:
        self.db.delete(method)

    def agregar_parametro(self, parameter: ParametroUML) -> ParametroUML:
        self.db.add(parameter)
        self.db.flush()
        self.db.refresh(parameter)
        return parameter

    def obtener_parametro(self, parameter_id: UUID) -> ParametroUML | None:
        return self.db.get(ParametroUML, parameter_id)

    def eliminar_parametro(self, parameter: ParametroUML) -> None:
        self.db.delete(parameter)

    def agregar_relacion(self, relationship: RelacionUML) -> RelacionUML:
        self.db.add(relationship)
        self.db.flush()
        self.db.refresh(relationship)
        return relationship

    def listar_relaciones(self, diagram_id: UUID) -> list[RelacionUML]:
        return list(
            self.db.scalars(
                select(RelacionUML).where(RelacionUML.diagram_id == diagram_id)
            )
        )

    def listar_relaciones_clase(self, class_id: UUID) -> list[RelacionUML]:
        uml_class = self.obtener_clase(class_id)
        if uml_class is None:
            return []
        relationships = self.listar_relaciones(uml_class.diagram_id)
        return [
            relationship
            for relationship in relationships
            if relationship.source_class_id == class_id
            or relationship.target_class_id == class_id
            or str(relationship.metadata_json.get("association_class_id")) == str(class_id)
        ]

    def obtener_relacion(self, relationship_id: UUID) -> RelacionUML | None:
        return self.db.get(RelacionUML, relationship_id)

    def eliminar_relacion(self, relationship: RelacionUML) -> None:
        self.db.delete(relationship)

    def eliminar_relaciones_por_diagrama(self, diagram_id: UUID) -> None:
        for relationship in self.listar_relaciones(diagram_id):
            self.db.delete(relationship)

    def agregar_elemento_visual(self, visual: ElementoVisualUML) -> ElementoVisualUML:
        self.db.add(visual)
        self.db.flush()
        self.db.refresh(visual)
        return visual

    def obtener_elemento_visual(
        self, diagram_id: UUID, element_type: str, element_id: UUID
    ) -> ElementoVisualUML | None:
        return self.db.scalar(
            select(ElementoVisualUML).where(
                ElementoVisualUML.diagram_id == diagram_id,
                ElementoVisualUML.element_type == element_type,
                ElementoVisualUML.element_id == element_id,
            )
        )

    def listar_elementos_visuales(self, diagram_id: UUID) -> list[ElementoVisualUML]:
        return list(
            self.db.scalars(select(ElementoVisualUML).where(ElementoVisualUML.diagram_id == diagram_id))
        )

    def eliminar_elementos_visuales_por_diagrama(self, diagram_id: UUID) -> None:
        for visual in self.listar_elementos_visuales(diagram_id):
            self.db.delete(visual)

    def eliminar_elemento_visual(
        self, diagram_id: UUID, element_type: str, element_id: UUID
    ) -> None:
        visual = self.obtener_elemento_visual(diagram_id, element_type, element_id)
        if visual is not None:
            self.db.delete(visual)

    def agregar_intercambio_xmi(self, exchange: IntercambioXMI) -> IntercambioXMI:
        self.db.add(exchange)
        self.db.flush()
        self.db.refresh(exchange)
        return exchange

    def eliminar_intercambios_xmi_por_diagrama(self, diagram_id: UUID) -> None:
        exchanges = self.db.scalars(select(IntercambioXMI).where(IntercambioXMI.diagram_id == diagram_id))
        for exchange in exchanges:
            self.db.delete(exchange)
