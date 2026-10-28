"""add the transactional MongoDB outbox

Revision ID: e7a1b2c3d4e5
Revises: da4e5f6a7b8c
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e7a1b2c3d4e5"
down_revision: str | None = "da4e5f6a7b8c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "nosql_outbox_events",
        sa.Column("aggregate_type", sa.String(length=80), nullable=False),
        sa.Column("aggregate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("idempotency_key", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_by", sa.String(length=120), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'retry', 'dead')",
            name="ck_nosql_outbox_status",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_nosql_outbox_idempotency"),
    )
    op.create_index(
        "ix_nosql_outbox_status_available",
        "nosql_outbox_events",
        ["status", "available_at"],
    )
    op.create_index(
        "ix_nosql_outbox_aggregate",
        "nosql_outbox_events",
        ["aggregate_type", "aggregate_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_nosql_outbox_aggregate", table_name="nosql_outbox_events")
    op.drop_index("ix_nosql_outbox_status_available", table_name="nosql_outbox_events")
    op.drop_table("nosql_outbox_events")
