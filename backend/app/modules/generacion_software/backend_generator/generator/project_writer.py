from dataclasses import dataclass
from pathlib import Path

from app.modules.generacion_software.backend_generator.analyzer.model_analyzer import (
    SpringBootProject,
)
from app.modules.generacion_software.backend_generator.templates import (
    package_path,
    render_application,
    render_application_properties,
    render_controller,
    render_database_init,
    render_docker_compose,
    render_dto_request,
    render_dto_response,
    render_entity,
    render_env_example,
    render_exception_handler,
    render_not_found_exception,
    render_pom,
    render_readme,
    render_repository,
    render_run_script_ps1,
    render_run_script_sh,
    render_security_config,
    render_service,
)


@dataclass(frozen=True)
class GeneratedFile:
    relative_path: str
    content: str


def build_file_set(project: SpringBootProject) -> list[GeneratedFile]:
    base = f"src/main/java/{package_path(project.base_package)}"
    files = [
        GeneratedFile("pom.xml", render_pom(project)),
        GeneratedFile("README.md", render_readme(project)),
        GeneratedFile(".env.example", render_env_example(project)),
        GeneratedFile("docker-compose.yml", render_docker_compose(project)),
        GeneratedFile("database/init.sql", render_database_init(project)),
        GeneratedFile("scripts/run.ps1", render_run_script_ps1(project)),
        GeneratedFile("scripts/run.sh", render_run_script_sh(project)),
        GeneratedFile(f"{base}/{project.name}Application.java", render_application(project)),
        GeneratedFile("src/main/resources/application.properties", render_application_properties(project)),
        GeneratedFile(f"{base}/config/SecurityConfig.java", render_security_config(project)),
        GeneratedFile(f"{base}/exception/ResourceNotFoundException.java", render_not_found_exception(project)),
        GeneratedFile(f"{base}/exception/GlobalExceptionHandler.java", render_exception_handler(project)),
    ]
    for entity in project.entities:
        files.extend(
            [
                GeneratedFile(f"{base}/entity/{entity.name}.java", render_entity(project, entity)),
                GeneratedFile(f"{base}/dto/{entity.name}Request.java", render_dto_request(project, entity)),
                GeneratedFile(f"{base}/dto/{entity.name}Response.java", render_dto_response(project, entity)),
                GeneratedFile(f"{base}/repository/{entity.name}Repository.java", render_repository(project, entity)),
                GeneratedFile(f"{base}/service/{entity.name}Service.java", render_service(project, entity)),
                GeneratedFile(f"{base}/controller/{entity.name}Controller.java", render_controller(project, entity)),
            ]
        )
    return files


def write_spring_boot_project(project: SpringBootProject, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for generated_file in build_file_set(project):
        target = output_dir / generated_file.relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(generated_file.content, encoding="utf-8")
        written.append(target)
    return written
