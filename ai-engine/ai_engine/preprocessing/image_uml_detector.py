import base64
import binascii
from dataclasses import dataclass, field

from ai_engine.preprocessing.text import normalize_text


@dataclass(frozen=True)
class DetectedBox:
    x: int
    y: int
    width: int
    height: int
    text: str = ""

    @property
    def center_x(self) -> float:
        return self.x + self.width / 2

    @property
    def center_y(self) -> float:
        return self.y + self.height / 2


@dataclass(frozen=True)
class DetectedUmlAttribute:
    name: str
    data_type: str = "String"


@dataclass(frozen=True)
class DetectedUmlMethod:
    name: str
    return_type: str = "void"


@dataclass(frozen=True)
class DetectedUmlClass:
    name: str
    attributes: list[DetectedUmlAttribute] = field(default_factory=list)
    methods: list[DetectedUmlMethod] = field(default_factory=list)
    box: DetectedBox | None = None


@dataclass(frozen=True)
class DetectedUmlRelationship:
    source: str
    target: str
    relationship_type: str = "association"
    label: str | None = None
    source_cardinality: str | None = None
    target_cardinality: str | None = None
    association_class_name: str | None = None


@dataclass(frozen=True)
class ImageUmlDetection:
    classes: list[DetectedUmlClass] = field(default_factory=list)
    relationships: list[DetectedUmlRelationship] = field(default_factory=list)
    boxes: list[DetectedBox] = field(default_factory=list)
    observations: list[str] = field(default_factory=list)
    signature: str | None = None


def analyze_uml_image(image_base64: str | None) -> ImageUmlDetection:
    if not image_base64:
        return ImageUmlDetection(observations=["No se recibio imagen para analizar."])
    try:
        image = _decode_image(image_base64)
    except (ValueError, binascii.Error) as exc:
        return ImageUmlDetection(observations=[f"No se pudo decodificar la imagen: {exc}"])
    if image is None:
        return ImageUmlDetection(observations=["OpenCV/Pillow no estan disponibles para detectar la imagen."])

    boxes = _detect_class_boxes(image)
    observations = [f"Detector visual encontro {len(boxes)} cajas UML candidatas."]
    boxes_with_text = [_read_box_text(image, box) for box in boxes]
    if any(box.text.strip() for box in boxes_with_text):
        observations.append("OCR local aplicado sobre las cajas detectadas.")
    else:
        observations.append("OCR local no disponible o sin lectura util; se usa estructura visual.")

    signature = _detect_signature(boxes_with_text)
    classes = [_parse_class_box(box) for box in boxes_with_text]
    classes = [uml_class for uml_class in classes if uml_class.name]
    if not classes and boxes_with_text:
        classes = _build_generic_visual_classes(boxes_with_text)
        observations.append(
            "No se leyo texto confiable por OCR; se generaron clases genericas desde las cajas detectadas."
        )
    relationships = _detect_relationships(classes, boxes_with_text, signature)
    return ImageUmlDetection(
        classes=classes,
        relationships=relationships,
        boxes=boxes_with_text,
        observations=observations,
        signature=signature,
    )


def _decode_image(image_base64: str):
    try:
        import cv2
        import numpy as np
    except ImportError:
        return None

    payload = image_base64.split(",", maxsplit=1)[-1]
    raw = base64.b64decode(payload)
    buffer = np.frombuffer(raw, dtype=np.uint8)
    image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("contenido base64 no representa una imagen valida")
    return image


def _detect_class_boxes(image) -> list[DetectedBox]:
    import cv2

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    threshold = cv2.adaptiveThreshold(
        blur,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        31,
        11,
    )
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    closed = cv2.morphologyEx(threshold, cv2.MORPH_CLOSE, kernel, iterations=1)
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    image_height, image_width = gray.shape
    candidates: list[DetectedBox] = []
    for contour in contours:
        x, y, width, height = cv2.boundingRect(contour)
        area = width * height
        if (
            area > image_width * image_height * 0.01
            and width > image_width * 0.12
            and height > image_height * 0.06
            and width < image_width * 0.85
            and height < image_height * 0.85
        ):
            candidates.append(DetectedBox(x=x, y=y, width=width, height=height))

    return sorted(_deduplicate_boxes(candidates), key=lambda box: (box.y, box.x))


def _deduplicate_boxes(boxes: list[DetectedBox]) -> list[DetectedBox]:
    deduplicated: list[DetectedBox] = []
    for box in sorted(boxes, key=lambda item: item.width * item.height, reverse=True):
        if not any(_overlap_ratio(box, existing) > 0.65 for existing in deduplicated):
            deduplicated.append(box)
    return list(reversed(deduplicated))


def _overlap_ratio(first: DetectedBox, second: DetectedBox) -> float:
    left = max(first.x, second.x)
    top = max(first.y, second.y)
    right = min(first.x + first.width, second.x + second.width)
    bottom = min(first.y + first.height, second.y + second.height)
    if right <= left or bottom <= top:
        return 0
    intersection = (right - left) * (bottom - top)
    smaller_area = min(first.width * first.height, second.width * second.height)
    return intersection / smaller_area


def _read_box_text(image, box: DetectedBox) -> DetectedBox:
    try:
        import cv2
        import pytesseract
    except ImportError:
        return box
    crop = image[max(box.y - 8, 0) : box.y + box.height + 8, max(box.x - 8, 0) : box.x + box.width + 8]
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    scaled = cv2.resize(gray, None, fx=1.8, fy=1.8, interpolation=cv2.INTER_CUBIC)
    threshold = cv2.adaptiveThreshold(
        scaled,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        35,
        9,
    )
    try:
        text = pytesseract.image_to_string(threshold, lang="eng+spa", config="--psm 6")
    except (pytesseract.TesseractError, pytesseract.TesseractNotFoundError):
        text = ""
    return DetectedBox(x=box.x, y=box.y, width=box.width, height=box.height, text=text)


def _parse_class_box(box: DetectedBox) -> DetectedUmlClass:
    lines = [_clean_ocr_line(line) for line in box.text.splitlines()]
    lines = [line for line in lines if line]
    if not lines:
        return DetectedUmlClass(name="", box=box)

    name = ""
    attributes: list[DetectedUmlAttribute] = []
    methods: list[DetectedUmlMethod] = []
    for line in lines:
        if not name and ":" not in line and "(" not in line and any(character.isalpha() for character in line):
            name = _to_pascal_identifier(line)
            continue
        if "(" in line:
            method_name, _, return_type = line.partition(":")
            methods.append(
                DetectedUmlMethod(
                    name=_to_camel_identifier(method_name.replace("+", "").replace("-", "")),
                    return_type=_normalize_type(return_type or "void"),
                )
            )
            continue
        if ":" in line:
            raw_name, _, raw_type = line.partition(":")
            attributes.append(
                DetectedUmlAttribute(
                    name=_to_camel_identifier(raw_name.replace("+", "").replace("-", "")),
                    data_type=_normalize_type(raw_type),
                )
            )
    return DetectedUmlClass(name=name, attributes=attributes, methods=methods, box=box)


def _clean_ocr_line(line: str) -> str:
    cleaned = normalize_text(line)
    return (
        cleaned.replace(";", ":")
        .replace(" uuid", " UUID")
        .replace(" string", " String")
        .replace(" integer", " Integer")
        .replace(" double", " Double")
        .replace(" date", " Date")
        .strip(" .|")
    )


def _normalize_type(raw_type: str) -> str:
    normalized = normalize_text(raw_type).replace(" ", "")
    type_map = {
        "uuid": "UUID",
        "string": "String",
        "str": "String",
        "integer": "Integer",
        "int": "Integer",
        "double": "Double",
        "date": "Date",
        "void": "void",
    }
    return type_map.get(normalized, normalized[:1].upper() + normalized[1:] if normalized else "String")


def _to_pascal_identifier(value: str) -> str:
    words = [word for word in normalize_text(value).replace("_", " ").split() if any(character.isalpha() for character in word)]
    return "".join(word[:1].upper() + word[1:] for word in words)


def _to_camel_identifier(value: str) -> str:
    pascal = _to_pascal_identifier(value)
    return pascal[:1].lower() + pascal[1:] if pascal else ""


def _detect_signature(boxes: list[DetectedBox]) -> str | None:
    if len(boxes) != 3:
        return None
    top_boxes = sorted(boxes[:2], key=lambda box: box.x)
    bottom_box = boxes[2]
    top_mid_y = sum(box.center_y for box in top_boxes) / 2
    top_left, top_right = top_boxes
    if (
        bottom_box.center_y > top_mid_y
        and top_left.center_x < bottom_box.center_x < top_right.center_x
        and abs(top_left.center_y - top_right.center_y) < max(top_left.height, top_right.height) * 0.45
    ):
        return "association_class_triangular"
    return None


def _build_generic_visual_classes(boxes: list[DetectedBox]) -> list[DetectedUmlClass]:
    return [
        DetectedUmlClass(
            name=f"Clase{index + 1}",
            attributes=[
                DetectedUmlAttribute(name="id", data_type="UUID"),
                DetectedUmlAttribute(name="nombre", data_type="String"),
            ],
            methods=[],
            box=box,
        )
        for index, box in enumerate(boxes)
    ]


def _detect_relationships(
    classes: list[DetectedUmlClass],
    boxes: list[DetectedBox],
    signature: str | None,
) -> list[DetectedUmlRelationship]:
    if signature == "association_class_triangular" and len(classes) == 3:
        top_classes = sorted(classes[:2], key=lambda uml_class: uml_class.box.center_x if uml_class.box else 0)
        bottom_class = classes[2]
        return [
            DetectedUmlRelationship(
                source=top_classes[0].name,
                target=top_classes[1].name,
                relationship_type="association",
                label=bottom_class.name[:1].lower() + bottom_class.name[1:],
                source_cardinality="*",
                target_cardinality="*",
                association_class_name=bottom_class.name,
            )
        ]
    if len(classes) >= 2:
        ordered = sorted(classes, key=lambda uml_class: uml_class.box.center_x if uml_class.box else 0)
        return [
            DetectedUmlRelationship(
                source=ordered[index].name,
                target=ordered[index + 1].name,
                relationship_type="association",
                label="asocia",
                source_cardinality="1",
                target_cardinality="*",
            )
            for index in range(len(ordered) - 1)
        ]
    if signature == "association_class_triangular" and len(boxes) == 3:
        return []
    return []
