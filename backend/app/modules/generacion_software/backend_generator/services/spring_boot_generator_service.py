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
from app.modules.generacion_software.coordinated_generator.contracts import GenerationPlan
from app.modules.generacion_software.coordinated_generator.emitters import emit_spring_semantics


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

    def generate(
        self,
        intermediate_model: dict,
        name: str,
        generation_id: str,
        *,
        generation_plan: GenerationPlan | None = None,
    ) -> SpringBootGenerationResult:
        project = parse_intermediate_model(intermediate_model, name)
        errors = validate_project(project)
        if errors:
            raise ValueError("; ".join(errors))

        target_dir = (self.storage_root / generation_id / project.artifact_id).resolve()
        if target_dir.exists():
            rmtree(target_dir)
        files = write_spring_boot_project(project, target_dir)
        if generation_plan is not None:
            files.extend(emit_spring_semantics(generation_plan, target_dir))
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
            "generator_version": "5.0",
        }
        return SpringBootGenerationResult(
            project_name=project.name,
            project_dir=target_dir,
            zip_path=zip_path,
            files=files,
            manifest=manifest,
        )
