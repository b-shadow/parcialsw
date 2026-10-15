import base64
import binascii
import re
import unicodedata
from dataclasses import dataclass, field
from difflib import get_close_matches
from functools import lru_cache

from ai_engine.preprocessing.text import normalize_text

MAX_IMAGE_BYTES = 15 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000
OCR_PSM_MODES = (6, 11)
KNOWN_TYPES = {
    "uuid": "UUID",
    "string": "String",
    "str": "String",
    "integer": "Integer",
    "int": "Integer",
    "long": "Long",
    "double": "Double",
    "float": "Float",
    "decimal": "Decimal",
    "boolean": "Boolean",
    "bool": "Boolean",
    "date": "Date",
    "datetime": "DateTime",
    "void": "void",
}


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


@dataclass(frozen=True)
class _OcrCandidate:
    text: str
    confidence: float
    score: float


def analyze_uml_image(image_base64: str | None) -> ImageUmlDetection:
    if not image_base64:
        return ImageUmlDetection(observations=["No se recibio imagen para analizar."])
    try:
        image = _decode_image(image_base64)
    except (ValueError, binascii.Error) as exc:
        return ImageUmlDetection(observations=[f"No se pudo decodificar la imagen: {exc}"])
    if image is None:
        return ImageUmlDetection(
            observations=["OpenCV no esta disponible para detectar la imagen."]
        )

    prepared, deskew_angle = _prepare_image(image)
    boxes = _detect_class_boxes(prepared)
    observations = [f"Detector visual encontro {len(boxes)} cajas UML candidatas."]
    if abs(deskew_angle) >= 0.4:
        observations.append(f"Se corrigio una inclinacion aproximada de {deskew_angle:.1f} grados.")

    boxes_with_text = [_read_box_text(prepared, box) for box in boxes]
    read_count = sum(bool(box.text.strip()) for box in boxes_with_text)
    if read_count:
        observations.append(
            f"OCR multipaso recupero texto util en {read_count} de {len(boxes_with_text)} cajas."
        )
    else:
        observations.append("OCR local no disponible o sin lectura util; se usa estructura visual.")

    signature = _detect_signature(boxes_with_text)
    classes = _parse_or_complete_classes(boxes_with_text)
    if boxes_with_text and not read_count:
        observations.append(
            "No se leyo texto confiable por OCR; se generaron clases genericas desde las cajas detectadas."
        )
    elif any(uml_class.name.startswith("Clase") for uml_class in classes):
        observations.append("Las cajas sin texto confiable se conservaron con nombres genericos.")

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

    payload = image_base64.split(",", maxsplit=1)[-1].strip()
    if not payload:
        raise ValueError("contenido base64 vacio")
    if len(payload) * 3 // 4 > MAX_IMAGE_BYTES:
        raise ValueError("la imagen supera el limite de 15 MB")
    raw = base64.b64decode(payload, validate=True)
    if len(raw) > MAX_IMAGE_BYTES:
        raise ValueError("la imagen supera el limite de 15 MB")
    image = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("contenido base64 no representa una imagen valida")
    height, width = image.shape[:2]
    if height * width > MAX_IMAGE_PIXELS:
        raise ValueError("la imagen supera el limite de 40 megapixeles")
    return image


def _prepare_image(image):
    import cv2
    import numpy as np

    height, width = image.shape[:2]
    longest_side = max(height, width)
    if longest_side < 1400:
        scale = min(2.0, 1400 / longest_side)
        image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    elif longest_side > 3200:
        scale = 3200 / longest_side
        image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(_remove_uneven_illumination(gray), 50, 150, apertureSize=3)
    min_line = max(50, min(image.shape[:2]) // 7)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 60, minLineLength=min_line, maxLineGap=20)
    angles: list[float] = []
    if lines is not None:
        for x1, y1, x2, y2 in lines.reshape(-1, 4):
            angle = float(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
            if -15 <= angle <= 15 and abs(x2 - x1) >= min_line:
                angles.append(angle)
    angle = float(np.median(angles)) if len(angles) >= 2 else 0.0
    if abs(angle) < 0.4 or abs(angle) > 12:
        return image, 0.0

    height, width = image.shape[:2]
    matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1.0)
    return cv2.warpAffine(
        image,
        matrix,
        (width, height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255),
    ), angle


def _remove_uneven_illumination(gray):
    import cv2

    kernel_size = max(15, (min(gray.shape[:2]) // 18) | 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    background = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
    return cv2.divide(gray, background, scale=255)


def _binary_variants(image) -> list:
    import cv2

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    normalized = _remove_uneven_illumination(gray)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(normalized)
    denoised = cv2.medianBlur(clahe, 3)
    _, otsu = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    adaptive = cv2.adaptiveThreshold(
        denoised,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        35,
        9,
    )
    return [otsu, adaptive]


def _detect_class_boxes(image) -> list[DetectedBox]:
    import cv2

    image_height, image_width = image.shape[:2]
    image_area = image_width * image_height
    candidates: list[DetectedBox] = []
    for threshold in _binary_variants(image):
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
        closed = cv2.morphologyEx(threshold, cv2.MORPH_CLOSE, kernel, iterations=1)
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            x, y, width, height = cv2.boundingRect(contour)
            area = width * height
            rectangularity = cv2.contourArea(contour) / area if area else 0
            if (
                area > image_area * 0.008
                and width > image_width * 0.11
                and height > image_height * 0.055
                and width < image_width * 0.9
                and height < image_height * 0.88
                and rectangularity > 0.5
            ):
                candidates.append(DetectedBox(x=x, y=y, width=width, height=height))
    return sorted(_deduplicate_boxes(candidates), key=lambda box: (box.y, box.x))


def _deduplicate_boxes(boxes: list[DetectedBox]) -> list[DetectedBox]:
    deduplicated: list[DetectedBox] = []
    for box in sorted(boxes, key=lambda item: item.width * item.height, reverse=True):
        if not any(_overlap_ratio(box, existing) > 0.65 for existing in deduplicated):
            deduplicated.append(box)
    return deduplicated


def _overlap_ratio(first: DetectedBox, second: DetectedBox) -> float:
    left, top = max(first.x, second.x), max(first.y, second.y)
    right = min(first.x + first.width, second.x + second.width)
    bottom = min(first.y + first.height, second.y + second.height)
    if right <= left or bottom <= top:
        return 0
    intersection = (right - left) * (bottom - top)
    return intersection / min(first.width * first.height, second.width * second.height)


def _read_box_text(image, box: DetectedBox) -> DetectedBox:
    try:
        import pytesseract
    except ImportError:
        return box

    inset = max(3, min(box.width, box.height) // 80)
    crop = image[
        max(box.y + inset, 0) : min(box.y + box.height - inset, image.shape[0]),
        max(box.x + inset, 0) : min(box.x + box.width - inset, image.shape[1]),
    ]
    if crop.size == 0:
        return box

    candidates: list[_OcrCandidate] = []
    language = _ocr_language()
    for variant in _ocr_variants(crop):
        for psm in OCR_PSM_MODES:
            candidate = _run_ocr(pytesseract, variant, language, psm)
            if candidate.text:
                candidates.append(candidate)
    if not candidates:
        return box
    best = max(candidates, key=lambda item: item.score)
    if best.score < 8:
        return box
    return DetectedBox(box.x, box.y, box.width, box.height, best.text)


def _ocr_variants(crop) -> list:
    import cv2

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    scale = max(1.5, min(3.0, 1200 / max(gray.shape[1], 1)))
    scaled = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    normalized = _remove_uneven_illumination(scaled)
    clahe = cv2.createCLAHE(clipLimit=2.8, tileGridSize=(8, 8)).apply(normalized)
    denoised = cv2.bilateralFilter(clahe, 7, 45, 45)
    _, otsu = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    adaptive = cv2.adaptiveThreshold(
        denoised,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        41,
        11,
    )
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    strengthened = cv2.morphologyEx(adaptive, cv2.MORPH_CLOSE, kernel, iterations=1)
    return [
        cv2.copyMakeBorder(item, 16, 16, 16, 16, cv2.BORDER_CONSTANT, value=255)
        for item in (denoised, otsu, strengthened)
    ]


@lru_cache(maxsize=1)
def _cached_languages() -> tuple[str, ...]:
    try:
        import pytesseract

        return tuple(pytesseract.get_languages(config=""))
    except (RuntimeError, OSError, ImportError):
        return ()


def _ocr_language() -> str:
    languages = set(_cached_languages())
    selected = [language for language in ("spa", "eng") if language in languages]
    return "+".join(selected) if selected else "eng"


def _run_ocr(pytesseract_module, image, language: str, psm: int) -> _OcrCandidate:
    config = f"--oem 1 --psm {psm} -c preserve_interword_spaces=1"
    try:
        data = pytesseract_module.image_to_data(
            image,
            lang=language,
            config=config,
            output_type=pytesseract_module.Output.DICT,
        )
    except (
        pytesseract_module.TesseractError,
        pytesseract_module.TesseractNotFoundError,
        RuntimeError,
        OSError,
    ):
        return _OcrCandidate(text="", confidence=0, score=0)

    text = _text_from_ocr_data(data)
    confidences = []
    for raw_confidence, token in zip(data.get("conf", []), data.get("text", []), strict=False):
        if not str(token).strip():
            continue
        try:
            confidence = float(raw_confidence)
        except (TypeError, ValueError):
            continue
        if confidence >= 0:
            confidences.append(confidence)
    mean_confidence = sum(confidences) / len(confidences) if confidences else 0
    return _OcrCandidate(text, mean_confidence, _score_ocr_candidate(text, mean_confidence))


def _text_from_ocr_data(data: dict) -> str:
    lines: dict[tuple[int, int, int], list[str]] = {}
    tokens = data.get("text", [])
    defaults = [0] * len(tokens)
    for index, token in enumerate(tokens):
        token = str(token).strip()
        if not token:
            continue
        key = (
            int(data.get("block_num", defaults)[index]),
            int(data.get("par_num", defaults)[index]),
            int(data.get("line_num", list(range(len(tokens))))[index]),
        )
        lines.setdefault(key, []).append(token)
    return "\n".join(" ".join(words) for words in lines.values())


def _score_ocr_candidate(text: str, confidence: float) -> float:
    if not text.strip():
        return 0
    cleaned_lines = [_clean_ocr_line(line) for line in text.splitlines()]
    useful = [line for line in cleaned_lines if any(character.isalpha() for character in line)]
    syntax_hits = sum(":" in line or "(" in line or ")" in line for line in useful)
    type_hits = sum(
        any(type_name in normalize_text(line).replace(" ", "") for type_name in KNOWN_TYPES)
        for line in useful
    )
    noise = sum(1 for character in text if not (character.isalnum() or character in " _:+-().,*\n"))
    return confidence * 0.45 + len(useful) * 5 + syntax_hits * 8 + type_hits * 5 - noise * 1.5


def _parse_or_complete_classes(boxes: list[DetectedBox]) -> list[DetectedUmlClass]:
    parsed = [_parse_class_box(box) for box in boxes]
    used_names = {uml_class.name.casefold() for uml_class in parsed if uml_class.name}
    completed: list[DetectedUmlClass] = []
    for index, (box, uml_class) in enumerate(zip(boxes, parsed, strict=False), start=1):
        if uml_class.name:
            completed.append(uml_class)
            continue
        suffix = index
        while f"clase{suffix}" in used_names:
            suffix += 1
        name = f"Clase{suffix}"
        used_names.add(name.casefold())
        completed.append(
            DetectedUmlClass(
                name=name,
                attributes=[
                    DetectedUmlAttribute("id", "UUID"),
                    DetectedUmlAttribute("nombre", "String"),
                ],
                box=box,
            )
        )
    return completed


def _parse_class_box(box: DetectedBox) -> DetectedUmlClass:
    lines = [cleaned for line in box.text.splitlines() if (cleaned := _clean_ocr_line(line))]
    if not lines:
        return DetectedUmlClass(name="", box=box)

    name = ""
    attributes: list[DetectedUmlAttribute] = []
    methods: list[DetectedUmlMethod] = []
    for line in lines:
        if not name and _looks_like_class_name(line):
            name = _to_pascal_identifier(line)
            continue
        if "(" in line or ")" in line:
            match = re.search(r"([A-Za-z][\w ]*)\s*\([^)]*\)\s*(?::|->)?\s*([\w]+)?", line)
            if match:
                methods.append(
                    DetectedUmlMethod(
                        _to_camel_identifier(match.group(1)),
                        _normalize_type(match.group(2) or "void"),
                    )
                )
            continue
        attribute = _parse_attribute_line(line)
        if attribute and attribute.name:
            attributes.append(attribute)
    return DetectedUmlClass(name, _unique_attributes(attributes), methods, box)


def _looks_like_class_name(line: str) -> bool:
    candidate = line.strip("+- ")
    return bool(candidate) and (
        ":" not in candidate
        and "(" not in candidate
        and 1 <= len(candidate.split()) <= 4
        and 2 <= len(candidate) <= 60
        and any(character.isalpha() for character in candidate)
        and sum(character.isalnum() or character in " _" for character in candidate)
        / len(candidate)
        > 0.75
    )


def _parse_attribute_line(line: str) -> DetectedUmlAttribute | None:
    candidate = line.strip("+- ")
    if ":" in candidate:
        raw_name, raw_type = candidate.split(":", maxsplit=1)
    else:
        match = re.match(
            r"(.+?)\s+(UUID|String|str|Integer|int|Long|Double|Float|Decimal|Boolean|bool|DateTime|Date)$",
            candidate,
            re.IGNORECASE,
        )
        if not match:
            return None
        raw_name, raw_type = match.groups()
    name = _to_camel_identifier(raw_name)
    return DetectedUmlAttribute(name, _normalize_type(raw_type)) if name else None


def _unique_attributes(attributes: list[DetectedUmlAttribute]) -> list[DetectedUmlAttribute]:
    unique: dict[str, DetectedUmlAttribute] = {}
    for attribute in attributes:
        unique.setdefault(attribute.name.casefold(), attribute)
    return list(unique.values())


def _clean_ocr_line(line: str) -> str:
    normalized = unicodedata.normalize("NFKD", line)
    cleaned = re.sub(r"\s+", " ", normalized.encode("ascii", "ignore").decode("ascii")).strip()
    cleaned = re.sub(r"^[|!\s]*([+\-~#])?\s*", lambda match: (match.group(1) or "") + " ", cleaned)
    cleaned = re.sub(r"\s*[:;=]\s*", ": ", cleaned)
    return (
        cleaned.replace("{", "(")
        .replace("[", "(")
        .replace("}", ")")
        .replace("]", ")")
        .strip(" .|_")
    )


def _normalize_type(raw_type: str) -> str:
    normalized = re.sub(r"[^a-z]", "", normalize_text(raw_type))
    if normalized in KNOWN_TYPES:
        return KNOWN_TYPES[normalized]
    close = get_close_matches(normalized, KNOWN_TYPES.keys(), n=1, cutoff=0.72)
    if close:
        return KNOWN_TYPES[close[0]]
    return normalized[:1].upper() + normalized[1:] if normalized else "String"


def _to_pascal_identifier(value: str) -> str:
    separated = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", value)
    words = re.findall(r"[A-Za-z][A-Za-z0-9]*", normalize_text(separated).replace("_", " "))
    return "".join(word[:1].upper() + word[1:] for word in words)


def _to_camel_identifier(value: str) -> str:
    pascal = _to_pascal_identifier(value)
    return pascal[:1].lower() + pascal[1:] if pascal else ""


def _detect_signature(boxes: list[DetectedBox]) -> str | None:
    if len(boxes) != 3:
        return None
    top_left, top_right = sorted(boxes[:2], key=lambda box: box.x)
    bottom_box = boxes[2]
    top_mid_y = (top_left.center_y + top_right.center_y) / 2
    if (
        bottom_box.center_y > top_mid_y
        and top_left.center_x < bottom_box.center_x < top_right.center_x
        and abs(top_left.center_y - top_right.center_y)
        < max(top_left.height, top_right.height) * 0.45
    ):
        return "association_class_triangular"
    return None


def _detect_relationships(
    classes: list[DetectedUmlClass],
    boxes: list[DetectedBox],
    signature: str | None,
) -> list[DetectedUmlRelationship]:
    if signature == "association_class_triangular" and len(classes) == 3:
        top_classes = sorted(classes[:2], key=lambda item: item.box.center_x if item.box else 0)
        association_class = classes[2]
        return [
            DetectedUmlRelationship(
                source=top_classes[0].name,
                target=top_classes[1].name,
                label=association_class.name[:1].lower() + association_class.name[1:],
                source_cardinality="*",
                target_cardinality="*",
                association_class_name=association_class.name,
            )
        ]
    if len(classes) >= 2:
        ordered = sorted(classes, key=lambda item: item.box.center_x if item.box else 0)
        return [
            DetectedUmlRelationship(
                source=ordered[index].name,
                target=ordered[index + 1].name,
                label="asocia",
                source_cardinality="1",
                target_cardinality="*",
            )
            for index in range(len(ordered) - 1)
        ]
    if signature == "association_class_triangular" and len(boxes) == 3:
        return []
    return []
