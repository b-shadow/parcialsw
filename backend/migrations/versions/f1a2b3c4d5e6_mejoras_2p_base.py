"""mejoras 2p base: timestamps, gemini provider, pending invitations index

Revision ID: f1a2b3c4d5e6
Revises: da4e5f6a7b8c
Create Date: 2026-10-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f1a2b3c4d5e6"
down_revision: str | None = "da4e5f6a7b8c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Defaults de timestamps para coordinated_generations y flutter_theme_presets
    op.alter_column("coordinated_generations", "created_at", server_default=sa.text("now()"))
    op.alter_column("coordinated_generations", "updated_at", server_default=sa.text("now()"))
    op.alter_column("flutter_theme_presets", "created_at", server_default=sa.text("now()"))
    op.alter_column("flutter_theme_presets", "updated_at", server_default=sa.text("now()"))

    # 2. Check constraint en ai_project_settings para permitir 'gemini'
    op.drop_constraint("ck_ai_project_settings_provider", "ai_project_settings", type_="check")
    op.create_check_constraint(
        "ck_ai_project_settings_provider",
        "ai_project_settings",
        "preferred_provider IN ('ollama','gemini','rule_engine')",
    )

    # 3. Índice único parcial para invitaciones pendientes por proyecto y correo (case-insensitive)
    op.create_index(
        "uq_project_invitations_pending",
        "project_invitations",
        ["project_id", sa.text("lower(invited_email)")],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
    )


def downgrade() -> None:
    # 3. Revertir índice
    op.drop_index(
        "uq_project_invitations_pending",
        table_name="project_invitations",
        postgresql_where=sa.text("status = 'pending'"),
    )

    # 2. Revertir check constraint de ai_project_settings
    op.drop_constraint("ck_ai_project_settings_provider", "ai_project_settings", type_="check")
    op.execute(
        "UPDATE ai_project_settings SET preferred_provider = 'ollama' WHERE preferred_provider = 'gemini'"
    )
    op.create_check_constraint(
        "ck_ai_project_settings_provider",
        "ai_project_settings",
        "preferred_provider IN ('ollama','rule_engine')",
    )

    # 1. Revertir defaults de timestamps
    op.alter_column("flutter_theme_presets", "updated_at", server_default=None)
    op.alter_column("flutter_theme_presets", "created_at", server_default=None)
    op.alter_column("coordinated_generations", "updated_at", server_default=None)
    op.alter_column("coordinated_generations", "created_at", server_default=None)
