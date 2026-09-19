"""seed system roles

Revision ID: c081b7d17f22
Revises: 3984b20ad386
Create Date: 2026-09-07 06:30:21.013232
"""

from collections.abc import Sequence

from alembic import op

revision: str = "c081b7d17f22"
down_revision: str | None = "3984b20ad386"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO roles (id, name, description, is_system, created_at, updated_at)
        VALUES
            ('00000000-0000-4000-8000-000000000001', 'ADMINISTRADOR', 'Rol global con administracion completa de la plataforma.', true, now(), now()),
            ('00000000-0000-4000-8000-000000000002', 'EDITOR', 'Rol global base para usuarios que crean y editan proyectos.', true, now(), now()),
            ('00000000-0000-4000-8000-000000000003', 'ORGANIZADOR', 'Rol de referencia para administracion dentro de proyectos colaborativos.', true, now(), now())
        ON CONFLICT (name) DO NOTHING;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM roles
        WHERE name IN ('ADMINISTRADOR', 'EDITOR', 'ORGANIZADOR')
          AND is_system = true;
        """
    )
