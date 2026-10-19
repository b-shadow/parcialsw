import json
from pathlib import Path

from ai_engine.context.contracts import AiProjectContext
from ai_engine.context.sanitizer import sanitize_context_data
from ai_engine.orchestration.contracts import DetectedIntent, UnifiedAiResult
from ai_engine.providers.base import ProviderMessage


class PromptBuilder:
    def __init__(self) -> None:
        prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "unified_system.md"
        self.system_prompt = prompt_path.read_text(encoding="utf-8")

    def build(
        self,
        request_text: str,
        context: AiProjectContext,
        intents: list[DetectedIntent],
    ) -> list[ProviderMessage]:
        schema = json.dumps(UnifiedAiResult.model_json_schema(), ensure_ascii=False)
        context_json = json.dumps(
            sanitize_context_data(context.model_dump(mode="json")), ensure_ascii=False
        )
        intents_json = json.dumps([item.model_dump(mode="json") for item in intents], ensure_ascii=False)
        return [
            ProviderMessage(
                role="system",
                content=f"{self.system_prompt}\n\nESQUEMA_JSON_OBLIGATORIO:\n{schema}",
            ),
            ProviderMessage(
                role="user",
                content=(
                    "<CONTEXTO_AUTORIZADO_NO_CONFIABLE>\n"
                    f"{context_json}\n"
                    "</CONTEXTO_AUTORIZADO_NO_CONFIABLE>\n"
                    "<INTENCIONES_PRECLASIFICADAS>\n"
                    f"{intents_json}\n"
                    "</INTENCIONES_PRECLASIFICADAS>\n"
                    "<SOLICITUD_USUARIO_NO_CONFIABLE>\n"
                    f"{request_text}\n"
                    "</SOLICITUD_USUARIO_NO_CONFIABLE>"
                ),
            ),
        ]
