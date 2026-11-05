import os

import pytest
from sqlalchemy import inspect

from app.core.database.sesion import engine

DATABASE_URL = os.getenv("DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="DATABASE_URL is required",
)

RETIRED_TABLES = {
    "ai_messages",
    "uml_attributes",
    "uml_classes",
    "uml_method_specifications",
    "uml_methods",
    "uml_parameters",
    "uml_relationships",
    "uml_visual_elements",
}


def test_phase14_document_content_tables_are_physically_retired() -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    assert RETIRED_TABLES.isdisjoint(tables)
    assert {"proyectos", "diagramas_uml", "conversaciones_ia", "versiones_proyecto"} <= tables

    for table_name in ("acciones_ia", "recomendaciones_ia"):
        foreign_keys = inspector.get_foreign_keys(table_name)
        assert all(
            foreign_key.get("referred_table") != "ai_messages"
            for foreign_key in foreign_keys
        )
