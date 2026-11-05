from __future__ import annotations

from dataclasses import dataclass
from inspect import isawaitable
from typing import Any

from pymongo import ASCENDING, DESCENDING, IndexModel
from pymongo.errors import CollectionInvalid, OperationFailure, PyMongoError

from app.core.nosql.contratos import ColeccionMongo
from app.core.nosql.errores import ErrorEsquemaMongo
from app.core.nosql.nombres_mongo import COLECCIONES, traducir_clave, traducir_documento

UUID_PATTERN = (
    "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)
HASH_PATTERN = "^[0-9a-f]{64}$"


def _base_properties() -> dict[str, Any]:
    return {
        "_id": {"bsonType": "string", "pattern": UUID_PATTERN},
        "schema_version": {"bsonType": "int", "minimum": 1},
        "created_at": {"bsonType": "date"},
        "updated_at": {"bsonType": "date"},
    }


def _validator(required: list[str], properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["_id", "schema_version", "created_at", "updated_at", *required],
            "properties": {**_base_properties(), **properties},
            "additionalProperties": True,
        }
    }


COLLECTION_VALIDATORS: dict[ColeccionMongo, dict[str, Any]] = {
    ColeccionMongo.UML_DIAGRAMS: _validator(
        ["project_id", "revision", "content", "content_hash"],
        {
            "project_id": {"bsonType": "string", "pattern": UUID_PATTERN},
            "revision": {"bsonType": "int", "minimum": 0},
            "content": {"bsonType": "object"},
            "content_hash": {"bsonType": "string", "pattern": HASH_PATTERN},
        },
    ),
    ColeccionMongo.UML_DIAGRAM_VERSIONS: _validator(
        [
            "project_id",
            "diagram_id",
            "version_number",
            "project_revision",
            "snapshot_schema_version",
            "name",
            "kind",
            "snapshot_size_bytes",
            "content",
            "content_hash",
        ],
        {
            "project_id": {"bsonType": "string", "pattern": UUID_PATTERN},
            "diagram_id": {"bsonType": "string", "pattern": UUID_PATTERN},
            "version_number": {"bsonType": "int", "minimum": 1},
            "project_revision": {"bsonType": "int", "minimum": 0},
            "snapshot_schema_version": {"bsonType": "int", "minimum": 1},
            "name": {"bsonType": "string", "minLength": 1, "maxLength": 120},
            "description": {"bsonType": ["string", "null"]},
            "kind": {"enum": ["manual", "pre_restore_backup"]},
            "snapshot_size_bytes": {"bsonType": "int", "minimum": 0},
            "content": {"bsonType": "object"},
            "content_hash": {"bsonType": "string", "pattern": HASH_PATTERN},
        },
    ),
    ColeccionMongo.AI_MESSAGES: _validator(
        [
            "project_id",
            "conversation_id",
            "role",
            "sequence_number",
            "content",
            "correlation_id",
            "status",
            "detected_intents",
            "references_json",
            "metadata_json",
            "content_hash",
        ],
        {
            "project_id": {"bsonType": "string", "pattern": UUID_PATTERN},
            "conversation_id": {"bsonType": "string", "pattern": UUID_PATTERN},
            "role": {"enum": ["user", "assistant", "system", "tool"]},
            "sequence_number": {"bsonType": "int", "minimum": 1},
            "content": {"bsonType": "string", "minLength": 1},
            "correlation_id": {"bsonType": "string", "pattern": UUID_PATTERN},
            "status": {"enum": ["pending", "streaming", "completed", "failed", "cancelled"]},
            "detected_intents": {"bsonType": "array"},
            "references_json": {"bsonType": "array"},
            "metadata_json": {"bsonType": "object"},
            "content_hash": {"bsonType": "string", "pattern": HASH_PATTERN},
        },
    ),
    ColeccionMongo.AI_CONTEXT_SNAPSHOTS: _validator(
        ["project_id", "conversation_id", "until_sequence", "summary", "content_hash"],
        {
            "project_id": {"bsonType": "string", "pattern": UUID_PATTERN},
            "conversation_id": {"bsonType": "string", "pattern": UUID_PATTERN},
            "until_sequence": {"bsonType": "int", "minimum": 0},
            "summary": {"bsonType": "string"},
            "content_hash": {"bsonType": "string", "pattern": HASH_PATTERN},
            "expires_at": {"bsonType": ["date", "null"]},
        },
    ),
    ColeccionMongo.MIGRATION_CHECKPOINTS: _validator(
        ["migration_name", "status", "processed_count", "failed_count"],
        {
            "migration_name": {"bsonType": "string", "minLength": 1},
            "status": {"enum": ["pending", "running", "completed", "failed"]},
            "processed_count": {"bsonType": "int", "minimum": 0},
            "failed_count": {"bsonType": "int", "minimum": 0},
        },
    ),
    ColeccionMongo.PROCESSED_EVENTS: _validator(
        ["idempotency_key", "event_id", "collection", "operation", "processed_at"],
        {
            "idempotency_key": {"bsonType": "string", "minLength": 1},
            "event_id": {"bsonType": "string", "pattern": UUID_PATTERN},
            "collection": {"bsonType": "string"},
            "operation": {"enum": ["upsert", "delete"]},
            "processed_at": {"bsonType": "date"},
        },
    ),
    ColeccionMongo.OPERATIONAL_AUDITS: _validator(
        ["status", "duration_ms", "findings", "metrics", "collection_reports"],
        {
            "status": {"enum": ["healthy", "degraded"]},
            "duration_ms": {"bsonType": "int", "minimum": 0},
            "findings": {"bsonType": "array"},
            "metrics": {"bsonType": "object"},
            "collection_reports": {"bsonType": "array"},
        },
    ),
}


@dataclass(frozen=True)
class DefinicionIndice:
    collection: ColeccionMongo
    indexes: tuple[IndexModel, ...]


INDEX_DEFINITIONS = (
    DefinicionIndice(
        ColeccionMongo.UML_DIAGRAMS,
        (
            IndexModel([("project_id", ASCENDING)], unique=True, name="uq_uml_diagrams_project"),
            IndexModel([("updated_at", DESCENDING)], name="ix_uml_diagrams_updated"),
        ),
    ),
    DefinicionIndice(
        ColeccionMongo.UML_DIAGRAM_VERSIONS,
        (
            IndexModel(
                [("diagram_id", ASCENDING), ("version_number", ASCENDING)],
                unique=True,
                name="uq_uml_versions_diagram_number",
            ),
            IndexModel(
                [("project_id", ASCENDING), ("created_at", DESCENDING)],
                name="ix_uml_versions_project_created",
            ),
            IndexModel(
                [("project_id", ASCENDING), ("version_number", ASCENDING)],
                unique=True,
                name="uq_uml_versions_project_number",
            ),
            IndexModel([("content_hash", ASCENDING)], name="ix_uml_versions_hash"),
        ),
    ),
    DefinicionIndice(
        ColeccionMongo.AI_MESSAGES,
        (
            IndexModel(
                [("conversation_id", ASCENDING), ("sequence_number", ASCENDING)],
                unique=True,
                name="uq_ai_messages_conversation_sequence",
            ),
            IndexModel(
                [("project_id", ASCENDING), ("created_at", DESCENDING)],
                name="ix_ai_messages_project_created",
            ),
            IndexModel(
                [("conversation_id", ASCENDING), ("client_message_id", ASCENDING)],
                unique=True,
                partialFilterExpression={"client_message_id": {"$type": "string"}},
                name="uq_ai_messages_client_id",
            ),
        ),
    ),
    DefinicionIndice(
        ColeccionMongo.AI_CONTEXT_SNAPSHOTS,
        (
            IndexModel(
                [("conversation_id", ASCENDING), ("until_sequence", DESCENDING)],
                unique=True,
                name="uq_ai_context_conversation_sequence",
            ),
            IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0, name="ttl_ai_context"),
        ),
    ),
    DefinicionIndice(
        ColeccionMongo.MIGRATION_CHECKPOINTS,
        (
            IndexModel([("migration_name", ASCENDING)], unique=True, name="uq_migration_name"),
            IndexModel(
                [("status", ASCENDING), ("updated_at", ASCENDING)], name="ix_migration_status"
            ),
        ),
    ),
    DefinicionIndice(
        ColeccionMongo.PROCESSED_EVENTS,
        (
            IndexModel(
                [("idempotency_key", ASCENDING)], unique=True, name="uq_processed_idempotency"
            ),
            IndexModel([("event_id", ASCENDING)], unique=True, name="uq_processed_event"),
            IndexModel([("processed_at", DESCENDING)], name="ix_processed_at"),
        ),
    ),
    DefinicionIndice(
        ColeccionMongo.OPERATIONAL_AUDITS,
        (
            IndexModel([("created_at", DESCENDING)], name="ix_operational_audits_created"),
            IndexModel(
                [("status", ASCENDING), ("created_at", DESCENDING)],
                name="ix_operational_audits_status_created",
            ),
        ),
    ),
)

NOMBRES_INDICES = {
    "uq_uml_diagrams_project": "uq_diagramas_uml_proyecto",
    "ix_uml_diagrams_updated": "ix_diagramas_uml_fecha_actualizacion",
    "uq_uml_versions_diagram_number": "uq_versiones_uml_diagrama_numero",
    "ix_uml_versions_project_created": "ix_versiones_uml_proyecto_fecha_creacion",
    "uq_uml_versions_project_number": "uq_versiones_uml_proyecto_numero",
    "ix_uml_versions_hash": "ix_versiones_uml_hash_contenido",
    "uq_ai_messages_conversation_sequence": "uq_mensajes_ia_conversacion_secuencia",
    "ix_ai_messages_project_created": "ix_mensajes_ia_proyecto_fecha_creacion",
    "uq_ai_messages_client_id": "uq_mensajes_ia_mensaje_cliente",
    "uq_ai_context_conversation_sequence": "uq_contexto_ia_conversacion_secuencia",
    "ttl_ai_context": "ttl_contexto_ia",
    "uq_migration_name": "uq_nombre_migracion",
    "ix_migration_status": "ix_migracion_estado",
    "uq_processed_idempotency": "uq_procesados_clave_idempotencia",
    "uq_processed_event": "uq_procesados_evento",
    "ix_processed_at": "ix_fecha_procesamiento",
    "ix_operational_audits_created": "ix_auditorias_fecha_creacion",
    "ix_operational_audits_status_created": "ix_auditorias_estado_fecha_creacion",
}

for validator in COLLECTION_VALIDATORS.values():
    esquema = validator["$jsonSchema"]
    esquema["required"] = [traducir_clave(campo, al_espanol=True) for campo in esquema["required"]]
    esquema["properties"] = traducir_documento(esquema["properties"], al_espanol=True)

INDEX_DEFINITIONS = tuple(
    DefinicionIndice(
        grupo.collection,
        tuple(
            IndexModel(
                [(traducir_clave(campo, al_espanol=True), direccion)
                 for campo, direccion in indice.document["key"].items()],
                **{
                    clave: (
                        NOMBRES_INDICES[valor] if clave == "name"
                        else traducir_documento(valor, al_espanol=True)
                        if clave == "partialFilterExpression" else valor
                    )
                    for clave, valor in indice.document.items() if clave != "key"
                },
            )
            for indice in grupo.indexes
        ),
    )
    for grupo in INDEX_DEFINITIONS
)


async def migrar_nombres_mongo(database: Any) -> None:
    """Migra colecciones y documentos antiguos antes de activar el validador nuevo.

    Se puede reanudar tras una interrupción. Una colisión de colecciones se detiene
    explícitamente para no sobrescribir datos de ninguna de las dos.
    """
    existentes = set(await database.list_collection_names())
    for antiguo, nuevo in COLECCIONES.items():
        if antiguo in existentes:
            if nuevo in existentes:
                raise ErrorEsquemaMongo(f"Existen ambas colecciones: {antiguo} y {nuevo}")
            await database[antiguo].rename(nuevo, dropTarget=False)
            existentes.discard(antiguo)
            existentes.add(nuevo)
        if nuevo not in existentes:
            continue
        coleccion = database[nuevo]
        pendiente = await coleccion.find_one({"schema_version": {"$exists": True}}, {"_id": 1})
        if pendiente is None:
            continue
        indices = coleccion.list_indexes()
        if isawaitable(indices):
            indices = await indices
        async for indice in indices:
            if indice["name"] in NOMBRES_INDICES:
                await coleccion.drop_index(indice["name"])
        await database.command({
            "collMod": nuevo,
            "validator": {"$jsonSchema": {"bsonType": "object"}},
        })
        async for original in coleccion.find({}):
            traducido = traducir_documento(original, al_espanol=True)
            if traducido != original:
                await coleccion.replace_one({"_id": original["_id"]}, traducido)


async def asegurar_esquema_mongo(database: Any) -> None:
    """Create or update all validators and indexes; safe to run on every startup."""
    try:
        await migrar_nombres_mongo(database)
        existing = set(await database.list_collection_names())
        for collection, validator in COLLECTION_VALIDATORS.items():
            if collection.value not in existing:
                try:
                    await database.create_collection(
                        collection.value,
                        validator=validator,
                        validationLevel="strict",
                        validationAction="error",
                    )
                except CollectionInvalid:
                    pass
            await database.command(
                {
                    "collMod": collection.value,
                    "validator": validator,
                    "validationLevel": "strict",
                    "validationAction": "error",
                }
            )
        for definition in INDEX_DEFINITIONS:
            coleccion = database[definition.collection.value]
            await coleccion.create_indexes(list(definition.indexes))
            indices = coleccion.list_indexes()
            if isawaitable(indices):
                indices = await indices
            async for indice in indices:
                if indice["name"] in NOMBRES_INDICES:
                    await coleccion.drop_index(indice["name"])
    except (OperationFailure, PyMongoError) as exc:
        raise ErrorEsquemaMongo(f"MongoDB schema bootstrap failed: {type(exc).__name__}") from exc
