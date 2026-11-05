import re
import unicodedata

from app.modules.modelado_uml.engine.modelo_interno import (
    ModeloAtributoUML,
    ModeloClaseUML,
    ModeloDiagramaUML,
    ModeloMetodoUML,
    ModeloRelacionUML,
    ModeloVisualUML,
)

_STOPWORDS = {
    "sistema",
    "crear",
    "crea",
    "con",
    "de",
    "del",
    "la",
    "el",
    "los",
    "las",
    "y",
    "para",
    "gestion",
    "gestionar",
}


def _nombre_clase(raw: str) -> str:
    cleaned = re.sub(r"[^A-Za-zÁÉÍÓÚáéíóúÑñ0-9_ ]", " ", raw).strip()
    words = [word for word in cleaned.split() if word.lower() not in _STOPWORDS]
    name = words[0] if words else "Entidad"
    return name[:1].upper() + name[1:].lower()


def _normalizar_texto(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", ascii_text.lower()).strip()


def _a_pascal_case(value: str) -> str:
    words = [word for word in re.findall(r"[a-zA-Z0-9_]+", value) if word]
    return "".join(word[:1].upper() + word[1:] for word in words)


def _a_camel_case(value: str) -> str:
    pascal = _a_pascal_case(value)
    return pascal[:1].lower() + pascal[1:] if pascal else ""


def _normalizar_tipo(raw_type: str) -> str:
    normalized = _normalizar_texto(raw_type).replace(" ", "")
    type_map = {
        "uuid": "UUID",
        "string": "String",
        "str": "String",
        "texto": "String",
        "integer": "Integer",
        "int": "Integer",
        "entero": "Integer",
        "long": "Long",
        "double": "Double",
        "decimal": "Double",
        "date": "Date",
        "fecha": "Date",
        "boolean": "Boolean",
        "bool": "Boolean",
    }
    return type_map.get(normalized, _a_pascal_case(normalized) or "String")


def _clase_unica_explicita_desde_texto(prompt: str, name: str) -> ModeloDiagramaUML | None:
    normalized = _normalizar_texto(prompt)
    if "clase" not in normalized or "atributo" not in normalized:
        return None

    class_match = re.search(
        r"\bclase\s+(?:llamada|nombrada|denominada|con\s+nombre)?\s*([a-zA-Z][a-zA-Z0-9_]*)",
        normalized,
    )
    class_name = "Entidad"
    if class_match and class_match.group(1) not in {"con", "que", "para", "atributo", "atributos"}:
        class_name = _a_pascal_case(class_match.group(1))

    attributes_section = normalized.split("atributos", maxsplit=1)[-1]
    pattern = re.compile(
        r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?::|que\s+es|de\s+tipo|tipo|es)\s*([a-zA-Z_][a-zA-Z0-9_]*)"
    )
    attributes: list[ModeloAtributoUML] = []
    seen: set[str] = set()
    for raw_name, raw_type in pattern.findall(attributes_section):
        attribute_name = _a_camel_case(raw_name)
        if not attribute_name or attribute_name.lower() in seen:
            continue
        attributes.append(
            ModeloAtributoUML(
                name=attribute_name,
                data_type=_normalizar_tipo(raw_type),
                visibility="private",
                is_required=attribute_name == "id",
            )
        )
        seen.add(attribute_name.lower())
    if not attributes:
        return None

    return ModeloDiagramaUML(
        name=name,
        description=prompt,
        classes=[
            ModeloClaseUML(
                name=class_name,
                attributes=attributes,
                methods=[],
                visual=ModeloVisualUML(x=100, y=100),
            )
        ],
        relationships=[],
    )


def construir_uml_desde_texto(prompt: str, name: str = "Diagrama generado") -> ModeloDiagramaUML:
    explicit_model = _clase_unica_explicita_desde_texto(prompt, name)
    if explicit_model:
        return explicit_model

    fragments = re.split(r",|;|\by\b|\bcon\b", prompt, flags=re.IGNORECASE)
    class_names: list[str] = []
    for fragment in fragments:
      class_name = _nombre_clase(fragment)
      if class_name and class_name != "Entidad" and class_name not in class_names:
          class_names.append(class_name)
    if not class_names:
        class_names = ["Usuario", "Registro", "Servicio"]

    classes = [
        ModeloClaseUML(
            name=class_name,
            attributes=[
                ModeloAtributoUML(name="id", data_type="UUID", visibility="private", is_required=True),
                ModeloAtributoUML(name="nombre", data_type="String", visibility="private", is_required=True),
            ],
            methods=[ModeloMetodoUML(name="validar", return_type="Boolean", visibility="public")],
            visual=ModeloVisualUML(x=80 + index * 260, y=100 + (index % 2) * 180),
        )
        for index, class_name in enumerate(class_names[:8])
    ]

    relationships = [
        ModeloRelacionUML(
            source_class_id=classes[index].name,
            target_class_id=classes[index + 1].name,
            relationship_type="association",
            label="relaciona",
        )
        for index in range(len(classes) - 1)
    ]

    return ModeloDiagramaUML(name=name, description=prompt, classes=classes, relationships=relationships)
