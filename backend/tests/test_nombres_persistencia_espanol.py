"""Contrato de nombres físicos en español y compatibilidad HTTP."""

import app.models as modelos
from app.core.database.configuracion_proyecto import (
    configuracion_al_codigo,
    configuracion_al_espanol,
)
from app.core.database.nombres_fisicos import COLUMNAS, TABLAS
from app.models import Base
from app.modules.asistente_proyecto.repositories import RepositorioAsistente


def test_esquema_activo_usa_nombres_fisicos_espanoles() -> None:
    assert all(hasattr(modelos, nombre) for nombre in modelos.__all__)
    assert {TABLAS[old] for old in TABLAS} <= set(Base.metadata.tables)
    for table in Base.metadata.tables.values():
        if table.name not in TABLAS.values():
            continue  # Los modelos SQL retirados no se recrean en PostgreSQL.
        for column in table.columns:
            assert column.name not in {old for old, new in COLUMNAS.items() if old != new}
    assert Base.metadata.tables["procesos_ia"].c.nombre_modelo.name == "nombre_modelo"
    assert hasattr(RepositorioAsistente, "obtener_mensaje")


def test_configuracion_jsonb_se_guarda_en_espanol_y_lee_contrato_vigente() -> None:
    legacy = {
        "ai": {"model_name": "qwen", "preferred_provider": "ollama"},
        "flutter_theme": {"config_json": {"primary": "#123456"}},
        "generation_settings": {"language": "java"},
    }
    stored = configuracion_al_espanol(legacy)
    assert stored == {
        "ia": {"nombre_modelo": "qwen", "proveedor_preferido": "ollama"},
        "tema_flutter": {"configuracion_json": {"primary": "#123456"}},
        "configuracion_generacion": {"language": "java"},
    }
    assert configuracion_al_codigo(stored) == legacy
