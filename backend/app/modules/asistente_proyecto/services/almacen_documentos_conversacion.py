from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from pymongo.errors import PyMongoError
from sqlalchemy.orm import Session

from app.core.config.configuracion import settings
from app.core.nosql.bandeja_salida import ServicioBandejaSalidaNoSQL
from app.core.nosql.cliente import GestorMongo, mongo_manager
from app.core.nosql.cliente_sincrono import GestorMongoSincrono, sync_mongo_manager
from app.core.nosql.conciliacion import canonical_sha256
from app.core.nosql.contratos import (
    ColeccionMongo,
    DocumentoInstantaneaContextoIA,
    DocumentoMensajeIA,
    MutacionMongo,
)
from app.core.nosql.errores import ErrorMongoNoDisponible
from app.core.nosql.nombres_mongo import adaptar_mongo
from app.modules.asistente_proyecto.models import ConversacionIA, MensajeIA

logger = logging.getLogger(__name__)


def _contenido_mensaje(message: MensajeIA | DocumentoMensajeIA) -> dict[str, Any]:
    return {
        "id": str(message.id),
        "conversation_id": str(message.conversation_id),
        "project_id": str(message.project_id),
        "author_user_id": str(message.author_user_id) if message.author_user_id else None,
        "role": message.role,
        "content": message.content,
        "sequence_number": message.sequence_number,
        "client_message_id": str(message.client_message_id) if message.client_message_id else None,
        "correlation_id": str(message.correlation_id),
        "status": message.status,
        "detected_intents": list(message.detected_intents),
        "references_json": list(message.references_json),
        "metadata_json": dict(message.metadata_json),
    }


def hash_contenido_mensaje(message: MensajeIA | DocumentoMensajeIA) -> str:
    return canonical_sha256(_contenido_mensaje(message))


def documento_mensaje_desde_sql(message: MensajeIA) -> DocumentoMensajeIA:
    now = datetime.now(UTC)
    return DocumentoMensajeIA(
        _id=message.id,
        project_id=message.project_id,
        conversation_id=message.conversation_id,
        author_user_id=message.author_user_id,
        role=message.role,
        content=message.content,
        sequence_number=message.sequence_number,
        client_message_id=message.client_message_id,
        correlation_id=message.correlation_id,
        status=message.status,
        detected_intents=list(message.detected_intents),
        references_json=list(message.references_json),
        metadata_json=dict(message.metadata_json),
        content_hash=hash_contenido_mensaje(message),
        created_at=message.created_at or now,
        updated_at=message.updated_at or now,
    )


def encolar_documento_mensaje(db: Session, message: MensajeIA) -> DocumentoMensajeIA:
    db.flush()
    document = documento_mensaje_desde_sql(message)
    mutation = MutacionMongo(
        collection=ColeccionMongo.AI_MESSAGES,
        operation="upsert",
        document_id=message.id,
        document=document.to_mongo(),
    )
    ServicioBandejaSalidaNoSQL(db).enqueue(
        aggregate_type="ai_message",
        aggregate_id=message.id,
        mutation=mutation,
        idempotency_key=f"ai-message:{message.id}:{document.content_hash}",
    )
    return document


def documento_instantanea_contexto(
    conversation: ConversacionIA,
    *,
    summary: str,
    context: dict[str, Any],
    until_sequence: int,
) -> DocumentoInstantaneaContextoIA:
    snapshot_id = uuid5(
        NAMESPACE_URL,
        f"case-inteligente:conversation:{conversation.id}:summary:{until_sequence}",
    )
    content_hash = canonical_sha256(
        {
            "conversation_id": str(conversation.id),
            "until_sequence": until_sequence,
            "summary": summary,
            "context": context,
        }
    )
    return DocumentoInstantaneaContextoIA(
        _id=snapshot_id,
        project_id=conversation.project_id,
        conversation_id=conversation.id,
        until_sequence=until_sequence,
        summary=summary,
        context=context,
        content_hash=content_hash,
    )


def encolar_instantanea_contexto(
    db: Session,
    conversation: ConversacionIA,
    *,
    summary: str,
    context: dict[str, Any],
    until_sequence: int,
) -> DocumentoInstantaneaContextoIA:
    document = documento_instantanea_contexto(
        conversation,
        summary=summary,
        context=context,
        until_sequence=until_sequence,
    )
    ServicioBandejaSalidaNoSQL(db).enqueue(
        aggregate_type="ai_context_snapshot",
        aggregate_id=document.id,
        mutation=MutacionMongo(
            collection=ColeccionMongo.AI_CONTEXT_SNAPSHOTS,
            operation="upsert",
            document_id=document.id,
            document=document.to_mongo(),
        ),
        idempotency_key=f"ai-context:{conversation.id}:{until_sequence}:{document.content_hash}",
    )
    return document


class AlmacenDocumentosConversacion:
    def __init__(self, manager: GestorMongo = mongo_manager, *, database=None) -> None:
        self.manager = manager
        self._database = adaptar_mongo(database) if database is not None else None

    @property
    def base_datos(self):
        return self._database if self._database is not None else self.manager.database

    async def listar_mensajes(
        self,
        conversation_id: UUID,
        *,
        before_sequence: int | None,
        after_sequence: int | None,
        limit: int,
    ) -> list[DocumentoMensajeIA]:
        filters: dict[str, Any] = {"conversation_id": str(conversation_id)}
        if before_sequence is not None:
            filters["sequence_number"] = {"$lt": before_sequence}
        if after_sequence is not None:
            filters["sequence_number"] = {"$gt": after_sequence}
        descending = after_sequence is None
        cursor = (
            self.base_datos[ColeccionMongo.AI_MESSAGES.value]
            .find(filters)
            .sort("sequence_number", -1 if descending else 1)
            .limit(max(1, min(limit, 100)))
        )
        documents = [DocumentoMensajeIA.model_validate(item) async for item in cursor]
        return list(reversed(documents)) if descending else documents

    async def existe_mensaje_anterior(self, conversation_id: UUID, sequence: int) -> bool:
        document = await self.base_datos[ColeccionMongo.AI_MESSAGES.value].find_one(
            {"conversation_id": str(conversation_id), "sequence_number": {"$lt": sequence}},
            {"_id": 1},
        )
        return document is not None

    async def existe_mensaje_posterior(self, conversation_id: UUID, sequence: int) -> bool:
        document = await self.base_datos[ColeccionMongo.AI_MESSAGES.value].find_one(
            {"conversation_id": str(conversation_id), "sequence_number": {"$gt": sequence}},
            {"_id": 1},
        )
        return document is not None

    async def obtener_contexto_reciente(self, conversation_id: UUID) -> DocumentoInstantaneaContextoIA | None:
        document = await self.base_datos[ColeccionMongo.AI_CONTEXT_SNAPSHOTS.value].find_one(
            {"conversation_id": str(conversation_id)},
            sort=[("until_sequence", -1)],
        )
        return DocumentoInstantaneaContextoIA.model_validate(document) if document else None

    async def guardar_o_actualizar_mensaje(self, document: DocumentoMensajeIA) -> None:
        await self.base_datos[ColeccionMongo.AI_MESSAGES.value].replace_one(
            {"_id": str(document.id)}, document.to_mongo(), upsert=True
        )

    async def guardar_o_actualizar_contexto(self, document: DocumentoInstantaneaContextoIA) -> None:
        await self.base_datos[ColeccionMongo.AI_CONTEXT_SNAPSHOTS.value].replace_one(
            {"_id": str(document.id)}, document.to_mongo(), upsert=True
        )

    async def listar_mensajes_seguro(self, *args, **kwargs) -> list[DocumentoMensajeIA] | None:
        if not settings.ai_messages_mongodb_read_enabled:
            return None
        try:
            return await self.listar_mensajes(*args, **kwargs)
        except (ErrorMongoNoDisponible, PyMongoError):
            logger.exception("MongoDB message read failed")
            if not settings.ai_messages_sql_fallback_enabled:
                raise
            return None

    async def existe_mensaje_anterior_seguro(self, conversation_id: UUID, sequence: int) -> bool:
        try:
            return await self.existe_mensaje_anterior(conversation_id, sequence)
        except (ErrorMongoNoDisponible, PyMongoError):
            if not settings.ai_messages_sql_fallback_enabled:
                raise
            return False

    async def existe_mensaje_posterior_seguro(self, conversation_id: UUID, sequence: int) -> bool:
        try:
            return await self.existe_mensaje_posterior(conversation_id, sequence)
        except (ErrorMongoNoDisponible, PyMongoError):
            if not settings.ai_messages_sql_fallback_enabled:
                raise
            return False

    async def obtener_contexto_reciente_seguro(self, conversation_id: UUID) -> DocumentoInstantaneaContextoIA | None:
        if not settings.ai_messages_mongodb_read_enabled:
            return None
        try:
            return await self.obtener_contexto_reciente(conversation_id)
        except (ErrorMongoNoDisponible, PyMongoError):
            if not settings.ai_messages_sql_fallback_enabled:
                raise
            return None


class AlmacenSincronoDocumentosConversacion:
    """Synchronous canonical message store used by thread-pool services."""

    def __init__(self, manager: GestorMongoSincrono = sync_mongo_manager, *, database=None) -> None:
        self.manager = manager
        self._database = adaptar_mongo(database) if database is not None else None

    @property
    def base_datos(self):
        return self._database if self._database is not None else self.manager.database

    @property
    def coleccion(self):
        return self.base_datos[ColeccionMongo.AI_MESSAGES.value]

    def guardar_o_actualizar(self, document: DocumentoMensajeIA) -> None:
        self.coleccion.replace_one({"_id": str(document.id)}, document.to_mongo(), upsert=True)

    def obtener(self, message_id: UUID) -> DocumentoMensajeIA | None:
        item = self.coleccion.find_one({"_id": str(message_id)})
        return DocumentoMensajeIA.model_validate(item) if item else None

    def obtener_por_id_cliente(
        self, conversation_id: UUID, author_user_id: UUID, client_message_id: UUID
    ) -> DocumentoMensajeIA | None:
        item = self.coleccion.find_one(
            {
                "conversation_id": str(conversation_id),
                "author_user_id": str(author_user_id),
                "client_message_id": str(client_message_id),
            }
        )
        return DocumentoMensajeIA.model_validate(item) if item else None

    def obtener_asistente_por_correlacion(
        self, conversation_id: UUID, correlation_id: UUID
    ) -> DocumentoMensajeIA | None:
        item = self.coleccion.find_one(
            {
                "conversation_id": str(conversation_id),
                "correlation_id": str(correlation_id),
                "role": "assistant",
            }
        )
        return DocumentoMensajeIA.model_validate(item) if item else None

    def listar_mensajes(
        self,
        conversation_id: UUID,
        *,
        before_sequence: int | None,
        after_sequence: int | None,
        limit: int,
    ) -> list[DocumentoMensajeIA]:
        filters: dict[str, Any] = {"conversation_id": str(conversation_id)}
        if before_sequence is not None:
            filters["sequence_number"] = {"$lt": before_sequence}
        if after_sequence is not None:
            filters["sequence_number"] = {"$gt": after_sequence}
        descending = after_sequence is None
        items = list(
            self.coleccion.find(filters)
            .sort("sequence_number", -1 if descending else 1)
            .limit(max(1, min(limit, 100)))
        )
        documents = [DocumentoMensajeIA.model_validate(item) for item in items]
        return list(reversed(documents)) if descending else documents

    def existe_anterior(self, conversation_id: UUID, sequence: int) -> bool:
        return (
            self.coleccion.find_one(
                {
                    "conversation_id": str(conversation_id),
                    "sequence_number": {"$lt": sequence},
                },
                {"_id": 1},
            )
            is not None
        )

    def existe_posterior(self, conversation_id: UUID, sequence: int) -> bool:
        return (
            self.coleccion.find_one(
                {
                    "conversation_id": str(conversation_id),
                    "sequence_number": {"$gt": sequence},
                },
                {"_id": 1},
            )
            is not None
        )
