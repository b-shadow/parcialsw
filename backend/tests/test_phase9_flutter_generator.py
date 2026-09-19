from pathlib import Path
from uuid import uuid4

from app.main import app
from app.modules.generacion_software.flutter_generator import FlutterGeneratorService


def _intermediate_model() -> dict:
    return {
        "classes": [
            {
                "id": "cliente-id",
                "name": "Cliente",
                "attributes": [
                    {"name": "nombre", "data_type": "String", "is_required": True},
                    {"name": "correo", "data_type": "String", "is_required": True},
                    {"name": "activo", "data_type": "Boolean", "is_required": False},
                ],
            },
            {
                "id": "pedido-id",
                "name": "Pedido",
                "attributes": [
                    {"name": "total", "data_type": "Double", "is_required": True},
                    {"name": "fecha", "data_type": "DateTime", "is_required": False},
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


def test_flutter_generator_writes_complete_project(tmp_path: Path) -> None:
    result = FlutterGeneratorService(storage_root=tmp_path).generate(
        _intermediate_model(),
        "Sistema Ventas Mobile",
        str(uuid4()),
        api_base_url="http://localhost:8080",
    )

    assert (result.project_dir / "pubspec.yaml").exists()
    assert (result.project_dir / "analysis_options.yaml").exists()
    assert (result.project_dir / "README.md").exists()
    assert (result.project_dir / "web/index.html").exists()
    assert (result.project_dir / "web/manifest.json").exists()
    assert (result.project_dir / "lib/main.dart").exists()
    assert result.zip_path.exists()
    assert result.manifest["technology"] == "Flutter"
    assert result.manifest["language"] == "Dart"
    assert result.manifest["entity_count"] == 2
    assert result.manifest["file_count"] >= 20

    model = result.project_dir / "lib/modules/cliente/cliente_model.dart"
    service = result.project_dir / "lib/modules/cliente/cliente_service.dart"
    provider = result.project_dir / "lib/modules/cliente/cliente_provider.dart"
    form = result.project_dir / "lib/modules/cliente/cliente_form_screen.dart"
    router = result.project_dir / "lib/core/routes/app_router.dart"

    assert "factory Cliente.fromJson" in model.read_text(encoding="utf-8")
    assert "Map<String, dynamic> toJson()" in model.read_text(encoding="utf-8")
    assert "Future<List<Cliente>> findAll()" in service.read_text(encoding="utf-8")
    assert "ChangeNotifier" in provider.read_text(encoding="utf-8")
    assert "TextFormField" in form.read_text(encoding="utf-8")
    assert "SwitchListTile" in form.read_text(encoding="utf-8")
    assert "'/cliente'" in router.read_text(encoding="utf-8")


def test_phase9_openapi_contracts_are_registered() -> None:
    paths = app.openapi()["paths"]
    assert "/api/v1/generation/flutter" in paths
    assert "/api/v1/generation/flutter/{frontend_id}/download" in paths
