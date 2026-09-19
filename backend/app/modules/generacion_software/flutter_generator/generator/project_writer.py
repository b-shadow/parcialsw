from dataclasses import dataclass
from pathlib import Path

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


def write_flutter_project(project: FlutterProject, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for generated_file in build_file_set(project):
        target = output_dir / generated_file.relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(generated_file.content, encoding="utf-8")
        written.append(target)
    return written
