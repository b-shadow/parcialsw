"""Move the active Flutter theme into projects.settings.

Revision ID: b6d8e0f2a4c5
Revises: a4f6c8d0e2b3
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b6d8e0f2a4c5"
down_revision: str = "a4f6c8d0e2b3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
        UPDATE projects AS p SET settings = jsonb_set(
            COALESCE(p.settings, '{}'::jsonb), '{flutter_theme}',
            jsonb_build_object(
                'id', t.id, 'config_json', t.config_json,
                'preset_name', t.preset_name, 'schema_version', t.schema_version,
                'revision', t.revision,
                'created_by_user_id', t.created_by_user_id,
                'updated_by_user_id', t.updated_by_user_id,
                'created_at', t.created_at, 'updated_at', t.updated_at
            ), true
        )
        FROM flutter_theme_settings AS t WHERE t.project_id = p.id
    """)
    op.drop_table("flutter_theme_settings")


def downgrade() -> None:
    op.create_table(
        "flutter_theme_settings",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("config_json", postgresql.JSONB(), nullable=False),
        sa.Column("preset_name", sa.String(120), nullable=True),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("project_id", name="uq_flutter_theme_settings_project"),
        sa.CheckConstraint("schema_version > 0", name="ck_flutter_theme_settings_schema_version"),
    )
    op.create_index("ix_flutter_theme_settings_project_id", "flutter_theme_settings", ["project_id"])
    op.execute("""
        INSERT INTO flutter_theme_settings (
            id, project_id, config_json, preset_name, schema_version, revision,
            created_by_user_id, updated_by_user_id, created_at, updated_at
        )
        SELECT (p.settings->'flutter_theme'->>'id')::uuid, p.id,
            p.settings->'flutter_theme'->'config_json',
            p.settings->'flutter_theme'->>'preset_name',
            (p.settings->'flutter_theme'->>'schema_version')::integer,
            (p.settings->'flutter_theme'->>'revision')::integer,
            (p.settings->'flutter_theme'->>'created_by_user_id')::uuid,
            (p.settings->'flutter_theme'->>'updated_by_user_id')::uuid,
            (p.settings->'flutter_theme'->>'created_at')::timestamptz,
            (p.settings->'flutter_theme'->>'updated_at')::timestamptz
        FROM projects p WHERE p.settings ? 'flutter_theme'
    """)
    op.execute("UPDATE projects SET settings = settings - 'flutter_theme' WHERE settings ? 'flutter_theme'")
