from fastapi import APIRouter

router = APIRouter(prefix="/acceso-usuarios", tags=["gestion-acceso-usuarios"])


@router.get("/health")
def module_health() -> dict[str, str]:
    return {"status": "ok", "module": "gestion_acceso_usuarios"}

