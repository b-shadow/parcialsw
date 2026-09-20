from dataclasses import dataclass
from pathlib import Path
from shutil import rmtree

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
    ) -> FlutterGenerationResult:
        project = analyze_uml_for_flutter(intermediate_model, name, api_base_url)
        errors = validate_project(project)
        if errors:
            raise ValueError("; ".join(errors))

        target_dir = (self.storage_root / generation_id / project.package_name).resolve()
        if target_dir.exists():
            rmtree(target_dir)
        write_result = write_flutter_project(project, target_dir)
        files = write_result.files
        zip_path = create_zip_archive(target_dir, target_dir.parent / f"{project.package_name}.zip")
        checksums = {path.relative_to(target_dir).as_posix(): checksum_file(path) for path in files}
        manifest = {
            "technology": "Flutter",
            "language": "Dart",
            "project_name": project.name,
            "package_name": project.package_name,
            "api_base_url": project.api_base_url,
            "state_management": "Provider",
            "platforms": write_result.scaffolded_platforms or ["source"],
            "generated_layers": ["models", "services", "providers", "screens", "forms", "routes", "network"],
            "entity_count": len(project.entities),
            "file_count": len(files),
            "zip_path": str(zip_path),
            "checksums": checksums,
            "source": "deterministic-rules-with-ai-plan",
        }
        return FlutterGenerationResult(
            project_name=project.name,
            project_dir=target_dir,
            zip_path=zip_path,
            files=files,
            manifest=manifest,
        )
