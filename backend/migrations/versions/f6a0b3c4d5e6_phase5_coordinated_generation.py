"""phase5 coordinated generation

Revision ID: f6a0b3c4d5e6
Revises: e5f9a2b3c4d5
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f6a0b3c4d5e6"
down_revision: str | None = "e5f9a2b3c4d5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "coordinated_generations",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("transformation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("backend_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("frontend_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("client_request_id", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("stage", sa.String(length=40), nullable=False),
        sa.Column("plan_hash", sa.String(length=64), nullable=True),
        sa.Column("plan_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("diagnostics", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("manifest", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("artifact_path", sa.String(length=500), nullable=True),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["backend_id"], ["generated_backends.id"]),
        sa.ForeignKeyConstraint(["frontend_id"], ["generated_frontends.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["transformation_id"], ["uml_transformations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "transformation_id",
            "requested_by_user_id",
            "client_request_id",
            name="uq_coordinated_generation_idempotency",
        ),
    )
    for column in ("project_id", "transformation_id", "requested_by_user_id", "status", "plan_hash"):
        op.create_index(f"ix_coordinated_generations_{column}", "coordinated_generations", [column])


def downgrade() -> None:
    op.drop_table("coordinated_generations")
