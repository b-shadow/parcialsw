from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.acceso_usuarios.models import Rol

GLOBAL_ROLE_NAMES = ("ADMINISTRADOR", "EDITOR")


class RepositorioRoles:
    def __init__(self, db: Session) -> None:
        self.db = db

    def obtener_por_nombre(self, name: str) -> Rol | None:
        return self.db.scalar(select(Rol).where(Rol.name == name))

    def obtener_por_id(self, role_id: UUID) -> Rol | None:
        return self.db.get(Rol, role_id)

    def list(self) -> list[Rol]:
        return list(
            self.db.scalars(
                select(Rol).where(Rol.name.in_(GLOBAL_ROLE_NAMES)).order_by(Rol.name)
            )
        )
