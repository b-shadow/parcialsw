"""allow multiple AI chats per project

Revision ID: da4e5f6a7b8c
Revises: c9d3e4f5a6b7
Create Date: 2026-10-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "da4e5f6a7b8c"
down_revision: str | None = "c9d3e4f5a6b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "ai_conversations",
        sa.Column("title", sa.String(length=160), nullable=False, server_default="Chat principal"),
    )
    op.add_column(
        "ai_conversations",
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_ai_conversations_created_by_user",
        "ai_conversations",
        "users",
        ["created_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_constraint("uq_ai_conversations_project", "ai_conversations", type_="unique")
    op.create_index(
        "ix_ai_conversations_project_updated",
        "ai_conversations",
        ["project_id", "updated_at"],
        unique=False,
    )
    op.alter_column("ai_conversations", "title", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_ai_conversations_project_updated", table_name="ai_conversations")
    op.create_unique_constraint(
        "uq_ai_conversations_project", "ai_conversations", ["project_id"]
    )
    op.drop_constraint(
        "fk_ai_conversations_created_by_user", "ai_conversations", type_="foreignkey"
    )
    op.drop_column("ai_conversations", "created_by_user_id")
    op.drop_column("ai_conversations", "title")
