"""Pruebas para validaciones del editor UML y XMI sin pérdida (V1.6)."""

from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.modelado_uml.engine.modelo_interno import (
    ModeloAtributoUML,
    ModeloClaseUML,
    ModeloDiagramaUML,
    ModeloMetodoUML,
    ModeloRelacionUML,
)
from app.modules.modelado_uml.engine.xmi import exportar_xmi, importar_xmi
from app.modules.modelado_uml.schemas.uml import (
    SolicitudCreacionAtributoUML,
    SolicitudCreacionClaseUML,
    SolicitudCreacionRelacionUML,
)
from app.modules.modelado_uml.services.servicio_uml import ServicioUML


class _DrawingImportRepository:
    def __init__(self) -> None:
        self.diagrams = []
        self.classes = []
        self.visuals = []
        self.relationships = []

    def agregar_diagrama(self, diagram):
        diagram.id = uuid4()
        self.diagrams.append(diagram)
        return diagram

    def agregar_clase(self, uml_class):
        uml_class.id = uuid4()
        self.classes.append(uml_class)
        return uml_class

    def agregar_elemento_visual(self, visual):
        visual.id = uuid4()
        self.visuals.append(visual)
        return visual

    def agregar_atributo(self, attribute):
        attribute.id = uuid4()
        return attribute

    def agregar_metodo(self, method):
        method.id = uuid4()
        return method

    def agregar_parametro(self, parameter):
        parameter.id = uuid4()
        return parameter

    def agregar_relacion(self, relationship):
        relationship.id = uuid4()
        self.relationships.append(relationship)
        return relationship


def test_class_element_type_validation_interface_ok_and_tabla_fails():
    # 201: element_type='interface' es válido
    valid_req = SolicitudCreacionClaseUML(name="Repositorio", element_type="interface")
    assert valid_req.element_type == "interface"

    # 422: element_type='tabla' es inválido
    with pytest.raises(ValidationError) as exc_info:
        SolicitudCreacionClaseUML(name="TablaInvalida", element_type="tabla")
    assert "El tipo de elemento debe ser uno de" in str(exc_info.value)


def test_attribute_visibility_validation_protected_ok_and_friend_fails():
    # 201: visibility='protected' es válido
    valid_attr = SolicitudCreacionAtributoUML(
        name="token", data_type="String", visibility="protected"
    )
    assert valid_attr.visibility == "protected"

    # 422: visibility='friend' es inválido
    with pytest.raises(ValidationError) as exc_info:
        SolicitudCreacionAtributoUML(
            name="secreto", data_type="String", visibility="friend"
        )
    assert "La visibilidad debe ser una de" in str(exc_info.value)


def test_relationship_type_dependency_and_realization_are_valid():
    src_id = uuid4()
    tgt_id = uuid4()

    rel_dep = SolicitudCreacionRelacionUML(
        source_class_id=src_id,
        target_class_id=tgt_id,
        relationship_type="dependency",
    )
    assert rel_dep.relationship_type == "dependency"

    rel_real = SolicitudCreacionRelacionUML(
        source_class_id=src_id,
        target_class_id=tgt_id,
        relationship_type="realization",
    )
    assert rel_real.relationship_type == "realization"

    with pytest.raises(ValidationError):
        SolicitudCreacionRelacionUML(
            source_class_id=src_id,
            target_class_id=tgt_id,
            relationship_type="tipo_inexistente",
        )


def test_xmi_roundtrip_preserves_composition_aggregation_inheritance_interface_enum_abstract():
    # Construir modelo con todas las variantes requeridas
    clase_interface = ModeloClaseUML(
        id="c-interface",
        name="IServicio",
        element_type="interface",
        visibility="public",
        attributes=[
            ModeloAtributoUML(name="versionApi", data_type="String", visibility="public")
        ],
        methods=[
            ModeloMetodoUML(name="ejecutar", return_type="void", visibility="public")
        ],
    )
    clase_enum = ModeloClaseUML(
        id="c-enum",
        name="EstadoOrden",
        element_type="enum",
        visibility="public",
        attributes=[
            ModeloAtributoUML(name="PENDIENTE", data_type="String", visibility="public"),
            ModeloAtributoUML(name="ENTREGADO", data_type="String", visibility="public"),
        ],
        methods=[],
    )
    clase_abstract = ModeloClaseUML(
        id="c-abstract",
        name="EntidadBase",
        element_type="abstract_class",
        visibility="public",
        attributes=[
            ModeloAtributoUML(name="id", data_type="Long", visibility="protected"),
            ModeloAtributoUML(name="activo", data_type="Boolean", visibility="package"),
        ],
        methods=[
            ModeloMetodoUML(name="validar", return_type="Boolean", visibility="protected")
        ],
    )
    clase_orden = ModeloClaseUML(
        id="c-orden",
        name="Orden",
        element_type="class",
        visibility="public",
        attributes=[
            ModeloAtributoUML(name="codigo", data_type="String", visibility="private")
        ],
        methods=[],
    )
    clase_item = ModeloClaseUML(
        id="c-item",
        name="ItemOrden",
        element_type="class",
        visibility="public",
        attributes=[
            ModeloAtributoUML(name="cantidad", data_type="Integer", visibility="private")
        ],
        methods=[],
    )
    clase_cliente = ModeloClaseUML(
        id="c-cliente",
        name="Cliente",
        element_type="class",
        visibility="public",
        attributes=[
            ModeloAtributoUML(name="nombre", data_type="String", visibility="public")
        ],
        methods=[],
    )

    relationships = [
        ModeloRelacionUML(
            id="rel-comp",
            source_class_id="Orden",
            target_class_id="ItemOrden",
            relationship_type="composition",
            source_cardinality="1",
            target_cardinality="1..*",
        ),
        ModeloRelacionUML(
            id="rel-agg",
            source_class_id="Orden",
            target_class_id="Cliente",
            relationship_type="aggregation",
            source_cardinality="0..*",
            target_cardinality="1",
        ),
        ModeloRelacionUML(
            id="rel-inh",
            source_class_id="Orden",
            target_class_id="EntidadBase",
            relationship_type="inheritance",
        ),
        ModeloRelacionUML(
            id="rel-real",
            source_class_id="Orden",
            target_class_id="IServicio",
            relationship_type="realization",
        ),
        ModeloRelacionUML(
            id="rel-dep",
            source_class_id="Orden",
            target_class_id="EstadoOrden",
            relationship_type="dependency",
        ),
    ]

    diagram = ModeloDiagramaUML(
        name="SistemaVentas",
        classes=[
            clase_interface,
            clase_enum,
            clase_abstract,
            clase_orden,
            clase_item,
            clase_cliente,
        ],
        relationships=relationships,
    )

    # Exportar e importar
    xmi_content = exportar_xmi(diagram)
    reimported = importar_xmi(xmi_content, name="SistemaVentas")

    class_by_name = {c.name: c for c in reimported.classes}
    assert "IServicio" in class_by_name
    assert class_by_name["IServicio"].element_type == "interface"

    assert "EstadoOrden" in class_by_name
    assert class_by_name["EstadoOrden"].element_type == "enum"

    assert "EntidadBase" in class_by_name
    assert class_by_name["EntidadBase"].element_type == "abstract_class"

    assert "Orden" in class_by_name
    assert class_by_name["Orden"].element_type == "class"

    # Verificar visibilidades de atributos en EntidadBase
    entidad_base = class_by_name["EntidadBase"]
    attrs_by_name = {a.name: a for a in entidad_base.attributes}
    assert attrs_by_name["id"].visibility == "protected"
    assert attrs_by_name["activo"].visibility == "package"

    # Verificar tipos de relaciones preservados
    rel_types = {r.relationship_type for r in reimported.relationships}
    assert "composition" in rel_types
    assert "aggregation" in rel_types
    assert "inheritance" in rel_types
    assert "realization" in rel_types
    assert "dependency" in rel_types


def test_import_exportar_xml_fixture_no_errors_same_class_count():
    fixture_path = Path(__file__).resolve().parents[2] / "exportar.xml"
    content = fixture_path.read_text(encoding="utf-8", errors="replace")

    imported = importar_xmi(content, name="exportar")
    assert imported.name == "clases"
    assert len(imported.classes) == 4
    class_names = {c.name for c in imported.classes}
    assert class_names == {"Inscripcion", "Tema", "Estudiante", "Curso"}


def test_import_xmi_with_uml_dependency_and_uml_abstraction_without_500():
    xmi_content = """<?xml version="1.0" encoding="windows-1252"?>
<XMI xmi.version="1.1" xmlns:UML="omg.org/UML1.3">
  <XMI.content>
    <UML:Model name="ModeloPrueba" xmi.id="MX_1">
      <UML:Namespace.ownedElement>
        <UML:Package name="paquete" xmi.id="PK_1">
          <UML:Namespace.ownedElement>
            <UML:Class name="ServicioWeb" xmi.id="EAID_C1" visibility="public" />
            <UML:Class name="ClienteApi" xmi.id="EAID_C2" visibility="public" />
            <UML:Class name="IContrato" xmi.id="EAID_C3" visibility="public" isAbstract="true" />
            <UML:Dependency xmi.id="EAID_DEP_1" name="depende" visibility="public" client="EAID_C2" supplier="EAID_C1" />
            <UML:Abstraction xmi.id="EAID_ABS_1" name="implementa" visibility="public" client="EAID_C1" supplier="EAID_C3" />
          </UML:Namespace.ownedElement>
        </UML:Package>
      </UML:Namespace.ownedElement>
    </UML:Model>
  </XMI.content>
</XMI>"""

    # Antes causaba AttributeError: 'NoneType' object has no attribute 'replace' -> HTTP 500
    imported = importar_xmi(xmi_content, name="prueba")
    assert len(imported.classes) == 3
    assert len(imported.relationships) == 2

    dep_rel = next(r for r in imported.relationships if r.relationship_type == "dependency")
    assert dep_rel.source_class_id == "ClienteApi"
    assert dep_rel.target_class_id == "ServicioWeb"

    abs_rel = next(r for r in imported.relationships if r.relationship_type == "realization")
    assert abs_rel.source_class_id == "ServicioWeb"
    assert abs_rel.target_class_id == "IContrato"

    # Verificar integración con _persist_internal_model
    repository = _DrawingImportRepository()
    service = ServicioUML.__new__(ServicioUML)
    service.uml = repository

    diagram = service._persistir_modelo_interno(imported, uuid4(), uuid4())
    assert diagram.id is not None
    assert len(repository.classes) == 3
    assert len(repository.relationships) == 2
