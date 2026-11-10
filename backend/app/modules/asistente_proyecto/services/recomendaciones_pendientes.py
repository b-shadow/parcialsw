"""Evita volver a ofrecer hallazgos que ya esperan una decisión del equipo."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.asistente_proyecto.models import RecomendacionIA


def clave_recomendacion(title: str, description: str) -> tuple[str, str]:
    return (" ".join(title.casefold().split()), " ".join(description.casefold().split()))


def claves_abiertas(db: Session, project_id) -> set[tuple[str, str]]:
    items = db.scalars(
        select(RecomendacionIA).where(
            RecomendacionIA.project_id == project_id,
            RecomendacionIA.status == "open",
        )
    )
    return {clave_recomendacion(item.title, item.description) for item in items}
