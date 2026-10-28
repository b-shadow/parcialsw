"""retire SQL UML content and AI messages

Revision ID: d2f6a7b8c9d0
Revises: c1e5f6a7b8c9
Create Date: 2026-10-21
"""

from collections.abc import Sequence

from alembic import op

revision: str = "d2f6a7b8c9d0"
down_revision: str | None = "c1e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("ai_actions_source_message_id_fkey", "ai_actions", type_="foreignkey")
    op.drop_constraint(
        "ai_recommendations_source_message_id_fkey",
        "ai_recommendations",
        type_="foreignkey",
    )

    op.drop_table("uml_method_specifications")
    op.drop_table("uml_parameters")
    op.drop_table("uml_attributes")
    op.drop_table("uml_relationships")
    op.drop_table("uml_visual_elements")
    op.drop_table("uml_methods")
    op.drop_table("uml_classes")
    op.drop_table("ai_messages")

    op.create_index("ix_ai_actions_source_message_id", "ai_actions", ["source_message_id"])
    op.create_index(
        "ix_ai_recommendations_source_message_id",
        "ai_recommendations",
        ["source_message_id"],
    )


def downgrade() -> None:
    raise RuntimeError(
        "This destructive document-store cutover is irreversible. "
        "Restore the pre-cutover PostgreSQL/MongoDB backup instead."
    )
