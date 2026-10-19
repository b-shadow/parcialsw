import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.main import app
from app.modules.generacion_software.coordinated_generator import compile_generation_plan
from app.modules.generacion_software.coordinated_generator.contracts import build_ui_manifest
from app.modules.generacion_software.flutter_generator import FlutterGeneratorService
from app.modules.generacion_software.routers.theme import _revision
from app.modules.generacion_software.schemas.theme_contract import (
    DEFAULT_THEME_V2,
    FlutterThemeConfigV2,
    contrast_ratio,
    normalize_theme,
)


def _model() -> dict:
    return {"schema_version": 2, "classes": [{"id": "course", "name": "Curso", "attributes": [
        {"id": "name", "name": "nombre", "data_type": "String", "is_required": True},
        {"id": "date", "name": "fechaInicio", "data_type": "LocalDate", "is_required": True},
    ], "methods": []}], "relationships": []}


def test_phase6_adapts_v1_and_normalizes_hex() -> None:
    theme, diagnostics, fields = normalize_theme({
        "primary_color": "#0f766e", "font_family": "Roboto", "border_radius": 12,
        "button_style": "outline", "density": "comfortable",
    })
    assert theme.schema_version == 2
    assert theme.light.primary == "#0F766E"
    assert theme.shape.card_radius == 12
    assert theme.components.button_style == "outline"
    assert "schema_version" in fields
    assert not diagnostics


def test_phase6_shared_component_recipes_match_runtime_contract() -> None:
    recipes = json.loads((Path(__file__).parents[2] / "contracts/flutter_component_recipes_v1.json").read_text(encoding="utf-8"))
    assert recipes["density"]["compact"] == {"screen_padding": 12, "section_gap": 8, "field_height": 44}
    assert recipes["density"]["normal"] == {"screen_padding": 16, "section_gap": 12, "field_height": 48}
    assert recipes["density"]["comfortable"] == {"screen_padding": 20, "section_gap": 16, "field_height": 52}
    assert recipes["navigation"] == {
        "automatic_bottom_bar_min_modules": 2,
        "automatic_bottom_bar_max_modules": 4,
    }


def test_phase6_blocks_inaccessible_contrast_and_extra_fields() -> None:
    raw = DEFAULT_THEME_V2.model_dump(mode="json")
    raw["light"]["on_primary"] = raw["light"]["primary"]
    _, diagnostics, _ = normalize_theme(raw)
    assert any(item.code == "theme_contrast_insufficient" and item.severity == "error" for item in diagnostics)
    assert contrast_ratio("#000000", "#FFFFFF") == 21.0
    with pytest.raises(ValidationError):
        FlutterThemeConfigV2.model_validate({**DEFAULT_THEME_V2.model_dump(), "unknown": True})


def test_phase6_ui_manifest_uses_real_entities_and_controls() -> None:
    plan = compile_generation_plan(_model(), "Academico", source_transformation_id="tx-1",
                                   theme=DEFAULT_THEME_V2.model_dump(mode="json"))
    manifest = build_ui_manifest(plan)
    assert manifest.source_hash == plan.canonical_hash
    assert manifest.source_transformation_id == "tx-1"
    assert manifest.modules[0].label == "Curso"
    form = next(item for item in manifest.modules[0].screens if item.kind == "form")
    assert {item.control for item in form.fields} == {"text_input", "date_picker"}


def test_phase6_flutter_contains_dark_theme_and_manifests(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.modules.generacion_software.flutter_generator.generator.project_writer.which",
        lambda _: None,
    )
    plan = compile_generation_plan(_model(), "Academico", theme=DEFAULT_THEME_V2.model_dump(mode="json"))
    result = FlutterGeneratorService(tmp_path).generate(
        _model(), "Academico", "phase6", theme_config=DEFAULT_THEME_V2.model_dump(mode="json"),
        generation_plan=plan,
    )
    app_theme = (result.project_dir / "lib/shared/themes/app_theme.dart").read_text(encoding="utf-8")
    main = (result.project_dir / "lib/main.dart").read_text(encoding="utf-8")
    router = (result.project_dir / "lib/core/routes/app_router.dart").read_text(encoding="utf-8")
    assert "static ThemeData get dark" in app_theme
    assert "error: Color(0xFFB91C1C)" in app_theme
    assert "outline: Color(0xFF64748B)" in app_theme
    assert "darkTheme: AppTheme.dark" in main
    assert "drawer: Drawer(" in router
    assert (result.project_dir / "test/goldens/theme_tokens.png").read_bytes().startswith(b"\x89PNG")
    assert json.loads((result.project_dir / "theme_manifest.json").read_text())["schema_version"] == 2
    assert json.loads((result.project_dir / "ui_manifest.json").read_text())["modules"][0]["label"] == "Curso"
    assert result.manifest["theme_contract_version"] == 2
    assert len(result.manifest["theme_hash"]) == 64


def test_phase6_openapi_exposes_theme_and_manifest_lifecycle() -> None:
    paths = app.openapi()["paths"]
    expected = {
        "/api/v1/projects/{project_id}/flutter-theme",
        "/api/v1/projects/{project_id}/flutter-theme/validate",
        "/api/v1/projects/{project_id}/flutter-theme/reset",
        "/api/v1/projects/{project_id}/flutter-theme/presets",
        "/api/v1/projects/{project_id}/flutter-theme/presets/{preset_id}",
        "/api/v1/projects/{project_id}/flutter-theme/presets/{preset_id}/apply",
        "/api/v1/generation/transformations/{transformation_id}/ui-manifest",
    }
    assert expected <= set(paths)


def test_phase6_revision_headers_preserve_zero_and_reject_malformed_values() -> None:
    assert _revision(None, "*") == 0
    assert _revision('"flutter-theme-revision-0"') == 0
    assert _revision('"flutter-theme-revision-12"') == 12
    assert _revision("12") is None
    assert _revision('"flutter-theme-revision-x"') is None
