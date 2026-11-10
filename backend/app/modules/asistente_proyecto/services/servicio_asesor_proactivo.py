"""Servicio de asesoría proactiva de la IA del proyecto (V2.1).

La IA actúa como un integrante más del equipo: observa el flujo de cambios en NoSQL,
detecta anomalías o eventos clave (versiones, importaciones, acumulación de cambios)
y propone mejoras sin necesidad de ser invocada explícitamente.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from ai_engine.orchestration.contratos import RecomendacionPlanificada
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.changelog.contratos import EntradaRegistroCambios
from app.core.config.configuracion import settings
from app.core.database.sesion import SessionLocal
from app.core.redis.cliente import clave_redis, obtener_redis
from app.modules.asistente_proyecto.models import RecomendacionIA
from app.modules.asistente_proyecto.schemas.esquemas_asistente import CreacionInternaMensajeIA
from app.modules.asistente_proyecto.services.publicador_eventos import PublicadorEventosIAProyecto
from app.modules.asistente_proyecto.services.recomendaciones_pendientes import (
    clave_recomendacion,
    claves_abiertas,
)
from app.modules.asistente_proyecto.services.servicio_asistente import ServicioContratoAsistente
from app.modules.modelado_uml.engine.modelo_interno import ModeloDiagramaUML
from app.modules.modelado_uml.engine.validador import validar_modelo_interno
from app.modules.modelado_uml.repositories.repositorio_uml import RepositorioUML
from app.modules.modelado_uml.services.servicio_uml import ServicioUML

logger = logging.getLogger(__name__)

# Fallback en memoria si Redis no está disponible
_MEMORY_PENDING: dict[str, int] = defaultdict(int)
_MEMORY_COOLDOWN: dict[str, float] = {}


class ServicioAsesorProactivo:
    def __init__(
        self,
        db_factory=SessionLocal,
        diagram_model_loader: Callable[[Session, UUID], ModeloDiagramaUML] | None = None,
    ) -> None:
        self.db_factory = db_factory
        self.diagram_model_loader = diagram_model_loader

    async def al_cambiar(self, entry: EntradaRegistroCambios) -> None:
        if not settings.ai_proactive_enabled:
            return

        # Ignorar cambios generados por el propio sistema para no crear ciclos
        if entry.source == "system":
            return

        project_id_str = str(entry.project_id)
        cooldown_k = clave_redis("proactive", "cooldown", project_id_str)
        pending_k = clave_redis("proactive", "pending", project_id_str)

        redis_client = obtener_redis()

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
            uml_repo = RepositorioUML(db)
            diagram_id = entry.diagram_id
            if not diagram_id:
                diagrams = uml_repo.listar_diagramas_por_proyecto(entry.project_id)
                if diagrams:
                    diagram_id = diagrams[0].id

            recommendations: list[RecomendacionPlanificada] = []
            if diagram_id:
                recommendations = self._revisar_diagrama(db, diagram_id)
            open_keys = claves_abiertas(db, entry.project_id)
            recommendations = [
                rec for rec in recommendations
                if clave_recomendacion(rec.title, rec.description) not in open_keys
            ]

            if not recommendations and trigger != "version":
                # Los hallazgos ya están pendientes de decisión o el diagrama no tiene hallazgos.
                if redis_client is not None:
                    try:
                        redis_client.delete(pending_k)
                    except Exception:
                        pass
                else:
                    _MEMORY_PENDING[project_id_str] = 0
                return

            if trigger == "version":
                content = self._resumen_version(db, entry.project_id)
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

    def _revisar_diagrama(self, db: Session, diagram_id: UUID) -> list[RecomendacionPlanificada]:
        uml_repo = RepositorioUML(db)
        diagram = uml_repo.obtener_diagrama(diagram_id)
        if not diagram:
            return []

        model = (
            self.diagram_model_loader(db, diagram_id)
            if self.diagram_model_loader is not None
            else ServicioUML(db)._construir_modelo_interno(diagram)
        )
        errors, warnings, recs = validar_modelo_interno(model)

        findings: list[RecomendacionPlanificada] = []
        for err in errors[:2]:
            findings.append(
                RecomendacionPlanificada(
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
                RecomendacionPlanificada(
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
                RecomendacionPlanificada(
                    category="architecture",
                    severity="info",
                    title="Sugerencia de diseño",
                    description=rec,
                    references=[],
                )
            )
        return findings[:3]

    def _resumen_version(self, db: Session, project_id: UUID) -> str:
        from app.core.changelog.servicio import ServicioRegistroCambios

        page = ServicioRegistroCambios().listar_proyecto(project_id, db=db, limit=40)
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
        recommendations: list[RecomendacionPlanificada],
        trigger: str,
        diagram_id: UUID | None,
    ) -> None:
        contract_service = ServicioContratoAsistente(db)
        correlation_id = uuid4()
        try:
            assistant_message, _ = contract_service.crear_mensaje(
                project_id=project_id,
                user_id=None,
                payload=CreacionInternaMensajeIA(
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

        created_recs: list[RecomendacionIA] = []
        for rec in recommendations:
            rec_model = RecomendacionIA(
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
        cooldown_k = clave_redis("proactive", "cooldown", project_id_str)
        pending_k = clave_redis("proactive", "pending", project_id_str)

        redis_client = obtener_redis()
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
        publisher = PublicadorEventosIAProyecto()
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
        await publisher.publicar_persistido(
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
            await publisher.publicar_persistido(
                project_id=project_id,
                actor_user_id=actor_user_id,
                event_type="AI_RECOMMENDATION_CREATED",
                payload=rec_payload,
                correlation_id=assistant_message.correlation_id,
                diagram_id=diagram_id,
                conversation_sequence=assistant_message.sequence_number,
            )
