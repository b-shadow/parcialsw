import subprocess
from dataclasses import dataclass
from pathlib import Path
from shutil import which

from app.modules.generacion_software.flutter_generator.templates import (
    renderizar_boton_compartido,
    renderizar_cliente_api,
    renderizar_indice_web,
    renderizar_manifiesto_android,
    renderizar_manifiesto_web,
    renderizar_modelo_entidad,
    renderizar_opciones_analisis,
    renderizar_pantalla_formulario_entidad,
    renderizar_pantalla_lista_entidad,
    renderizar_png_referencia_tema,
    renderizar_principal,
    renderizar_proveedor_entidad,
    renderizar_prueba_widget,
    renderizar_pubspec,
    renderizar_readme,
    renderizar_rutas_aplicacion,
    renderizar_servicio_entidad,
    renderizar_tema_aplicacion,
)
from app.modules.generacion_software.flutter_generator.uml_analyzer.analizador_modelo import (
    ProyectoFlutter,
)


@dataclass(frozen=True)
class ArchivoFlutterGenerado:
    relative_path: str
    content: str | bytes


@dataclass(frozen=True)
class ResultadoEscrituraFlutter:
    files: list[Path]
    scaffolded_platforms: list[str]


def _crear_plataformas_flutter(project: ProyectoFlutter, output_dir: Path) -> list[str]:
    flutter = which("flutter")
    if flutter is None:
        return []

    command = [
        flutter,
        "create",
        "--platforms=android,web",
        "--no-pub",
        "--project-name",
        project.package_name,
        ".",
    ]
    try:
        subprocess.run(
            command,
            cwd=output_dir,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )
    except subprocess.CalledProcessError as exc:
        output = "\n".join(part for part in [exc.stdout, exc.stderr] if part).strip()
        detail = output or f"Flutter create fallo con codigo {exc.returncode}."
        raise ValueError(detail) from exc
    except subprocess.TimeoutExpired as exc:
        raise ValueError("Flutter create excedio el tiempo maximo de 180 segundos.") from exc
    return ["android", "web"]


def construir_conjunto_archivos(project: ProyectoFlutter) -> list[ArchivoFlutterGenerado]:
    files = [
        ArchivoFlutterGenerado("pubspec.yaml", renderizar_pubspec(project)),
        ArchivoFlutterGenerado("analysis_options.yaml", renderizar_opciones_analisis()),
        ArchivoFlutterGenerado("android/app/src/main/AndroidManifest.xml", renderizar_manifiesto_android(project)),
        ArchivoFlutterGenerado("README.md", renderizar_readme(project)),
        ArchivoFlutterGenerado("web/index.html", renderizar_indice_web(project)),
        ArchivoFlutterGenerado("web/manifest.json", renderizar_manifiesto_web(project)),
        ArchivoFlutterGenerado("test/widget_test.dart", renderizar_prueba_widget(project)),
        ArchivoFlutterGenerado("test/goldens/theme_tokens.png", renderizar_png_referencia_tema(project)),
        ArchivoFlutterGenerado("lib/main.dart", renderizar_principal(project)),
        ArchivoFlutterGenerado("lib/core/network/api_client.dart", renderizar_cliente_api(project)),
        ArchivoFlutterGenerado("lib/core/routes/app_router.dart", renderizar_rutas_aplicacion(project)),
        ArchivoFlutterGenerado("lib/shared/themes/app_theme.dart", renderizar_tema_aplicacion(project)),
        ArchivoFlutterGenerado("lib/shared/widgets/primary_action_button.dart", renderizar_boton_compartido(project)),
    ]
    for entity in project.entities:
        module = entity.module_name
        files.extend(
            [
                ArchivoFlutterGenerado(f"lib/modules/{module}/{module}_model.dart", renderizar_modelo_entidad(entity)),
                ArchivoFlutterGenerado(f"lib/modules/{module}/{module}_service.dart", renderizar_servicio_entidad(entity)),
                ArchivoFlutterGenerado(f"lib/modules/{module}/{module}_provider.dart", renderizar_proveedor_entidad(entity)),
                ArchivoFlutterGenerado(f"lib/modules/{module}/{module}_list_screen.dart", renderizar_pantalla_lista_entidad(entity)),
                ArchivoFlutterGenerado(f"lib/modules/{module}/{module}_form_screen.dart", renderizar_pantalla_formulario_entidad(entity, project.theme_config.show_field_labels)),
            ]
        )
    return files


def escribir_proyecto_flutter(project: ProyectoFlutter, output_dir: Path) -> ResultadoEscrituraFlutter:
    output_dir.mkdir(parents=True, exist_ok=True)
    scaffolded_platforms = _crear_plataformas_flutter(project, output_dir)
    written: list[Path] = []
    for generated_file in construir_conjunto_archivos(project):
        target = output_dir / generated_file.relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(generated_file.content, bytes):
            target.write_bytes(generated_file.content)
        else:
            target.write_text(generated_file.content, encoding="utf-8")
        written.append(target)
    if scaffolded_platforms:
        for path in output_dir.rglob("*"):
            if path.is_file() and path not in written:
                written.append(path)
    return ResultadoEscrituraFlutter(files=written, scaffolded_platforms=scaffolded_platforms)
