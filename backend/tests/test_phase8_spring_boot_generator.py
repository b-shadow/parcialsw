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
    assert result.zip_path.exists()
    assert result.manifest["technology"] == "Spring Boot"
    assert result.manifest["entity_count"] == 2
    assert result.manifest["file_count"] >= 19

    entity = next(path for path in result.files if path.name == "Pedido.java")
    service = next(path for path in result.files if path.name == "PedidoService.java")
    controller = next(path for path in result.files if path.name == "PedidoController.java")

    assert "@ManyToOne" in entity.read_text(encoding="utf-8")
    assert "public PedidoResponse create" in service.read_text(encoding="utf-8")
    assert "@DeleteMapping" in controller.read_text(encoding="utf-8")


def test_phase8_openapi_contracts_are_registered() -> None:
    paths = app.openapi()["paths"]
    assert "/api/v1/generation/spring-boot" in paths
    assert "/api/v1/generation/spring-boot/{backend_id}/download" in paths
