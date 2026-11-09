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
    "datos",
    "diagrama",
    "diagramas",
    "uml",
}


def normalizar_texto(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", ascii_text.lower()).strip()


def extraer_terminos_dominio(text: str) -> list[str]:
    normalized = normalizar_texto(text)
    fragments = re.split(r",|;|\.|\by\b|\bcon\b|\bpara\b", normalized)
    terms: list[str] = []
    for fragment in fragments:
        words = [word for word in re.findall(r"[a-zA-Z0-9_]+", fragment) if word not in STOPWORDS]
        if not words:
            continue
        term = words[-1]
        # Los sustantivos enumerados suelen venir en plural; una clase UML
        # representa el concepto singular. No altera nombres terminados en s
        # que no parecen plurales regulares.
        if len(term) > 5 and term.endswith(("nes", "res")) and term[-4] in "aeiou":
            term = term[:-2]
        elif len(term) > 4 and term.endswith("s") and term[-2] in "aeiou":
            term = term[:-1]
        class_name = term[:1].upper() + term[1:]
        if class_name not in terms:
            terms.append(class_name)
    return terms
