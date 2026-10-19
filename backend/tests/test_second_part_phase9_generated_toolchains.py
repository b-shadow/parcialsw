import os
import shutil
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest

from app.modules.generacion_software.backend_generator import SpringBootGeneratorService
from app.modules.generacion_software.flutter_generator import FlutterGeneratorService


def _model() -> dict:
    return {
        "classes": [
            {
                "id": "student",
                "name": "Estudiante",
                "attributes": [
                    {"name": "nombre", "data_type": "String", "is_required": True},
                    {"name": "fechaNacimiento", "data_type": "LocalDate"},
                ],
            },
            {
                "id": "course",
                "name": "Curso",
                "attributes": [
                    {"name": "nombre", "data_type": "String", "is_required": True},
                ],
            },
            {
                "id": "enrollment",
                "name": "Inscripcion",
                "attributes": [
                    {"name": "notaFinal", "data_type": "Double"},
                    {"name": "fecha", "data_type": "LocalDate", "is_required": True},
                ],
            },
        ],
        "relationships": [
            {
                "source_class_id": "student",
                "target_class_id": "course",
                "relationship_type": "association",
                "source_cardinality": "*",
                "target_cardinality": "*",
                "metadata_json": {"association_class_id": "enrollment"},
            }
        ],
    }


def _run(command: list[str], cwd: Path, timeout: int = 600) -> None:
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )
    assert result.returncode == 0, "\n".join(
        [f"Comando fallido: {' '.join(command)}", result.stdout[-4000:], result.stderr[-4000:]]
    )


@pytest.mark.skipif(
    os.getenv("CASE_VERIFY_GENERATED_SPRING") != "1",
    reason="Gate externo: habilitar CASE_VERIFY_GENERATED_SPRING=1 con Maven disponible.",
)
def test_generated_spring_project_compiles_without_manual_changes(tmp_path: Path) -> None:
    maven = shutil.which("mvn")
    assert maven, "Maven no esta disponible en PATH."
    result = SpringBootGeneratorService(tmp_path).generate(
        _model(), "Academico", str(uuid4())
    )

    _run([maven, "--batch-mode", "--no-transfer-progress", "test"], result.project_dir)


@pytest.mark.skipif(
    os.getenv("CASE_VERIFY_GENERATED_FLUTTER") != "1",
    reason="Gate externo: habilitar CASE_VERIFY_GENERATED_FLUTTER=1 con Flutter disponible.",
)
def test_generated_flutter_project_passes_full_toolchain(tmp_path: Path) -> None:
    flutter = shutil.which("flutter")
    dart = shutil.which("dart")
    assert flutter and dart, "Flutter y Dart deben estar disponibles en PATH."
    result = FlutterGeneratorService(tmp_path).generate(
        _model(),
        "Academico Mobile",
        str(uuid4()),
        api_base_url="http://10.0.2.2:8080",
    )

    _run([flutter, "pub", "get"], result.project_dir)
    _run(
        [dart, "format", "--output=none", "--set-exit-if-changed", "lib", "test"],
        result.project_dir,
    )
    _run([flutter, "analyze"], result.project_dir)
    _run([flutter, "test"], result.project_dir)
    _run([flutter, "build", "web"], result.project_dir, timeout=900)
