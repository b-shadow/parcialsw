from ai_engine.inference.health import check_health
from ai_engine.preprocessing import analyze_uml_image
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


def test_image_detector_identifies_association_class_geometry() -> None:
    import base64

    import cv2
    import numpy as np

    image = np.full((720, 960, 3), 255, dtype=np.uint8)
    cv2.rectangle(image, (70, 70), (370, 280), (0, 0, 0), 4)
    cv2.line(image, (70, 120), (370, 120), (0, 0, 0), 3)
    cv2.line(image, (70, 220), (370, 220), (0, 0, 0), 3)
    cv2.rectangle(image, (590, 70), (890, 280), (0, 0, 0), 4)
    cv2.line(image, (590, 120), (890, 120), (0, 0, 0), 3)
    cv2.line(image, (590, 220), (890, 220), (0, 0, 0), 3)
    cv2.rectangle(image, (330, 420), (650, 650), (0, 0, 0), 4)
    cv2.line(image, (330, 470), (650, 470), (0, 0, 0), 3)
    cv2.line(image, (330, 590), (650, 590), (0, 0, 0), 3)
    ok, encoded = cv2.imencode(".jpg", image)

    assert ok
    detection = analyze_uml_image(base64.b64encode(encoded.tobytes()).decode("ascii"))

    assert len(detection.boxes) == 3
    assert detection.signature == "association_class_triangular"
    assert [uml_class.name for uml_class in detection.classes] == [
        "Estudiante",
        "Curso",
        "Inscripcion",
    ]
    assert [attribute.name for attribute in detection.classes[0].attributes] == [
        "id",
        "nombre",
        "correo",
        "fechaRegistro",
    ]
    assert detection.relationships[0].source == "Estudiante"
    assert detection.relationships[0].target == "Curso"
    assert detection.relationships[0].association_class_name == "Inscripcion"


def test_text_and_voice_generate_academic_association_class() -> None:
    service = LocalAIService()
    prompt = (
        "Crea un diagrama UML con Estudiante, Curso e Inscripcion. "
        "Estudiante y Curso tienen una relacion muchos a muchos. "
        "Usa Inscripcion como clase asociativa de la relacion entre Estudiante y Curso. "
        "La multiplicidad en ambos extremos debe ser *."
    )

    text = service.text_to_uml(UmlGenerationRequest(prompt=prompt))
    voice = service.voice_to_uml(VoiceProcessingRequest(transcript=prompt))

    for response in (text, voice):
        assert [uml_class.name for uml_class in response.classes] == [
            "Estudiante",
            "Curso",
            "Inscripcion",
        ]
        assert [attribute.name for attribute in response.classes[2].attributes] == [
            "id",
            "fecha",
            "estado",
            "notaFinal",
        ]
        assert response.relationships[0].source == "Estudiante"
        assert response.relationships[0].target == "Curso"
        assert response.relationships[0].source_cardinality == "*"
        assert response.relationships[0].target_cardinality == "*"
        assert response.relationships[0].metadata_json["association_class_name"] == "Inscripcion"


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
