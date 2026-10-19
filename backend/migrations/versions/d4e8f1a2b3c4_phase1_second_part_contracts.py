"""phase 1 second part contracts and persistence

Revision ID: d4e8f1a2b3c4
Revises: b21a9d4c6e70
Create Date: 2026-10-15 18:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d4e8f1a2b3c4"
down_revision: str | None = "b21a9d4c6e70"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "uml_method_specifications",
        sa.Column("method_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("operation_kind", sa.String(length=40), server_default="custom", nullable=False),
        sa.Column("exposure", sa.String(length=30), server_default="internal", nullable=False),
        sa.Column("preconditions", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("postconditions", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("business_rules", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("validations", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("side_effects", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("required_permissions", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("related_entities", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("backend_contract", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("frontend_contract", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("schema_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        *_timestamps(),
        sa.CheckConstraint(
            "operation_kind IN ('create','read','update','delete','search','calculate','business_action','custom')",
            name="ck_uml_method_specifications_operation_kind",
        ),
        sa.CheckConstraint(
            "exposure IN ('internal','api','user_action')",
            name="ck_uml_method_specifications_exposure",
        ),
        sa.CheckConstraint("schema_version > 0", name="ck_uml_method_specifications_schema_version"),
        sa.ForeignKeyConstraint(["method_id"], ["uml_methods.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("method_id", name="uq_uml_method_specifications_method"),
    )
    op.create_index("ix_uml_method_specifications_method_id", "uml_method_specifications", ["method_id"])

    op.create_table(
        "ai_project_settings",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("preferred_provider", sa.String(length=40), server_default="ollama", nullable=False),
        sa.Column(
            "model_name",
            sa.String(length=120),
            server_default="qwen2.5-coder:7b",
            nullable=False,
        ),
        sa.Column("fallback_enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("require_confirmation", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("max_context_messages", sa.Integer(), server_default="40", nullable=False),
        sa.Column("summary_trigger_messages", sa.Integer(), server_default="30", nullable=False),
        sa.Column("settings_json", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("preferred_provider IN ('ollama','rule_engine')", name="ck_ai_project_settings_provider"),
        sa.CheckConstraint("max_context_messages BETWEEN 5 AND 200", name="ck_ai_project_settings_max_context"),
        sa.CheckConstraint("summary_trigger_messages BETWEEN 5 AND 200", name="ck_ai_project_settings_summary_trigger"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", name="uq_ai_project_settings_project"),
    )
    op.create_index("ix_ai_project_settings_project_id", "ai_project_settings", ["project_id"])

    op.create_table(
        "ai_conversations",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="active", nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("summary_until_sequence", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_message_sequence", sa.Integer(), server_default="0", nullable=False),
        sa.Column("schema_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("status IN ('active','archived')", name="ck_ai_conversations_status"),
        sa.CheckConstraint("summary_until_sequence >= 0", name="ck_ai_conversations_summary_sequence"),
        sa.CheckConstraint("last_message_sequence >= 0", name="ck_ai_conversations_last_sequence"),
        sa.CheckConstraint("schema_version > 0", name="ck_ai_conversations_schema_version"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", name="uq_ai_conversations_project"),
    )
    op.create_index("ix_ai_conversations_project_id", "ai_conversations", ["project_id"])

    op.create_table(
        "ai_messages",
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("author_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("client_message_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="completed", nullable=False),
        sa.Column("detected_intents", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("references_json", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("role IN ('user','assistant','system','tool')", name="ck_ai_messages_role"),
        sa.CheckConstraint("status IN ('pending','streaming','completed','failed','cancelled')", name="ck_ai_messages_status"),
        sa.CheckConstraint("char_length(content) BETWEEN 1 AND 20000", name="ck_ai_messages_content"),
        sa.CheckConstraint(
            "role <> 'user' OR author_user_id IS NOT NULL",
            name="ck_ai_messages_user_author",
        ),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["conversation_id"], ["ai_conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("conversation_id", "sequence_number", name="uq_ai_messages_conversation_sequence"),
        sa.UniqueConstraint("conversation_id", "author_user_id", "client_message_id", name="uq_ai_messages_client_message"),
    )
    op.create_index("ix_ai_messages_project_sequence", "ai_messages", ["project_id", "sequence_number"])
    op.create_index("ix_ai_messages_correlation_id", "ai_messages", ["correlation_id"])

    op.create_table(
        "ai_actions",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_message_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action_type", sa.String(length=80), nullable=False),
        sa.Column("target_type", sa.String(length=80), nullable=True),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payload", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("risk_level", sa.String(length=20), server_default="low", nullable=False),
        sa.Column("requires_confirmation", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="proposed", nullable=False),
        sa.Column("confirmed_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result_json", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("idempotency_key", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("risk_level IN ('low','medium','high')", name="ck_ai_actions_risk"),
        sa.CheckConstraint("status IN ('proposed','confirmed','executing','applied','rejected','failed','cancelled')", name="ck_ai_actions_status"),
        sa.ForeignKeyConstraint(["confirmed_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["conversation_id"], ["ai_conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["source_message_id"], ["ai_messages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "idempotency_key", name="uq_ai_actions_idempotency"),
    )
    op.create_index("ix_ai_actions_project_id", "ai_actions", ["project_id"])
    op.create_index("ix_ai_actions_action_type", "ai_actions", ["action_type"])

    op.create_table(
        "ai_recommendations",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_message_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=20), server_default="info", nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("references_json", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="open", nullable=False),
        sa.Column("resolved_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("severity IN ('info','warning','critical')", name="ck_ai_recommendations_severity"),
        sa.CheckConstraint("status IN ('open','accepted','dismissed','resolved')", name="ck_ai_recommendations_status"),
        sa.ForeignKeyConstraint(["conversation_id"], ["ai_conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resolved_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["source_message_id"], ["ai_messages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_recommendations_project_id", "ai_recommendations", ["project_id"])
    op.create_index("ix_ai_recommendations_category", "ai_recommendations", ["category"])

    op.create_table(
        "flutter_theme_settings",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("config_json", postgresql.JSONB(), nullable=False),
        sa.Column("preset_name", sa.String(length=120), nullable=True),
        sa.Column("schema_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("schema_version > 0", name="ck_flutter_theme_settings_schema_version"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", name="uq_flutter_theme_settings_project"),
    )
    op.create_index("ix_flutter_theme_settings_project_id", "flutter_theme_settings", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_flutter_theme_settings_project_id", table_name="flutter_theme_settings")
    op.drop_table("flutter_theme_settings")
    op.drop_index("ix_ai_recommendations_category", table_name="ai_recommendations")
    op.drop_index("ix_ai_recommendations_project_id", table_name="ai_recommendations")
    op.drop_table("ai_recommendations")
    op.drop_index("ix_ai_actions_action_type", table_name="ai_actions")
    op.drop_index("ix_ai_actions_project_id", table_name="ai_actions")
    op.drop_table("ai_actions")
    op.drop_index("ix_ai_messages_correlation_id", table_name="ai_messages")
    op.drop_index("ix_ai_messages_project_sequence", table_name="ai_messages")
    op.drop_table("ai_messages")
    op.drop_index("ix_ai_conversations_project_id", table_name="ai_conversations")
    op.drop_table("ai_conversations")
    op.drop_index("ix_ai_project_settings_project_id", table_name="ai_project_settings")
    op.drop_table("ai_project_settings")
    op.drop_index("ix_uml_method_specifications_method_id", table_name="uml_method_specifications")
    op.drop_table("uml_method_specifications")
