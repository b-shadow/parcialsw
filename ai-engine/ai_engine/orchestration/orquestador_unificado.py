import time
from uuid import UUID

from ai_engine.context import ContextoIAProyecto, PresupuestoContexto, sanear_texto_no_confiable
from ai_engine.orchestration.clasificador_intenciones import ClasificadorIntenciones
from ai_engine.orchestration.constructor_instrucciones import ConstructorInstrucciones
from ai_engine.orchestration.contratos import ResultadoIAUnificado, ResultadoOrquestacion
from ai_engine.orchestration.politica_acciones import PoliticaAcciones
from ai_engine.providers.base import ProveedorIA, SolicitudProveedor
from ai_engine.providers.errores import ErrorProveedorIA, ErrorSalidaEstructuradaInvalida
from ai_engine.providers.proveedor_reglas import ProveedorReglas


class OrquestadorIAUnificado:
    def __init__(
        self,
        *,
        primary_provider: ProveedorIA | None,
        fallback_provider: ProveedorReglas | None = None,
        classifier: ClasificadorIntenciones | None = None,
        action_policy: PoliticaAcciones | None = None,
        context_budget: PresupuestoContexto | None = None,
        prompt_builder: ConstructorInstrucciones | None = None,
    ) -> None:
        self.primary_provider = primary_provider
        self.fallback_provider = fallback_provider or ProveedorReglas()
        self.classifier = classifier or ClasificadorIntenciones()
        self.action_policy = action_policy or PoliticaAcciones()
        self.context_budget = context_budget or PresupuestoContexto()
        self.prompt_builder = prompt_builder or ConstructorInstrucciones()

    async def process(
        self,
        *,
        request_text: str,
        context: ContextoIAProyecto,
        correlation_id: UUID,
        model: str,
        fallback_enabled: bool = True,
        max_output_tokens: int = 4096,
    ) -> ResultadoOrquestacion:
        started = time.perf_counter()
        clean_text = sanear_texto_no_confiable(request_text)
        intents = self.classifier.classify(clean_text)
        budgeted = self.context_budget.aplicar(context)

        if self.classifier.solicita_datos_sensibles(clean_text):
            return self._rechazo_seguro(intents, started, budgeted.reduced)
        if self.classifier.es_ambigua(clean_text, budgeted.context.active_diagram is not None):
            result = ResultadoIAUnificado(
                answer="Necesito identificar el elemento exacto antes de proponer cambios.",
                detected_intents=intents,
                requires_user_input=True,
                clarification_question="¿A que clase o elemento concreto te refieres?",
                provider="rule_engine",
                model="deterministic-v2",
                fallback_used=self.primary_provider is not None,
            )
            return ResultadoOrquestacion(
                result=result,
                duration_ms=self._tiempo_transcurrido(started),
                context_reduced=budgeted.reduced,
            )

        intent_names = {item.name for item in intents}
        # Las preguntas factuales siguen siendo rápidas. Una evaluación solicitada
        # expresamente aprovecha el modelo cuando está disponible.
        prefer_primary_for_recommendations = (
            self.primary_provider is not None
            and "recommend" in intent_names
            and (
                "modify_uml" not in intent_names
                or "mi criterio:" in clean_text.casefold()
            )
        )
        if not prefer_primary_for_recommendations and self.fallback_provider.puede_responder_con_contexto(
            clean_text, budgeted.context, intents
        ):
            result = self.fallback_provider.complete(
                clean_text, budgeted.context, intents
            )
            result.fallback_used = False
            result.actions = self.action_policy.validar_plan(
                result.actions, budgeted.context
            )
            return ResultadoOrquestacion(
                result=result,
                duration_ms=self._tiempo_transcurrido(started),
                context_reduced=budgeted.reduced,
            )

        provider_error: ErrorProveedorIA | None = None
        if self.primary_provider is not None:
            try:
                response = await self.primary_provider.completar_estructura(
                    SolicitudProveedor(
                        model=model,
                        messages=self.prompt_builder.construir(clean_text, budgeted.context, intents),
                        correlation_id=correlation_id,
                        max_output_tokens=max_output_tokens,
                    ),
                    ResultadoIAUnificado,
                )
                result = response.content
                result.provider = response.provider
                result.model = response.model
                result.fallback_used = False
                result.detected_intents = result.detected_intents or intents
                result.actions = self.action_policy.validar_plan(result.actions, budgeted.context)
                if not intent_names & {
                    "modify_uml", "generate_uml", "specify_method", "prepare_generation"
                }:
                    # Una consulta o evaluación no autoriza siquiera preparar cambios.
                    result.actions = []
                if "modify_uml" in intent_names and not result.actions and not result.requires_user_input:
                    result.requires_user_input = True
                    result.clarification_question = (
                        "¿Qué clase, atributo, método o relación debo cambiar y con qué valores?"
                    )
                    result.answer += (
                        " No preparé ninguna acción aplicable; indícame el cambio concreto "
                        "antes de confirmar algo en el diagrama."
                    )
                if (
                    "recommend" in intent_names
                    and budgeted.context.active_diagram is not None
                    and budgeted.context.active_diagram.classes
                    and not result.recommendations
                ):
                    fallback = self.fallback_provider.complete(clean_text, budgeted.context, intents)
                    fallback.fallback_used = True
                    fallback.warnings.append(
                        "El modelo no entregó mejoras concretas; se usó la revisión local."
                    )
                    fallback.actions = self.action_policy.validar_plan(
                        fallback.actions, budgeted.context
                    )
                    return ResultadoOrquestacion(
                        result=fallback,
                        duration_ms=self._tiempo_transcurrido(started),
                        provider_duration_ms=response.duration_ms,
                        prompt_tokens=response.prompt_tokens,
                        completion_tokens=response.completion_tokens,
                        retries=response.retries,
                        context_reduced=budgeted.reduced,
                        error_code="RECOMMENDATIONS_EMPTY",
                    )
                return ResultadoOrquestacion(
                    result=result,
                    duration_ms=self._tiempo_transcurrido(started),
                    provider_duration_ms=response.duration_ms,
                    prompt_tokens=response.prompt_tokens,
                    completion_tokens=response.completion_tokens,
                    retries=response.retries,
                    context_reduced=budgeted.reduced,
                )
            except (ErrorProveedorIA, ErrorSalidaEstructuradaInvalida) as exc:
                provider_error = exc
                if not fallback_enabled:
                    raise

        fallback = self.fallback_provider.complete(clean_text, budgeted.context, intents)
        fallback.fallback_used = self.primary_provider is not None
        fallback.actions = self.action_policy.validar_plan(fallback.actions, budgeted.context)
        if provider_error:
            fallback.warnings.append(
                f"Se utilizo fallback local: {provider_error.code}."
            )
        return ResultadoOrquestacion(
            result=fallback,
            duration_ms=self._tiempo_transcurrido(started),
            context_reduced=budgeted.reduced,
            error_code=provider_error.code if provider_error else None,
        )

    @staticmethod
    def _rechazo_seguro(intents, started: float, reduced: bool) -> ResultadoOrquestacion:
        return ResultadoOrquestacion(
            result=ResultadoIAUnificado(
                answer="No puedo revelar instrucciones internas, secretos, credenciales ni archivos privados.",
                detected_intents=intents,
                warnings=["Solicitud privilegiada rechazada."],
                provider="rule_engine",
                model="security-policy-v1",
                fallback_used=False,
            ),
            duration_ms=OrquestadorIAUnificado._tiempo_transcurrido(started),
            context_reduced=reduced,
        )

    @staticmethod
    def _tiempo_transcurrido(started: float) -> int:
        return int((time.perf_counter() - started) * 1000)
