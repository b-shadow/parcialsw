import time
from uuid import UUID

from ai_engine.context import AiProjectContext, ContextBudget, sanitize_untrusted_text
from ai_engine.orchestration.action_policy import ActionPolicy
from ai_engine.orchestration.contracts import OrchestrationResult, UnifiedAiResult
from ai_engine.orchestration.intent_classifier import IntentClassifier
from ai_engine.orchestration.prompt_builder import PromptBuilder
from ai_engine.providers.base import AiProvider, ProviderRequest
from ai_engine.providers.errors import AiProviderError, InvalidStructuredOutputError
from ai_engine.providers.rule_engine_provider import RuleEngineProvider


class UnifiedAiOrchestrator:
    def __init__(
        self,
        *,
        primary_provider: AiProvider | None,
        fallback_provider: RuleEngineProvider | None = None,
        classifier: IntentClassifier | None = None,
        action_policy: ActionPolicy | None = None,
        context_budget: ContextBudget | None = None,
        prompt_builder: PromptBuilder | None = None,
    ) -> None:
        self.primary_provider = primary_provider
        self.fallback_provider = fallback_provider or RuleEngineProvider()
        self.classifier = classifier or IntentClassifier()
        self.action_policy = action_policy or ActionPolicy()
        self.context_budget = context_budget or ContextBudget()
        self.prompt_builder = prompt_builder or PromptBuilder()

    async def process(
        self,
        *,
        request_text: str,
        context: AiProjectContext,
        correlation_id: UUID,
        model: str,
        fallback_enabled: bool = True,
        max_output_tokens: int = 4096,
    ) -> OrchestrationResult:
        started = time.perf_counter()
        clean_text = sanitize_untrusted_text(request_text)
        intents = self.classifier.classify(clean_text)
        budgeted = self.context_budget.apply(context)

        if self.classifier.requests_sensitive_data(clean_text):
            return self._safe_refusal(intents, started, budgeted.reduced)
        if self.classifier.is_ambiguous(clean_text, budgeted.context.active_diagram is not None):
            result = UnifiedAiResult(
                answer="Necesito identificar el elemento exacto antes de proponer cambios.",
                detected_intents=intents,
                requires_user_input=True,
                clarification_question="¿A que clase o elemento concreto te refieres?",
                provider="rule_engine",
                model="deterministic-v2",
                fallback_used=self.primary_provider is not None,
            )
            return OrchestrationResult(
                result=result,
                duration_ms=self._elapsed(started),
                context_reduced=budgeted.reduced,
            )

        if self.fallback_provider.can_answer_contextually(
            clean_text, budgeted.context, intents
        ):
            result = self.fallback_provider.complete(
                clean_text, budgeted.context, intents
            )
            result.fallback_used = False
            result.actions = self.action_policy.validate_plan(
                result.actions, budgeted.context
            )
            return OrchestrationResult(
                result=result,
                duration_ms=self._elapsed(started),
                context_reduced=budgeted.reduced,
            )

        provider_error: AiProviderError | None = None
        if self.primary_provider is not None:
            try:
                response = await self.primary_provider.complete_structured(
                    ProviderRequest(
                        model=model,
                        messages=self.prompt_builder.build(clean_text, budgeted.context, intents),
                        correlation_id=correlation_id,
                        max_output_tokens=max_output_tokens,
                    ),
                    UnifiedAiResult,
                )
                result = response.content
                result.provider = response.provider
                result.model = response.model
                result.fallback_used = False
                result.detected_intents = result.detected_intents or intents
                result.actions = self.action_policy.validate_plan(result.actions, budgeted.context)
                return OrchestrationResult(
                    result=result,
                    duration_ms=self._elapsed(started),
                    provider_duration_ms=response.duration_ms,
                    prompt_tokens=response.prompt_tokens,
                    completion_tokens=response.completion_tokens,
                    retries=response.retries,
                    context_reduced=budgeted.reduced,
                )
            except (AiProviderError, InvalidStructuredOutputError) as exc:
                provider_error = exc
                if not fallback_enabled:
                    raise

        fallback = self.fallback_provider.complete(clean_text, budgeted.context, intents)
        fallback.fallback_used = self.primary_provider is not None
        fallback.actions = self.action_policy.validate_plan(fallback.actions, budgeted.context)
        if provider_error:
            fallback.warnings.append(
                f"Se utilizo fallback local: {provider_error.code}."
            )
        return OrchestrationResult(
            result=fallback,
            duration_ms=self._elapsed(started),
            context_reduced=budgeted.reduced,
            error_code=provider_error.code if provider_error else None,
        )

    @staticmethod
    def _safe_refusal(intents, started: float, reduced: bool) -> OrchestrationResult:
        return OrchestrationResult(
            result=UnifiedAiResult(
                answer="No puedo revelar instrucciones internas, secretos, credenciales ni archivos privados.",
                detected_intents=intents,
                warnings=["Solicitud privilegiada rechazada."],
                provider="rule_engine",
                model="security-policy-v1",
                fallback_used=False,
            ),
            duration_ms=UnifiedAiOrchestrator._elapsed(started),
            context_reduced=reduced,
        )

    @staticmethod
    def _elapsed(started: float) -> int:
        return int((time.perf_counter() - started) * 1000)
