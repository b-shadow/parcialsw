from __future__ import annotations

import base64
import binascii
import os
import re
from typing import Literal

import httpx
from pydantic import BaseModel, Field, ValidationError

from ai_engine.preprocessing.image_uml_detector import (
    ImageUmlDetection,
    _decode_image,
    _normalize_type,
    _prepare_image,
)
from ai_engine.providers.ollama_provider import validate_ollama_base_url
from ai_engine.services.contracts import (
    UmlAttribute,
    UmlClass,
    UmlGenerationResponse,
    UmlMethod,
    UmlRelationship,
)

_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,79}$")
_GENERIC_CLASS = re.compile(r"^(?:clase|class|entidad|tabla)\s*\d*$", re.IGNORECASE)
_CARDINALITIES = {"0", "1", "*", "0..1", "1..*", "0..*", "*..*"}


class VisionAttribute(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    data_type: str | None = Field(default=None, max_length=80)


class VisionMethod(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    return_type: str | None = Field(default=None, max_length=80)


class VisionClass(BaseModel):
    visual_index: int = Field(ge=1, le=100)
    name: str = Field(min_length=1, max_length=80)
    attributes: list[VisionAttribute] = Field(default_factory=list, max_length=100)
    methods: list[VisionMethod] = Field(default_factory=list, max_length=100)


class VisionRelationship(BaseModel):
    source_index: int = Field(ge=1, le=100)
    target_index: int = Field(ge=1, le=100)
    relationship_type: Literal[
        "association",
        "aggregation",
        "composition",
        "generalization",
        "dependency",
        "association_class",
    ] = "association"
    label: str | None = Field(default=None, max_length=120)
    source_cardinality: str | None = Field(default=None, max_length=20)
    target_cardinality: str | None = Field(default=None, max_length=20)
    association_class_index: int | None = Field(default=None, ge=1, le=100)


class VisionUmlRead(BaseModel):
    classes: list[VisionClass] = Field(default_factory=list, max_length=100)
    relationships: list[VisionRelationship] = Field(default_factory=list, max_length=200)
    unreadable_items: list[str] = Field(default_factory=list, max_length=100)


class VisionUmlReader:
    """Second-pass visual reader for photos that classical OCR cannot transcribe."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
        enabled: bool | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        raw_enabled = os.getenv("OLLAMA_VISION_ENABLED", "true").strip().lower()
        self.enabled = enabled if enabled is not None else raw_enabled in {"1", "true", "yes", "on"}
        self.base_url = validate_ollama_base_url(
            base_url or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        )
        self.model = model or os.getenv("OLLAMA_VISION_MODEL", "qwen3-vl:2b-instruct")
        timeout = timeout_seconds or float(os.getenv("OLLAMA_VISION_TIMEOUT_SECONDS", "900"))
        self._owns_client = client is None
        self.client = client or httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout, connect=3),
            follow_redirects=False,
        )

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def read(
        self,
        image_base64: str,
        detection: ImageUmlDetection,
    ) -> UmlGenerationResponse | None:
        if not self.enabled or not detection.boxes:
            return None
        try:
            if not self._model_is_available():
                return None
            images = self._build_visual_evidence(image_base64, detection)
            visual = self._complete(self._prompt(len(detection.boxes)), images)
            visual = self._refine_uncertain_classes(image_base64, visual, detection)
            return self._validated_response(visual, detection)
        except (
            httpx.HTTPError,
            ValueError,
            ValidationError,
            binascii.Error,
            KeyError,
            TypeError,
        ):
            return None

    def _complete(self, prompt: str, images: list[str]) -> VisionUmlRead:
        response = self.client.post(
            "/api/chat",
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt, "images": images}],
                "stream": False,
                "format": VisionUmlRead.model_json_schema(),
                "options": {
                    "temperature": 0,
                    "num_ctx": 8192,
                    "num_predict": 1400,
                },
                "keep_alive": "10m",
                "think": False,
            },
        )
        if 300 <= response.status_code < 400:
            raise ValueError("Ollama no debe redirigir solicitudes")
        response.raise_for_status()
        content = response.json().get("message", {}).get("content")
        if not isinstance(content, str) or len(content.encode("utf-8")) > 2_000_000:
            raise ValueError("Respuesta visual ausente o demasiado grande")
        return VisionUmlRead.model_validate_json(content)

    def _refine_uncertain_classes(
        self,
        image_base64: str,
        visual: VisionUmlRead,
        detection: ImageUmlDetection,
    ) -> VisionUmlRead:
        unreadable = " ".join(visual.unreadable_items).casefold()
        replacements: dict[int, VisionClass] = {}
        for item in visual.classes:
            if len(item.attributes) > 1 or item.name.casefold() not in unreadable:
                continue
            box_index = item.visual_index - 1
            if box_index not in range(len(detection.boxes)):
                continue
            focused = self._complete(
                self._focused_prompt(item.name),
                self._build_focused_evidence(image_base64, detection.boxes[box_index]),
            )
            if len(focused.classes) != 1:
                continue
            candidate = focused.classes[0].model_copy(update={"visual_index": item.visual_index})
            if len(candidate.attributes) > len(item.attributes):
                replacements[item.visual_index] = candidate
        if not replacements:
            return visual
        refined_names = {
            replacements[index].name.casefold() for index in replacements
        }
        unreadable_items = [
            item
            for item in visual.unreadable_items
            if item.strip().casefold().rstrip("s") not in refined_names
        ]
        return visual.model_copy(
            update={
                "classes": [
                    replacements.get(item.visual_index, item) for item in visual.classes
                ],
                "unreadable_items": unreadable_items,
            }
        )

    @staticmethod
    def _focused_prompt(tentative_name: str) -> str:
        return f"""
Transcribe literalmente una sola caja UML mostrada dos veces: ORIGINAL y CONTRAST. Ambas vistas
son la misma caja. El nombre leido inicialmente fue '{tentative_name}', pero debes verificarlo en
la imagen. Devuelve exactamente una clase con visual_index 1 y relationships vacio.
La primera linea de la caja es el nombre. Cada renglon no vacio entre el primer y segundo separador
horizontal es un atributo, incluso si contiene solo una o dos letras. No omitas signos o renglones
tenues. No inventes texto. Usa data_type null si el tipo no esta escrito explicitamente.
Devuelve solo JSON conforme al esquema.
""".strip()

    def _model_is_available(self) -> bool:
        response = self.client.get("/api/tags")
        if 300 <= response.status_code < 400:
            return False
        response.raise_for_status()
        names = {
            str(item.get("name") or item.get("model"))
            for item in response.json().get("models", [])
            if item.get("name") or item.get("model")
        }
        requested_base = self.model.split(":", 1)[0]
        return any(
            name == self.model
            or (":" not in self.model and name.split(":", 1)[0] == requested_base)
            for name in names
        )

    @staticmethod
    def _prompt(box_count: int) -> str:
        return f"""
Eres un transcriptor visual estricto de diagramas UML de clases fotografiados.
Recibes una lamina con {box_count} recortes ampliados y rotulados BOX 1, BOX 2, ..., BOX
{box_count}. Los rotulos indican el orden de lectura original del diagrama.
Otro detector ya resolvio lineas y multiplicidades; tu unica tarea es transcribir las cajas.

Devuelve JSON que cumpla exactamente el esquema indicado. Reglas obligatorias:
1. Devuelve exactamente {box_count} clases, una por recorte, con visual_index de 1 a {box_count}.
2. Transcribe solo texto realmente visible. No uses ejemplos, dominios frecuentes ni conocimiento
   del mundo para completar nombres, atributos o metodos.
3. Corrige un caracter solo cuando la palabra manuscrita sea visualmente clara (por ejemplo UUID).
4. Si un atributo no muestra tipo, usa null. Si un compartimento esta vacio, devuelve lista vacia.
5. La primera linea es el nombre de clase. Cada renglon manuscrito no vacio entre el primer y el
   segundo separador horizontal es un atributo. No omitas identificadores cortos de una o dos
   letras ni los confundas con los signos de visibilidad UML.
6. No deduzcas tipos por el significado del atributo. data_type debe ser null salvo que el tipo
   aparezca escrito en el mismo renglon despues de ':' u otra separacion explicita.
7. Devuelve relationships como lista vacia; no intentes reconstruir conexiones desde los recortes.
8. No conviertas palabras dudosas en nombres conocidos. Anotalas en unreadable_items.
9. No expliques nada fuera del JSON.
""".strip()

    @staticmethod
    def _build_visual_evidence(
        image_base64: str,
        detection: ImageUmlDetection,
    ) -> list[str]:
        import cv2

        image = _decode_image(image_base64)
        if image is None:
            raise ValueError("OpenCV no esta disponible")
        prepared, _angle = _prepare_image(image)
        crops = []
        for box in detection.boxes:
            margin = max(8, min(box.width, box.height) // 18)
            left = max(0, box.x - margin)
            top = max(0, box.y - margin)
            right = min(prepared.shape[1], box.x + box.width + margin)
            bottom = min(prepared.shape[0], box.y + box.height + margin)
            crop = prepared[top:bottom, left:right]
            if crop.size == 0:
                raise ValueError("Recorte visual vacio")
            enhanced = VisionUmlReader._enhance_handwriting(crop)
            scale = max(1.0, min(5.0, 480 / max(enhanced.shape[1], 1)))
            enlarged = cv2.resize(
                enhanced,
                None,
                fx=scale,
                fy=scale,
                interpolation=cv2.INTER_CUBIC,
            )
            crops.append(enlarged)
        return [VisionUmlReader._encode_image(VisionUmlReader._contact_sheet(crops))]

    @staticmethod
    def _build_focused_evidence(image_base64: str, box) -> list[str]:
        import cv2

        image = _decode_image(image_base64)
        if image is None:
            raise ValueError("OpenCV no esta disponible")
        prepared, _angle = _prepare_image(image)
        margin = max(8, min(box.width, box.height) // 18)
        crop = prepared[
            max(0, box.y - margin) : min(prepared.shape[0], box.y + box.height + margin),
            max(0, box.x - margin) : min(prepared.shape[1], box.x + box.width + margin),
        ]
        if crop.size == 0:
            raise ValueError("Recorte visual vacio")
        scale = max(1.0, min(6.0, 700 / max(crop.shape[1], 1)))
        original = cv2.resize(crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        enhanced = VisionUmlReader._enhance_handwriting(crop)
        enhanced = cv2.resize(enhanced, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        sheet = VisionUmlReader._contact_sheet(
            [original, enhanced], labels=["ORIGINAL", "CONTRAST"]
        )
        return [VisionUmlReader._encode_image(sheet)]

    @staticmethod
    def _contact_sheet(crops: list, labels: list[str] | None = None):
        import cv2
        import numpy as np

        if not crops:
            raise ValueError("No hay recortes visuales")
        crops = [
            cv2.cvtColor(item, cv2.COLOR_GRAY2BGR) if item.ndim == 2 else item
            for item in crops
        ]
        columns = min(3, len(crops))
        padding = 18
        label_height = 38
        cell_width = max(item.shape[1] for item in crops)
        rows = []
        for start in range(0, len(crops), columns):
            row_crops = crops[start : start + columns]
            row_height = max(item.shape[0] for item in row_crops) + label_height
            row = np.full(
                (
                    row_height + padding * 2,
                    cell_width * columns + padding * (columns + 1),
                    3,
                ),
                255,
                dtype=np.uint8,
            )
            for offset, crop in enumerate(row_crops):
                index = start + offset + 1
                left = padding + offset * (cell_width + padding)
                top = padding + label_height
                row[top : top + crop.shape[0], left : left + crop.shape[1]] = crop
                label = labels[index - 1] if labels and index <= len(labels) else f"BOX {index}"
                cv2.putText(
                    row,
                    label,
                    (left, padding + 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.72,
                    (0, 0, 0),
                    2,
                    cv2.LINE_AA,
                )
            rows.append(row)
        sheet_width = max(item.shape[1] for item in rows)
        sheet_height = sum(item.shape[0] for item in rows) + padding * (len(rows) - 1)
        sheet = np.full((sheet_height, sheet_width, 3), 255, dtype=np.uint8)
        top = 0
        for row in rows:
            sheet[top : top + row.shape[0], : row.shape[1]] = row
            top += row.shape[0] + padding
        return sheet

    @staticmethod
    def _enhance_handwriting(crop):
        import cv2
        import numpy as np

        # The minimum RGB channel preserves blue, red, gray and black marker while
        # suppressing whiteboard glare. This is visual preprocessing, not semantic filling.
        minimum_channel = np.min(crop, axis=2).astype(np.uint8)
        ink = 255 - minimum_channel
        background_level = int(np.percentile(ink, 65))
        strengthened = cv2.convertScaleAbs(
            ink,
            alpha=2.2,
            beta=-max(8, background_level),
        )
        strengthened = cv2.morphologyEx(
            strengthened,
            cv2.MORPH_CLOSE,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2)),
        )
        return 255 - strengthened

    @staticmethod
    def _encode_image(image) -> str:
        import cv2

        ok, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 92])
        if not ok:
            raise ValueError("No se pudo preparar la evidencia visual")
        return base64.b64encode(encoded.tobytes()).decode("ascii")

    def _validated_response(
        self,
        visual: VisionUmlRead,
        detection: ImageUmlDetection,
    ) -> UmlGenerationResponse | None:
        expected_indices = set(range(1, len(detection.boxes) + 1))
        received_indices = {item.visual_index for item in visual.classes}
        if len(visual.classes) != len(detection.boxes) or received_indices != expected_indices:
            return None

        ordered = sorted(visual.classes, key=lambda item: item.visual_index)
        names = [self._identifier(item.name, pascal=True) for item in ordered]
        if (
            any(not name or _GENERIC_CLASS.fullmatch(name) for name in names)
            or len({name.casefold() for name in names}) != len(names)
        ):
            return None

        classes = [
            UmlClass(
                name=names[index],
                stereotype="entity",
                attributes=self._attributes(item.attributes),
                methods=self._methods(item.methods),
            )
            for index, item in enumerate(ordered)
        ]
        relationships = self._relationships(visual, detection, names)
        if detection.relationships and not relationships:
            return None

        transcribed_members = sum(len(item.attributes) + len(item.methods) for item in classes)
        confidence = min(
            0.94,
            0.74 + min(transcribed_members, 8) * 0.015 + (0.06 if relationships else 0),
        )
        observations = [
            *detection.observations,
            f"OCR visual multimodal local aplicado con {self.model}.",
            "La lectura semantica fue contrastada con las cajas y conexiones detectadas por OpenCV.",
        ]
        recovered_names = {
            item.name.casefold() for item in classes if item.attributes or item.methods
        }
        unresolved_items = [
            item
            for item in visual.unreadable_items
            if item.strip().casefold().rstrip("s") not in recovered_names
        ]
        if unresolved_items:
            observations.append(
                "Elementos no legibles omitidos: " + ", ".join(unresolved_items[:8]) + "."
            )
        return UmlGenerationResponse(
            classes=classes,
            relationships=relationships,
            confidence=confidence,
            observations=observations,
            knowledge_context=[],
            engine=f"local-offline+ollama-vision:{self.model}",
        )

    @staticmethod
    def _identifier(value: str, *, pascal: bool = False) -> str:
        words = re.findall(r"[A-Za-z0-9]+", value.strip())
        if not words:
            return ""
        compact = "".join(words)
        if not pascal and (
            compact.casefold() == "id"
            or re.fullmatch(r"[1il][d8b]", compact, re.IGNORECASE)
        ):
            return "id"
        if pascal:
            result = "".join(word[:1].upper() + word[1:] for word in words)
        else:
            first, *rest = words
            result = first[:1].lower() + first[1:] + "".join(
                word[:1].upper() + word[1:] for word in rest
            )
        return result if _IDENTIFIER.fullmatch(result) else ""

    def _attributes(self, values: list[VisionAttribute]) -> list[UmlAttribute]:
        result: list[UmlAttribute] = []
        seen: set[str] = set()
        for value in values:
            name = self._identifier(value.name)
            if not name or name.casefold() in seen:
                continue
            raw_type = (value.data_type or "").strip()
            if raw_type.casefold() in {"", "null", "none", "n/a", "unknown"}:
                raw_type = self._inferred_type(name)
            data_type = _normalize_type(raw_type)
            result.append(
                UmlAttribute(
                    name=name,
                    data_type=data_type or "String",
                    is_required=name.casefold() == "id",
                )
            )
            seen.add(name.casefold())
        return result

    def _methods(self, values: list[VisionMethod]) -> list[UmlMethod]:
        result: list[UmlMethod] = []
        seen: set[str] = set()
        for value in values:
            name = self._identifier(value.name)
            if not name or name.casefold() in seen:
                continue
            result.append(
                UmlMethod(name=name, return_type=_normalize_type(value.return_type or "void"))
            )
            seen.add(name.casefold())
        return result

    @staticmethod
    def _inferred_type(name: str) -> str:
        normalized = name.casefold()
        if normalized == "id" or normalized.endswith("id"):
            return "UUID"
        if normalized.startswith("fecha"):
            return "Date"
        if normalized in {"precio", "total", "monto", "saldo"}:
            return "Decimal"
        if normalized in {"stock", "cantidad", "edad"}:
            return "Integer"
        return "String"

    def _relationships(
        self,
        visual: VisionUmlRead,
        detection: ImageUmlDetection,
        names: list[str],
    ) -> list[UmlRelationship]:
        index_by_detected_name = {
            item.name.casefold(): index
            for index, item in enumerate(detection.classes, start=1)
        }
        visual_by_pair = {
            (item.source_index, item.target_index): item for item in visual.relationships
        }
        relationships: list[UmlRelationship] = []

        for geometric in detection.relationships:
            source_index = index_by_detected_name.get(geometric.source.casefold())
            target_index = index_by_detected_name.get(geometric.target.casefold())
            if not source_index or not target_index or source_index == target_index:
                continue
            semantic = visual_by_pair.get((source_index, target_index)) or visual_by_pair.get(
                (target_index, source_index)
            )
            association_index = index_by_detected_name.get(
                (geometric.association_class_name or "").casefold()
            )
            metadata = {}
            if association_index:
                metadata["association_class_name"] = names[association_index - 1]
            relationships.append(
                UmlRelationship(
                    source=names[source_index - 1],
                    target=names[target_index - 1],
                    relationship_type=(
                        "association"
                        if geometric.association_class_name
                        else (semantic.relationship_type if semantic else geometric.relationship_type)
                    ),
                    label=semantic.label if semantic else geometric.label,
                    source_cardinality=self._cardinality(
                        geometric.source_cardinality
                        or (semantic.source_cardinality if semantic else None)
                    ),
                    target_cardinality=self._cardinality(
                        geometric.target_cardinality
                        or (semantic.target_cardinality if semantic else None)
                    ),
                    metadata_json=metadata,
                )
            )

        if relationships:
            return relationships

        for item in visual.relationships:
            if (
                item.source_index not in range(1, len(names) + 1)
                or item.target_index not in range(1, len(names) + 1)
                or item.source_index == item.target_index
            ):
                continue
            metadata = {}
            if item.association_class_index in range(1, len(names) + 1):
                metadata["association_class_name"] = names[item.association_class_index - 1]
            relationships.append(
                UmlRelationship(
                    source=names[item.source_index - 1],
                    target=names[item.target_index - 1],
                    relationship_type=(
                        "association" if item.relationship_type == "association_class" else item.relationship_type
                    ),
                    label=item.label,
                    source_cardinality=self._cardinality(item.source_cardinality),
                    target_cardinality=self._cardinality(item.target_cardinality),
                    metadata_json=metadata,
                )
            )
        return relationships

    @staticmethod
    def _cardinality(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().replace(" ", "").replace("n", "*").replace("N", "*")
        return normalized if normalized in _CARDINALITIES else None
