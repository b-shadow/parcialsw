"""phase6 flutter visual editor

Revision ID: a7b1c2d3e4f5
Revises: f6a0b3c4d5e6
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a7b1c2d3e4f5"
down_revision: str | None = "f6a0b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("flutter_theme_settings", sa.Column("revision", sa.Integer(), nullable=False, server_default="1"))
    op.create_table(
        "flutter_theme_presets",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("config_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("schema_version > 0", name="ck_flutter_theme_preset_schema_version"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_flutter_theme_presets_project_id", "flutter_theme_presets", ["project_id"])
    op.execute("CREATE UNIQUE INDEX uq_flutter_theme_preset_project_name_ci "
               "ON flutter_theme_presets (project_id, lower(name))")


def downgrade() -> None:
    op.drop_table("flutter_theme_presets")
    op.drop_column("flutter_theme_settings", "revision")
