"""Consolidate project AI settings and fixed project-role permissions.

Revision ID: a4f6c8d0e2b3
Revises: e3a7b8c9d0e1
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a4f6c8d0e2b3"
down_revision: str = "e3a7b8c9d0e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # La copia y el borrado ocurren en la misma transacción de Alembic.
    op.execute("""
        UPDATE projects AS p SET settings = jsonb_set(
            COALESCE(p.settings, '{}'::jsonb), '{ai}',
            jsonb_build_object(
                'id', a.id, 'enabled', a.enabled,
                'preferred_provider', a.preferred_provider, 'model_name', a.model_name,
                'fallback_enabled', a.fallback_enabled,
                'require_confirmation', a.require_confirmation,
                'max_context_messages', a.max_context_messages,
                'summary_trigger_messages', a.summary_trigger_messages,
                'settings_json', a.settings_json,
                'created_by_user_id', a.created_by_user_id,
                'updated_by_user_id', a.updated_by_user_id,
                'created_at', a.created_at, 'updated_at', a.updated_at
            ), true
        )
        FROM ai_project_settings AS a WHERE a.project_id = p.id
    """)
    op.drop_table("project_permissions")
    op.drop_table("ai_project_settings")


def downgrade() -> None:
    op.create_table(
        "project_permissions",
        sa.Column("member_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("project_members.id"), nullable=False),
        sa.Column("permission_code", sa.String(80), nullable=False),
        sa.Column("is_allowed", sa.Boolean(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("member_id", "permission_code", name="uq_project_permissions_member_code"),
    )
    op.create_index("ix_project_permissions_member_id", "project_permissions", ["member_id"])
    op.create_index("ix_project_permissions_permission_code", "project_permissions", ["permission_code"])
    op.create_table(
        "ai_project_settings",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("preferred_provider", sa.String(40), nullable=False),
        sa.Column("model_name", sa.String(120), nullable=False),
        sa.Column("fallback_enabled", sa.Boolean(), nullable=False),
        sa.Column("require_confirmation", sa.Boolean(), nullable=False),
        sa.Column("max_context_messages", sa.Integer(), nullable=False),
        sa.Column("summary_trigger_messages", sa.Integer(), nullable=False),
        sa.Column("settings_json", postgresql.JSONB(), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("project_id", name="uq_ai_project_settings_project"),
    )
    op.create_index("ix_ai_project_settings_project_id", "ai_project_settings", ["project_id"])
    op.execute("""
        INSERT INTO ai_project_settings (
            id, project_id, enabled, preferred_provider, model_name, fallback_enabled,
            require_confirmation, max_context_messages, summary_trigger_messages,
            settings_json, created_by_user_id, updated_by_user_id, created_at, updated_at
        )
        SELECT (p.settings->'ai'->>'id')::uuid, p.id,
            (p.settings->'ai'->>'enabled')::boolean,
            p.settings->'ai'->>'preferred_provider', p.settings->'ai'->>'model_name',
            (p.settings->'ai'->>'fallback_enabled')::boolean,
            (p.settings->'ai'->>'require_confirmation')::boolean,
            (p.settings->'ai'->>'max_context_messages')::integer,
            (p.settings->'ai'->>'summary_trigger_messages')::integer,
            p.settings->'ai'->'settings_json',
            (p.settings->'ai'->>'created_by_user_id')::uuid,
            (p.settings->'ai'->>'updated_by_user_id')::uuid,
            (p.settings->'ai'->>'created_at')::timestamptz,
            (p.settings->'ai'->>'updated_at')::timestamptz
        FROM projects p WHERE p.settings ? 'ai'
    """)
    op.execute("UPDATE projects SET settings = settings - 'ai' WHERE settings ? 'ai'")
