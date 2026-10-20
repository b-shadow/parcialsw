"""Servicio de asesoría proactiva de la IA del proyecto (V2.1).

La IA actúa como un integrante más del equipo: observa el flujo de cambios en NoSQL,
detecta anomalías o eventos clave (versiones, importaciones, acumulación de cambios)
y propone mejoras sin necesidad de ser invocada explícitamente.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_engine.orchestration.contracts import PlannedRecommendation
from app.core.changelog.contracts import ChangeLogEntry
from app.core.config.settings import settings
from app.core.database.session import SessionLocal
from app.core.redis.client import get_redis, redis_key
from app.modules.asistente_proyecto.models import AiMessage, AiRecommendation
from app.modules.asistente_proyecto.schemas.assistant import AiMessageCreateInternal
from app.modules.asistente_proyecto.services.assistant_service import AssistantContractService
from app.modules.asistente_proyecto.services.event_publisher import ProjectAiEventPublisher
from app.modules.modelado_uml.engine.validator import validate_internal_model
from app.modules.modelado_uml.repositories.uml_repository import UmlRepository
from app.modules.modelado_uml.services.uml_service import UmlService
from app.modules.proyectos_colaboracion.models import Project

logger = logging.getLogger(__name__)

# Fallback en memoria si Redis no está disponible
_MEMORY_PENDING: dict[str, int] = defaultdict(int)
_MEMORY_COOLDOWN: dict[str, float] = {}


class ProactiveAdvisorService:
    def __init__(self, db_factory=SessionLocal) -> None:
        self.db_factory = db_factory

    async def on_change(self, entry: ChangeLogEntry) -> None:
        if not settings.ai_proactive_enabled:
            return

        # Ignorar cambios generados por el propio sistema para no crear ciclos
        if entry.source == "system":
            return

        project_id_str = str(entry.project_id)
        cooldown_k = redis_key("proactive", "cooldown", project_id_str)
        pending_k = redis_key("proactive", "pending", project_id_str)

        redis_client = get_redis()

        # Comprobar cooldown
        if redis_client is not None:
            try:
                if redis_client.get(cooldown_k):
                    return
            except Exception as exc:
                logger.warning("Error leyendo cooldown en Redis: %s", exc)
        else:
            now_ts = datetime.now(UTC).timestamp()
            if _MEMORY_COOLDOWN.get(project_id_str, 0) > now_ts:
                return

        # Determinar disparador
        trigger: str | None = None
        if entry.action == "CREATE_PROJECT_VERSION":
            trigger = "version"
        elif entry.action in ("IMPORT_XMI", "IMPORT_XMI_REPLACE_DIAGRAM"):
            trigger = "import"
        else:
            # Incrementar contador de cambios pendientes
            current_pending = 1
            if redis_client is not None:
                try:
                    current_pending = redis_client.incr(pending_k)
                except Exception as exc:
                    logger.warning("Error incrementando pending en Redis: %s", exc)
                    _MEMORY_PENDING[project_id_str] += 1
                    current_pending = _MEMORY_PENDING[project_id_str]
            else:
                _MEMORY_PENDING[project_id_str] += 1
                current_pending = _MEMORY_PENDING[project_id_str]

            if current_pending >= settings.ai_proactive_min_changes:
                trigger = "min_changes"

        if not trigger:
            return

        # Procesar con sesión de base de datos
        with self.db_factory() as db:
            uml_repo = UmlRepository(db)
            diagram_id = entry.diagram_id
            if not diagram_id:
                diagrams = uml_repo.list_diagrams_by_project(entry.project_id)
                if diagrams:
                    diagram_id = diagrams[0].id

            recommendations: list[PlannedRecommendation] = []
            if diagram_id:
                recommendations = self._review_diagram(db, diagram_id)

            if trigger == "version":
                content = self._version_summary(db, entry.project_id)
                if not content and not recommendations:
                    return
                if not content:
                    content = (
                        "Nueva versión registrada en el proyecto. He analizado el diagrama "
                        f"y preparé {len(recommendations)} recomendaciones de consistencia."
                    )
            elif trigger == "import":
                if not recommendations:
                    return
                content = (
                    f"He analizado el modelo XMI importado y detecté {len(recommendations)} "
                    "aspectos que conviene revisar en el diagrama."
                )
            else:  # min_changes
                if not recommendations:
                    # Sin hallazgos no hace ruido
                    if redis_client is not None:
                        try:
                            redis_client.delete(pending_k)
                        except Exception:
                            pass
                    else:
                        _MEMORY_PENDING[project_id_str] = 0
                    return
                content = (
                    f"He revisado el diagrama tras acumular {settings.ai_proactive_min_changes} cambios "
                    f"del equipo y encontré {len(recommendations)} aspectos para mejorar."
                )

            actor_id = entry.actor_user_id or uuid4()
            await self._publish(
                db=db,
                project_id=entry.project_id,
                actor_user_id=actor_id,
                content=content,
                recommendations=recommendations,
                trigger=trigger,
                diagram_id=diagram_id,
            )

    def _review_diagram(self, db: Session, diagram_id: UUID) -> list[PlannedRecommendation]:
        uml_repo = UmlRepository(db)
        diagram = uml_repo.get_diagram(diagram_id)
        if not diagram:
            return []

        uml_service = UmlService(db)
        model = uml_service._build_internal_model(diagram)
        errors, warnings, recs = validate_internal_model(model)

        findings: list[PlannedRecommendation] = []
        for err in errors[:2]:
            findings.append(
                PlannedRecommendation(
                    category="uml_quality",
                    severity="critical",
                    title="Inconsistencia en el modelo UML",
                    description=err,
                    references=[],
                )
            )
        for warn in warnings[:2]:
            if len(findings) >= 3:
                break
            findings.append(
                PlannedRecommendation(
                    category="uml_quality",
                    severity="warning",
                    title="Advertencia de calidad UML",
                    description=warn,
                    references=[],
                )
            )
        for rec in recs[:2]:
            if len(findings) >= 3:
                break
            findings.append(
                PlannedRecommendation(
                    category="architecture",
                    severity="info",
                    title="Sugerencia de diseño",
                    description=rec,
                    references=[],
                )
            )
        return findings[:3]

    def _version_summary(self, db: Session, project_id: UUID) -> str:
        from app.core.changelog.service import ChangeLogService

        page = ChangeLogService().list_project(project_id, db=db, limit=40)
        if not page.items:
            return ""

        actors_summary: dict[str, list[str]] = defaultdict(list)
        for it in page.items:
            if it.action == "CREATE_PROJECT_VERSION":
                continue
            author = it.summary.split(":", 1)[0] if ":" in it.summary else "Integrante"
            summary_clean = it.summary
            if summary_clean not in actors_summary[author]:
                actors_summary[author].append(summary_clean)

        lines = ["Resumen de cambios de la nueva versión del proyecto:"]
        for author, actions in actors_summary.items():
            recent = actions[:3]
            lines.append(f"• {author}: {'; '.join(recent)}.")
        return "\n".join(lines)

    async def _publish(
        self,
        *,
        db: Session,
        project_id: UUID,
        actor_user_id: UUID,
        content: str,
        recommendations: list[PlannedRecommendation],
        trigger: str,
        diagram_id: UUID | None,
    ) -> None:
        contract_service = AssistantContractService(db)
        correlation_id = uuid4()
        try:
            assistant_message, _ = contract_service.create_message(
                project_id=project_id,
                user_id=None,
                payload=AiMessageCreateInternal(
                    role="assistant",
                    content=content,
                    correlation_id=correlation_id,
                    metadata_json={
                        "kind": "proactive",
                        "trigger": trigger,
                        "created_at": datetime.now(UTC).isoformat(),
                    },
                ),
            )
        except HTTPException as exc:
            if exc.status_code == 409:
                logger.info(
                    "El proyecto %s todavía no tiene conversación, no se publica sugerencia proactiva",
                    project_id,
                )
                return
            raise

        created_recs: list[AiRecommendation] = []
        for rec in recommendations:
            rec_model = AiRecommendation(
                project_id=project_id,
                conversation_id=assistant_message.conversation_id,
                source_message_id=assistant_message.id,
                category=rec.category,
                severity=rec.severity,
                title=rec.title,
                description=rec.description,
                references_json=rec.references,
                status="open",
            )
            db.add(rec_model)
            created_recs.append(rec_model)

        db.commit()
        db.refresh(assistant_message)
        for r in created_recs:
            db.refresh(r)

        # Aplicar cooldown y resetear pendientes
        project_id_str = str(project_id)
        cooldown_k = redis_key("proactive", "cooldown", project_id_str)
        pending_k = redis_key("proactive", "pending", project_id_str)

        redis_client = get_redis()
        if redis_client is not None:
            try:
                redis_client.set(cooldown_k, "1", ex=settings.ai_proactive_cooldown_seconds)
                redis_client.delete(pending_k)
            except Exception as exc:
                logger.warning("Error guardando cooldown en Redis: %s", exc)
        else:
            _MEMORY_COOLDOWN[project_id_str] = (
                datetime.now(UTC).timestamp() + settings.ai_proactive_cooldown_seconds
            )
            _MEMORY_PENDING[project_id_str] = 0

        # Publicar eventos WebSocket persistidos
        publisher = ProjectAiEventPublisher()
        msg_payload = {
            "id": str(assistant_message.id),
            "project_id": str(project_id),
            "conversation_id": str(assistant_message.conversation_id),
            "sequence_number": assistant_message.sequence_number,
            "role": "assistant",
            "author_user_id": None,
            "author_display_name": "Asistente CASE",
            "content": assistant_message.content,
            "status": "completed",
            "metadata_json": assistant_message.metadata_json or {},
            "created_at": assistant_message.created_at.isoformat(),
        }
        await publisher.publish_persisted(
            project_id=project_id,
            actor_user_id=actor_user_id,
            event_type="AI_MESSAGE_CREATED",
            payload=msg_payload,
            correlation_id=assistant_message.correlation_id,
            diagram_id=diagram_id,
            conversation_sequence=assistant_message.sequence_number,
        )

        for r in created_recs:
            rec_payload = {
                "id": str(r.id),
                "project_id": str(project_id),
                "conversation_id": str(r.conversation_id),
                "source_message_id": str(r.source_message_id),
                "category": r.category,
                "severity": r.severity,
                "title": r.title,
                "description": r.description,
                "references": r.references_json or [],
                "status": r.status,
                "created_at": r.created_at.isoformat(),
            }
            await publisher.publish_persisted(
                project_id=project_id,
                actor_user_id=actor_user_id,
                event_type="AI_RECOMMENDATION_CREATED",
                payload=rec_payload,
                correlation_id=assistant_message.correlation_id,
                diagram_id=diagram_id,
                conversation_sequence=assistant_message.sequence_number,
            )
