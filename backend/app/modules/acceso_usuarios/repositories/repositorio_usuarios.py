from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.acceso_usuarios.models import Usuario


class RepositorioUsuarios:
    def __init__(self, db: Session) -> None:
        self.db = db

    def obtener_por_id(self, user_id: UUID) -> Usuario | None:
        return self.db.get(Usuario, user_id)

    def obtener_por_correo(self, email: str) -> Usuario | None:
        return self.db.scalar(select(Usuario).where(Usuario.email == email.lower()))

    def list(self) -> list[Usuario]:
        return list(self.db.scalars(select(Usuario).order_by(Usuario.created_at.desc())))

    def add(self, user: Usuario) -> Usuario:
        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)
        return user
