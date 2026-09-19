from app.main import app
from app.modules.modelado_uml.engine.internal_model import (
    UmlClassModel,
    UmlDiagramModel,
    UmlRelationshipModel,
)
from app.modules.modelado_uml.engine.text_parser import build_uml_from_text
from app.modules.modelado_uml.engine.validator import validate_internal_model
from app.modules.modelado_uml.engine.xmi import export_xmi, import_xmi


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

    assert imported.name == "Importado"
    assert {uml_class.name for uml_class in imported.classes} == {
        uml_class.name for uml_class in source.classes
    }


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
        "/api/v1/uml/diagrams/{diagram_id}/xmi",
    }
    assert expected_paths.issubset(paths.keys())
