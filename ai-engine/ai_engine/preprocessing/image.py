from ai_engine.preprocessing.text import normalize_text


def normalize_image_description(
    description: str | None,
    image_base64: str | None = None,
    file_name: str | None = None,
) -> str:
    if description:
        return normalize_text(description)
    if file_name:
        stem = file_name.rsplit(".", maxsplit=1)[0].replace("_", " ").replace("-", " ")
        return normalize_text(f"diagrama uml con {stem}")
    if image_base64:
        return "diagrama uml con clase usuario clase servicio relacion"
    return "diagrama uml con clase importada"
