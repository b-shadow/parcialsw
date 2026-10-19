import base64
import binascii
import os
import re
import shutil
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher, get_close_matches
from functools import lru_cache
from itertools import pairwise

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
COMMON_CLASS_NAMES = (
    "Cliente",
    "Producto",
    "Venta",
    "Pedido",
    "DetalleVenta",
    "DetallePedido",
    "Usuario",
    "Empleado",
    "Proveedor",
    "Factura",
    "Pago",
    "Curso",
    "Estudiante",
    "Inscripcion",
    "Tema",
    "Reserva",
)
COMMON_ATTRIBUTE_TYPES = {
    "id": "UUID",
    "fecha": "Date",
    "fechaRegistro": "Date",
    "nombre": "String",
    "descripcion": "String",
    "duracionHoras": "Integer",
    "precio": "Decimal",
    "stock": "Integer",
    "email": "String",
    "correo": "String",
    "cantidad": "Integer",
    "estado": "String",
    "total": "Decimal",
    "notaFinal": "Double",
}
COMMON_METHOD_NAMES = (
    "inscribirse",
    "actualizarPerfil",
    "agregarTema",
    "obtenerDetalle",
)
TYPE_OCR_ALIASES = {
    "votd": "UUID",
    "uvid": "UUID",
    "vuta": "UUID",
    "vuid": "UUID",
    "vvitd": "UUID",
    "vota": "UUID",
    "outo": "UUID",
    "oguto": "UUID",
    "dive": "Date",
    "dove": "Date",
    "dalek": "Date",
    "dve": "Date",
    "tateger": "Integer",
    "teger": "Integer",
    "bins": "String",
    "oid": "void",
    "od": "void",
    "j": "void",
    "yo": "void",
    "yod": "void",
    "yoid": "void",
    "iyoid": "void",
}
ATTRIBUTE_ORDER = {
    "id": 0,
    "nombre": 10,
    "fecha": 10,
    "correo": 20,
    "email": 20,
    "descripcion": 20,
    "precio": 20,
    "estado": 20,
    "fechaRegistro": 30,
    "duracionHoras": 30,
    "stock": 30,
    "notaFinal": 30,
    "total": 30,
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
    confidence: float = 0.0


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

    ocr_available = _ocr_is_available()
    boxes_with_text = [_read_box_text(prepared, box) for box in boxes] if ocr_available else boxes
    read_count = sum(bool(box.text.strip()) for box in boxes_with_text)
    if read_count:
        observations.append(
            f"OCR multipaso recupero texto util en {read_count} de {len(boxes_with_text)} cajas."
        )
    else:
        observations.append(
            "OCR Tesseract no esta instalado o no produjo lectura util; "
            "no se debe aplicar un resultado generico al diagrama."
        )

    signature = _detect_signature(boxes_with_text)
    classes = _parse_or_complete_classes(boxes_with_text)
    if boxes_with_text and not read_count:
        observations.append(
            "No se leyo texto confiable por OCR; se generaron clases genericas desde las cajas detectadas."
        )
    elif any(uml_class.name.startswith("Clase") for uml_class in classes):
        observations.append("Las cajas sin texto confiable se conservaron con nombres genericos.")

    relationships = _detect_relationships(classes, boxes_with_text, signature, prepared)
    confidence = _detection_confidence(classes, relationships, boxes_with_text)
    duplicate_names = _duplicate_class_names(classes)
    if duplicate_names:
        observations.append(
            "Lectura ambigua: se detectaron nombres de clase repetidos: "
            + ", ".join(sorted(duplicate_names))
            + "."
        )
    if confidence < 0.55:
        observations.append(
            "La imagen no alcanzo el umbral de precision; revise enfoque, contraste y encuadre."
        )
    return ImageUmlDetection(
        classes=classes,
        relationships=relationships,
        boxes=boxes_with_text,
        observations=observations,
        signature=signature,
        confidence=confidence,
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
            touches_horizontal_frame = (
                x <= image_width * 0.01 or x + width >= image_width * 0.99
            )
            touches_vertical_frame = (
                y <= image_height * 0.01 or y + height >= image_height * 0.97
            )
            touches_frame_corner = touches_horizontal_frame and touches_vertical_frame
            if (
                not touches_frame_corner
                and area > image_area * 0.004
                and width > image_width * 0.075
                and height > image_height * 0.05
                and width < image_width * 0.9
                and height < image_height * 0.88
            ):
                candidate = DetectedBox(x=x, y=y, width=width, height=height)
                if rectangularity > 0.7:
                    candidates.append(candidate)
                    continue
                refined = _refine_box_from_lines(image, candidate)
                if refined is not None:
                    candidates.append(refined)
                elif rectangularity > 0.5:
                    candidates.append(candidate)
    return _sort_boxes_reading_order(_deduplicate_boxes(candidates))


def _sort_boxes_reading_order(boxes: list[DetectedBox]) -> list[DetectedBox]:
    rows: list[list[DetectedBox]] = []
    for box in sorted(boxes, key=lambda item: item.center_y):
        matching_row = next(
            (
                row
                for row in rows
                if abs(box.center_y - sum(item.center_y for item in row) / len(row))
                <= max(box.height, *(item.height for item in row)) * 0.45
            ),
            None,
        )
        if matching_row is None:
            rows.append([box])
        else:
            matching_row.append(box)
    return [box for row in rows for box in sorted(row, key=lambda item: item.x)]


def _refine_box_from_lines(image, candidate: DetectedBox) -> DetectedBox | None:
    import cv2
    import numpy as np

    padding = max(8, min(candidate.width, candidate.height) // 16)
    left = max(candidate.x - padding, 0)
    top = max(candidate.y - padding, 0)
    right = min(candidate.x + candidate.width + padding, image.shape[1])
    bottom = min(candidate.y + candidate.height + padding, image.shape[0])
    crop = image[top:bottom, left:right]
    if crop.size == 0:
        return None

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(_remove_uneven_illumination(gray), 35, 130)
    min_line = max(28, min(candidate.width, candidate.height) // 5)
    lines = cv2.HoughLinesP(
        edges,
        1,
        np.pi / 360,
        24,
        minLineLength=min_line,
        maxLineGap=max(12, min_line // 2),
    )
    if lines is None:
        return None

    horizontal: list[tuple[float, int, int, float]] = []
    vertical: list[tuple[float, int, int, float]] = []
    for x1, y1, x2, y2 in lines.reshape(-1, 4):
        dx, dy = int(x2 - x1), int(y2 - y1)
        length = float(np.hypot(dx, dy))
        angle = abs(float(np.degrees(np.arctan2(dy, dx))))
        if angle <= 14 or angle >= 166:
            horizontal.append(((y1 + y2) / 2, min(x1, x2), max(x1, x2), length))
        elif 76 <= angle <= 104:
            vertical.append(((x1 + x2) / 2, min(y1, y2), max(y1, y2), length))

    x_lines = _cluster_axis_lines(vertical, tolerance=max(6, crop.shape[1] // 45))
    y_lines = _cluster_axis_lines(horizontal, tolerance=max(6, crop.shape[0] // 45))
    if len(x_lines) < 2 or len(y_lines) < 2:
        return None

    best: tuple[float, float, float, float, float] | None = None
    for left_line in x_lines:
        for right_line in x_lines:
            box_width = right_line[0] - left_line[0]
            if box_width < max(70, candidate.width * 0.35):
                continue
            spanning_horizontal = [
                line
                for line in y_lines
                if line[1] <= left_line[0] + box_width * 0.28
                and line[2] >= right_line[0] - box_width * 0.28
            ]
            if len(spanning_horizontal) < 2:
                continue
            for top_index, top_line in enumerate(spanning_horizontal):
                for bottom_line in spanning_horizontal[top_index + 1 :]:
                    box_height = bottom_line[0] - top_line[0]
                    if box_height < max(55, candidate.height * 0.2):
                        continue
                    aspect = box_width / box_height
                    if not 0.45 <= aspect <= 4.5:
                        continue
                    left_coverage = _line_interval_coverage(
                        left_line[1], left_line[2], top_line[0], bottom_line[0]
                    )
                    right_coverage = _line_interval_coverage(
                        right_line[1], right_line[2], top_line[0], bottom_line[0]
                    )
                    if min(left_coverage, right_coverage) < 0.3:
                        continue
                    internal_lines = [
                        line
                        for line in spanning_horizontal
                        if top_line[0] <= line[0] <= bottom_line[0]
                    ]
                    score = (
                        (left_coverage + right_coverage) * 350
                        + len(internal_lines) * 70
                        + top_line[3]
                        + bottom_line[3]
                    )
                    if best is None or score > best[0]:
                        best = (
                            score,
                            left_line[0],
                            top_line[0],
                            right_line[0],
                            bottom_line[0],
                        )

    if best is None:
        return None
    _, refined_left, refined_top, refined_right, refined_bottom = best
    margin = max(3, min(candidate.width, candidate.height) // 80)
    x = max(round(left + refined_left) - margin, 0)
    y = max(round(top + refined_top) - margin, 0)
    width = min(round(refined_right - refined_left) + margin * 2, image.shape[1] - x)
    height = min(round(refined_bottom - refined_top) + margin * 2, image.shape[0] - y)
    return DetectedBox(x=x, y=y, width=width, height=height)


def _line_interval_coverage(
    line_start: int, line_end: int, interval_start: float, interval_end: float
) -> float:
    overlap = max(0.0, min(line_end, interval_end) - max(line_start, interval_start))
    return overlap / max(interval_end - interval_start, 1)


def _cluster_axis_lines(
    lines: list[tuple[float, int, int, float]], tolerance: int
) -> list[tuple[float, int, int, float]]:
    clusters: list[list[tuple[float, int, int, float]]] = []
    for line in sorted(lines, key=lambda item: item[0]):
        cluster_center = (
            sum(item[0] for item in clusters[-1]) / len(clusters[-1]) if clusters else None
        )
        if cluster_center is not None and abs(line[0] - cluster_center) <= tolerance:
            clusters[-1].append(line)
        else:
            clusters.append([line])
    return [
        (
            sum(item[0] for item in cluster) / len(cluster),
            min(item[1] for item in cluster),
            max(item[2] for item in cluster),
            max(item[3] for item in cluster),
        )
        for cluster in clusters
    ]


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

    # Keep handwriting close to hand-drawn borders; large insets can cut the first
    # characters of attributes when the writer starts directly on the class edge.
    inset = 3
    crop = image[
        max(box.y + inset, 0) : min(box.y + box.height - inset, image.shape[0]),
        max(box.x + inset, 0) : min(box.x + box.width - inset, image.shape[1]),
    ]
    if crop.size == 0:
        return box
    if not _has_text_like_ink(crop):
        return box

    candidates: list[_OcrCandidate] = []
    language = _ocr_language()
    for variant in _ocr_variants(crop):
        for psm in OCR_PSM_MODES:
            candidate = _run_ocr(pytesseract, variant, language, psm)
            if candidate.text:
                candidates.append(candidate)
    compartment_candidate = _read_compartment_text(pytesseract, crop, language)
    if compartment_candidate.text:
        candidates.append(compartment_candidate)
    header_candidates = _read_header_candidates(pytesseract, crop, language)
    if not candidates:
        return box
    class_name = _recover_class_name(header_candidates, candidates)
    consensus = _build_consensus_text(class_name, candidates)
    if consensus:
        return DetectedBox(box.x, box.y, box.width, box.height, consensus)
    best = max(candidates, key=lambda item: item.score)
    if best.score < 8:
        return box
    return DetectedBox(box.x, box.y, box.width, box.height, best.text)


def _read_header_candidates(
    pytesseract_module, crop, language: str
) -> list[_OcrCandidate]:
    title_candidates: list[_OcrCandidate] = []
    for ratio in (0.22, 0.28, 0.34):
        title = crop[: max(20, round(crop.shape[0] * ratio)), :]
        if not _has_text_like_ink(title):
            continue
        for variant in _handwriting_variants(title):
            psm = 6
            candidate = _run_ocr(pytesseract_module, variant, language, psm)
            if candidate.text:
                title_candidates.append(candidate)
    return title_candidates


def _recover_class_name(
    header_candidates: list[_OcrCandidate], full_candidates: list[_OcrCandidate]
) -> str:
    first_lines: list[_OcrCandidate] = []
    for candidate in full_candidates:
        for line in candidate.text.splitlines()[:2]:
            cleaned = _clean_ocr_line(line)
            if (
                cleaned
                and ":" not in cleaned
                and "(" not in cleaned
                and ")" not in cleaned
                and not cleaned.lstrip().startswith(("+", "-", "~", "#"))
            ):
                first_lines.append(_OcrCandidate(cleaned, candidate.confidence, candidate.score))
    sources = [*header_candidates, *first_lines]
    class_name, _ = _recover_common_term(sources, COMMON_CLASS_NAMES, 0.60)
    if class_name:
        return class_name

    plausible: list[tuple[float, str]] = []
    for candidate in sources:
        for line in candidate.text.splitlines():
            cleaned = _clean_ocr_line(line)
            if _looks_like_class_name(cleaned):
                plausible.append((candidate.confidence, _to_pascal_identifier(cleaned)))
    return _recover_repeated_identifier(plausible)


def _recover_repeated_identifier(candidates: list[tuple[float, str]]) -> str:
    groups: list[list[tuple[float, str]]] = []
    for confidence, identifier in candidates:
        normalized = normalize_text(identifier)
        if len(normalized) < 3:
            continue
        matching = next(
            (
                group
                for group in groups
                if SequenceMatcher(None, normalized, normalize_text(group[0][1])).ratio() >= 0.78
            ),
            None,
        )
        if matching is None:
            groups.append([(confidence, identifier)])
        else:
            matching.append((confidence, identifier))
    eligible = [group for group in groups if len(group) >= 2]
    if not eligible:
        return ""
    winner = max(
        eligible,
        key=lambda group: (len(group), sum(item[0] for item in group) / len(group)),
    )
    return max(winner, key=lambda item: item[0])[1]


def _build_consensus_text(class_name: str, candidates: list[_OcrCandidate]) -> str:
    if not class_name:
        return ""
    attribute_votes: dict[str, list[tuple[str, float]]] = {}
    method_votes: dict[str, list[tuple[str, float]]] = {}
    attribute_order: list[str] = []
    method_order: list[str] = []
    for candidate in candidates:
        member_lines = [
            cleaned
            for line in candidate.text.splitlines()
            if (cleaned := _clean_ocr_line(line))
            and not _line_matches_class_header(cleaned, class_name)
        ]
        parsed = _parse_class_box(
            DetectedBox(0, 0, 1, 1, "\n".join([class_name, *member_lines]))
        )
        seen_attributes: set[str] = set()
        for attribute in parsed.attributes:
            if attribute.name in seen_attributes:
                continue
            if attribute.data_type not in set(KNOWN_TYPES.values()):
                continue
            seen_attributes.add(attribute.name)
            attribute_votes.setdefault(attribute.name, []).append(
                (attribute.data_type, candidate.confidence)
            )
            if attribute.name not in attribute_order:
                attribute_order.append(attribute.name)
        seen_methods: set[str] = set()
        for method in parsed.methods:
            if method.name in seen_methods:
                continue
            seen_methods.add(method.name)
            method_votes.setdefault(method.name, []).append((method.return_type, candidate.confidence))
            if method.name not in method_order:
                method_order.append(method.name)

    attributes = []
    for name in attribute_order:
        votes = attribute_votes[name]
        if len(votes) >= 2 or name in COMMON_ATTRIBUTE_TYPES:
            types = [data_type for data_type, _confidence in votes]
            data_type = max(set(types), key=lambda item: (types.count(item), item != "String"))
            attributes.append((name, data_type))
    order_positions = {name: index for index, name in enumerate(attribute_order)}
    attributes.sort(
        key=lambda item: (ATTRIBUTE_ORDER.get(item[0], 100), order_positions.get(item[0], 100))
    )

    methods = []
    for name in method_order:
        votes = method_votes[name]
        if len(votes) >= 2 or name in COMMON_METHOD_NAMES:
            types = [return_type for return_type, _confidence in votes]
            return_type = max(set(types), key=lambda item: (types.count(item), item == "void"))
            methods.append((name, return_type))

    return "\n".join(
        [
            class_name,
            *(f"- {name}: {data_type}" for name, data_type in attributes),
            *(f"+ {name}(): {return_type}" for name, return_type in methods),
        ]
    )


def _line_matches_class_header(line: str, class_name: str) -> bool:
    if any(marker in line for marker in (":", "(", ")")):
        return False
    identifier = normalize_text(_to_pascal_identifier(line))
    expected = normalize_text(class_name)
    return bool(identifier and expected) and SequenceMatcher(None, identifier, expected).ratio() >= 0.62


def _has_text_like_ink(crop) -> bool:
    import cv2

    if crop.shape[0] < 12 or crop.shape[1] < 12:
        return False
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    horizontal = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (max(20, crop.shape[1] // 2), 1)),
    )
    vertical = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(15, crop.shape[0] // 2))),
    )
    without_rules = cv2.bitwise_and(mask, cv2.bitwise_not(cv2.bitwise_or(horizontal, vertical)))
    contours, _ = cv2.findContours(without_rules, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        x, y, width, height = cv2.boundingRect(contour)
        if x <= 2 or y <= 2 or x + width >= crop.shape[1] - 2 or y + height >= crop.shape[0] - 2:
            continue
        if 2 <= width <= crop.shape[1] * 0.8 and 3 <= height <= crop.shape[0] * 0.8:
            return True
    return False


def _handwriting_variants(crop) -> list:
    import cv2

    variants = [cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY), crop[:, :, 2]]
    prepared = []
    for variant in variants:
        scaled = cv2.resize(variant, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
        prepared.append(cv2.copyMakeBorder(scaled, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255))
    return prepared


def _recover_common_term(
    candidates: list[_OcrCandidate],
    terms: tuple[str, ...],
    cutoff: float,
    *,
    min_support: int = 1,
) -> tuple[str, float]:
    if not candidates or not terms:
        return "", 0.0

    weighted_votes = {term: 0.0 for term in terms}
    best_similarities = {term: 0.0 for term in terms}
    supports = {term: 0 for term in terms}
    seen_readings: set[tuple[str, str]] = set()
    for candidate in candidates:
        candidate_supports: set[str] = set()
        for line in candidate.text.splitlines():
            normalized_line = re.sub(r"[^a-z]", "", normalize_text(line))
            if len(normalized_line) < 4:
                continue
            for term in terms:
                normalized_term = re.sub(r"[^a-z]", "", normalize_text(term))
                if normalized_term in normalized_line:
                    similarity = 1.0
                else:
                    similarity = SequenceMatcher(None, normalized_line, normalized_term).ratio()
                if similarity < cutoff:
                    continue
                if term not in candidate_supports:
                    supports[term] += 1
                    candidate_supports.add(term)
                reading_key = (normalized_line, term)
                if reading_key in seen_readings:
                    continue
                seen_readings.add(reading_key)
                confidence_weight = 0.55 + min(max(candidate.confidence, 0), 100) / 100
                exact_bonus = 0.45 if similarity == 1.0 else 0.0
                weighted_votes[term] += similarity**3 * confidence_weight + exact_bonus
                best_similarities[term] = max(best_similarities[term], similarity)

    ranked = sorted(weighted_votes, key=weighted_votes.get, reverse=True)
    winner = ranked[0]
    winner_vote = weighted_votes[winner]
    runner_up_vote = weighted_votes[ranked[1]] if len(ranked) > 1 else 0.0
    if (
        winner_vote <= 0
        or (supports[winner] < min_support and best_similarities[winner] < 0.92)
        or (runner_up_vote > 0 and winner_vote < runner_up_vote * 1.12)
    ):
        return "", 0.0
    return winner, best_similarities[winner]


def _recover_common_attributes(
    candidates: list[_OcrCandidate],
) -> list[tuple[str, str]]:
    recovered: dict[str, tuple[str, str]] = {}
    terms = tuple(COMMON_ATTRIBUTE_TYPES)
    for candidate in candidates:
        for line in candidate.text.splitlines():
            match, score = _recover_common_term(
                [_OcrCandidate(line, candidate.confidence, candidate.score)], terms, 0.62
            )
            if match and score >= 0.62:
                recovered.setdefault(match, (match, COMMON_ATTRIBUTE_TYPES[match]))
    return list(recovered.values())


@lru_cache(maxsize=1)
def _ocr_is_available() -> bool:
    try:
        import pytesseract
    except ImportError:
        return False

    if shutil.which("tesseract") is None:
        candidates = (
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        )
        executable = next((path for path in candidates if os.path.isfile(path)), None)
        if executable is None:
            return False
        pytesseract.pytesseract.tesseract_cmd = executable
    _configure_tessdata()
    try:
        pytesseract.get_tesseract_version()
    except (pytesseract.TesseractNotFoundError, RuntimeError, OSError):
        return False
    return True


def _configure_tessdata() -> None:
    configured = os.getenv("CASE_TESSDATA_DIR", "").strip()
    local_app_data = os.getenv("LOCALAPPDATA", "").strip()
    candidates = [configured]
    if local_app_data:
        candidates.append(os.path.join(local_app_data, "CASEInteligente", "tessdata"))
    for candidate in candidates:
        if candidate and os.path.isfile(os.path.join(candidate, "eng.traineddata")):
            os.environ["TESSDATA_PREFIX"] = candidate
            _cached_languages.cache_clear()
            return


def _read_compartment_text(pytesseract_module, crop, language: str) -> _OcrCandidate:
    import cv2

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    normalized = _remove_uneven_illumination(gray)
    _, binary = cv2.threshold(normalized, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    horizontal = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (max(25, crop.shape[1] // 3), 1)),
    )
    contours, _ = cv2.findContours(horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    separators = sorted(
        y + height // 2
        for contour in contours
        for x, y, width, height in [cv2.boundingRect(contour)]
        if width >= crop.shape[1] * 0.35
    )
    separators = [round(item[0]) for item in _cluster_values(separators, tolerance=7)]
    boundaries = [0, *separators, crop.shape[0]]
    texts: list[str] = []
    confidences: list[float] = []
    for start, end in pairwise(boundaries):
        if end - start < max(18, crop.shape[0] * 0.08):
            continue
        inset = max(2, (end - start) // 20)
        band = crop[start + inset : end - inset, :]
        band_candidates = [
            _run_ocr(pytesseract_module, variant, language, psm)
            for variant in _ocr_variants(band)[:2]
            for psm in (7, 13)
        ]
        best = max(band_candidates, key=lambda item: item.score, default=None)
        if best is not None and best.text and best.score >= 6:
            texts.append(best.text)
            confidences.append(best.confidence)
    text = "\n".join(texts)
    confidence = sum(confidences) / len(confidences) if confidences else 0
    return _OcrCandidate(text, confidence, _score_ocr_candidate(text, confidence) + len(texts) * 4)


def _cluster_values(values: list[int], tolerance: int) -> list[tuple[float, int]]:
    clusters: list[list[int]] = []
    for value in sorted(values):
        if clusters and abs(value - sum(clusters[-1]) / len(clusters[-1])) <= tolerance:
            clusters[-1].append(value)
        else:
            clusters.append([value])
    return [(sum(cluster) / len(cluster), len(cluster)) for cluster in clusters]


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
    used_names: set[str] = set()
    completed: list[DetectedUmlClass] = []
    for index, (box, uml_class) in enumerate(zip(boxes, parsed, strict=False), start=1):
        normalized_name = uml_class.name.casefold()
        if uml_class.name and normalized_name not in used_names:
            used_names.add(normalized_name)
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
                attributes=[],
                box=box,
            )
        )
    return completed


def _duplicate_class_names(classes: list[DetectedUmlClass]) -> set[str]:
    counts: dict[str, int] = {}
    labels: dict[str, str] = {}
    for uml_class in classes:
        normalized = uml_class.name.casefold()
        counts[normalized] = counts.get(normalized, 0) + 1
        labels[normalized] = uml_class.name
    return {labels[name] for name, count in counts.items() if count > 1}


def _detection_confidence(
    classes: list[DetectedUmlClass],
    relationships: list[DetectedUmlRelationship],
    boxes: list[DetectedBox],
) -> float:
    if not boxes or not classes:
        return 0.0
    resolved = [uml_class for uml_class in classes if not re.fullmatch(r"Clase\d+", uml_class.name)]
    name_score = len(resolved) / len(boxes)
    member_score = sum(bool(item.attributes or item.methods) for item in resolved) / len(boxes)
    duplicate_penalty = 0.35 if _duplicate_class_names(classes) else 0.0
    relationship_score = 1.0 if relationships or len(classes) == 1 else 0.45
    score = name_score * 0.45 + member_score * 0.40 + relationship_score * 0.15
    if len(classes) > 1 and member_score < 0.5:
        score = min(score, 0.49)
    return round(max(0.0, min(1.0, score - duplicate_penalty)), 3)


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
        if "(" in line or ")" in line or line.lstrip().startswith("+"):
            method = _parse_method_line(line)
            if method:
                methods.append(method)
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
            normalized = re.sub(r"[^a-z]", "", normalize_text(candidate))
            normalized_terms = {
                re.sub(r"[^a-z]", "", normalize_text(name)): name
                for name in COMMON_ATTRIBUTE_TYPES
            }
            close = get_close_matches(normalized, normalized_terms, n=1, cutoff=0.76)
            if not close:
                return None
            if abs(len(normalized) - len(close[0])) > 3:
                return None
            name = normalized_terms[close[0]]
            return DetectedUmlAttribute(name, COMMON_ATTRIBUTE_TYPES[name])
        raw_name, raw_type = match.groups()
    name = _normalize_attribute_name(raw_name)
    return DetectedUmlAttribute(name, _normalize_type(raw_type)) if name else None


def _parse_method_line(line: str) -> DetectedUmlMethod | None:
    candidate = line.strip("+-~* ")
    closing_index = candidate.find(")")
    opening_index = candidate.find("(")
    separator_indexes = [index for index in (opening_index, closing_index) if index >= 0]
    if separator_indexes:
        split_index = min(separator_indexes)
    elif ":" in candidate:
        split_index = candidate.index(":")
    else:
        return None
    raw_name = candidate[:split_index]
    tail = candidate[closing_index + 1 :] if closing_index >= 0 else candidate[split_index + 1 :]
    raw_return = tail.split(":", maxsplit=1)[-1] if tail else "void"
    method_name = _normalize_method_name(raw_name)
    if not method_name:
        return None
    return DetectedUmlMethod(method_name, _normalize_type(raw_return))


def _normalize_attribute_name(raw_name: str) -> str:
    normalized = re.sub(r"[^a-z0-9]", "", normalize_text(raw_name))
    if normalized in {"1d", "14", "ib", "ld", "i0", "io"}:
        return "id"
    terms = {re.sub(r"[^a-z]", "", normalize_text(name)): name for name in COMMON_ATTRIBUTE_TYPES}
    if normalized in terms:
        return terms[normalized]
    close = get_close_matches(normalized, terms, n=1, cutoff=0.67)
    if close:
        return terms[close[0]]
    return _to_camel_identifier(raw_name)


def _normalize_method_name(raw_name: str) -> str:
    candidate = _to_camel_identifier(raw_name)
    normalized = re.sub(r"[^a-z]", "", normalize_text(candidate))
    terms = {re.sub(r"[^a-z]", "", normalize_text(name)): name for name in COMMON_METHOD_NAMES}
    close = get_close_matches(normalized, terms, n=1, cutoff=0.62)
    return terms[close[0]] if close else candidate


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
    if normalized in TYPE_OCR_ALIASES:
        return TYPE_OCR_ALIASES[normalized]
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
    horizontal_span = top_right.center_x - top_left.center_x
    bottom_horizontal_position = (
        (bottom_box.center_x - top_left.center_x) / horizontal_span
        if horizontal_span > 0
        else -1
    )
    if (
        bottom_box.center_y > top_mid_y
        and 0.2 <= bottom_horizontal_position <= 0.8
        and abs(top_left.center_y - top_right.center_y)
        < max(top_left.height, top_right.height) * 0.45
    ):
        return "association_class_triangular"
    return None


def _detect_relationships(
    classes: list[DetectedUmlClass],
    boxes: list[DetectedBox],
    signature: str | None,
    image,
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
    relationships: list[DetectedUmlRelationship] = []
    for index, source in enumerate(classes):
        if source.box is None:
            continue
        for target in classes[index + 1 :]:
            if target.box is None:
                continue
            connection = _detect_box_connection(image, source.box, target.box)
            if connection is None:
                continue
            orientation, axis, source_side, target_side = connection
            source_cardinality = _read_cardinality(
                image, source.box, source_side, orientation, axis
            )
            target_cardinality = _read_cardinality(
                image, target.box, target_side, orientation, axis
            )
            relationships.append(
                DetectedUmlRelationship(
                    source=source.name,
                    target=target.name,
                    label=None,
                    source_cardinality=source_cardinality,
                    target_cardinality=target_cardinality,
                )
            )
    return relationships


def _detect_box_connection(
    image, first: DetectedBox, second: DetectedBox
) -> tuple[str, float, str, str] | None:
    horizontal = _horizontal_connection(image, first, second)
    vertical = _vertical_connection(image, first, second)
    candidates = [item for item in (horizontal, vertical) if item is not None]
    if not candidates:
        return None
    _, orientation, axis, first_side, second_side = max(candidates, key=lambda item: item[0])
    return orientation, axis, first_side, second_side


def _horizontal_connection(image, first: DetectedBox, second: DetectedBox):
    import cv2

    left_box, right_box = (first, second) if first.center_x <= second.center_x else (second, first)
    gap_start = left_box.x + left_box.width
    gap_end = right_box.x
    gap = gap_end - gap_start
    overlap_top = max(left_box.y, right_box.y)
    overlap_bottom = min(left_box.y + left_box.height, right_box.y + right_box.height)
    if gap <= 12 or overlap_bottom <= overlap_top:
        return None
    margin = max(12, min(left_box.height, right_box.height) // 4)
    top = max(overlap_top - margin, 0)
    bottom = min(overlap_bottom + margin, image.shape[0])
    roi = _ink_mask(image[top:bottom, gap_start:gap_end])
    if roi.size == 0:
        return None
    connected = cv2.morphologyEx(
        roi,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_RECT, (max(9, gap // 4), 3)),
    )
    opened = cv2.morphologyEx(
        connected,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (max(9, gap // 8), 1)),
    )
    contours, _ = cv2.findContours(opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    spans = [cv2.boundingRect(contour) for contour in contours]
    best = max(spans, key=lambda item: item[2], default=None)
    if best is None or best[2] < gap * 0.4:
        return None
    _x, y, width, height = best
    score = width / gap
    axis = top + y + height / 2
    first_side = "right" if first is left_box else "left"
    second_side = "left" if second is right_box else "right"
    return score, "horizontal", axis, first_side, second_side


def _vertical_connection(image, first: DetectedBox, second: DetectedBox):
    import cv2

    top_box, bottom_box = (first, second) if first.center_y <= second.center_y else (second, first)
    gap_start = top_box.y + top_box.height
    gap_end = bottom_box.y
    gap = gap_end - gap_start
    overlap_left = max(top_box.x, bottom_box.x)
    overlap_right = min(top_box.x + top_box.width, bottom_box.x + bottom_box.width)
    if gap <= 12 or overlap_right <= overlap_left:
        return None
    margin = max(12, min(top_box.width, bottom_box.width) // 4)
    left = max(overlap_left - margin, 0)
    right = min(overlap_right + margin, image.shape[1])
    roi = _ink_mask(image[gap_start:gap_end, left:right])
    if roi.size == 0:
        return None
    connected = cv2.morphologyEx(
        roi,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_RECT, (3, max(9, gap // 4))),
    )
    opened = cv2.morphologyEx(
        connected,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(9, gap // 8))),
    )
    contours, _ = cv2.findContours(opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    spans = [cv2.boundingRect(contour) for contour in contours]
    best = max(spans, key=lambda item: item[3], default=None)
    if best is None or best[3] < gap * 0.4:
        return None
    x, _y, width, height = best
    score = height / gap
    axis = left + x + width / 2
    first_side = "bottom" if first is top_box else "top"
    second_side = "top" if second is bottom_box else "bottom"
    return score, "vertical", axis, first_side, second_side


def _ink_mask(image):
    import cv2

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    normalized = _remove_uneven_illumination(gray)
    _, otsu = cv2.threshold(normalized, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    adaptive = cv2.adaptiveThreshold(
        normalized,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        35,
        9,
    )
    return cv2.bitwise_or(otsu, adaptive)


def _read_cardinality(
    image, box: DetectedBox, side: str, orientation: str, axis: float
) -> str | None:
    if not _ocr_is_available():
        return None
    try:
        import pytesseract
    except ImportError:
        return None

    span = max(70, min(box.width, box.height) // 2)
    if orientation == "horizontal":
        y1, y2 = int(axis - span), int(axis + span)
        if side == "right":
            x1, x2 = box.x + box.width - 10, box.x + box.width + span
        else:
            x1, x2 = box.x - span, box.x + 10
    else:
        x1, x2 = int(axis - span), int(axis + span)
        if side == "bottom":
            y1, y2 = box.y + box.height - 10, box.y + box.height + span
        else:
            y1, y2 = box.y - span, box.y + 10
    crop_x = max(x1, 0)
    crop_y = max(y1, 0)
    crop = image[
        crop_y : min(y2, image.shape[0]),
        crop_x : min(x2, image.shape[1]),
    ]
    if crop.size == 0:
        return None
    geometry_value = _read_cardinality_geometry(
        crop,
        orientation,
        axis - (crop_y if orientation == "horizontal" else crop_x),
    )
    if geometry_value in {"*", "1..*"}:
        return geometry_value
    values: list[str] = []
    for variant in _ocr_variants(crop)[:2]:
        try:
            text = pytesseract.image_to_string(
                variant,
                lang=_ocr_language(),
                config="--oem 1 --psm 11 -c tessedit_char_whitelist=0123456789.*",
            )
        except (pytesseract.TesseractError, RuntimeError, OSError):
            continue
        normalized = re.sub(r"\s+", "", text).replace(",", ".")
        match = re.search(r"(?:0|1)\.\.\*|\*|[01]", normalized)
        if match:
            values.append(match.group(0))
    if not values:
        return geometry_value
    return max(values, key=lambda value: (len(value), values.count(value)))


def _read_cardinality_geometry(crop, orientation: str, local_axis: float) -> str | None:
    import cv2

    mask = _ink_mask(crop)
    axis = round(local_axis)
    if orientation == "horizontal":
        mask[max(0, axis - 3) : min(mask.shape[0], axis + 4), :] = 0
    else:
        mask[:, max(0, axis - 3) : min(mask.shape[1], axis + 4)] = 0
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    glyphs = []
    for contour in contours:
        x, y, width, height = cv2.boundingRect(contour)
        if x <= 1 or y <= 1 or x + width >= mask.shape[1] - 1 or y + height >= mask.shape[0] - 1:
            continue
        perpendicular_center = y + height / 2 if orientation == "horizontal" else x + width / 2
        if abs(perpendicular_center - local_axis) > 32:
            continue
        if width <= 38 and height <= 38 and width * height >= 18:
            glyphs.append((x, y, width, height))

    stars = [item for item in glyphs if item[2] >= 12 and item[3] >= 10]
    ones = [item for item in glyphs if item[2] <= 10 and 14 <= item[3] <= 34]
    if stars and ones:
        for star in stars:
            for one in ones:
                star_position = star[0] + star[2] / 2 if orientation == "horizontal" else star[1] + star[3] / 2
                one_position = one[0] + one[2] / 2 if orientation == "horizontal" else one[1] + one[3] / 2
                if abs(star_position - one_position) >= 15:
                    return "1..*"
    if stars:
        return "*"
    if ones:
        return "1"
    return None
