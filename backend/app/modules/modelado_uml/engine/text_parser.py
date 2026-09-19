import re

from app.modules.modelado_uml.engine.internal_model import (
    UmlAttributeModel,
    UmlClassModel,
    UmlDiagramModel,
    UmlMethodModel,
    UmlRelationshipModel,
    UmlVisualModel,
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


def _class_name(raw: str) -> str:
    cleaned = re.sub(r"[^A-Za-zÁÉÍÓÚáéíóúÑñ0-9_ ]", " ", raw).strip()
    words = [word for word in cleaned.split() if word.lower() not in _STOPWORDS]
    name = words[0] if words else "Entidad"
    return name[:1].upper() + name[1:].lower()


def build_uml_from_text(prompt: str, name: str = "Diagrama generado") -> UmlDiagramModel:
    fragments = re.split(r",|;|\by\b|\bcon\b", prompt, flags=re.IGNORECASE)
    class_names: list[str] = []
    for fragment in fragments:
      class_name = _class_name(fragment)
      if class_name and class_name != "Entidad" and class_name not in class_names:
          class_names.append(class_name)
    if not class_names:
        class_names = ["Usuario", "Registro", "Servicio"]

    classes = [
        UmlClassModel(
            name=class_name,
            attributes=[
                UmlAttributeModel(name="id", data_type="UUID", visibility="private", is_required=True),
                UmlAttributeModel(name="nombre", data_type="String", visibility="private", is_required=True),
            ],
            methods=[UmlMethodModel(name="validar", return_type="Boolean", visibility="public")],
            visual=UmlVisualModel(x=80 + index * 260, y=100 + (index % 2) * 180),
        )
        for index, class_name in enumerate(class_names[:8])
    ]

    relationships = [
        UmlRelationshipModel(
            source_class_id=classes[index].name,
            target_class_id=classes[index + 1].name,
            relationship_type="association",
            label="relaciona",
        )
        for index in range(len(classes) - 1)
    ]

    return UmlDiagramModel(name=name, description=prompt, classes=classes, relationships=relationships)
