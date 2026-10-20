"""Pruebas de migración de la Ola 0 (V0.1)."""

import os
import pytest
from sqlalchemy import create_engine, text
from alembic import command
from alembic.config import Config


@pytest.fixture
def test_db_url():
    url = os.getenv("CASE_TEST_DATABASE_URL")
    if not url:
        pytest.skip("CASE_TEST_DATABASE_URL no está definida. Omitiendo prueba de migración en BD real.")
    return url


def test_v0_migration_upgrade_and_downgrade(test_db_url):
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", test_db_url)

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

        # 2. Verificar que ai_project_settings acepta gemini
        # Insertar proyecto y verificar que preferred_provider='gemini' no viole el check
        res = conn.execute(text("""
            SELECT conname, pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conname = 'ck_ai_project_settings_provider';
        """)).fetchall()
        assert len(res) == 1
        assert "gemini" in res[0][1]

    # Downgrade -1 y volver a subir a head
    command.downgrade(alembic_cfg, "-1")
    command.upgrade(alembic_cfg, "head")
