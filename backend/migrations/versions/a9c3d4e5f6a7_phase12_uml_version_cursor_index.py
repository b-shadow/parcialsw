"""add the resumable UML version migration index

Revision ID: a9c3d4e5f6a7
Revises: f8b2c3d4e5f6
"""

from collections.abc import Sequence

from alembic import op

revision: str = "a9c3d4e5f6a7"
down_revision: str | None = "f8b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_project_versions_created_id",
        "project_versions",
        ["created_at", "id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_project_versions_created_id", table_name="project_versions")
