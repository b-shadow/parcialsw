"""harden collaboration events

Revision ID: 8f39c4d7a2b1
Revises: c081b7d17f22
Create Date: 2026-10-14 15:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "8f39c4d7a2b1"
down_revision: str | None = "c081b7d17f22"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "collaboration_events",
        sa.Column("client_event_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "collaboration_events",
        sa.Column("sequence_number", sa.Integer(), nullable=True),
    )
    op.execute("UPDATE collaboration_events SET client_event_id = id")
    op.execute(
        """
        WITH numbered AS (
            SELECT id, ROW_NUMBER() OVER (
                PARTITION BY project_id ORDER BY created_at, id
            ) AS sequence_number
            FROM collaboration_events
        )
        UPDATE collaboration_events AS event
        SET sequence_number = numbered.sequence_number
        FROM numbered
        WHERE event.id = numbered.id
        """
    )
    op.alter_column("collaboration_events", "client_event_id", nullable=False)
    op.alter_column("collaboration_events", "sequence_number", nullable=False)
    op.create_unique_constraint(
        "uq_collaboration_events_project_sequence",
        "collaboration_events",
        ["project_id", "sequence_number"],
    )
    op.create_unique_constraint(
        "uq_collaboration_events_client_event",
        "collaboration_events",
        ["project_id", "user_id", "client_event_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_collaboration_events_client_event",
        "collaboration_events",
        type_="unique",
    )
    op.drop_constraint(
        "uq_collaboration_events_project_sequence",
        "collaboration_events",
        type_="unique",
    )
    op.drop_column("collaboration_events", "sequence_number")
    op.drop_column("collaboration_events", "client_event_id")
