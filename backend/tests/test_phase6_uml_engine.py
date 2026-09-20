from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from app.main import app
from app.modules.modelado_uml.services.uml_service import UmlService
from app.modules.modelado_uml.engine.internal_model import (
    UmlClassModel,
    UmlDiagramModel,
    UmlRelationshipModel,
)
from app.modules.modelado_uml.engine.text_parser import build_uml_from_text
from app.modules.modelado_uml.engine.validator import validate_internal_model
from app.modules.modelado_uml.engine.xmi import export_xmi, import_xmi


class _DrawingImportRepository:
    def __init__(self) -> None:
        self.diagrams = []
        self.classes = []
        self.visuals = []
        self.relationships = []

    def add_diagram(self, diagram):
        diagram.id = uuid4()
        self.diagrams.append(diagram)
        return diagram

    def add_class(self, uml_class):
        uml_class.id = uuid4()
        self.classes.append(uml_class)
        return uml_class

    def add_visual_element(self, visual):
        visual.id = uuid4()
        self.visuals.append(visual)
        return visual

    def add_attribute(self, attribute):
        attribute.id = uuid4()
        return attribute

    def add_method(self, method):
        method.id = uuid4()
        return method

    def add_parameter(self, parameter):
        parameter.id = uuid4()
        return parameter

    def add_relationship(self, relationship):
        relationship.id = uuid4()
        self.relationships.append(relationship)
        return relationship


def _assert_joint_canvas_drawable_repository(repository: _DrawingImportRepository) -> None:
    class_ids = {uml_class.id for uml_class in repository.classes}
    visual_ids = {visual.element_id for visual in repository.visuals}
    relationship_endpoints = {
        relationship.source_class_id
        for relationship in repository.relationships
    } | {
        relationship.target_class_id
        for relationship in repository.relationships
    }
    association_class_ids = {
        relationship.metadata_json.get("association_class_id")
        for relationship in repository.relationships
        if relationship.metadata_json.get("association_class_id")
    }

    assert len(repository.classes) == 4
    assert len(repository.relationships) == 2
    assert class_ids == visual_ids
    assert relationship_endpoints.issubset(class_ids)
    assert association_class_ids.issubset({str(class_id) for class_id in class_ids})


def test_text_prompt_generates_internal_uml_model() -> None:
    model = build_uml_from_text("Crear sistema de biblioteca con libros, usuarios y prestamos")

    class_names = {uml_class.name for uml_class in model.classes}
    assert {"Biblioteca", "Libros", "Usuarios", "Prestamos"}.issubset(class_names)
    assert all(uml_class.attributes for uml_class in model.classes)
    assert model.relationships


def test_internal_uml_validator_detects_design_findings() -> None:
    model = UmlDiagramModel(
        name="Duplicados",
        classes=[UmlClassModel(name="Cliente"), UmlClassModel(name="Cliente")],
        relationships=[
            UmlRelationshipModel(
                source_class_id="Cliente",
                target_class_id="Cliente",
                relationship_type="association",
            )
        ],
    )

    errors, warnings, recommendations = validate_internal_model(model)

    assert errors == []
    assert any("duplicados" in warning for warning in warnings)
    assert any("relacion reflexiva" in warning for warning in warnings)
    assert recommendations


def test_xmi_export_import_roundtrip_keeps_classes() -> None:
    source = build_uml_from_text("Crear sistema academico con estudiantes, cursos y matriculas")

    xmi = export_xmi(source)
    imported = import_xmi(xmi, name="Importado")

    assert 'xmi.version="1.1"' in xmi
    assert 'xmlns:UML="omg.org/UML1.3"' in xmi
    assert "<XMI.header>" in xmi
    assert "<XMI.content>" in xmi
    assert "<XMI.exporter>Enterprise Architect</XMI.exporter>" in xmi
    assert "<UML:Package" in xmi
    assert "<UML:Class" in xmi
    assert "<UML:Diagram" in xmi
    assert '<XMI.extensions xmi.extender="Enterprise Architect 2.5"' in xmi
    assert imported.name == source.name
    assert {uml_class.name for uml_class in imported.classes} == {
        uml_class.name for uml_class in source.classes
    }


def test_enterprise_architect_xml_import_reads_class_diagram() -> None:
    ea_xml = """<?xml version="1.0" encoding="windows-1252"?>
<XMI xmi.version="1.1" xmlns:UML="omg.org/UML1.3">
  <XMI.content>
    <UML:Model name="EA Model" xmi.id="MX_EAID_TEST">
      <UML:Namespace.ownedElement>
        <UML:Class name="EARootClass" xmi.id="EAID_ROOT" isRoot="true"/>
        <UML:Package name="clases" xmi.id="EAPK_CLASSES">
          <UML:Namespace.ownedElement>
            <UML:Class name="Estudiante" xmi.id="EAID_ESTUDIANTE" visibility="public" namespace="EAPK_CLASSES">
              <UML:Classifier.feature>
                <UML:Attribute name="nombre" visibility="private">
                  <UML:ModelElement.taggedValue>
                    <UML:TaggedValue tag="type" value="char"/>
                    <UML:TaggedValue tag="position" value="0"/>
                  </UML:ModelElement.taggedValue>
                </UML:Attribute>
                <UML:Operation name="inscribirse" visibility="public">
                  <UML:ModelElement.taggedValue>
                    <UML:TaggedValue tag="type" value="void"/>
                    <UML:TaggedValue tag="position" value="0"/>
                  </UML:ModelElement.taggedValue>
                </UML:Operation>
              </UML:Classifier.feature>
            </UML:Class>
            <UML:Class name="Curso" xmi.id="EAID_CURSO" visibility="public" namespace="EAPK_CLASSES"/>
            <UML:Association xmi.id="EAID_REL" visibility="public">
              <UML:Association.connection>
                <UML:AssociationEnd type="EAID_ESTUDIANTE" multiplicity="*"/>
                <UML:AssociationEnd type="EAID_CURSO" multiplicity="1"/>
              </UML:Association.connection>
            </UML:Association>
          </UML:Namespace.ownedElement>
        </UML:Package>
      </UML:Namespace.ownedElement>
    </UML:Model>
    <UML:Diagram name="clases" xmi.id="EAID_DIAGRAM" diagramType="ClassDiagram" owner="EAPK_CLASSES">
      <UML:Diagram.element>
        <UML:DiagramElement geometry="Left=200;Top=120;Right=300;Bottom=200;" subject="EAID_ESTUDIANTE"/>
        <UML:DiagramElement geometry="Left=260;Top=50;Right=360;Bottom=130;" subject="EAID_CURSO"/>
        <UML:DiagramElement geometry="EDGE=2;Path=;" subject="EAID_REL"/>
      </UML:Diagram.element>
    </UML:Diagram>
  </XMI.content>
</XMI>"""

    imported = import_xmi(ea_xml, name="archivo")

    assert imported.name == "clases"
    assert [uml_class.name for uml_class in imported.classes] == ["Estudiante", "Curso"]
    assert imported.classes[0].attributes[0].data_type == "char"
    assert imported.classes[0].methods[0].return_type == "void"
    assert imported.classes[0].visual.x == 200
    assert imported.classes[0].visual.width == 100
    assert len(imported.relationships) == 1
    assert imported.relationships[0].source_class_id == "Estudiante"
    assert imported.relationships[0].target_class_id == "Curso"
    assert imported.relationships[0].source_cardinality == "*"
    assert imported.relationships[0].target_cardinality == "1"


def test_enterprise_architect_exportar_xml_fixture_imports_real_class_diagram() -> None:
    fixture_path = Path(__file__).resolve().parents[2] / "exportar.xml"
    imported = import_xmi(fixture_path.read_text(encoding="utf-8", errors="replace"), name="exportar")

    assert imported.name == "clases"
    assert [uml_class.name for uml_class in imported.classes] == [
        "Inscripcion",
        "Tema",
        "Estudiante",
        "Curso",
    ]
    assert len(imported.relationships) == 2
    assert {(relationship.source_class_id, relationship.target_class_id) for relationship in imported.relationships} == {
        ("Curso", "Tema"),
        ("Estudiante", "Curso"),
    }
    assert any(
        relationship.metadata_json.get("association_class_id")
        for relationship in imported.relationships
    )
    assert all(uml_class.visual.width and uml_class.visual.height for uml_class in imported.classes)


def test_editor_import_replace_flow_becomes_joint_canvas_drawable_model() -> None:
    fixture_path = Path(__file__).resolve().parents[2] / "exportar.xml"
    imported = import_xmi(fixture_path.read_text(encoding="utf-8", errors="replace"), name="exportar")
    repository = _DrawingImportRepository()
    service = UmlService.__new__(UmlService)
    service.uml = repository

    service._populate_existing_diagram_from_model(SimpleNamespace(id=uuid4()), imported)

    _assert_joint_canvas_drawable_repository(repository)


def test_collaborative_import_new_diagram_flow_becomes_joint_canvas_drawable_model() -> None:
    fixture_path = Path(__file__).resolve().parents[2] / "exportar.xml"
    imported = import_xmi(fixture_path.read_text(encoding="utf-8", errors="replace"), name="exportar")
    repository = _DrawingImportRepository()
    service = UmlService.__new__(UmlService)
    service.uml = repository

    diagram = service._persist_internal_model(imported, uuid4(), uuid4())

    assert diagram.id == repository.diagrams[0].id
    assert diagram.name == "clases"
    _assert_joint_canvas_drawable_repository(repository)


def test_enterprise_architect_xml_import_export_roundtrip_keeps_drawable_relationships() -> None:
    fixture_path = Path(__file__).resolve().parents[2] / "exportar.xml"
    imported = import_xmi(fixture_path.read_text(encoding="utf-8", errors="replace"), name="exportar")

    exported = export_xmi(imported)
    reimported = import_xmi(exported, name="reimportado")

    assert exported.startswith('<?xml version="1.0" encoding="windows-1252"?>')
    assert "<XMI.exporter>Enterprise Architect</XMI.exporter>" in exported
    assert 'tag="associationclass"' in exported
    assert reimported.name == "clases"
    assert {uml_class.name for uml_class in reimported.classes} == {
        "Inscripcion",
        "Tema",
        "Estudiante",
        "Curso",
    }
    assert len(reimported.relationships) == 2
    assert any(
        relationship.metadata_json.get("association_class_id")
        for relationship in reimported.relationships
    )


def test_phase6_openapi_contracts_are_registered() -> None:
    paths = app.openapi()["paths"]
    expected_paths = {
        "/api/v1/uml/diagrams/{diagram_id}/model",
        "/api/v1/uml/classes/{class_id}",
        "/api/v1/uml/methods/{method_id}/parameters",
        "/api/v1/uml/relationships/{relationship_id}",
        "/api/v1/uml/diagrams/{diagram_id}/visual-elements",
        "/api/v1/uml/generate",
        "/api/v1/uml/xmi/import",
        "/api/v1/uml/diagrams/{diagram_id}/xmi/import",
        "/api/v1/uml/diagrams/{diagram_id}/xmi",
    }
    assert expected_paths.issubset(paths.keys())
