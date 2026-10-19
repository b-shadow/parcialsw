import json
import os
import re
import shutil
import subprocess
import zipfile
from dataclasses import dataclass
from pathlib import Path

from app.modules.generacion_software.backend_generator import SpringBootGeneratorService
from app.modules.generacion_software.coordinated_generator.compiler import (
    compile_generation_plan,
)
from app.modules.generacion_software.coordinated_generator.contracts import GenerationPlan
from app.modules.generacion_software.coordinated_generator.validators import (
    ensure_plan_ready,
    validate_cross_contract,
)
from app.modules.generacion_software.flutter_generator import FlutterGeneratorService


@dataclass(frozen=True)
class CoordinatedGenerationResult:
    plan: GenerationPlan
    root_dir: Path
    backend_dir: Path
    frontend_dir: Path
    bundle_path: Path
    manifest: dict


class CoordinatedGeneratorService:
    def __init__(self, storage_root: Path | None = None) -> None:
        self.storage_root = storage_root or Path("..") / "storage" / "generated" / "coordinated"

    def preflight(
        self,
        intermediate_model: dict,
        name: str,
        *,
        source_transformation_id: str | None = None,
        theme: dict | None = None,
    ) -> GenerationPlan:
        return compile_generation_plan(
            intermediate_model,
            name,
            source_transformation_id=source_transformation_id,
            theme=theme,
        )

    def generate(
        self,
        intermediate_model: dict,
        name: str,
        generation_id: str,
        *,
        api_base_url: str = "http://localhost:8080",
        theme: dict | None = None,
        verify: bool = True,
        allow_unverified: bool = False,
        source_transformation_id: str | None = None,
    ) -> CoordinatedGenerationResult:
        plan = ensure_plan_ready(
            self.preflight(
                intermediate_model,
                name,
                source_transformation_id=source_transformation_id,
                theme=theme,
            )
        )
        final_root = (self.storage_root / generation_id).resolve()
        staging_root = (self.storage_root / f".{generation_id}.staging").resolve()
        if staging_root.exists():
            shutil.rmtree(staging_root)
        staging_root.mkdir(parents=True, exist_ok=True)
        try:
            backend = SpringBootGeneratorService(staging_root / "backend").generate(
                intermediate_model,
                name,
                "project",
                generation_plan=plan,
            )
            frontend = FlutterGeneratorService(staging_root / "frontend").generate(
                intermediate_model,
                f"{name} Mobile",
                "project",
                api_base_url=api_base_url,
                theme_config=theme,
                generation_plan=plan,
            )
            cross = validate_cross_contract(plan, backend.manifest, frontend.manifest)
            cross_errors = [item for item in cross if item.severity == "error"]
            if cross_errors:
                raise ValueError("; ".join(item.message for item in cross_errors))
            secret_findings = _scan_secrets(backend.project_dir, frontend.project_dir)
            if secret_findings:
                raise ValueError("Se detectaron secretos potenciales: " + ", ".join(secret_findings))
            verification = (
                {
                    "backend": _verify_backend(backend.project_dir),
                    "frontend": _verify_frontend(frontend.project_dir),
                }
                if verify
                else {
                    "backend": _not_run("Verificacion no solicitada"),
                    "frontend": _not_run("Verificacion no solicitada"),
                }
            )
            failures = [
                key for key, value in verification.items() if value["status"] == "failed"
            ]
            unavailable = [
                key
                for key, value in verification.items()
                if value["status"] in {"not_run", "generated_unverified"}
            ]
            if failures:
                raise ValueError("Fallo la verificacion de: " + ", ".join(failures))
            if unavailable and not allow_unverified:
                raise ValueError(
                    "No fue posible verificar: "
                    + ", ".join(unavailable)
                    + ". Active allow_unverified de forma explicita."
                )
            backend_manifest = {
                **backend.manifest,
                "zip_path": backend.zip_path.relative_to(staging_root).as_posix(),
            }
            frontend_manifest = {
                **frontend.manifest,
                "zip_path": frontend.zip_path.relative_to(staging_root).as_posix(),
            }
            manifest = {
                "schema_version": 1,
                "generation_id": generation_id,
                "plan_hash": plan.canonical_hash,
                "status": "verified" if not unavailable else "generated_unverified",
                "backend": backend_manifest,
                "frontend": frontend_manifest,
                "verification": verification,
                "cross_validation": {
                    "status": "passed",
                    "diagnostics": [item.model_dump(mode="json") for item in cross],
                },
                "security": {"secret_scan": "passed"},
            }
            (staging_root / "generation-manifest.json").write_text(
                json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
            )
            bundle = staging_root / f"{plan.project.artifact_id}-full-stack.zip"
            _bundle(staging_root, bundle)
            if final_root.exists():
                shutil.rmtree(final_root)
            staging_root.replace(final_root)
            return CoordinatedGenerationResult(
                plan=plan,
                root_dir=final_root,
                backend_dir=_relocated(backend.project_dir, staging_root, final_root),
                frontend_dir=_relocated(frontend.project_dir, staging_root, final_root),
                bundle_path=final_root / bundle.name,
                manifest=manifest,
            )
        except Exception:
            if staging_root.exists():
                shutil.rmtree(staging_root)
            raise


def _relocated(path: Path, old_root: Path, new_root: Path) -> Path:
    return new_root / path.relative_to(old_root)


def _not_run(detail: str) -> dict:
    return {"status": "not_run", "commands": [], "detail": detail}


def _run(command: list[str], cwd: Path, timeout: int) -> dict:
    env = os.environ.copy()
    env.pop("AWS_SECRET_ACCESS_KEY", None)
    env.pop("OPENAI_API_KEY", None)
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"command": command, "exit_code": None, "status": "failed", "output": "Tiempo excedido"}
    output = "\n".join(part for part in (completed.stdout, completed.stderr) if part)[-6000:]
    return {
        "command": command,
        "exit_code": completed.returncode,
        "status": "passed" if completed.returncode == 0 else "failed",
        "output": output,
    }


def _verify_backend(project_dir: Path) -> dict:
    executable = shutil.which("mvn")
    wrapper = project_dir / ("mvnw.cmd" if os.name == "nt" else "mvnw")
    if wrapper.exists():
        executable = str(wrapper)
    if not executable:
        return {"status": "generated_unverified", "commands": [], "detail": "Maven no disponible"}
    result = _run([executable, "-q", "test"], project_dir, 300)
    return {
        "status": "verified" if result["status"] == "passed" else "failed",
        "commands": [result],
        "detail": "mvn test",
    }


def _verify_frontend(project_dir: Path) -> dict:
    flutter = shutil.which("flutter")
    if not flutter:
        return {"status": "generated_unverified", "commands": [], "detail": "Flutter no disponible"}
    commands = [
        _run([flutter, "pub", "get"], project_dir, 300),
        _run([flutter, "analyze"], project_dir, 300),
        _run([flutter, "test"], project_dir, 300),
        _run([flutter, "build", "web", "--release"], project_dir, 600),
    ]
    return {
        "status": "verified" if all(item["status"] == "passed" for item in commands) else "failed",
        "commands": commands,
        "detail": "flutter pub get, analyze, test y build web --release",
    }


SECRET_PATTERNS = (
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)(secret|password|api[_-]?key)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
)


def _scan_secrets(*roots: Path) -> list[str]:
    findings = []
    ignored = {".git", ".dart_tool", "build", "target"}
    for root in roots:
        for path in root.rglob("*"):
            if not path.is_file() or any(part in ignored for part in path.parts):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if any(pattern.search(text) for pattern in SECRET_PATTERNS):
                findings.append(path.relative_to(root).as_posix())
    return sorted(set(findings))


def _bundle(root: Path, target: Path) -> None:
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(root.rglob("*")):
            if path.is_file() and path != target and path.suffix != ".zip":
                archive.write(path, path.relative_to(root).as_posix())
