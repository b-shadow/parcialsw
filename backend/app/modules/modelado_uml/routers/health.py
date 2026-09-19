from fastapi import APIRouter

router = APIRouter(prefix="/modelado-uml", tags=["modelado-uml-inteligente"])


@router.get("/health")
def module_health() -> dict[str, str]:
    return {"status": "ok", "module": "modelado_uml_inteligente"}

