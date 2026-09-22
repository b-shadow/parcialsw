from pathlib import Path
import subprocess
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


def _association_class_model() -> dict:
    return {
        "classes": [
            {
                "id": "estudiante",
                "name": "Estudiante",
                "attributes": [
                    {"name": "nombre", "data_type": "String", "is_required": True},
                    {"name": "correo", "data_type": "String", "is_required": False},
                ],
            },
            {
                "id": "curso",
                "name": "Curso",
                "attributes": [
                    {"name": "nombre", "data_type": "String", "is_required": True},
                    {"name": "descripcion", "data_type": "String", "is_required": False},
                ],
            },
            {
                "id": "inscripcion",
                "name": "Inscripcion",
                "attributes": [
                    {"name": "estado", "data_type": "String", "is_required": False},
                    {"name": "notaFinal", "data_type": "Double", "is_required": False},
                ],
            },
        ],
        "relationships": [
            {
                "source_class_id": "estudiante",
                "target_class_id": "curso",
                "relationship_type": "association",
                "source_cardinality": "*",
                "target_cardinality": "*",
                "metadata_json": {"association_class_id": "inscripcion"},
            }
        ],
    }


def test_flutter_generator_writes_complete_project(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.modules.generacion_software.flutter_generator.generator.project_writer.which",
        lambda _: None,
    )

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
    assert result.manifest["platforms"] == ["source"]
    assert result.manifest["entity_count"] == 2
    assert result.manifest["file_count"] >= 20

    model = result.project_dir / "lib/modules/cliente/cliente_model.dart"
    service = result.project_dir / "lib/modules/cliente/cliente_service.dart"
    provider = result.project_dir / "lib/modules/cliente/cliente_provider.dart"
    form = result.project_dir / "lib/modules/cliente/cliente_form_screen.dart"
    router = result.project_dir / "lib/core/routes/app_router.dart"
    pedido_model = result.project_dir / "lib/modules/pedido/pedido_model.dart"
    pedido_form = result.project_dir / "lib/modules/pedido/pedido_form_screen.dart"

    assert "factory Cliente.fromJson" in model.read_text(encoding="utf-8")
    assert "Map<String, dynamic> toJson()" in model.read_text(encoding="utf-8")
    assert "Future<List<Cliente>> findAll()" in service.read_text(encoding="utf-8")
    assert "ChangeNotifier" in provider.read_text(encoding="utf-8")
    assert "TextFormField" in form.read_text(encoding="utf-8")
    assert "SwitchListTile" in form.read_text(encoding="utf-8")
    assert "'/cliente'" in router.read_text(encoding="utf-8")
    assert "Card(" in router.read_text(encoding="utf-8")
    assert "showDatePicker" in pedido_form.read_text(encoding="utf-8")
    assert "readOnly: true" in pedido_form.read_text(encoding="utf-8")
    assert "toIso8601String" not in pedido_model.read_text(encoding="utf-8")
    assert "padLeft(2, '0')" in pedido_model.read_text(encoding="utf-8")


def test_flutter_generator_scaffolds_android_when_flutter_cli_exists(tmp_path: Path, monkeypatch) -> None:
    def fake_run(args, cwd, check, capture_output, text, encoding, errors, timeout):
        assert "create" in args
        assert "--platforms=android,web" in args
        assert "--no-pub" in args
        assert encoding == "utf-8"
        assert errors == "replace"
        (Path(cwd) / "android" / "app" / "build.gradle.kts").parent.mkdir(parents=True)
        (Path(cwd) / "android" / "app" / "build.gradle.kts").write_text("// android", encoding="utf-8")
        (Path(cwd) / "web").mkdir(exist_ok=True)

    monkeypatch.setattr(
        "app.modules.generacion_software.flutter_generator.generator.project_writer.which",
        lambda _: "flutter",
    )
    monkeypatch.setattr(
        "app.modules.generacion_software.flutter_generator.generator.project_writer.subprocess.run",
        fake_run,
    )

    result = FlutterGeneratorService(storage_root=tmp_path).generate(
        _intermediate_model(),
        "Sistema Ventas Mobile",
        str(uuid4()),
        api_base_url="http://localhost:8080",
    )

    assert (result.project_dir / "android/app/build.gradle.kts").exists()
    assert result.manifest["platforms"] == ["android", "web"]
    assert "android/app/build.gradle.kts" in result.manifest["checksums"]


def test_flutter_generator_reports_flutter_cli_failures(tmp_path: Path, monkeypatch) -> None:
    def fake_run(args, cwd, check, capture_output, text, encoding, errors, timeout):
        raise subprocess.CalledProcessError(
            returncode=69,
            cmd=args,
            output="Error al crear proyecto Flutter",
            stderr="Detalle del fallo",
        )

    monkeypatch.setattr(
        "app.modules.generacion_software.flutter_generator.generator.project_writer.which",
        lambda _: "flutter",
    )
    monkeypatch.setattr(
        "app.modules.generacion_software.flutter_generator.generator.project_writer.subprocess.run",
        fake_run,
    )

    try:
        FlutterGeneratorService(storage_root=tmp_path).generate(
            _intermediate_model(),
            "Sistema Ventas Mobile",
            str(uuid4()),
            api_base_url="http://localhost:8080",
        )
    except ValueError as exc:
        assert "Error al crear proyecto Flutter" in str(exc)
        assert "Detalle del fallo" in str(exc)
    else:
        raise AssertionError("Se esperaba ValueError cuando flutter create falla")


def test_flutter_generator_renders_dropdowns_for_association_class_foreign_keys(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.modules.generacion_software.flutter_generator.generator.project_writer.which",
        lambda _: None,
    )

    result = FlutterGeneratorService(storage_root=tmp_path).generate(
        _association_class_model(),
        "Academico Mobile",
        str(uuid4()),
        api_base_url="http://localhost:8080",
    )

    model = result.project_dir / "lib/modules/inscripcion/inscripcion_model.dart"
    form = result.project_dir / "lib/modules/inscripcion/inscripcion_form_screen.dart"
    model_text = model.read_text(encoding="utf-8")
    form_text = form.read_text(encoding="utf-8")

    assert "final String? estudianteId;" in model_text
    assert "final String? cursoId;" in model_text
    assert "DropdownButtonFormField<String>" in form_text
    assert "isExpanded: true" in form_text
    assert "_compactDisplayLabel(item.toJson())" in form_text
    assert "EstudianteService().findAll()" in form_text
    assert "CursoService().findAll()" in form_text
    assert "_displayLabel(item.toJson())" in form_text


def test_phase9_openapi_contracts_are_registered() -> None:
    paths = app.openapi()["paths"]
    assert "/api/v1/generation/flutter" in paths
    assert "/api/v1/generation/flutter/{frontend_id}/download" in paths
