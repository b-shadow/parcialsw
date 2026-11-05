from dataclasses import dataclass
from pathlib import Path

from app.modules.generacion_software.backend_generator.analyzer.analizador_modelo import (
    ProyectoSpringBoot,
)
from app.modules.generacion_software.backend_generator.templates import (
    renderizar_aplicacion,
    renderizar_configuracion_seguridad,
    renderizar_controlador,
    renderizar_docker_compose,
    renderizar_ejemplo_entorno,
    renderizar_entidad,
    renderizar_excepcion_no_encontrada,
    renderizar_inicializacion_bd,
    renderizar_manejador_excepciones,
    renderizar_pom,
    renderizar_propiedades_aplicacion,
    renderizar_readme,
    renderizar_repositorio,
    renderizar_respuesta_dto,
    renderizar_script_ejecucion_ps1,
    renderizar_script_ejecucion_sh,
    renderizar_servicio,
    renderizar_solicitud_dto,
    ruta_paquete,
)


@dataclass(frozen=True)
class ArchivoGenerado:
    relative_path: str
    content: str


def construir_conjunto_archivos(project: ProyectoSpringBoot) -> list[ArchivoGenerado]:
    base = f"src/main/java/{ruta_paquete(project.base_package)}"
    files = [
        ArchivoGenerado("pom.xml", renderizar_pom(project)),
        ArchivoGenerado("README.md", renderizar_readme(project)),
        ArchivoGenerado(".env.example", renderizar_ejemplo_entorno(project)),
        ArchivoGenerado("docker-compose.yml", renderizar_docker_compose(project)),
        ArchivoGenerado("database/init.sql", renderizar_inicializacion_bd(project)),
        ArchivoGenerado("scripts/run.ps1", renderizar_script_ejecucion_ps1(project)),
        ArchivoGenerado("scripts/run.sh", renderizar_script_ejecucion_sh(project)),
        ArchivoGenerado(f"{base}/{project.name}Application.java", renderizar_aplicacion(project)),
        ArchivoGenerado("src/main/resources/application.properties", renderizar_propiedades_aplicacion(project)),
        ArchivoGenerado(f"{base}/config/SecurityConfig.java", renderizar_configuracion_seguridad(project)),
        ArchivoGenerado(f"{base}/exception/ResourceNotFoundException.java", renderizar_excepcion_no_encontrada(project)),
        ArchivoGenerado(f"{base}/exception/GlobalExceptionHandler.java", renderizar_manejador_excepciones(project)),
    ]
    for entity in project.entities:
        files.extend(
            [
                ArchivoGenerado(f"{base}/entity/{entity.name}.java", renderizar_entidad(project, entity)),
                ArchivoGenerado(f"{base}/dto/{entity.name}Request.java", renderizar_solicitud_dto(project, entity)),
                ArchivoGenerado(f"{base}/dto/{entity.name}Response.java", renderizar_respuesta_dto(project, entity)),
                ArchivoGenerado(f"{base}/repository/{entity.name}Repository.java", renderizar_repositorio(project, entity)),
                ArchivoGenerado(f"{base}/service/{entity.name}Service.java", renderizar_servicio(project, entity)),
                ArchivoGenerado(f"{base}/controller/{entity.name}Controller.java", renderizar_controlador(project, entity)),
            ]
        )
    return files


def escribir_proyecto_spring_boot(project: ProyectoSpringBoot, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for generated_file in construir_conjunto_archivos(project):
        target = output_dir / generated_file.relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(generated_file.content, encoding="utf-8")
        written.append(target)
    return written
