"""add the resumable active UML migration index

Revision ID: b0d4e5f6a7b8
Revises: a9c3d4e5f6a7
"""

from collections.abc import Sequence

from alembic import op

revision: str = "b0d4e5f6a7b8"
down_revision: str | None = "a9c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_uml_diagrams_updated_id",
        "uml_diagrams",
        ["updated_at", "id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_uml_diagrams_updated_id", table_name="uml_diagrams")
