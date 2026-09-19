from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.mixins import TimestampMixin, UuidPrimaryKeyMixin
from app.core.database.session import Base

if TYPE_CHECKING:
    from app.modules.proyectos_colaboracion.models.project_member import ProjectMember


class ProjectPermission(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "project_permissions"
    __table_args__ = (
        UniqueConstraint("member_id", "permission_code", name="uq_project_permissions_member_code"),
    )

    member_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("project_members.id"), index=True
    )
    permission_code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    is_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    member: Mapped[ProjectMember] = relationship(back_populates="permissions")
