"""merge NoSQL migration and second-part improvements heads

Revision ID: e3a7b8c9d0e1
Revises: d2f6a7b8c9d0, f1a2b3c4d5e6
Create Date: 2026-10-28
"""

from collections.abc import Sequence

revision: str = "e3a7b8c9d0e1"
down_revision: tuple[str, str] = ("d2f6a7b8c9d0", "f1a2b3c4d5e6")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Converge both migration branches without additional schema changes."""


def downgrade() -> None:
    """Split the migration graph back into its two parent heads."""
