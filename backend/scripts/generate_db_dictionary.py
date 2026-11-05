"""Generate the physical PostgreSQL dictionary from the migrated database.

Run from backend/: .venv/Scripts/python -m scripts.generate_db_dictionary
Only schema metadata is read; no application rows are accessed.
"""

from collections import OrderedDict
from pathlib import Path

from sqlalchemy import create_engine, inspect, text

from app.core.config.configuracion import settings
from app.core.database.nombres_fisicos import COLUMNAS, TABLAS

REVISION = "e9a1b3c5d7f8"
OUTPUT = Path(__file__).resolve().parents[2] / "docs" / "segundo_parcial" / "bd.md"

SECTIONS = OrderedDict(
    [
        ("Acceso y usuarios", ["users", "roles", "user_roles", "user_sessions", "audit_logs"]),
        ("Proyectos y colaboración", ["projects", "project_members", "project_invitations", "collaboration_events", "project_versions", "project_restore_operations"]),
        ("Registro UML e intercambio", ["uml_diagrams", "xmi_exchanges"]),
        ("Asistente e IA", ["ai_conversations", "ai_actions", "ai_recommendations", "ai_processes"]),
        ("Generación de software", ["uml_transformations", "generated_backends", "generated_frontends", "generated_artifacts", "coordinated_generations", "flutter_theme_presets"]),
        ("Notificaciones", ["notifications", "notification_outbox", "notification_preferences", "push_subscriptions"]),
        ("Infraestructura SQL", ["nosql_outbox_events"]),
        ("Control de migraciones", ["alembic_version"]),
    ]
)

TABLE_DESCRIPTIONS = {
    "users": "Cuentas de acceso al sistema.",
    "roles": "Roles globales disponibles para usuarios.",
    "user_roles": "Asignación del rol global a cada usuario.",
    "user_sessions": "Sesiones y tokens de renovación de acceso.",
    "audit_logs": "Trazas de auditoría por usuario, proyecto y módulo.",
    "projects": "Identidad, configuración y revisión del proyecto; cada proyecto corresponde a un diagrama de clases en la aplicación.",
    "project_members": "Usuarios que participan en un proyecto y su rol local.",
    "project_invitations": "Invitaciones pendientes o resueltas para colaborar.",
    "collaboration_events": "Registro ordenado de eventos colaborativos y de IA.",
    "project_versions": "Registro SQL de versiones del proyecto.",
    "project_restore_operations": "Operaciones idempotentes de restauración y sus respaldos.",
    "uml_diagrams": "Identidad, estado y metadatos SQL del diagrama.",
    "xmi_exchanges": "Historial de importaciones y exportaciones XMI.",
    "ai_conversations": "Identidad y metadatos SQL de los chats del proyecto.",
    "ai_actions": "Propuestas y confirmaciones de cambios del asistente.",
    "ai_recommendations": "Recomendaciones emitidas por el asistente y su resolución.",
    "ai_processes": "Trazas de ejecuciones de IA.",
    "uml_transformations": "Transformaciones derivadas del diagrama para generar software; no son el contenido UML canónico.",
    "generated_backends": "Versiones de backend generadas y sus artefactos.",
    "generated_frontends": "Versiones Flutter generadas y backend de origen.",
    "generated_artifacts": "Archivos descargables producidos por la generación.",
    "coordinated_generations": "Estado de la generación coordinada de backend y frontend.",
    "flutter_theme_presets": "Temas Flutter reutilizables del proyecto.",
    "notifications": "Avisos dirigidos a usuarios.",
    "notification_outbox": "Entregas pendientes o completadas de avisos.",
    "notification_preferences": "Preferencias de notificación por usuario y proyecto.",
    "push_subscriptions": "Suscripciones push de navegadores y dispositivos.",
    "nosql_outbox_events": "Tabla SQL de eventos transaccionales pendientes de publicación.",
    "alembic_version": "Revisión de migraciones Alembic aplicada a PostgreSQL.",
}

SECTIONS = OrderedDict((group, [TABLAS.get(table, table) for table in tables]) for group, tables in SECTIONS.items())
TABLE_DESCRIPTIONS = {TABLAS.get(table, table): description for table, description in TABLE_DESCRIPTIONS.items()}
ORIGINAL_COLUMNS = {spanish: english for english, spanish in COLUMNAS.items()}

DESCRIPTIONS = {
    "id": "Identificador del registro.", "created_at": "Fecha de creación del registro.",
    "updated_at": "Fecha de última actualización.", "full_name": "Nombre completo del usuario.",
    "email": "Correo electrónico de acceso.", "password_hash": "Hash de la contraseña.",
    "is_active": "Indica si el registro está activo.", "last_access_at": "Último acceso del usuario.",
    "name": "Nombre del registro.", "title": "Título mostrado al usuario.",
    "description": "Descripción del registro.", "status": "Estado actual del proceso o registro.",
    "is_system": "Indica si es un rol propio del sistema.",
    "refresh_token_hash": "Hash del token de renovación.", "ip_address": "Dirección IP de la sesión.",
    "user_agent": "Agente del navegador o dispositivo.", "revoked_at": "Fecha de revocación.",
    "expires_at": "Fecha de vencimiento.", "module": "Módulo que originó la operación.",
    "action": "Acción realizada.", "result": "Resultado de la operación.",
    "detail": "Detalle adicional de auditoría.", "metadata_json": "Metadatos adicionales en JSON.",
    "settings": "Configuración general del proyecto.", "revision": "Número de revisión para control de cambios.",
    "next_version_number": "Siguiente número de versión del proyecto.",
    "project_role": "Rol del integrante dentro del proyecto.", "joined_at": "Fecha de incorporación al proyecto.",
    "permission_code": "Código del permiso específico.", "is_allowed": "Indica si se concede el permiso.",
    "invited_email": "Correo de la persona invitada.", "responded_at": "Fecha de respuesta a la invitación.",
    "client_event_id": "Identificador idempotente del evento de cliente.",
    "sequence_number": "Orden del evento en el proyecto o chat.",
    "event_type": "Tipo de evento registrado.", "element_type": "Tipo de elemento afectado.",
    "element_id": "Identificador lógico del elemento afectado.",
    "base_version": "Versión del elemento antes del cambio.",
    "payload": "Datos del evento o acción en JSON.",
    "actor_display_name": "Nombre del actor al registrar el evento.",
    "resource_type": "Tipo de recurso vinculado al evento.",
    "resource_id": "Identificador lógico del recurso vinculado.",
    "correlation_id": "Identificador para correlacionar eventos.",
    "causation_id": "Identificador del evento que lo originó.",
    "summary_key": "Clave de resumen de actividad.",
    "version_number": "Número de versión dentro del proyecto.",
    "snapshot": "Campo JSON de compatibilidad del registro de versión.",
    "kind": "Clase de versión o registro.",
    "snapshot_schema_version": "Versión del contrato del snapshot.",
    "snapshot_hash": "Hash de integridad de la versión.",
    "snapshot_size_bytes": "Tamaño del snapshot en bytes.",
    "project_revision": "Revisión del proyecto capturada.",
    "idempotency_key": "Clave para evitar operaciones duplicadas.",
    "snapshot_storage": "Código de almacenamiento de la versión.",
    "source_snapshot_hash": "Hash del snapshot que se va a restaurar.",
    "before_snapshot_hash": "Hash del estado previo a la restauración.",
    "after_snapshot_hash": "Hash del estado posterior a la restauración.",
    "project_revision_before": "Revisión anterior del proyecto.",
    "project_revision_after": "Revisión posterior del proyecto.",
    "diagnostics_json": "Diagnósticos de la restauración en JSON.",
    "started_at": "Inicio de la operación.", "completed_at": "Fin de la operación.",
    "diagram_type": "Tipo de diagrama registrado.", "current_version": "Versión actual del diagrama.",
    "content_storage": "Código de almacenamiento del contenido.",
    "exchange_type": "Importación o exportación XMI.", "tool_name": "Herramienta externa de intercambio.",
    "file_name": "Nombre del archivo.", "file_path": "Ruta del archivo generado o recibido.",
    "error_detail": "Detalle del error si ocurrió.",
    "summary": "Campo de compatibilidad para el resumen del chat.",
    "summary_until_sequence": "Última secuencia incluida en el resumen.",
    "last_message_sequence": "Última secuencia de mensaje del chat.",
    "schema_version": "Versión del contrato de datos.",
    "message_storage": "Código de almacenamiento de mensajes.",
    "enabled": "Indica si la función está habilitada.",
    "preferred_provider": "Proveedor de IA configurado.", "model_name": "Nombre del modelo de IA.",
    "fallback_enabled": "Permite usar el motor alternativo.",
    "require_confirmation": "Exige aprobación antes de ejecutar acciones.",
    "requires_confirmation": "Indica si la propuesta requiere aprobación.",
    "max_context_messages": "Máximo de mensajes recientes en el contexto.",
    "summary_trigger_messages": "Umbral de mensajes para generar un resumen.",
    "settings_json": "Parámetros adicionales de IA en JSON.",
    "source_message_id": "Identificador del mensaje que originó el registro; sin FK SQL.",
    "action_type": "Tipo de cambio propuesto por la IA.",
    "target_type": "Tipo del elemento objetivo.",
    "target_id": "Identificador lógico del elemento objetivo.",
    "risk_level": "Nivel de riesgo de la propuesta.",
    "confirmed_at": "Fecha de aprobación de la acción.",
    "executed_at": "Fecha de ejecución de la acción.",
    "result_json": "Resultado de ejecutar la acción en JSON.",
    "error_message": "Mensaje de error de la acción.",
    "category": "Categoría de la recomendación o preferencia.",
    "severity": "Severidad del aviso o recomendación.",
    "references_json": "Referencias de la recomendación en JSON.",
    "resolved_at": "Fecha de resolución de la recomendación.",
    "resolution_note": "Motivo o nota de resolución.",
    "process_type": "Tipo de procesamiento de IA.",
    "model_provider": "Proveedor que ejecutó el modelo.",
    "input_payload": "Entrada registrada para la ejecución de IA.",
    "output_payload": "Salida registrada de la ejecución de IA.",
    "source_version": "Versión de origen de la transformación.",
    "target_platform": "Plataforma objetivo de generación.",
    "intermediate_model": "Modelo intermedio derivado para generar código; no es el diagrama canónico.",
    "technology": "Tecnología del artefacto generado.",
    "language": "Lenguaje de programación generado.",
    "database_engine": "Motor de base de datos del backend generado.",
    "version_label": "Etiqueta visible de la versión generada.",
    "artifact_path": "Ruta del artefacto descargable.",
    "manifest": "Manifiesto del resultado de generación en JSON.",
    "artifact_type": "Tipo de archivo generado.",
    "checksum": "Suma de verificación del archivo.",
    "client_request_id": "Identificador idempotente de la solicitud.",
    "stage": "Etapa actual del proceso de generación.",
    "plan_hash": "Hash del plan de generación.",
    "plan_json": "Plan de generación en JSON.",
    "diagnostics": "Diagnósticos de generación en JSON.",
    "config_json": "Configuración visual Flutter en JSON.",
    "preset_name": "Nombre del preset visual aplicado.",
    "recipient_user_id": "Usuario destinatario de la notificación.",
    "type": "Tipo de notificación.", "body": "Contenido de la notificación.",
    "deep_link": "Destino de navegación de la notificación en JSON.",
    "dedup_key": "Clave para no duplicar el aviso.",
    "group_key": "Clave de agrupación de avisos.",
    "occurred_at": "Fecha del suceso notificado.",
    "read_at": "Fecha de lectura del aviso.",
    "clicked_at": "Fecha de apertura del aviso.",
    "archived_at": "Fecha de archivo del aviso.",
    "channel": "Canal de entrega de la notificación.",
    "attempt_count": "Número de intentos de entrega o publicación.",
    "available_at": "Fecha desde la que se puede procesar.",
    "locked_at": "Fecha en que un trabajador tomó el registro.",
    "locked_by": "Trabajador que tomó el registro.",
    "last_error_code": "Código del último fallo de entrega.",
    "delivered_at": "Fecha de entrega de la notificación.",
    "in_app_enabled": "Permite notificaciones dentro de la aplicación.",
    "push_enabled": "Permite notificaciones push.",
    "muted_until": "Silencio de avisos hasta esta fecha.",
    "endpoint": "URL de suscripción push.",
    "p256dh": "Clave pública de cifrado push.",
    "auth": "Secreto de autenticación push.",
    "content_encoding": "Codificación del contenido push.",
    "failure_count": "Número de fallos de entrega push.",
    "last_success_at": "Última entrega push correcta.",
    "aggregate_type": "Tipo de agregado asociado al evento SQL.",
    "aggregate_id": "Identificador del agregado asociado al evento SQL.",
    "processed_at": "Fecha de publicación satisfactoria.",
    "last_error": "Descripción del último error de publicación.",
    "version_num": "Revisión Alembic aplicada.",
}


def data_type(column: dict) -> str:
    kind = column["type"]
    if str(kind) == "TIMESTAMP" and getattr(kind, "timezone", False):
        return "TIMESTAMPTZ"
    return str(kind)


def size(column: dict) -> str:
    kind = data_type(column)
    if kind.startswith("VARCHAR("):
        return kind[8:-1]
    return {
        "UUID": "16 bytes", "BOOLEAN": "1 byte", "SMALLINT": "2 bytes",
        "INTEGER": "4 bytes", "BIGINT": "8 bytes", "DATE": "4 bytes",
        "TIMESTAMPTZ": "8 bytes", "TIMESTAMP": "8 bytes",
        "TEXT": "Variable", "JSONB": "Variable",
    }.get(kind, "Variable")


def describe(table: str, name: str, foreign_keys: dict[str, str]) -> str:
    if name in foreign_keys:
        return f"Referencia a `{foreign_keys[name]}`."
    original = ORIGINAL_COLUMNS.get(name, name)
    if original in DESCRIPTIONS:
        return DESCRIPTIONS[original]
    if name.endswith("_id"):
        return f"Identificador lógico de {name[:-3].replace('_', ' ')}."
    raise ValueError(f"Falta descripción para {table}.{name}")


def construir() -> str:
    engine = create_engine(settings.database_url)
    inspector = inspect(engine)
    with engine.connect() as connection:
        revisions = connection.execute(text("SELECT version_num FROM alembic_version")).scalars().all()
    if revisions != [REVISION]:
        raise RuntimeError(f"Se esperaba la revisión {REVISION}; se encontró {revisions}")
    expected = {table for tables in SECTIONS.values() for table in tables}
    actual = set(inspector.get_table_names(schema="public"))
    if actual != expected:
        raise RuntimeError(f"Esquema distinto del documentado: faltan {sorted(expected - actual)}, sobran {sorted(actual - expected)}")

    lines = [
        "# Diccionario físico de PostgreSQL",
        "",
        f"Esquema verificado directamente en PostgreSQL con la revisión Alembic `{REVISION}`.",
        "Solo aparecen las tablas y columnas físicas existentes en PostgreSQL.",
        "",
        "## Diseño físico de datos",
        "",
        "### Volumen y diccionario de datos",
        "",
        "Cada tabla muestra sus columnas reales. **Tamaño** indica longitud máxima para `VARCHAR`, tamaño físico de tipos fijos o `Variable` para `TEXT` y `JSONB`. **Nulos** procede de la restricción SQL `NOT NULL`; **Llave** señala únicamente `PK` y `FK` declaradas en PostgreSQL.",
        "",
    ]
    number = 0
    for section, tables in SECTIONS.items():
        lines += [f"### {section}", ""]
        for table in tables:
            number += 1
            columns = inspector.get_columns(table)
            pk = set(inspector.get_pk_constraint(table)["constrained_columns"])
            fks = inspector.get_foreign_keys(table)
            fk_map = {
                column: f"{fk['referred_table']}.{target}"
                for fk in fks
                for column, target in zip(fk["constrained_columns"], fk["referred_columns"])
            }
            lines += [f"#### Tabla {number}. Diccionario de `{table}`", "", TABLE_DESCRIPTIONS[table], "", "| Atributo | Tipo de dato | Descripción | Tamaño | Nulos | Llave |", "| --- | --- | --- | --- | --- | --- |"]
            ordered = sorted(columns, key=lambda column: (0 if column["name"] in pk else 2 if column["name"] in {"fecha_creacion", "fecha_actualizacion"} else 1, columns.index(column)))
            for column in ordered:
                name = column["name"]
                keys = "/".join(key for key, present in (("PK", name in pk), ("FK", name in fk_map)) if present) or "—"
                lines.append(f"| `{name}` | `{data_type(column)}` | {describe(table, name, fk_map)} | {size(column)} | {'Sí' if column['nullable'] else 'No'} | {keys} |")
            lines.append("")
            if fks:
                relations = "; ".join(f"`{column}` → `{target}`" for column, target in sorted(fk_map.items()))
                lines += [f"**Relaciones:** {relations}.", ""]
            unique = {
                "UNIQUE(" + ", ".join(f"`{column}`" for column in item["column_names"]) + ")"
                for item in inspector.get_unique_constraints(table)
                if item.get("column_names")
            }
            for index in inspector.get_indexes(table):
                if not index.get("unique"):
                    continue
                expressions = index.get("expressions") or index.get("column_names") or []
                fields = ", ".join(f"`{expression}`" for expression in expressions)
                condition = index.get("dialect_options", {}).get("postgresql_where")
                unique.add(f"UNIQUE({fields})" + (f" WHERE `{condition}`" if condition else ""))
            if unique:
                constraints = "; ".join(sorted(unique))
                lines += [f"**Unicidad:** {constraints}.", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    OUTPUT.write_text(construir(), encoding="utf-8")
    print(f"Diccionario generado: {OUTPUT}")
