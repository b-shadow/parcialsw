"""Routers para gestión de invitaciones al proyecto (Ola 0 vacíos)."""

from fastapi import APIRouter

router = APIRouter(prefix="/projects", tags=["invitaciones"])
my_router = APIRouter(prefix="/invitations", tags=["invitaciones"])
