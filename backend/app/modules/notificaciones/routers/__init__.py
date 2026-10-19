from fastapi import APIRouter

from app.modules.notificaciones.routers.notifications import router as inbox_router
from app.modules.notificaciones.routers.push import router as push_router

router = APIRouter()
router.include_router(inbox_router)
router.include_router(push_router)

__all__ = ["router"]
