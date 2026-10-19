"""enforce one global role per user

Revision ID: c9d3e4f5a6b7
Revises: b8c2d3e4f5a6
"""

from collections.abc import Sequence

from alembic import op

revision: str = "c9d3e4f5a6b7"
down_revision: str | None = "b8c2d3e4f5a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        WITH ranked_roles AS (
            SELECT ur.id,
                   row_number() OVER (
                       PARTITION BY ur.user_id
                       ORDER BY CASE r.name
                           WHEN 'ADMINISTRADOR' THEN 1
                           WHEN 'EDITOR' THEN 2
                           ELSE 3
                       END, ur.created_at, ur.id
                   ) AS position
            FROM user_roles ur
            JOIN roles r ON r.id = ur.role_id
        )
        DELETE FROM user_roles
        WHERE id IN (SELECT id FROM ranked_roles WHERE position > 1)
        """
    )
    op.execute(
        """
        UPDATE user_roles
        SET role_id = (SELECT id FROM roles WHERE name = 'EDITOR')
        WHERE role_id = (SELECT id FROM roles WHERE name = 'ORGANIZADOR')
        """
    )
    op.drop_constraint("uq_user_roles_user_role", "user_roles", type_="unique")
    op.create_unique_constraint("uq_user_roles_user", "user_roles", ["user_id"])
    op.execute("DELETE FROM roles WHERE name = 'ORGANIZADOR'")


def downgrade() -> None:
    op.execute(
        """
        INSERT INTO roles (id, name, description, is_system, created_at, updated_at)
        VALUES (
            '00000000-0000-4000-8000-000000000003',
            'ORGANIZADOR',
            'Rol historico; la organizacion activa pertenece a project_members.',
            true,
            now(),
            now()
        )
        ON CONFLICT (name) DO NOTHING
        """
    )
    op.drop_constraint("uq_user_roles_user", "user_roles", type_="unique")
    op.create_unique_constraint(
        "uq_user_roles_user_role", "user_roles", ["user_id", "role_id"]
    )
