"""Add optimistic revision to UML method specifications.

Revision ID: e5f9a2b3c4d5
Revises: d4e8f1a2b3c4
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e5f9a2b3c4d5"
down_revision: str | None = "d4e8f1a2b3c4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "uml_method_specifications",
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_check_constraint(
        "ck_uml_method_specifications_revision",
        "uml_method_specifications",
        "revision > 0",
    )
    op.alter_column("uml_method_specifications", "revision", server_default=None)


def downgrade() -> None:
    op.drop_constraint(
        "ck_uml_method_specifications_revision",
        "uml_method_specifications",
        type_="check",
    )
    op.drop_column("uml_method_specifications", "revision")
