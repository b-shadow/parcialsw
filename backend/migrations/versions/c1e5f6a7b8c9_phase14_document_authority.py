"""record MongoDB authority for document-backed aggregates

Revision ID: c1e5f6a7b8c9
Revises: b0d4e5f6a7b8
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c1e5f6a7b8c9"
down_revision: str | None = "b0d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "uml_diagrams",
        sa.Column(
            "content_storage", sa.String(length=20), server_default="mongodb", nullable=False
        ),
    )
    op.add_column(
        "ai_conversations",
        sa.Column(
            "message_storage", sa.String(length=20), server_default="mongodb", nullable=False
        ),
    )
    op.add_column(
        "project_versions",
        sa.Column(
            "snapshot_storage", sa.String(length=20), server_default="mongodb", nullable=False
        ),
    )
    op.create_check_constraint(
        "ck_uml_diagrams_content_storage",
        "uml_diagrams",
        "content_storage = 'mongodb'",
    )
    op.create_check_constraint(
        "ck_ai_conversations_message_storage",
        "ai_conversations",
        "message_storage = 'mongodb'",
    )
    op.create_check_constraint(
        "ck_project_versions_snapshot_storage",
        "project_versions",
        "snapshot_storage = 'mongodb'",
    )


def downgrade() -> None:
    op.drop_constraint("ck_project_versions_snapshot_storage", "project_versions", type_="check")
    op.drop_constraint("ck_ai_conversations_message_storage", "ai_conversations", type_="check")
    op.drop_constraint("ck_uml_diagrams_content_storage", "uml_diagrams", type_="check")
    op.drop_column("project_versions", "snapshot_storage")
    op.drop_column("ai_conversations", "message_storage")
    op.drop_column("uml_diagrams", "content_storage")
