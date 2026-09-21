from dataclasses import dataclass
from pathlib import Path
from shutil import rmtree

from app.modules.generacion_software.backend_generator.exporter import (
    checksum_file,
    create_zip_archive,
)
from app.modules.generacion_software.backend_generator.generator import write_spring_boot_project
from app.modules.generacion_software.backend_generator.uml_parser import parse_intermediate_model
from app.modules.generacion_software.backend_generator.validators import validate_project


@dataclass(frozen=True)
class SpringBootGenerationResult:
    project_name: str
    project_dir: Path
    zip_path: Path
    files: list[Path]
    manifest: dict


class SpringBootGeneratorService:
    def __init__(self, storage_root: Path | None = None) -> None:
        self.storage_root = storage_root or Path("..") / "storage" / "generated" / "backend"

    def generate(self, intermediate_model: dict, name: str, generation_id: str) -> SpringBootGenerationResult:
        project = parse_intermediate_model(intermediate_model, name)
        errors = validate_project(project)
        if errors:
            raise ValueError("; ".join(errors))

        target_dir = (self.storage_root / generation_id / project.artifact_id).resolve()
        if target_dir.exists():
            rmtree(target_dir)
        files = write_spring_boot_project(project, target_dir)
        zip_path = create_zip_archive(target_dir, target_dir.parent / f"{project.artifact_id}.zip")
        checksums = {path.relative_to(target_dir).as_posix(): checksum_file(path) for path in files}
        manifest = {
            "technology": "Spring Boot",
            "language": "Java",
            "database": "PostgreSQL",
            "database_name": project.artifact_id.replace("-", "_"),
            "database_port": 55432,
            "database_bootstrap": ["docker-compose.yml", "database/init.sql", "scripts/run.ps1", "scripts/run.sh"],
            "project_name": project.name,
            "artifact_id": project.artifact_id,
            "base_package": project.base_package,
            "generated_layers": ["config", "controller", "dto", "entity", "repository", "service", "exception"],
            "entity_count": len(project.entities),
            "relationship_count": len(project.relationships),
            "file_count": len(files),
            "zip_path": str(zip_path),
            "checksums": checksums,
            "source": "deterministic-rules-with-ai-plan",
        }
        return SpringBootGenerationResult(
            project_name=project.name,
            project_dir=target_dir,
            zip_path=zip_path,
            files=files,
            manifest=manifest,
        )
