import re
import unicodedata

STOPWORDS = {
    "crear",
    "crea",
    "sistema",
    "plataforma",
    "aplicacion",
    "app",
    "de",
    "del",
    "la",
    "el",
    "los",
    "las",
    "un",
    "una",
    "con",
    "para",
    "y",
    "que",
    "permita",
    "gestionar",
    "gestion",
}


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", ascii_text.lower()).strip()


def extract_domain_terms(text: str) -> list[str]:
    normalized = normalize_text(text)
    fragments = re.split(r",|;|\.|\by\b|\bcon\b|\bpara\b", normalized)
    terms: list[str] = []
    for fragment in fragments:
        words = [word for word in re.findall(r"[a-zA-Z0-9_]+", fragment) if word not in STOPWORDS]
        if not words:
            continue
        term = words[-1]
        class_name = term[:1].upper() + term[1:]
        if class_name not in terms:
            terms.append(class_name)
    return terms
