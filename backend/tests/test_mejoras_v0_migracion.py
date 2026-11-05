"""Pruebas de migración de la Ola 0 (V0.1)."""

import os

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text


@pytest.fixture
def test_db_url():
    url = os.getenv("CASE_TEST_DATABASE_URL")
    if not url:
        pytest.skip("CASE_TEST_DATABASE_URL no está definida. Omitiendo prueba de migración en BD real.")
    return url


def test_v0_migration_upgrade_and_downgrade(test_db_url):
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.attributes["database_url_override"] = test_db_url

    engine = create_engine(test_db_url)

    # Upgrade to head
    command.upgrade(alembic_cfg, "head")

    with engine.connect() as conn:
        # 1. Verificar que ninguna columna created_at o updated_at NOT NULL quede sin DEFAULT
        query = text("""
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND column_name IN ('created_at', 'updated_at')
              AND is_nullable = 'NO'
              AND column_default IS NULL;
        """)
        rows = conn.execute(query).fetchall()
        assert len(rows) == 0, f"Hay columnas NOT NULL sin default: {rows}"

        # 2. La configuración de IA ahora es un valor de projects.settings.ai.
        res = conn.execute(text("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name IN ('ai_project_settings', 'project_permissions');
        """)).fetchall()
        assert res == []
        assert conn.execute(text("SELECT count(*) FROM proyectos WHERE configuracion IS NULL")).scalar() == 0

    # Downgrade -1 y volver a subir a head
    command.downgrade(alembic_cfg, "-1")
    command.upgrade(alembic_cfg, "head")
