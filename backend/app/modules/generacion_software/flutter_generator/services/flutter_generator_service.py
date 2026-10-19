import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from shutil import rmtree
from subprocess import run as run_process

from app.modules.generacion_software.coordinated_generator.contracts import GenerationPlan
from app.modules.generacion_software.coordinated_generator.emitters import emit_flutter_semantics
from app.modules.generacion_software.flutter_generator.exporter import (
    checksum_file,
    create_zip_archive,
)
from app.modules.generacion_software.flutter_generator.generator import write_flutter_project
from app.modules.generacion_software.flutter_generator.uml_analyzer import analyze_uml_for_flutter
from app.modules.generacion_software.flutter_generator.validators import validate_project


@dataclass(frozen=True)
class FlutterGenerationResult:
    project_name: str
    project_dir: Path
    zip_path: Path
    files: list[Path]
    manifest: dict


class FlutterGeneratorService:
    def __init__(self, storage_root: Path | None = None) -> None:
        self.storage_root = storage_root or Path("..") / "storage" / "generated" / "flutter"

    def generate(
        self,
        intermediate_model: dict,
        name: str,
        generation_id: str,
        api_base_url: str = "http://localhost:8080",
        theme_config: dict | None = None,
        generation_plan: GenerationPlan | None = None,
    ) -> FlutterGenerationResult:
        project = analyze_uml_for_flutter(intermediate_model, name, api_base_url, theme_config)
        errors = validate_project(project)
        if errors:
            raise ValueError("; ".join(errors))

        target_dir = (self.storage_root / generation_id / project.package_name).resolve()
        if target_dir.exists():
            rmtree(target_dir)
        write_result = write_flutter_project(project, target_dir)
        files = write_result.files
        theme_json = json.dumps(project.theme_config.raw_v2, indent=2, sort_keys=True)
        theme_manifest = target_dir / "theme_manifest.json"
        theme_manifest.write_text(theme_json, encoding="utf-8")
        files.append(theme_manifest)
        if generation_plan is not None:
            files.extend(emit_flutter_semantics(generation_plan, target_dir))
        dart = shutil.which("dart")
        if dart:
            dart_tool = target_dir / ".dart_tool"
            package_config = dart_tool / "package_config.json"
            temporary_package_config = not package_config.exists()
            if temporary_package_config:
                dart_tool.mkdir(exist_ok=True)
                package_config.write_text(json.dumps({
                    "configVersion": 2,
                    "packages": [{"name": project.package_name, "rootUri": "../",
                                  "packageUri": "lib/", "languageVersion": "3.4"}],
                }), encoding="utf-8")
            try:
                format_result = run_process(
                    [dart, "format", "--output=write", "lib", "test"], cwd=target_dir,
                    capture_output=True, text=True, timeout=120, check=False,
                )
            finally:
                if temporary_package_config:
                    shutil.rmtree(dart_tool)
            if format_result.returncode != 0:
                raise ValueError(f"No se pudo formatear el proyecto Flutter: {format_result.stderr[-500:]}")
        zip_path = create_zip_archive(target_dir, target_dir.parent / f"{project.package_name}.zip")
        checksums = {path.relative_to(target_dir).as_posix(): checksum_file(path) for path in files}
        manifest = {
            "technology": "Flutter",
            "language": "Dart",
            "project_name": project.name,
            "package_name": project.package_name,
            "api_base_url": project.api_base_url,
            "theme_config": {
                **project.theme_config.raw_v2,
                "primary_color": project.theme_config.primary_color,
                "secondary_color": project.theme_config.secondary_color,
                "background_color": project.theme_config.background_color,
                "surface_color": project.theme_config.surface_color,
                "button_color": project.theme_config.button_color,
                "font_family": project.theme_config.font_family,
                "border_radius": project.theme_config.border_radius,
                "button_style": project.theme_config.button_style,
                "density": project.theme_config.density,
            },
            "theme_contract_version": 2,
            "theme_hash": hashlib.sha256(json.dumps(project.theme_config.raw_v2, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            "state_management": "Provider",
            "platforms": write_result.scaffolded_platforms or ["source"],
            "generated_layers": ["models", "services", "providers", "screens", "forms", "routes", "network"],
            "entity_count": len(project.entities),
            "operation_count": len(generation_plan.operations) if generation_plan else 0,
            "plan_hash": generation_plan.canonical_hash if generation_plan else None,
            "functional_routes": [
                {
                    "operation_id": route.operation_id,
                    "http_method": route.http_method,
                    "path": route.effective_path,
                }
                for route in (generation_plan.routes if generation_plan else ())
            ],
            "functional_dtos": {
                operation.id: [
                    item.name for item in operation.parameters if item.location == "body"
                ]
                for operation in (generation_plan.operations if generation_plan else ())
                if operation.route
            },
            "verification_status": "not_run",
            "file_count": len(files),
            "zip_path": str(zip_path),
            "checksums": checksums,
            "source": "deterministic-rules-with-ai-plan",
            "generator_version": "6.0",
        }
        return FlutterGenerationResult(
            project_name=project.name,
            project_dir=target_dir,
            zip_path=zip_path,
            files=files,
            manifest=manifest,
        )
