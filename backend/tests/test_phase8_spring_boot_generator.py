from pathlib import Path
from uuid import uuid4

from app.main import app
from app.modules.generacion_software.backend_generator import SpringBootGeneratorService


def _intermediate_model() -> dict:
    return {
        "classes": [
            {
                "id": "cliente-id",
                "name": "Cliente",
                "attributes": [
                    {"name": "nombre", "data_type": "String", "is_required": True},
                    {"name": "correo", "data_type": "String", "is_required": True},
                ],
            },
            {
                "id": "pedido-id",
                "name": "Pedido",
                "attributes": [
                    {"name": "total", "data_type": "Double", "is_required": True},
                ],
            },
        ],
        "relationships": [
            {
                "source_class_id": "Pedido",
                "target_class_id": "Cliente",
                "type": "association",
            }
        ],
    }


def test_spring_boot_generator_writes_complete_project(tmp_path: Path) -> None:
    result = SpringBootGeneratorService(storage_root=tmp_path).generate(
        _intermediate_model(),
        "Sistema Ventas",
        str(uuid4()),
    )

    assert (result.project_dir / "pom.xml").exists()
    assert (result.project_dir / "README.md").exists()
    assert (result.project_dir / "docker-compose.yml").exists()
    assert (result.project_dir / ".env.example").exists()
    assert (result.project_dir / "database" / "init.sql").exists()
    assert (result.project_dir / "scripts" / "run.ps1").exists()
    assert (result.project_dir / "scripts" / "run.sh").exists()
    assert result.zip_path.exists()
    assert result.manifest["technology"] == "Spring Boot"
    assert result.manifest["database_bootstrap"] == [
        "docker-compose.yml",
        "database/init.sql",
        "scripts/run.ps1",
        "scripts/run.sh",
    ]
    assert result.manifest["entity_count"] == 2
    assert result.manifest["file_count"] >= 19

    entity = next(path for path in result.files if path.name == "Pedido.java")
    service = next(path for path in result.files if path.name == "PedidoService.java")
    controller = next(path for path in result.files if path.name == "PedidoController.java")

    assert "@ManyToOne" in entity.read_text(encoding="utf-8")
    assert "public PedidoResponse create" in service.read_text(encoding="utf-8")
    assert "@DeleteMapping" in controller.read_text(encoding="utf-8")


def test_spring_boot_generator_uses_multiplicity_and_association_class_foreign_keys(tmp_path: Path) -> None:
    model = {
        "classes": [
            {"id": "curso", "name": "Curso", "attributes": [{"name": "nombre", "data_type": "String", "is_required": True}]},
            {"id": "tema", "name": "Tema", "attributes": [{"name": "titulo", "data_type": "String", "is_required": True}]},
            {
                "id": "estudiante",
                "name": "Estudiante",
                "attributes": [{"name": "nombre", "data_type": "String", "is_required": True}],
            },
            {
                "id": "inscripcion",
                "name": "Inscripcion",
                "attributes": [{"name": "notaFinal", "data_type": "Double", "is_required": False}],
            },
        ],
        "relationships": [
            {
                "source_class_id": "curso",
                "target_class_id": "tema",
                "type": "association",
                "source_cardinality": "1",
                "target_cardinality": "*",
            },
            {
                "source_class_id": "estudiante",
                "target_class_id": "curso",
                "type": "association",
                "source_cardinality": "*",
                "target_cardinality": "*",
                "metadata_json": {"association_class_id": "inscripcion"},
            },
        ],
    }

    result = SpringBootGeneratorService(storage_root=tmp_path).generate(model, "Academico", str(uuid4()))

    tema_request = (result.project_dir / "src/main/java/com/caseinteligente/generated/academico/dto/TemaRequest.java").read_text(
        encoding="utf-8"
    )
    inscripcion_request = (
        result.project_dir / "src/main/java/com/caseinteligente/generated/academico/dto/InscripcionRequest.java"
    ).read_text(encoding="utf-8")
    tema_entity = (result.project_dir / "src/main/java/com/caseinteligente/generated/academico/entity/Tema.java").read_text(
        encoding="utf-8"
    )
    inscripcion_entity = (
        result.project_dir / "src/main/java/com/caseinteligente/generated/academico/entity/Inscripcion.java"
    ).read_text(encoding="utf-8")

    assert "private UUID cursoId;" in tema_request
    assert "private UUID cursoId;" in inscripcion_request
    assert "private UUID estudianteId;" in inscripcion_request
    assert "private Curso curso;" in tema_entity
    assert "private Curso curso;" in inscripcion_entity
    assert "private Estudiante estudiante;" in inscripcion_entity


def test_phase8_openapi_contracts_are_registered() -> None:
    paths = app.openapi()["paths"]
    assert "/api/v1/generation/spring-boot" in paths
    assert "/api/v1/generation/spring-boot/{backend_id}/download" in paths
