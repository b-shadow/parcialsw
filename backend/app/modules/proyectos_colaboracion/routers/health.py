from fastapi import APIRouter

router = APIRouter(prefix="/proyectos-colaboracion", tags=["gestion-proyectos-colaboracion"])


@router.get("/health")
def module_health() -> dict[str, str]:
    return {"status": "ok", "module": "gestion_proyectos_colaboracion"}

