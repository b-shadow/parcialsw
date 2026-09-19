from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.security.dependencies import get_current_user
from app.modules.acceso_usuarios.models import User
from app.modules.generacion_software.schemas.ai import (
    AiCodeGenerationRequest,
    AiCodeGenerationResponse,
    AiDatasetSummaryResponse,
    AiEvaluationResponse,
    AiImageRequest,
    AiKnowledgeItemResponse,
    AiKnowledgeSearchRequest,
    AiModelProfileResponse,
    AiModificationRequest,
    AiModificationResponse,
    AiSoftwarePlanRequest,
    AiSoftwarePlanResponse,
    AiTextRequest,
    AiTrainingPlanResponse,
    AiUmlResponse,
    AiValidationRequest,
    AiValidationResponse,
    AiVoiceRequest,
)
from app.modules.generacion_software.services.ai_service import AiService

router = APIRouter(prefix="/ai", tags=["ia-local-offline"])


@router.get("/profile", response_model=AiModelProfileResponse)
def profile(_: Annotated[User, Depends(get_current_user)]) -> AiModelProfileResponse:
    return AiService().profile()


@router.post("/uml/text", response_model=AiUmlResponse)
def text_to_uml(
    payload: AiTextRequest,
    _: Annotated[User, Depends(get_current_user)],
) -> AiUmlResponse:
    return AiService().text_to_uml(payload)


@router.post("/generate-uml", response_model=AiUmlResponse)
def generate_uml_alias(
    payload: AiTextRequest,
    _: Annotated[User, Depends(get_current_user)],
) -> AiUmlResponse:
    return AiService().text_to_uml(payload)


@router.post("/uml/voice", response_model=AiUmlResponse)
def voice_to_uml(
    payload: AiVoiceRequest,
    _: Annotated[User, Depends(get_current_user)],
) -> AiUmlResponse:
    return AiService().voice_to_uml(payload)


@router.post("/uml/image", response_model=AiUmlResponse)
def image_to_uml(
    payload: AiImageRequest,
    _: Annotated[User, Depends(get_current_user)],
) -> AiUmlResponse:
    return AiService().image_to_uml(payload)


@router.post("/analyze-image", response_model=AiUmlResponse)
def analyze_image_alias(
    payload: AiImageRequest,
    _: Annotated[User, Depends(get_current_user)],
) -> AiUmlResponse:
    return AiService().image_to_uml(payload)


@router.post("/uml/validate", response_model=AiValidationResponse)
def validate_uml(
    payload: AiValidationRequest,
    _: Annotated[User, Depends(get_current_user)],
) -> AiValidationResponse:
    return AiService().validate_uml(payload)


@router.post("/validate-model", response_model=AiValidationResponse)
def validate_model_alias(
    payload: AiValidationRequest,
    _: Annotated[User, Depends(get_current_user)],
) -> AiValidationResponse:
    return AiService().validate_uml(payload)


@router.post("/software/plan", response_model=AiSoftwarePlanResponse)
def software_plan(
    payload: AiSoftwarePlanRequest,
    _: Annotated[User, Depends(get_current_user)],
) -> AiSoftwarePlanResponse:
    return AiService().software_plan(payload)


@router.post("/uml/modify", response_model=AiModificationResponse)
def modify_uml(
    payload: AiModificationRequest,
    _: Annotated[User, Depends(get_current_user)],
) -> AiModificationResponse:
    return AiService().modify_uml(payload)


@router.post("/generate-code", response_model=AiCodeGenerationResponse)
def generate_code(
    payload: AiCodeGenerationRequest,
    _: Annotated[User, Depends(get_current_user)],
) -> AiCodeGenerationResponse:
    return AiService().generate_code_guidance(payload)


@router.post("/knowledge/search", response_model=list[AiKnowledgeItemResponse])
def search_knowledge(
    payload: AiKnowledgeSearchRequest,
    _: Annotated[User, Depends(get_current_user)],
) -> list[AiKnowledgeItemResponse]:
    return AiService().search_knowledge(payload)


@router.get("/dataset/summary", response_model=AiDatasetSummaryResponse)
def dataset_summary(_: Annotated[User, Depends(get_current_user)]) -> AiDatasetSummaryResponse:
    return AiService().dataset_summary()


@router.get("/training/plan", response_model=AiTrainingPlanResponse)
def training_plan(_: Annotated[User, Depends(get_current_user)]) -> AiTrainingPlanResponse:
    return AiService().training_plan()


@router.get("/evaluation/offline", response_model=AiEvaluationResponse)
def evaluate_offline(_: Annotated[User, Depends(get_current_user)]) -> AiEvaluationResponse:
    return AiService().evaluate_offline()
