from ai_engine.inference.local_engine import engine
from ai_engine.services.contracts import (
    CodeGenerationRequest,
    CodeGenerationResponse,
    DatasetSummaryResponse,
    EvaluationResponse,
    ImageProcessingRequest,
    KnowledgeItemResponse,
    KnowledgeSearchRequest,
    ModelProfile,
    SoftwarePlanRequest,
    SoftwarePlanResponse,
    TrainingPlanResponse,
    UmlGenerationRequest,
    UmlGenerationResponse,
    UmlModificationRequest,
    UmlModificationResponse,
    UmlValidationRequest,
    UmlValidationResponse,
    VoiceProcessingRequest,
)


class LocalAIService:
    def profile(self) -> ModelProfile:
        return engine.profile()

    def text_to_uml(self, request: UmlGenerationRequest) -> UmlGenerationResponse:
        return engine.generate_uml(request)

    def voice_to_uml(self, request: VoiceProcessingRequest) -> UmlGenerationResponse:
        return engine.generate_uml_from_voice(request)

    def image_to_uml(self, request: ImageProcessingRequest) -> UmlGenerationResponse:
        return engine.generate_uml_from_image(request)

    def validate_uml(self, request: UmlValidationRequest) -> UmlValidationResponse:
        return engine.validate_uml(request)

    def software_plan(self, request: SoftwarePlanRequest) -> SoftwarePlanResponse:
        return engine.plan_software(request)

    def modify_uml(self, request: UmlModificationRequest) -> UmlModificationResponse:
        return engine.modify_uml(request)

    def generate_code_guidance(self, request: CodeGenerationRequest) -> CodeGenerationResponse:
        return engine.generate_code_guidance(request)

    def search_knowledge(self, request: KnowledgeSearchRequest) -> list[KnowledgeItemResponse]:
        return engine.search_knowledge(request)

    def dataset_summary(self) -> DatasetSummaryResponse:
        return engine.dataset_summary()

    def training_plan(self) -> TrainingPlanResponse:
        return engine.training_plan()

    def evaluate_offline(self) -> EvaluationResponse:
        return engine.evaluate_offline()
