import subprocess
from dataclasses import dataclass
from pathlib import Path
from shutil import which

from app.modules.generacion_software.flutter_generator.templates import (
    render_analysis_options,
    render_api_client,
    render_app_router,
    render_app_theme,
    render_entity_form_screen,
    render_entity_list_screen,
    render_entity_model,
    render_entity_provider,
    render_entity_service,
    render_main,
    render_pubspec,
    render_readme,
    render_shared_button,
    render_web_index,
    render_web_manifest,
)
from app.modules.generacion_software.flutter_generator.uml_analyzer.model_analyzer import (
    FlutterProject,
)


@dataclass(frozen=True)
class GeneratedFlutterFile:
    relative_path: str
    content: str


@dataclass(frozen=True)
class FlutterWriteResult:
    files: list[Path]
    scaffolded_platforms: list[str]


def _scaffold_flutter_platforms(project: FlutterProject, output_dir: Path) -> list[str]:
    flutter = which("flutter")
    if flutter is None:
        return []

    subprocess.run(
        [
            flutter,
            "create",
            "--platforms=android,web",
            "--project-name",
            project.package_name,
            ".",
        ],
        cwd=output_dir,
        check=True,
        capture_output=True,
        text=True,
        timeout=180,
    )
    return ["android", "web"]


def build_file_set(project: FlutterProject) -> list[GeneratedFlutterFile]:
    files = [
        GeneratedFlutterFile("pubspec.yaml", render_pubspec(project)),
        GeneratedFlutterFile("analysis_options.yaml", render_analysis_options()),
        GeneratedFlutterFile("README.md", render_readme(project)),
        GeneratedFlutterFile("web/index.html", render_web_index(project)),
        GeneratedFlutterFile("web/manifest.json", render_web_manifest(project)),
        GeneratedFlutterFile("lib/main.dart", render_main(project)),
        GeneratedFlutterFile("lib/core/network/api_client.dart", render_api_client(project)),
        GeneratedFlutterFile("lib/core/routes/app_router.dart", render_app_router(project)),
        GeneratedFlutterFile("lib/shared/themes/app_theme.dart", render_app_theme()),
        GeneratedFlutterFile("lib/shared/widgets/primary_action_button.dart", render_shared_button()),
    ]
    for entity in project.entities:
        module = entity.module_name
        files.extend(
            [
                GeneratedFlutterFile(f"lib/modules/{module}/{module}_model.dart", render_entity_model(entity)),
                GeneratedFlutterFile(f"lib/modules/{module}/{module}_service.dart", render_entity_service(entity)),
                GeneratedFlutterFile(f"lib/modules/{module}/{module}_provider.dart", render_entity_provider(entity)),
                GeneratedFlutterFile(f"lib/modules/{module}/{module}_list_screen.dart", render_entity_list_screen(entity)),
                GeneratedFlutterFile(f"lib/modules/{module}/{module}_form_screen.dart", render_entity_form_screen(entity)),
            ]
        )
    return files


def write_flutter_project(project: FlutterProject, output_dir: Path) -> FlutterWriteResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    scaffolded_platforms = _scaffold_flutter_platforms(project, output_dir)
    written: list[Path] = []
    for generated_file in build_file_set(project):
        target = output_dir / generated_file.relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(generated_file.content, encoding="utf-8")
        written.append(target)
    if scaffolded_platforms:
        for path in output_dir.rglob("*"):
            if path.is_file() and path not in written:
                written.append(path)
    return FlutterWriteResult(files=written, scaffolded_platforms=scaffolded_platforms)
