import asyncio
import logging
from uuid import UUID, uuid4

from ai_engine.context import PresupuestoContexto
from ai_engine.orchestration import OrquestadorIAUnificado
from ai_engine.providers.errores import ErrorProveedorIA
from ai_engine.providers.proveedor_reglas import ProveedorReglas
from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config.configuracion import settings as app_settings
from app.modules.asistente_proyecto.models import AccionIA, RecomendacionIA
from app.modules.asistente_proyecto.repositories.repositorio_asistente import RepositorioAsistente
from app.modules.asistente_proyecto.schemas.esquemas_asistente import (
    CreacionInternaMensajeIA,
    EstadoProveedorIA,
    ReferenciaIA,
    RespuestaInteraccionIA,
    SolicitudInteraccionIA,
)
from app.modules.asistente_proyecto.services.constructor_contexto import ConstructorContextoProyecto
from app.modules.asistente_proyecto.services.fabrica_proveedores import (
    obtener_url_ollama,
    seleccionar_proveedor,
)
from app.modules.asistente_proyecto.services.limitador_solicitudes import (
    limitador_solicitudes_ia_proyecto,
)
from app.modules.asistente_proyecto.services.publicador_eventos import PublicadorEventosIAProyecto
from app.modules.asistente_proyecto.services.recomendaciones_pendientes import clave_recomendacion, claves_abiertas
from app.modules.asistente_proyecto.services.servicio_asistente import ServicioContratoAsistente
from app.modules.modelado_uml.repositories.repositorio_uml import RepositorioUML

_INFERENCE_LIMIT = asyncio.Semaphore(max(1, app_settings.ai_max_concurrent_requests))
logger = logging.getLogger(__name__)


class ServicioAplicacionIAProyecto:
    @staticmethod
    def _texto_para_inferencia(payload: SolicitudInteraccionIA) -> str:
        if payload.recommendation_id is None:
            return payload.content
        return f"{payload.content}\nID de recomendacion: {payload.recommendation_id}"

    def __init__(self, db: Session) -> None:
        self.db = db
        self.contracts = ServicioContratoAsistente(db)
        self.repository = RepositorioAsistente(db)
        self.uml = RepositorioUML(db)

    @staticmethod
    def _referencias_validas(references: list[dict]) -> list[ReferenciaIA]:
        valid = []
        for reference in references:
            try:
                valid.append(ReferenciaIA.model_validate(reference))
            except ValidationError:
                logger.warning("AI result contains an invalid reference; ignoring it")
        return valid

    def _resolver_id_diagrama_proyecto(
        self, project_id: UUID, requested_diagram_id: UUID | None
    ) -> UUID:
        diagrams = self.uml.listar_diagramas_por_proyecto(project_id)
        if requested_diagram_id is not None:
            if not any(item.id == requested_diagram_id for item in diagrams):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "code": "PROJECT_DIAGRAM_NOT_FOUND",
                        "message": "El diagrama no pertenece al proyecto activo",
                    },
                )
            return requested_diagram_id
        if not diagrams:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "PROJECT_DIAGRAM_NOT_INITIALIZED",
                    "message": "El proyecto no tiene su diagrama inicializado",
                },
            )
        if len(diagrams) > 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "PROJECT_DIAGRAM_AMBIGUOUS",
                    "message": "El proyecto contiene mas de un diagrama y requiere normalizacion",
                },
            )
        return diagrams[0].id

    async def estado_proveedor(self, project_id: UUID, user_id: UUID) -> EstadoProveedorIA:
        project_settings = self.contracts.obtener_configuracion(project_id, user_id)
        configured = [source for source in ("local", "aws") if obtener_url_ollama(source)]
        gemini_configured = bool(app_settings.gemini_api_key)
        if project_settings.preferred_provider == "rule_engine":
            return EstadoProveedorIA(
                provider="rule_engine",
                available=True,
                models=["deterministic-v2"],
                selected_model="deterministic-v2",
                selected_model_available=True,
                latency_ms=0,
                configured_sources=configured,
                gemini_configured=gemini_configured,
            )
        provider, selected_model = await seleccionar_proveedor(
            project_settings.preferred_provider, project_settings.model_name,
            (getattr(project_settings, "settings_json", None) or {}).get("origen_ollama", app_settings.ollama_default_source),
        )
        if provider is None:
            return EstadoProveedorIA(
                provider=project_settings.preferred_provider,
                available=False,
                models=[],
                selected_model=selected_model,
                selected_model_available=False,
                latency_ms=0,
                error_code="missing_api_key" if project_settings.preferred_provider == "gemini" else "ollama_source_unavailable",
                error_message="Falta GEMINI_API_KEY" if project_settings.preferred_provider == "gemini" else "El origen Ollama del proyecto no esta configurado en este servidor",
                configured_sources=configured,
                gemini_configured=gemini_configured,
            )
        health = await provider.health(selected_model)
        return EstadoProveedorIA(
            provider=health.provider,
            available=health.available,
            models=health.installed_models,
            selected_model=selected_model,
            selected_model_available=bool(health.requested_model_available),
            latency_ms=health.latency_ms,
            error_code=health.error_code,
            error_message=health.error_message,
            configured_sources=configured,
            gemini_configured=gemini_configured,
        )

    async def interactuar(
        self, project_id: UUID, user_id: UUID, payload: SolicitudInteraccionIA
    ) -> RespuestaInteraccionIA:
        if len(payload.content) > app_settings.ai_max_input_chars:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"El mensaje supera {app_settings.ai_max_input_chars} caracteres",
            )
        project, member = self.contracts._proyecto_y_miembro(project_id, user_id)
        diagram_id = self._resolver_id_diagrama_proyecto(project_id, payload.diagram_id)
        project_settings = self.contracts.obtener_configuracion(project_id, user_id)
        if not project_settings.enabled:
            raise HTTPException(status_code=409, detail="El asistente esta deshabilitado")
        conversation = self.contracts.obtener_conversacion(project_id, user_id, payload.conversation_id)
        context = await ConstructorContextoProyecto(self.db).construir(
            project=project,
            member=member,
            user_id=user_id,
            conversation=conversation,
            settings=project_settings,
            diagram_id=diagram_id,
            requested=payload.requested_context,
        )
        correlation_id = uuid4()
        user_message, created = self.contracts.crear_mensaje(
            project_id,
            user_id,
            CreacionInternaMensajeIA(
                role="user",
                content=payload.content,
                client_message_id=payload.client_message_id,
                correlation_id=correlation_id,
                status="pending",
            ),
            conversation.id,
        )
        if not created:
            assistant_message = self.repository.obtener_mensaje_asistente_por_correlacion(
                conversation.id, user_message.correlation_id
            )
            if assistant_message is None:
                raise HTTPException(status_code=409, detail="La interaccion ya esta en proceso")
            return self._respuesta_desde_persistencia(assistant_message, idempotent=True)

        actor_name = context.actor.display_name
        context_actor_name = actor_name
        rate_key = f"{project_id}:{user_id}"
        try:
            await limitador_solicitudes_ia_proyecto.adquirir(rate_key)
        except HTTPException:
            user_message.status = "failed"
            self.repository.guardar_mensaje(user_message)
            self.db.commit()
            raise
        publisher = PublicadorEventosIAProyecto()
        await self._publicar_seguro(
            publisher.publicar_persistido,
            project_id=project_id,
            actor_user_id=user_id,
            event_type="AI_MESSAGE_CREATED",
            payload=self._contenido_evento_mensaje(user_message, actor_name),
            correlation_id=user_message.correlation_id,
            diagram_id=diagram_id,
            conversation_sequence=user_message.sequence_number,
        )
        await self._publicar_seguro(
            publisher.publicar_efimero,
            project_id=project_id,
            actor_user_id=user_id,
            actor_name=actor_name,
            event_type="AI_PROCESSING_STARTED",
            payload={
                "message_id": str(user_message.id),
                "conversation_id": str(conversation.id),
            },
            correlation_id=user_message.correlation_id,
            conversation_sequence=user_message.sequence_number,
        )
        persisted_user_message_id = user_message.id
        persisted_correlation_id = user_message.correlation_id
        try:
            preferred_provider, selected_model = await seleccionar_proveedor(
                project_settings.preferred_provider, project_settings.model_name,
                (getattr(project_settings, "settings_json", None) or {}).get("origen_ollama", app_settings.ollama_default_source),
            )
            fallback_enabled = (
                project_settings.fallback_enabled and app_settings.ai_rule_fallback_enabled
            )
            orchestrator = OrquestadorIAUnificado(
                primary_provider=preferred_provider,
                fallback_provider=ProveedorReglas(),
                context_budget=PresupuestoContexto(app_settings.ai_max_context_chars),
            )
            # Libera cualquier transaccion de lectura antes de esperar inferencia local.
            self.db.rollback()
            async with _INFERENCE_LIMIT:
                outcome = await orchestrator.process(
                    request_text=self._texto_para_inferencia(payload),
                    context=context,
                    correlation_id=persisted_correlation_id,
                    model=selected_model,
                    fallback_enabled=fallback_enabled,
                )
        except Exception as exc:
            self.db.rollback()
            failed = self.repository.obtener_mensaje(persisted_user_message_id)
            if failed is not None:
                failed.status = "failed"
                self.repository.guardar_mensaje(failed)
                self.db.commit()
                await self._publicar_seguro(
                    publisher.publicar_persistido,
                    project_id=project_id,
                    actor_user_id=user_id,
                    event_type="AI_MESSAGE_STATUS_CHANGED",
                    payload=self._contenido_evento_mensaje(failed, actor_name),
                    correlation_id=persisted_correlation_id,
                    diagram_id=diagram_id,
                    conversation_sequence=failed.sequence_number,
                )
            await self._publicar_seguro(
                publisher.publicar_efimero,
                project_id=project_id,
                actor_user_id=user_id,
                actor_name=context_actor_name,
                event_type="AI_PROCESSING_FAILED",
                payload={
                    "message_id": str(persisted_user_message_id),
                    "conversation_id": str(conversation.id),
                    "recoverable": True,
                },
                correlation_id=persisted_correlation_id,
            )
            if isinstance(exc, ErrorProveedorIA):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail={"code": exc.code, "message": str(exc)},
                ) from exc
            raise
        finally:
            await limitador_solicitudes_ia_proyecto.liberar(rate_key)
        if member.project_role not in {"EDITOR", "ORGANIZADOR"} and outcome.result.actions:
            outcome.result.actions = []
            outcome.result.warnings.append(
                "Tu rol permite consultar, pero no proponer cambios aplicables al proyecto."
            )
        try:
            assistant_message = self._persistir_resultado(
                project_id=project_id,
                conversation_id=conversation.id,
                user_id=user_id,
                user_message_id=persisted_user_message_id,
                correlation_id=persisted_correlation_id,
                diagram_id=diagram_id,
                base_diagram_version=payload.base_diagram_version,
                outcome=outcome,
            )
        except Exception:
            self.db.rollback()
            if self.repository.obtener_mensaje_asistente_por_correlacion(
                conversation.id, persisted_correlation_id
            ) is None:
                failed = self.repository.obtener_mensaje(persisted_user_message_id)
                if failed is not None and failed.status == "pending":
                    failed.status = "failed"
                    self.repository.guardar_mensaje(failed)
                    self.db.commit()
                    await self._publicar_seguro(
                        publisher.publicar_persistido,
                        project_id=project_id,
                        actor_user_id=user_id,
                        event_type="AI_MESSAGE_STATUS_CHANGED",
                        payload=self._contenido_evento_mensaje(failed, actor_name),
                        correlation_id=persisted_correlation_id,
                        diagram_id=diagram_id,
                        conversation_sequence=failed.sequence_number,
                    )
            await self._publicar_seguro(
                publisher.publicar_efimero,
                project_id=project_id,
                actor_user_id=user_id,
                actor_name=actor_name,
                event_type="AI_PROCESSING_FAILED",
                payload={
                    "message_id": str(persisted_user_message_id),
                    "conversation_id": str(conversation.id),
                    "recoverable": True,
                },
                correlation_id=persisted_correlation_id,
            )
            logger.exception("No se pudo persistir la respuesta del asistente")
            raise
        await self._publicar_resultado(
            publisher=publisher,
            project_id=project_id,
            conversation_id=conversation.id,
            user_id=user_id,
            actor_name=actor_name,
            assistant_message=assistant_message,
            diagram_id=diagram_id,
        )
        logger.info(
            "ai_interaction_completed",
            extra={
                "correlation_id": str(persisted_correlation_id),
                "project_id": str(project_id),
                "user_id": str(user_id),
                "provider": outcome.result.provider,
                "model": outcome.result.model,
                "intents": [item.name for item in outcome.result.detected_intents],
                "duration_ms": outcome.duration_ms,
                "provider_duration_ms": outcome.provider_duration_ms,
                "prompt_tokens": outcome.prompt_tokens,
                "completion_tokens": outcome.completion_tokens,
                "retries": outcome.retries,
                "fallback_used": outcome.result.fallback_used,
                "actions_count": len(outcome.result.actions),
                "recommendations_count": len(outcome.result.recommendations),
                "error_code": outcome.error_code,
            },
        )
        return self._respuesta_desde_persistencia(assistant_message)

    async def _publicar_resultado(
        self,
        *,
        publisher: PublicadorEventosIAProyecto,
        project_id: UUID,
        conversation_id: UUID,
        user_id: UUID,
        actor_name: str,
        assistant_message,
        diagram_id: UUID | None,
    ) -> None:
        await self._publicar_seguro(
            publisher.publicar_persistido,
            project_id=project_id,
            actor_user_id=user_id,
            event_type="AI_MESSAGE_CREATED",
            payload=self._contenido_evento_mensaje(assistant_message, "Asistente CASE"),
            correlation_id=assistant_message.correlation_id,
            diagram_id=diagram_id,
            conversation_sequence=assistant_message.sequence_number,
        )
        for action in self.repository.listar_acciones_por_mensaje(assistant_message.id):
            await self._publicar_seguro(
                publisher.publicar_persistido,
                project_id=project_id,
                actor_user_id=user_id,
                event_type="AI_ACTION_PROPOSED",
                payload=self._diccionario_accion(action),
                correlation_id=assistant_message.correlation_id,
                diagram_id=diagram_id,
                conversation_sequence=assistant_message.sequence_number,
            )
        for recommendation in self.repository.listar_recomendaciones_por_mensaje(
            assistant_message.id
        ):
            await self._publicar_seguro(
                publisher.publicar_persistido,
                project_id=project_id,
                actor_user_id=user_id,
                event_type="AI_RECOMMENDATION_CREATED",
                payload=self._diccionario_recomendacion(recommendation),
                correlation_id=assistant_message.correlation_id,
                diagram_id=diagram_id,
                conversation_sequence=assistant_message.sequence_number,
            )
        await self._publicar_seguro(
            publisher.publicar_efimero,
            project_id=project_id,
            actor_user_id=user_id,
            actor_name=actor_name,
            event_type="AI_PROCESSING_FINISHED",
            payload={
                "message_id": str(assistant_message.id),
                "conversation_id": str(conversation_id),
            },
            correlation_id=assistant_message.correlation_id,
            conversation_sequence=assistant_message.sequence_number,
        )

    @staticmethod
    async def _publicar_seguro(callable_, **kwargs) -> None:
        try:
            await callable_(**kwargs)
        except Exception:
            logger.exception("No se pudo publicar un evento colaborativo de IA")

    @staticmethod
    def _contenido_evento_mensaje(message, author_name: str) -> dict:
        return {
            "id": str(message.id),
            "conversation_id": str(message.conversation_id),
            "project_id": str(message.project_id),
            "author_user_id": str(message.author_user_id) if message.author_user_id else None,
            "author_display_name": author_name,
            "role": message.role,
            "content": message.content,
            "sequence_number": message.sequence_number,
            "client_message_id": (
                str(message.client_message_id) if message.client_message_id else None
            ),
            "correlation_id": str(message.correlation_id),
            "status": message.status,
            "detected_intents": message.detected_intents,
            "references_json": message.references_json,
            "metadata_json": message.metadata_json,
            "created_at": message.created_at.isoformat(),
            "updated_at": message.updated_at.isoformat(),
        }

    def _persistir_resultado(
        self,
        *,
        project_id: UUID,
        conversation_id: UUID,
        user_id: UUID,
        user_message_id: UUID,
        correlation_id: UUID,
        diagram_id: UUID | None,
        base_diagram_version: int | None,
        outcome,
    ):
        conversation = self.repository.obtener_conversacion(
            project_id, conversation_id, for_update=True
        )
        if conversation is None:
            raise HTTPException(status_code=409, detail="La conversacion no esta disponible")
        existing = self.repository.obtener_mensaje_asistente_por_correlacion(
            conversation.id, correlation_id
        )
        if existing is not None:
            return existing
        user_message = self.repository.obtener_mensaje(user_message_id)
        if user_message is None:
            raise HTTPException(status_code=409, detail="El mensaje original no esta disponible")
        result = outcome.result
        assistant_message, _ = self.contracts.crear_mensaje(
            project_id,
            None,
            CreacionInternaMensajeIA(
                role="assistant",
                content=result.answer,
                correlation_id=correlation_id,
                status="completed",
                detected_intents=[intent.name for intent in result.detected_intents],
                references=self._referencias_validas(result.references),
                metadata_json={
                    "provider": result.provider,
                    "model": result.model,
                    "fallback_used": result.fallback_used,
                    "warnings": result.warnings,
                    "requires_user_input": result.requires_user_input,
                    "clarification_question": result.clarification_question,
                    "duration_ms": outcome.duration_ms,
                    "provider_duration_ms": outcome.provider_duration_ms,
                    "prompt_tokens": outcome.prompt_tokens,
                    "completion_tokens": outcome.completion_tokens,
                    "retries": outcome.retries,
                    "context_reduced": outcome.context_reduced,
                    "error_code": outcome.error_code,
                },
            ),
            conversation.id,
        )
        for action in result.actions:
            effective_diagram_id = action.diagram_id or diagram_id
            action_payload = dict(action.payload)
            action_payload["_plan"] = {
                "temporary_id": str(action.id),
                "order": action.order,
                "depends_on": [str(item) for item in action.depends_on],
                "diagram_id": str(effective_diagram_id) if effective_diagram_id else None,
                "base_diagram_version": action.base_diagram_version
                if action.base_diagram_version is not None
                else base_diagram_version,
                "target_name": action.target_name,
                "confidence": action.confidence,
                "explanation": action.explanation,
            }
            self.db.add(
                AccionIA(
                    project_id=project_id,
                    conversation_id=conversation.id,
                    source_message_id=assistant_message.id,
                    requested_by_user_id=user_id,
                    action_type=action.action_type,
                    target_type=action.target_type,
                    target_id=action.target_id,
                    payload=action_payload,
                    risk_level=action.risk_level,
                    requires_confirmation=action.requires_confirmation,
                    status="proposed",
                    idempotency_key=action.id,
                )
            )
        open_keys = claves_abiertas(self.db, project_id)
        for recommendation in result.recommendations:
            key = clave_recomendacion(recommendation.title, recommendation.description)
            if key in open_keys:
                continue
            open_keys.add(key)
            self.db.add(
                RecomendacionIA(
                    project_id=project_id,
                    conversation_id=conversation.id,
                    source_message_id=assistant_message.id,
                    category=recommendation.category,
                    severity=recommendation.severity,
                    title=recommendation.title,
                    description=recommendation.description,
                    references_json=[
                        item.model_dump(mode="json")
                        for item in self._referencias_validas(recommendation.references)
                    ],
                    status="open",
                )
            )
        user_message.status = "completed"
        user_message.detected_intents = [item.name for item in result.detected_intents]
        self.repository.guardar_mensaje(user_message)
        self.db.commit()
        return assistant_message

    def _respuesta_desde_persistencia(
        self, message, *, idempotent: bool = False
    ) -> RespuestaInteraccionIA:
        actions = self.repository.listar_acciones_por_mensaje(message.id)
        recommendations = self.repository.listar_recomendaciones_por_mensaje(message.id)
        metadata = message.metadata_json or {}
        warnings = list(metadata.get("warnings") or [])
        if idempotent:
            warnings.append("Respuesta idempotente reutilizada.")
        return RespuestaInteraccionIA(
            message_id=message.id,
            correlation_id=message.correlation_id,
            status=message.status,
            detected_intents=message.detected_intents,
            answer=message.content,
            actions=[self._diccionario_accion(item) for item in actions],
            recommendations=[self._diccionario_recomendacion(item) for item in recommendations],
            conversation_sequence=message.sequence_number,
            provider=metadata.get("provider", "unknown"),
            model=metadata.get("model", "unknown"),
            fallback_used=bool(metadata.get("fallback_used", False)),
            warnings=warnings,
            requires_user_input=bool(metadata.get("requires_user_input", False)),
            clarification_question=metadata.get("clarification_question"),
            duration_ms=int(metadata.get("duration_ms") or 0),
            context_reduced=bool(metadata.get("context_reduced", False)),
        )

    @staticmethod
    def _diccionario_accion(item: AccionIA) -> dict:
        from app.modules.asistente_proyecto.schemas.esquemas_asistente import RespuestaAccionIA

        return RespuestaAccionIA.model_validate(item).model_dump(mode="json")

    @staticmethod
    def _diccionario_recomendacion(item: RecomendacionIA) -> dict:
        from app.modules.asistente_proyecto.schemas.esquemas_asistente import (
            RespuestaRecomendacionIA,
        )

        return RespuestaRecomendacionIA.model_validate(item).model_dump(mode="json")
