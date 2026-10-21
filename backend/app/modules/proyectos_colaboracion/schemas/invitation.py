"""Esquemas Pydantic para invitaciones de proyectos (V2.3)."""

from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, EmailStr


class InvitationCreateRequest(BaseModel):
    email: EmailStr
    project_role: Literal["EDITOR", "LECTOR"] = "EDITOR"


class InvitationResponse(BaseModel):
    id: UUID
    project_id: UUID
    project_name: str
    invited_email: str
    project_role: str
    status: str
    invited_by_name: str
    expires_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
