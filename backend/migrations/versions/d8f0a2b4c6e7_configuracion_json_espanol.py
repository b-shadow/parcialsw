"""Spanish keys for project settings JSONB.

Revision ID: d8f0a2b4c6e7
Revises: c7e9f1a3b5d6
"""

from collections.abc import Sequence

from alembic import op

revision: str = "d8f0a2b4c6e7"
down_revision: str = "c7e9f1a3b5d6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

IA = {
    "enabled": "habilitado",
    "preferred_provider": "proveedor_preferido",
    "model_name": "nombre_modelo",
    "fallback_enabled": "respaldo_habilitado",
    "require_confirmation": "requiere_confirmacion",
    "max_context_messages": "max_mensajes_contexto",
    "summary_trigger_messages": "umbral_mensajes_resumen",
    "settings_json": "configuracion_json",
    "created_by_user_id": "usuario_creador_id",
    "updated_by_user_id": "usuario_actualizador_id",
    "created_at": "fecha_creacion",
    "updated_at": "fecha_actualizacion",
}
TEMA = {
    "config_json": "configuracion_json",
    "preset_name": "nombre_tema_predefinido",
    "schema_version": "version_esquema",
    "created_by_user_id": "usuario_creador_id",
    "updated_by_user_id": "usuario_actualizador_id",
    "created_at": "fecha_creacion",
    "updated_at": "fecha_actualizacion",
}


def _objeto_traducido(expresion: str, mapping: dict[str, str]) -> str:
    clauses = " ".join(f"WHEN '{old}' THEN '{new}'" for old, new in mapping.items())
    return (
        "(SELECT COALESCE(jsonb_object_agg(CASE key " + clauses + " ELSE key END, value), "
        "'{}'::jsonb) FROM jsonb_each(" + expresion + "))"
    )


def _mover_raiz(anterior: str, nuevo: str, mapping: dict[str, str] | None = None) -> None:
    value = f"configuracion->'{anterior}'"
    if mapping:
        translated = _objeto_traducido(value, mapping)
        value = f"CASE WHEN jsonb_typeof({value}) = 'object' THEN {translated} ELSE {value} END"
    op.execute(
        f"UPDATE proyectos SET configuracion = (configuracion - '{anterior}') "
        f"|| jsonb_build_object('{nuevo}', {value}) WHERE configuracion ? '{anterior}'"
    )


def upgrade() -> None:
    _mover_raiz("ai", "ia", IA)
    _mover_raiz("flutter_theme", "tema_flutter", TEMA)
    _mover_raiz("generation_settings", "configuracion_generacion")


def downgrade() -> None:
    _mover_raiz("configuracion_generacion", "generation_settings")
    _mover_raiz("tema_flutter", "flutter_theme", {value: key for key, value in TEMA.items()})
    _mover_raiz("ia", "ai", {value: key for key, value in IA.items()})
