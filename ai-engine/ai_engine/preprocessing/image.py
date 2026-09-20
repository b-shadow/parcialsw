from ai_engine.preprocessing.text import normalize_text


GENERIC_IMAGE_NAME_MARKERS = (
    "whatsapp image",
    "img ",
    "image ",
    "photo ",
    "screenshot",
    "captura",
)


def _has_meaningful_filename_terms(normalized_stem: str) -> bool:
    if any(marker in normalized_stem for marker in GENERIC_IMAGE_NAME_MARKERS):
        return False
    words = normalized_stem.split()
    alphabetic_words = [word for word in words if any(character.isalpha() for character in word)]
    if not alphabetic_words:
        return False
    numeric_words = [word for word in words if word.isdigit()]
    return len(alphabetic_words) >= 2 and len(numeric_words) <= len(alphabetic_words)


def normalize_image_description(
    description: str | None,
    image_base64: str | None = None,
    file_name: str | None = None,
) -> str:
    if description:
        return normalize_text(description)
    if file_name:
        stem = file_name.rsplit(".", maxsplit=1)[0].replace("_", " ").replace("-", " ")
        normalized_stem = normalize_text(stem)
        if _has_meaningful_filename_terms(normalized_stem):
            return normalized_stem
    if image_base64:
        return "diagrama uml de clases dibujado en imagen"
    return "diagrama uml con clase importada"
