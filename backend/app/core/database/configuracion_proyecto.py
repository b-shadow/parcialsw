"""Traducción de claves persistidas de configuración del proyecto.

La API conserva sus claves históricas; el documento JSONB se guarda en español.
"""

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TypeDecorator

from app.core.database.nombres_fisicos import COLUMNAS

RAIZ = {
    "ai": "ia",
    "flutter_theme": "tema_flutter",
    "generation_settings": "configuracion_generacion",
}
IA = {
    "enabled": "habilitado",
    "preferred_provider": "proveedor_preferido",
    "model_name": "nombre_modelo",
    "fallback_enabled": "respaldo_habilitado",
    "require_confirmation": "requiere_confirmacion",
    "max_context_messages": "max_mensajes_contexto",
    "summary_trigger_messages": "umbral_mensajes_resumen",
    "settings_json": "configuracion_json",
    **{key: COLUMNAS[key] for key in (
        "created_by_user_id", "updated_by_user_id", "created_at", "updated_at",
    )},
}
TEMA = {
    "config_json": "configuracion_json",
    "preset_name": "nombre_tema_predefinido",
    **{key: COLUMNAS[key] for key in (
        "schema_version", "created_by_user_id", "updated_by_user_id", "created_at", "updated_at",
    )},
}


def _traducir(data: dict, mapping: dict[str, str], *, to_spanish: bool) -> dict:
    if not isinstance(data, dict):
        return data
    names = mapping if to_spanish else {spanish: english for english, spanish in mapping.items()}
    return {names.get(key, key): value for key, value in data.items()}


def configuracion_al_espanol(data: dict | None) -> dict | None:
    if data is None:
        return None
    result = dict(data)
    for old, new, nested in (("ai", "ia", IA), ("flutter_theme", "tema_flutter", TEMA)):
        if old in result:
            result[new] = _traducir(result.pop(old), nested, to_spanish=True)
    return _traducir(result, RAIZ, to_spanish=True)


def configuracion_al_codigo(data: dict | None) -> dict | None:
    if data is None:
        return None
    result = dict(data)
    for old, new, nested in (("ia", "ai", IA), ("tema_flutter", "flutter_theme", TEMA)):
        if old in result:
            result[new] = _traducir(result.pop(old), nested, to_spanish=False)
    return _traducir(result, RAIZ, to_spanish=False)


class ConfiguracionProyectoJSON(TypeDecorator):
    impl = JSONB
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return configuracion_al_espanol(value)

    def process_result_value(self, value, dialect):
        return configuracion_al_codigo(value)
