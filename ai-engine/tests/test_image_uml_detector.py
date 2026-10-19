import base64
from pathlib import Path

import cv2
import numpy as np

from ai_engine.preprocessing.image_uml_detector import (
    DetectedBox,
    _normalize_type,
    _ocr_is_available,
    _OcrCandidate,
    _parse_class_box,
    _parse_or_complete_classes,
    _read_cardinality_geometry,
    _recover_common_term,
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
    if _ocr_is_available():
        assert [uml_class.name for uml_class in detection.classes] == [
            "Estudiante",
            "Curso",
            "Inscripcion",
        ]
        assert [
            [(attribute.name, attribute.data_type) for attribute in uml_class.attributes]
            for uml_class in detection.classes
        ] == [
            [
                ("id", "UUID"),
                ("nombre", "String"),
                ("correo", "String"),
                ("fechaRegistro", "Date"),
            ],
            [
                ("id", "UUID"),
                ("nombre", "String"),
                ("descripcion", "String"),
                ("duracionHoras", "Integer"),
            ],
            [
                ("id", "UUID"),
                ("fecha", "Date"),
                ("estado", "String"),
                ("notaFinal", "Double"),
            ],
        ]
        assert [
            [(method.name, method.return_type) for method in uml_class.methods]
            for uml_class in detection.classes
        ] == [
            [("inscribirse", "void"), ("actualizarPerfil", "void")],
            [("agregarTema", "void"), ("obtenerDetalle", "void")],
            [("obtenerDetalle", "void")],
        ]


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
    assert detection.confidence < 0.55
    assert all(uml_class.attributes == [] for uml_class in detection.classes)
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


def test_parser_infers_types_for_bare_handwritten_attribute_names() -> None:
    parsed = _parse_class_box(
        DetectedBox(0, 0, 260, 220, "Producto\nid\nnombre\nprecio\nstock")
    )

    assert parsed.name == "Producto"
    assert [(attribute.name, attribute.data_type) for attribute in parsed.attributes] == [
        ("id", "UUID"),
        ("nombre", "String"),
        ("precio", "Decimal"),
        ("stock", "Integer"),
    ]


def test_handwritten_header_voting_recovers_noisy_common_class_name() -> None:
    name, score = _recover_common_term(
        [_OcrCandidate(text="[cueste ]", confidence=34, score=20)],
        ("Cliente", "Producto", "Venta"),
        0.60,
    )

    assert name == "Cliente"
    assert score >= 0.60


def test_header_voting_requires_a_clear_winner() -> None:
    name, score = _recover_common_term(
        [
            _OcrCandidate(text="Reserva", confidence=45, score=20),
            _OcrCandidate(text="Pedido", confidence=45, score=20),
        ],
        ("Reserva", "Pedido"),
        0.60,
    )

    assert name == ""
    assert score == 0.0


def test_unreadable_and_duplicate_classes_are_not_filled_with_invented_members() -> None:
    classes = _parse_or_complete_classes(
        [
            DetectedBox(0, 0, 100, 100, "Cliente\n- correo: String"),
            DetectedBox(120, 0, 100, 100, "Cliente\n- nombre: String"),
            DetectedBox(240, 0, 100, 100, ""),
        ]
    )

    assert classes[0].name == "Cliente"
    assert classes[1].name.startswith("Clase")
    assert classes[1].attributes == []
    assert classes[2].name.startswith("Clase")
    assert classes[2].attributes == []


def test_cardinality_geometry_distinguishes_star_one_and_one_to_many() -> None:
    star = np.full((100, 100, 3), 255, dtype=np.uint8)
    cv2.line(star, (0, 50), (99, 50), (0, 0, 0), 2)
    cv2.line(star, (43, 39), (57, 61), (0, 0, 0), 3)
    cv2.line(star, (57, 39), (43, 61), (0, 0, 0), 3)

    one_to_many = np.full((100, 100, 3), 255, dtype=np.uint8)
    cv2.line(one_to_many, (0, 50), (99, 50), (0, 0, 0), 2)
    cv2.line(one_to_many, (22, 18), (22, 42), (0, 0, 0), 3)
    cv2.circle(one_to_many, (31, 31), 2, (0, 0, 0), -1)
    cv2.circle(one_to_many, (36, 31), 2, (0, 0, 0), -1)
    cv2.line(one_to_many, (43, 20), (57, 42), (0, 0, 0), 3)
    cv2.line(one_to_many, (57, 20), (43, 42), (0, 0, 0), 3)

    one = np.full((100, 100, 3), 255, dtype=np.uint8)
    cv2.line(one, (50, 0), (50, 99), (0, 0, 0), 2)
    cv2.line(one, (39, 38), (39, 61), (0, 0, 0), 3)

    assert _read_cardinality_geometry(star, "horizontal", 50) == "*"
    assert _read_cardinality_geometry(one_to_many, "horizontal", 50) == "1..*"
    assert _read_cardinality_geometry(one, "vertical", 50) == "1"


def test_invalid_or_oversized_image_is_rejected_without_crashing() -> None:
    invalid = analyze_uml_image(base64.b64encode(b"not an image").decode("ascii"))
    oversized = analyze_uml_image(base64.b64encode(b"x" * (15 * 1024 * 1024 + 1)).decode("ascii"))

    assert invalid.classes == []
    assert "imagen valida" in invalid.observations[0]
    assert oversized.classes == []
    assert "15 MB" in oversized.observations[0]
