"""add the resumable AI message migration index

Revision ID: f8b2c3d4e5f6
Revises: e7a1b2c3d4e5
"""

from collections.abc import Sequence

from alembic import op

revision: str = "f8b2c3d4e5f6"
down_revision: str | None = "e7a1b2c3d4e5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_ai_messages_created_id",
        "ai_messages",
        ["created_at", "id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_ai_messages_created_id", table_name="ai_messages")
