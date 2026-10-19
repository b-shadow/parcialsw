import asyncio
import logging
from uuid import UUID, uuid4

from ai_engine.context import ContextBudget
from ai_engine.orchestration import UnifiedAiOrchestrator
from ai_engine.providers.errors import AiProviderError
from ai_engine.providers.rule_engine_provider import RuleEngineProvider
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config.settings import settings as app_settings
from app.modules.asistente_proyecto.models import AiAction, AiMessage, AiRecommendation
from app.modules.asistente_proyecto.repositories.assistant_repository import AssistantRepository
from app.modules.asistente_proyecto.schemas.assistant import (
    AiInteractionRequest,
    AiInteractionResponse,
    AiMessageCreateInternal,
    AiProviderHealthResponse,
)
from app.modules.asistente_proyecto.services.assistant_service import AssistantContractService
from app.modules.asistente_proyecto.services.context_builder import ProjectContextBuilder
from app.modules.asistente_proyecto.services.event_publisher import ProjectAiEventPublisher
from app.modules.asistente_proyecto.services.provider_factory import (
    get_ollama_provider,
    resolve_ollama_model,
)
from app.modules.asistente_proyecto.services.rate_limiter import project_ai_rate_limiter
from app.modules.modelado_uml.repositories.uml_repository import UmlRepository

_INFERENCE_LIMIT = asyncio.Semaphore(max(1, app_settings.ai_max_concurrent_requests))
logger = logging.getLogger(__name__)


class ProjectAiApplicationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.contracts = AssistantContractService(db)
        self.repository = AssistantRepository(db)
        self.uml = UmlRepository(db)

    def _resolve_project_diagram_id(
        self, project_id: UUID, requested_diagram_id: UUID | None
    ) -> UUID:
        diagrams = self.uml.list_diagrams_by_project(project_id)
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

    async def provider_health(self, project_id: UUID, user_id: UUID) -> AiProviderHealthResponse:
        project_settings = self.contracts.get_settings(project_id, user_id)
        if project_settings.preferred_provider == "rule_engine":
            return AiProviderHealthResponse(
                provider="rule_engine",
                available=True,
                models=["deterministic-v2"],
                selected_model="deterministic-v2",
                selected_model_available=True,
                latency_ms=0,
            )
        provider = get_ollama_provider()
        selected_model = await resolve_ollama_model(provider, project_settings.model_name)
        health = await provider.health(selected_model)
        return AiProviderHealthResponse(
            provider=health.provider,
            available=health.available,
            models=health.installed_models,
            selected_model=selected_model,
            selected_model_available=bool(health.requested_model_available),
            latency_ms=health.latency_ms,
            error_code=health.error_code,
            error_message=health.error_message,
        )

    async def interact(
        self, project_id: UUID, user_id: UUID, payload: AiInteractionRequest
    ) -> AiInteractionResponse:
        if len(payload.content) > app_settings.ai_max_input_chars:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"El mensaje supera {app_settings.ai_max_input_chars} caracteres",
            )
        project, member = self.contracts._project_and_member(project_id, user_id)
        diagram_id = self._resolve_project_diagram_id(project_id, payload.diagram_id)
        project_settings = self.contracts.get_settings(project_id, user_id)
        if not project_settings.enabled:
            raise HTTPException(status_code=409, detail="El asistente esta deshabilitado")
        conversation = self.contracts.get_conversation(
            project_id, user_id, payload.conversation_id
        )
        context = ProjectContextBuilder(self.db).build(
            project=project,
            member=member,
            user_id=user_id,
            conversation=conversation,
            settings=project_settings,
            diagram_id=diagram_id,
            requested=payload.requested_context,
        )
        correlation_id = uuid4()
        user_message, created = self.contracts.create_message(
            project_id,
            user_id,
            AiMessageCreateInternal(
                role="user",
                content=payload.content,
                client_message_id=payload.client_message_id,
                correlation_id=correlation_id,
                status="pending",
            ),
            conversation.id,
        )
        if not created:
            assistant_message = self.repository.get_assistant_message_by_correlation(
                conversation.id, user_message.correlation_id
            )
            if assistant_message is None:
                raise HTTPException(status_code=409, detail="La interaccion ya esta en proceso")
            return self._response_from_persistence(assistant_message, idempotent=True)

        actor_name = context.actor.display_name
        context_actor_name = actor_name
        rate_key = f"{project_id}:{user_id}"
        try:
            await project_ai_rate_limiter.acquire(rate_key)
        except HTTPException:
            user_message.status = "failed"
            self.db.commit()
            raise
        publisher = ProjectAiEventPublisher()
        await self._safe_publish(
            publisher.publish_persisted,
            project_id=project_id,
            actor_user_id=user_id,
            event_type="AI_MESSAGE_CREATED",
            payload=self._message_event_payload(user_message, actor_name),
            correlation_id=user_message.correlation_id,
            diagram_id=diagram_id,
            conversation_sequence=user_message.sequence_number,
        )
        await self._safe_publish(
            publisher.publish_ephemeral,
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
        preferred_provider = (
            get_ollama_provider() if project_settings.preferred_provider == "ollama" else None
        )
        fallback_enabled = project_settings.fallback_enabled and app_settings.ai_rule_fallback_enabled
        selected_model = project_settings.model_name
        if preferred_provider is not None:
            selected_model = await resolve_ollama_model(
                preferred_provider, project_settings.model_name
            )
        persisted_user_message_id = user_message.id
        persisted_correlation_id = user_message.correlation_id
        orchestrator = UnifiedAiOrchestrator(
            primary_provider=preferred_provider,
            fallback_provider=RuleEngineProvider(),
            context_budget=ContextBudget(app_settings.ai_max_context_chars),
        )
        # Libera cualquier transaccion de lectura antes de esperar inferencia local.
        self.db.rollback()
        try:
            async with _INFERENCE_LIMIT:
                outcome = await orchestrator.process(
                    request_text=payload.content,
                    context=context,
                    correlation_id=persisted_correlation_id,
                    model=selected_model,
                    fallback_enabled=fallback_enabled,
                )
        except Exception as exc:
            failed = self.db.get(AiMessage, persisted_user_message_id)
            if failed is not None:
                failed.status = "failed"
                self.db.commit()
            await self._safe_publish(
                publisher.publish_ephemeral,
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
            if isinstance(exc, AiProviderError):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail={"code": exc.code, "message": str(exc)},
                ) from exc
            raise
        finally:
            await project_ai_rate_limiter.release(rate_key)
        if member.project_role not in {"EDITOR", "ORGANIZADOR"} and outcome.result.actions:
            outcome.result.actions = []
            outcome.result.warnings.append(
                "Tu rol permite consultar, pero no proponer cambios aplicables al proyecto."
            )
        assistant_message = self._persist_result(
            project_id=project_id,
            conversation_id=conversation.id,
            user_id=user_id,
            user_message_id=persisted_user_message_id,
            correlation_id=persisted_correlation_id,
            diagram_id=diagram_id,
            base_diagram_version=payload.base_diagram_version,
            outcome=outcome,
        )
        await self._publish_result(
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
        return self._response_from_persistence(assistant_message)

    async def _publish_result(
        self,
        *,
        publisher: ProjectAiEventPublisher,
        project_id: UUID,
        conversation_id: UUID,
        user_id: UUID,
        actor_name: str,
        assistant_message: AiMessage,
        diagram_id: UUID | None,
    ) -> None:
        await self._safe_publish(
            publisher.publish_persisted,
            project_id=project_id,
            actor_user_id=user_id,
            event_type="AI_MESSAGE_CREATED",
            payload=self._message_event_payload(assistant_message, "Asistente CASE"),
            correlation_id=assistant_message.correlation_id,
            diagram_id=diagram_id,
            conversation_sequence=assistant_message.sequence_number,
        )
        for action in self.repository.list_actions_for_message(assistant_message.id):
            await self._safe_publish(
                publisher.publish_persisted,
                project_id=project_id,
                actor_user_id=user_id,
                event_type="AI_ACTION_PROPOSED",
                payload=self._action_dict(action),
                correlation_id=assistant_message.correlation_id,
                diagram_id=diagram_id,
                conversation_sequence=assistant_message.sequence_number,
            )
        for recommendation in self.repository.list_recommendations_for_message(
            assistant_message.id
        ):
            await self._safe_publish(
                publisher.publish_persisted,
                project_id=project_id,
                actor_user_id=user_id,
                event_type="AI_RECOMMENDATION_CREATED",
                payload=self._recommendation_dict(recommendation),
                correlation_id=assistant_message.correlation_id,
                diagram_id=diagram_id,
                conversation_sequence=assistant_message.sequence_number,
            )
        await self._safe_publish(
            publisher.publish_ephemeral,
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
    async def _safe_publish(callable_, **kwargs) -> None:
        try:
            await callable_(**kwargs)
        except Exception:
            logger.exception("No se pudo publicar un evento colaborativo de IA")

    @staticmethod
    def _message_event_payload(message: AiMessage, author_name: str) -> dict:
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

    def _persist_result(
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
    ) -> AiMessage:
        conversation = self.repository.get_conversation(
            project_id, conversation_id, for_update=True
        )
        if conversation is None:
            raise HTTPException(status_code=409, detail="La conversacion no esta disponible")
        existing = self.repository.get_assistant_message_by_correlation(
            conversation.id, correlation_id
        )
        if existing is not None:
            return existing
        user_message = self.db.get(AiMessage, user_message_id)
        if user_message is None:
            raise HTTPException(status_code=409, detail="El mensaje original no esta disponible")
        result = outcome.result
        conversation.last_message_sequence += 1
        assistant_message = AiMessage(
            conversation_id=conversation.id,
            project_id=project_id,
            author_user_id=None,
            role="assistant",
            content=result.answer,
            sequence_number=conversation.last_message_sequence,
            correlation_id=correlation_id,
            status="completed",
            detected_intents=[item.name for item in result.detected_intents],
            references_json=result.references,
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
        )
        self.db.add(assistant_message)
        self.db.flush()
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
                AiAction(
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
        for recommendation in result.recommendations:
            self.db.add(
                AiRecommendation(
                    project_id=project_id,
                    conversation_id=conversation.id,
                    source_message_id=assistant_message.id,
                    category=recommendation.category,
                    severity=recommendation.severity,
                    title=recommendation.title,
                    description=recommendation.description,
                    references_json=recommendation.references,
                    status="open",
                )
            )
        user_message.status = "completed"
        user_message.detected_intents = [item.name for item in result.detected_intents]
        self.db.commit()
        self.db.refresh(assistant_message)
        return assistant_message

    def _response_from_persistence(
        self, message: AiMessage, *, idempotent: bool = False
    ) -> AiInteractionResponse:
        actions = self.repository.list_actions_for_message(message.id)
        recommendations = self.repository.list_recommendations_for_message(message.id)
        metadata = message.metadata_json or {}
        warnings = list(metadata.get("warnings") or [])
        if idempotent:
            warnings.append("Respuesta idempotente reutilizada.")
        return AiInteractionResponse(
            message_id=message.id,
            correlation_id=message.correlation_id,
            status=message.status,
            detected_intents=message.detected_intents,
            answer=message.content,
            actions=[self._action_dict(item) for item in actions],
            recommendations=[self._recommendation_dict(item) for item in recommendations],
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
    def _action_dict(item: AiAction) -> dict:
        from app.modules.asistente_proyecto.schemas.assistant import AiActionResponse

        return AiActionResponse.model_validate(item).model_dump(mode="json")

    @staticmethod
    def _recommendation_dict(item: AiRecommendation) -> dict:
        from app.modules.asistente_proyecto.schemas.assistant import AiRecommendationResponse

        return AiRecommendationResponse.model_validate(item).model_dump(mode="json")
