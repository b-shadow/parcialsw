"""phase7 versioning activity and durable notifications

Revision ID: b8c2d3e4f5a6
Revises: a7b1c2d3e4f5
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b8c2d3e4f5a6"
down_revision: str | None = "a7b1c2d3e4f5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("revision", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("projects", sa.Column("next_version_number", sa.Integer(), nullable=False, server_default="1"))
    op.execute(
        "UPDATE projects p SET next_version_number = COALESCE((SELECT MAX(version_number) + 1 "
        "FROM project_versions v WHERE v.project_id = p.id), 1)"
    )

    op.add_column("project_versions", sa.Column("kind", sa.String(40), nullable=False, server_default="manual"))
    op.add_column("project_versions", sa.Column("snapshot_schema_version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("project_versions", sa.Column("snapshot_hash", sa.String(64), nullable=False, server_default=""))
    op.add_column("project_versions", sa.Column("snapshot_size_bytes", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("project_versions", sa.Column("project_revision", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("project_versions", sa.Column("idempotency_key", sa.String(120)))
    op.add_column("project_versions", sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default="{}"))
    op.execute("UPDATE project_versions SET status = 'available' WHERE status IN ('saved', 'restored')")
    op.create_check_constraint("ck_project_versions_number_positive", "project_versions", "version_number > 0")
    op.create_check_constraint("ck_project_versions_schema_positive", "project_versions", "snapshot_schema_version > 0")
    op.create_check_constraint("ck_project_versions_kind", "project_versions", "kind IN ('manual', 'pre_restore_backup')")
    op.create_unique_constraint(
        "uq_project_versions_idempotency", "project_versions",
        ["project_id", "created_by_user_id", "idempotency_key"],
    )
    op.create_index("ix_project_versions_kind", "project_versions", ["kind"])
    op.create_index("ix_project_versions_project_created", "project_versions", ["project_id", "created_at"])

    for name, type_ in (
        ("actor_display_name", sa.String(160)), ("resource_type", sa.String(80)),
        ("resource_id", postgresql.UUID(as_uuid=True)),
        ("correlation_id", postgresql.UUID(as_uuid=True)),
        ("causation_id", postgresql.UUID(as_uuid=True)), ("summary_key", sa.String(160)),
    ):
        op.add_column("collaboration_events", sa.Column(name, type_))
    op.create_index("ix_collaboration_events_correlation_id", "collaboration_events", ["correlation_id"])

    op.create_table(
        "project_restore_operations",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("backup_version_id", postgresql.UUID(as_uuid=True)),
        sa.Column("requested_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("idempotency_key", sa.String(120), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("source_snapshot_hash", sa.String(64), nullable=False),
        sa.Column("before_snapshot_hash", sa.String(64), nullable=False),
        sa.Column("after_snapshot_hash", sa.String(64)),
        sa.Column("project_revision_before", sa.Integer(), nullable=False),
        sa.Column("project_revision_after", sa.Integer()),
        sa.Column("diagnostics_json", postgresql.JSONB(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_version_id"], ["project_versions.id"]),
        sa.ForeignKeyConstraint(["backup_version_id"], ["project_versions.id"]),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"]),
        sa.UniqueConstraint("project_id", "requested_by_user_id", "idempotency_key", name="uq_project_restore_idempotency"),
        sa.CheckConstraint("status IN ('validating', 'completed', 'failed')", name="ck_project_restore_status"),
    )
    op.create_index("ix_project_restore_operations_project_id", "project_restore_operations", ["project_id"])
    op.create_index("ix_project_restore_operations_requested_by_user_id", "project_restore_operations", ["requested_by_user_id"])

    op.create_table(
        "notifications",
        sa.Column("recipient_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True)),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True)),
        sa.Column("type", sa.String(80), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("title", sa.String(180), nullable=False),
        sa.Column("body", sa.String(500), nullable=False),
        sa.Column("resource_type", sa.String(80)),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True)),
        sa.Column("deep_link", postgresql.JSONB(), nullable=False),
        sa.Column("dedup_key", sa.String(200), nullable=False),
        sa.Column("group_key", sa.String(200)),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.Column("clicked_at", sa.DateTime(timezone=True)),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["recipient_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.UniqueConstraint("recipient_user_id", "dedup_key", name="uq_notifications_recipient_dedup"),
        sa.CheckConstraint("severity IN ('info', 'success', 'warning', 'error')", name="ck_notifications_severity"),
    )
    op.create_index("ix_notifications_recipient_occurred", "notifications", ["recipient_user_id", "occurred_at"])
    op.create_index("ix_notifications_recipient_read_at", "notifications", ["recipient_user_id", "read_at"])
    op.create_index("ix_notifications_project_id", "notifications", ["project_id"])
    op.create_index("ix_notifications_type", "notifications", ["type"])
    op.create_index("ix_notifications_group_key", "notifications", ["group_key"])

    op.create_table(
        "notification_preferences",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True)),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("in_app_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("push_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("muted_until", sa.DateTime(timezone=True)),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "project_id", "category", name="uq_notification_preferences_scope"),
    )
    op.create_index("ix_notification_preferences_user_id", "notification_preferences", ["user_id"])
    op.create_index(
        "uq_notification_preferences_global",
        "notification_preferences",
        ["user_id", "category"],
        unique=True,
        postgresql_where=sa.text("project_id IS NULL"),
    )

    op.create_table(
        "notification_outbox",
        sa.Column("notification_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True)),
        sa.Column("locked_by", sa.String(120)),
        sa.Column("last_error_code", sa.String(120)),
        sa.Column("delivered_at", sa.DateTime(timezone=True)),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["notification_id"], ["notifications.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("notification_id", "channel", name="uq_notification_outbox_channel"),
        sa.CheckConstraint("status IN ('pending', 'processing', 'delivered', 'retry', 'dead')", name="ck_notification_outbox_status"),
    )
    op.create_index("ix_notification_outbox_status_available", "notification_outbox", ["status", "available_at"])


def downgrade() -> None:
    op.drop_table("notification_outbox")
    op.drop_table("notification_preferences")
    op.drop_table("notifications")
    op.drop_table("project_restore_operations")
    op.drop_index("ix_collaboration_events_correlation_id", table_name="collaboration_events")
    for name in ("summary_key", "causation_id", "correlation_id", "resource_id", "resource_type", "actor_display_name"):
        op.drop_column("collaboration_events", name)
    op.drop_index("ix_project_versions_project_created", table_name="project_versions")
    op.drop_index("ix_project_versions_kind", table_name="project_versions")
    op.drop_constraint("uq_project_versions_idempotency", "project_versions", type_="unique")
    op.drop_constraint("ck_project_versions_kind", "project_versions", type_="check")
    op.drop_constraint("ck_project_versions_schema_positive", "project_versions", type_="check")
    op.drop_constraint("ck_project_versions_number_positive", "project_versions", type_="check")
    for name in ("metadata_json", "idempotency_key", "project_revision", "snapshot_size_bytes", "snapshot_hash", "snapshot_schema_version", "kind"):
        op.drop_column("project_versions", name)
    op.drop_column("projects", "next_version_number")
    op.drop_column("projects", "revision")
