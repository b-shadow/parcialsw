import json
from pathlib import Path

from ai_engine.context.contratos import ContextoIAProyecto
from ai_engine.context.saneador import sanear_datos_contexto
from ai_engine.orchestration.contratos import IntencionDetectada, ResultadoIAUnificado
from ai_engine.providers.base import MensajeProveedor


class ConstructorInstrucciones:
    def __init__(self) -> None:
        prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "unified_system.md"
        self.system_prompt = prompt_path.read_text(encoding="utf-8")

    def construir(
        self,
        request_text: str,
        context: ContextoIAProyecto,
        intents: list[IntencionDetectada],
    ) -> list[MensajeProveedor]:
        schema = json.dumps(ResultadoIAUnificado.model_json_schema(), ensure_ascii=False)
        context_json = json.dumps(
            sanear_datos_contexto(context.model_dump(mode="json")), ensure_ascii=False
        )
        intents_json = json.dumps([item.model_dump(mode="json") for item in intents], ensure_ascii=False)
        return [
            MensajeProveedor(
                role="system",
                content=f"{self.system_prompt}\n\nESQUEMA_JSON_OBLIGATORIO:\n{schema}",
            ),
            MensajeProveedor(
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
