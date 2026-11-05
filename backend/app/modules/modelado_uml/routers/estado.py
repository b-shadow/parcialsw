from fastapi import APIRouter

router = APIRouter(prefix="/modelado-uml", tags=["modelado-uml-inteligente"])


@router.get("/health")
def estado_modulo() -> dict[str, str]:
    return {"status": "ok", "module": "modelado_uml_inteligente"}

