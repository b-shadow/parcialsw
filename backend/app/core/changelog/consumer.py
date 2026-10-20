"""Consumidor del registro de cambios en NoSQL (Redis Streams) (V2.1).

Lee del stream global con el grupo 'case-workers', difunde eventos CHANGE_LOGGED
a los clientes conectados vía WebSocket y notifica al servicio de asesoría proactiva.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from uuid import UUID, uuid4

from app.core.changelog.contracts import ChangeLogEntry
from app.core.config.settings import settings
from app.core.database.session import SessionLocal
from app.core.redis.client import get_redis, redis_key
from app.modules.acceso_usuarios.repositories.user_repository import UserRepository
from app.modules.asistente_proyecto.services.proactive_advisor_service import (
    ProactiveAdvisorService,
)
from app.websocket.connection_manager import manager

logger = logging.getLogger(__name__)

CONSUMER_GROUP = "case-workers"


class ChangeLogConsumer:
    def __init__(
        self,
        advisor: ProactiveAdvisorService | None = None,
        consumer_name: str | None = None,
    ) -> None:
        self.advisor = advisor or ProactiveAdvisorService()
        self.consumer_name = consumer_name or f"worker-{uuid4().hex[:8]}"
        self._user_cache: dict[UUID, str] = {}

    def _ensure_group(self, stream_key: str) -> None:
        client = get_redis()
        if client is None:
            return
        try:
            client.xgroup_create(stream_key, CONSUMER_GROUP, id="0", mkstream=True)
        except Exception as exc:
            # Si el grupo ya existe (BUSYGROUP), se ignora
            if "BUSYGROUP" not in str(exc):
                logger.debug("Info al inicializar grupo Redis Streams: %s", exc)

    def _parse_entry(self, entry_id: str, fields: dict) -> ChangeLogEntry:
        # Asegurarse de decodificar si son bytes o strings
        def get_val(key: str, default: str = "") -> str:
            val = fields.get(key)
            if val is None:
                return default
            if isinstance(val, bytes):
                return val.decode("utf-8")
            return str(val)

        meta_raw = get_val("metadata", "{}")
        try:
            meta = json.loads(meta_raw)
        except Exception:
            meta = {}

        occurred_str = get_val("occurred_at")
        try:
            occurred = datetime.fromisoformat(occurred_str)
        except Exception:
            from datetime import timezone
            occurred = datetime.now(timezone.utc)

        actor_str = get_val("actor_user_id")
        actor_id = UUID(actor_str) if actor_str else None

        diag_str = get_val("diagram_id")
        diag_id = UUID(diag_str) if diag_str else None

        entity_id_val = get_val("entity_id")
        entity_type_val = get_val("entity_type")

        return ChangeLogEntry(
            id=entry_id if isinstance(entry_id, str) else entry_id.decode("utf-8"),
            project_id=UUID(get_val("project_id")),
            occurred_at=occurred,
            actor_user_id=actor_id,
            source=get_val("source", "ui"),
            module=get_val("module"),
            action=get_val("action"),
            entity_type=entity_type_val or None,
            entity_id=entity_id_val or None,
            diagram_id=diag_id,
            summary=get_val("summary"),
            metadata=meta,
        )

    def _resolve_actor_name(self, actor_id: UUID | None) -> str:
        if not actor_id:
            return "Sistema"
        if actor_id in self._user_cache:
            return self._user_cache[actor_id]

        try:
            with SessionLocal() as db:
                user = UserRepository(db).get_by_id(actor_id)
                name = user.full_name if user else "Usuario"
                self._user_cache[actor_id] = name
                return name
        except Exception:
            return "Usuario"

    async def _broadcast(self, entry: ChangeLogEntry) -> None:
        actor_display_name = self._resolve_actor_name(entry.actor_user_id)
        project_id_str = str(entry.project_id)

        event_payload = {
            "protocol_version": 2,
            "type": "CHANGE_LOGGED",
            "event_id": str(uuid4()),
            "project_id": project_id_str,
            "sequence_number": 0,
            "occurred_at": entry.occurred_at.isoformat(),
            "persistent": False,
            "actor": {
                "user_id": str(entry.actor_user_id) if entry.actor_user_id else "",
                "display_name": actor_display_name,
            },
            "payload": {
                **entry.model_dump(mode="json"),
                "actor_display_name": actor_display_name,
            },
        }

        try:
            await manager.broadcast(project_id_str, event_payload)
        except Exception as exc:
            logger.warning("Fallo al difundir CHANGE_LOGGED: %s", exc)

    async def run(self, stop: asyncio.Event) -> None:
        global_stream = redis_key("changelog", "all")
        self._ensure_group(global_stream)

        logger.info("ChangeLogConsumer activo en stream %s (grupo: %s)", global_stream, CONSUMER_GROUP)

        while not stop.is_set():
            client = get_redis()
            if client is None:
                await asyncio.sleep(2)
                continue

            try:
                # Leer mensajes nuevos asignados al grupo
                result = await asyncio.to_thread(
                    client.xreadgroup,
                    CONSUMER_GROUP,
                    self.consumer_name,
                    {global_stream: ">"},
                    count=50,
                    block=2000,
                )

                if not result:
                    continue

                for _stream, messages in result:
                    for msg_id, fields in messages:
                        if stop.is_set():
                            break
                        try:
                            entry = self._parse_entry(msg_id, fields)
                            await self._broadcast(entry)
                            await self.advisor.on_change(entry)
                            # Confirmar mensaje procesado
                            await asyncio.to_thread(
                                client.xack, global_stream, CONSUMER_GROUP, msg_id
                            )
                        except Exception as item_err:
                            logger.exception("Error procesando entrada %s: %s", msg_id, item_err)

            except Exception as stream_err:
                if stop.is_set():
                    break
                logger.warning("Excepción en ciclo ChangeLogConsumer: %s", stream_err)
                await asyncio.sleep(1)
