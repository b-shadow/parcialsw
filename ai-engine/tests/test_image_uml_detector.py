import base64
from pathlib import Path

import cv2
import numpy as np

from ai_engine.preprocessing.image_uml_detector import (
    DetectedBox,
    _normalize_type,
    _parse_class_box,
    _score_ocr_candidate,
    analyze_uml_image,
)


def _encode(image: np.ndarray) -> str:
    ok, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 72])
    assert ok
    return base64.b64encode(encoded.tobytes()).decode("ascii")


def test_real_handwritten_photo_keeps_three_uml_boxes_and_association_class() -> None:
    image_path = Path(__file__).parents[2] / "imapru.jpeg"

    detection = analyze_uml_image(base64.b64encode(image_path.read_bytes()).decode("ascii"))

    assert len(detection.boxes) == 3
    assert detection.signature == "association_class_triangular"
    assert len(detection.classes) == 3
    assert detection.relationships[0].association_class_name == detection.classes[2].name


def test_detector_handles_low_contrast_noise_and_rotation() -> None:
    height, width = 720, 1000
    gradient = np.tile(np.linspace(245, 205, width, dtype=np.uint8), (height, 1))
    image = cv2.cvtColor(gradient, cv2.COLOR_GRAY2BGR)
    for left, right in ((80, 410), (590, 920)):
        cv2.rectangle(image, (left, 130), (right, 450), (65, 65, 65), 5)
        cv2.line(image, (left, 200), (right, 200), (65, 65, 65), 4)
        cv2.line(image, (left, 350), (right, 350), (65, 65, 65), 4)
    noise = np.random.default_rng(7).normal(0, 3, image.shape).astype(np.int16)
    image = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    matrix = cv2.getRotationMatrix2D((width / 2, height / 2), 5.5, 1)
    rotated = cv2.warpAffine(image, matrix, (width, height), borderValue=(255, 255, 255))

    detection = analyze_uml_image(_encode(rotated))

    assert len(detection.boxes) == 2
    assert len(detection.classes) == 2
    assert any("inclinacion" in observation for observation in detection.observations)


def test_parser_recovers_uml_syntax_and_approximate_types_from_irregular_ocr() -> None:
    parsed = _parse_class_box(
        DetectedBox(
            0,
            0,
            300,
            240,
            "Inscripcion\n- id ; UUlD\n- fecha = Dote\n+ obtenerDetalle{} ; vo1d",
        )
    )

    assert parsed.name == "Inscripcion"
    assert [(attribute.name, attribute.data_type) for attribute in parsed.attributes] == [
        ("id", "UUID"),
        ("fecha", "Date"),
    ]
    assert [(method.name, method.return_type) for method in parsed.methods] == [
        ("obtenerDetalle", "void")
    ]


def test_ocr_candidate_prefers_uml_structure_over_high_confidence_noise() -> None:
    uml_score = _score_ocr_candidate(
        "Curso\n- id: UUID\n- nombre: String\n+ guardar(): void",
        58,
    )
    noise_score = _score_ocr_candidate("papel sombra margen cualquier texto", 91)

    assert uml_score > noise_score


def test_type_normalization_tolerates_common_handwriting_ocr_errors() -> None:
    assert _normalize_type("UUlD") == "UUID"
    assert _normalize_type("Dote") == "Date"
    assert _normalize_type("vo1d") == "void"


def test_invalid_or_oversized_image_is_rejected_without_crashing() -> None:
    invalid = analyze_uml_image(base64.b64encode(b"not an image").decode("ascii"))
    oversized = analyze_uml_image(base64.b64encode(b"x" * (15 * 1024 * 1024 + 1)).decode("ascii"))

    assert invalid.classes == []
    assert "imagen valida" in invalid.observations[0]
    assert oversized.classes == []
    assert "15 MB" in oversized.observations[0]
