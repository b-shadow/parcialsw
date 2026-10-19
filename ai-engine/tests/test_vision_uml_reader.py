import base64
import json

import cv2
import httpx
import numpy as np

from ai_engine.inference.vision_uml_reader import VisionUmlRead, VisionUmlReader
from ai_engine.preprocessing.image_uml_detector import (
    DetectedBox,
    DetectedUmlClass,
    DetectedUmlRelationship,
    ImageUmlDetection,
)


def _image_payload() -> str:
    image = np.full((360, 640, 3), 255, dtype=np.uint8)
    cv2.rectangle(image, (40, 50), (250, 260), (0, 0, 0), 3)
    cv2.rectangle(image, (390, 50), (600, 260), (0, 0, 0), 3)
    ok, encoded = cv2.imencode(".jpg", image)
    assert ok
    return base64.b64encode(encoded.tobytes()).decode("ascii")


def _detection() -> ImageUmlDetection:
    boxes = [
        DetectedBox(40, 50, 210, 210, "Clase1"),
        DetectedBox(390, 50, 210, 210, "Clase2"),
    ]
    return ImageUmlDetection(
        boxes=boxes,
        classes=[
            DetectedUmlClass(name="Clase1", box=boxes[0]),
            DetectedUmlClass(name="Clase2", box=boxes[1]),
        ],
        relationships=[
            DetectedUmlRelationship(
                source="Clase1",
                target="Clase2",
                source_cardinality="1",
                target_cardinality="*",
            )
        ],
        confidence=0.31,
    )


def test_vision_reader_sends_numbered_contact_sheet_for_detected_boxes() -> None:
    captured: dict = {}
    content = {
        "classes": [
            {
                "visual_index": 1,
                "name": "Venta",
                "attributes": [{"name": "id", "data_type": None}],
                "methods": [],
            },
            {
                "visual_index": 2,
                "name": "Producto",
                "attributes": [{"name": "precio", "data_type": None}],
                "methods": [],
            },
        ],
        "relationships": [
            {
                "source_index": 1,
                "target_index": 2,
                "relationship_type": "association",
                "source_cardinality": "1",
                "target_cardinality": "*",
            }
        ],
        "unreadable_items": [],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": "qwen3-vl:2b-instruct"}]})
        captured.update(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "model": "qwen3-vl:2b-instruct",
                "message": {"content": json.dumps(content)},
            },
        )

    client = httpx.Client(
        transport=httpx.MockTransport(handler), base_url="http://127.0.0.1:11434"
    )
    reader = VisionUmlReader(client=client)

    result = reader.read(_image_payload(), _detection())

    assert result is not None
    assert [item.name for item in result.classes] == ["Venta", "Producto"]
    assert [(item.name, item.data_type) for item in result.classes[0].attributes] == [
        ("id", "UUID")
    ]
    assert result.relationships[0].source == "Venta"
    assert result.relationships[0].target == "Producto"
    assert len(captured["messages"][0]["images"]) == 1
    assert captured["options"]["temperature"] == 0
    assert captured["options"]["num_ctx"] == 8192


def test_vision_reader_rejects_missing_or_invented_boxes() -> None:
    reader = VisionUmlReader(enabled=False)
    visual = VisionUmlRead.model_validate(
        {
            "classes": [
                {"visual_index": 1, "name": "Venta"},
                {"visual_index": 2, "name": "Producto"},
                {"visual_index": 3, "name": "FacturaInventada"},
            ]
        }
    )

    assert reader._validated_response(visual, _detection()) is None
    reader.close()


def test_vision_reader_rejects_generic_or_duplicate_class_names() -> None:
    reader = VisionUmlReader(enabled=False)
    generic = VisionUmlRead.model_validate(
        {
            "classes": [
                {"visual_index": 1, "name": "Clase1"},
                {"visual_index": 2, "name": "Producto"},
            ]
        }
    )
    duplicate = VisionUmlRead.model_validate(
        {
            "classes": [
                {"visual_index": 1, "name": "Venta"},
                {"visual_index": 2, "name": "venta"},
            ]
        }
    )

    assert reader._validated_response(generic, _detection()) is None
    assert reader._validated_response(duplicate, _detection()) is None
    reader.close()


def test_vision_reader_returns_none_when_model_is_not_installed() -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(
                200, json={"models": [{"name": "qwen2.5-coder:7b"}]}
            )
        ),
        base_url="http://127.0.0.1:11434",
    )
    reader = VisionUmlReader(client=client)

    assert reader.read(_image_payload(), _detection()) is None


def test_short_handwritten_id_confusions_are_normalized_without_class_templates() -> None:
    reader = VisionUmlReader(enabled=False)

    assert reader._identifier("ID") == "id"
    assert reader._identifier("1d") == "id"
    assert reader._identifier("18") == "id"
    assert reader._identifier("precio") == "precio"
    reader.close()
