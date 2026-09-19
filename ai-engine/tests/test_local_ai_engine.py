from ai_engine.inference.health import check_health
from ai_engine.services import LocalAIService
from ai_engine.services.contracts import (
    ImageProcessingRequest,
    SoftwarePlanRequest,
    UmlGenerationRequest,
    UmlValidationRequest,
    VoiceProcessingRequest,
)


def test_ai_engine_health_is_offline() -> None:
    health = check_health()

    assert health["status"] == "ok"
    assert health["mode"] == "local-offline"
    assert health["offline"] is True


def test_text_voice_and_image_generate_structured_uml() -> None:
    service = LocalAIService()

    text = service.text_to_uml(
        UmlGenerationRequest(prompt="Crear sistema de biblioteca con libros, usuarios y prestamos")
    )
    voice = service.voice_to_uml(VoiceProcessingRequest(transcript="Sistema academico con cursos y docentes"))
    image = service.image_to_uml(ImageProcessingRequest(description="Diagrama UML con Cliente y Pedido"))

    assert text.classes
    assert voice.classes
    assert image.classes
    assert text.engine == "local-offline"
    assert text.confidence > 0


def test_ai_validation_and_software_plan() -> None:
    service = LocalAIService()
    uml = service.text_to_uml(UmlGenerationRequest(prompt="Crear sistema con cliente y pedido"))

    validation = service.validate_uml(
        UmlValidationRequest(classes=uml.classes, relationships=uml.relationships)
    )
    spring = service.software_plan(
        SoftwarePlanRequest(classes=uml.classes, relationships=uml.relationships, target="spring_boot")
    )
    flutter = service.software_plan(
        SoftwarePlanRequest(classes=uml.classes, relationships=uml.relationships, target="flutter")
    )

    assert validation.score > 0
    assert any(file.endswith(".java") for file in spring.files)
    assert any(file.endswith(".dart") for file in flutter.files)
