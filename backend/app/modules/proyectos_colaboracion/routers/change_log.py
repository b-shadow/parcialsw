"""Router para el registro de cambios (Change Log NoSQL)."""

from fastapi import APIRouter

router = APIRouter(prefix="/projects", tags=["registro-cambios"])
