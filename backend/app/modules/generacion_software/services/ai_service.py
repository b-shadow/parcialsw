from ai_engine.services import LocalAIService
from ai_engine.services.contracts import (
    CodeGenerationRequest,
    ImageProcessingRequest,
    KnowledgeSearchRequest,
    SoftwarePlanRequest,
    UmlGenerationRequest,
    UmlModificationRequest,
    UmlValidationRequest,
    VoiceProcessingRequest,
)

from app.modules.generacion_software.schemas.ai import (
    AiCodeGenerationRequest,
    AiImageRequest,
    AiKnowledgeSearchRequest,
    AiModificationRequest,
    AiSoftwarePlanRequest,
    AiTextRequest,
    AiValidationRequest,
    AiVoiceRequest,
)


class AiService:
    def __init__(self) -> None:
        self.local_ai = LocalAIService()

    def profile(self):
        return self.local_ai.profile()

    def text_to_uml(self, payload: AiTextRequest):
        return self.local_ai.text_to_uml(UmlGenerationRequest(**payload.model_dump()))

    def voice_to_uml(self, payload: AiVoiceRequest):
        return self.local_ai.voice_to_uml(VoiceProcessingRequest(**payload.model_dump()))

    def image_to_uml(self, payload: AiImageRequest):
        return self.local_ai.image_to_uml(ImageProcessingRequest(**payload.model_dump()))

    def validate_uml(self, payload: AiValidationRequest):
        return self.local_ai.validate_uml(UmlValidationRequest(**payload.model_dump()))

    def software_plan(self, payload: AiSoftwarePlanRequest):
        return self.local_ai.software_plan(SoftwarePlanRequest(**payload.model_dump()))

    def modify_uml(self, payload: AiModificationRequest):
        return self.local_ai.modify_uml(UmlModificationRequest(**payload.model_dump()))

    def generate_code_guidance(self, payload: AiCodeGenerationRequest):
        return self.local_ai.generate_code_guidance(CodeGenerationRequest(**payload.model_dump()))

    def search_knowledge(self, payload: AiKnowledgeSearchRequest):
        return self.local_ai.search_knowledge(KnowledgeSearchRequest(**payload.model_dump()))

    def dataset_summary(self):
        return self.local_ai.dataset_summary()

    def training_plan(self):
        return self.local_ai.training_plan()

    def evaluate_offline(self):
        return self.local_ai.evaluate_offline()
