from fastapi import APIRouter

router = APIRouter(prefix="/generacion-software", tags=["transformacion-generacion-software"])


@router.get("/health")
def estado_modulo() -> dict[str, str]:
    return {"status": "ok", "module": "transformacion_generacion_software"}

