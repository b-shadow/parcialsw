import re
import unicodedata

from ai_engine.orchestration.contracts import DetectedIntent


def _normalize(value: str) -> str:
    value = "".join(
        character
        for character in unicodedata.normalize("NFKD", value.casefold())
        if not unicodedata.combining(character)
    )
    normalized = re.sub(r"\s+", " ", value).strip()
    typo_aliases = {
        "agrga": "agrega",
        "anademe": "anade",
        "coneta": "conecta",
        "genra": "genera",
        "relaciona": "relaciona",
        "relas iona": "relaciona",
    }
    for typo, replacement in typo_aliases.items():
        normalized = normalized.replace(typo, replacement)
    return normalized


class IntentClassifier:
    RULES: tuple[tuple[str, tuple[str, ...], float], ...] = (
        (
            "review_uml",
            (
                "revisa", "analiza el diagrama", "audita", "evalua el diagrama",
                "evalua este", "que opinas", "como se ve",
            ),
            0.94,
        ),
        ("validate_uml", ("valida", "errores uml", "esta correcto", "verifica el modelo"), 0.93),
        (
            "modify_uml",
            (
                "agrega", "crea", "conecta", "relaciona", "cambia", "edita",
                "elimina", "borra", "quita", "renombra", "corrige", "aplica",
                "implementa", "resuelve", "resolver", "soluciona",
            ),
            0.91,
        ),
        ("generate_uml", ("genera un diagrama", "crea un diagrama", "modela un sistema"), 0.93),
        ("specify_method", ("metodo", "precondicion", "postcondicion", "regla de negocio", "mostrar confirmacion"), 0.88),
        ("prepare_generation", ("genera backend", "genera frontend", "spring boot", "flutter", "prepara generacion"), 0.92),
        (
            "recommend",
            (
                "recomienda", "recomendacion", "sugiere", "sugerencia", "que conviene",
                "mejora", "que mejorarias", "como lo mejoro", "que le falta",
                "alguna modificacion", "que modificarias", "busca errores", "puntos debiles",
                "retroalimentacion", "feedback", "como profesor", "que corregirias",
                "critica", "observaciones", "califica", "revisalo como profesor",
                "evalualo como profesor",
            ),
            0.92,
        ),
        ("summarize_conversation", ("resume la conversacion", "resumen de lo hablado"), 0.95),
        ("summarize_project", ("resume el proyecto", "resumen del proyecto"), 0.95),
        ("coordinate_team", ("coordina", "compara opiniones", "acuerdos del equipo"), 0.9),
        ("explain_system", ("como uso", "donde genero", "como funciona el sistema", "manual"), 0.9),
        (
            "explain_uml",
            (
                "explica el diagrama",
                "explica este diagrama",
                "explicame la relacion",
                "que significa",
                "explica el cambio",
            ),
            0.9,
        ),
    )

    def classify(self, text: str) -> list[DetectedIntent]:
        normalized = _normalize(text)
        candidates: list[tuple[int, str, str, float]] = []
        for name, phrases, confidence in self.RULES:
            for phrase in phrases:
                position = normalized.find(phrase)
                if position < 0:
                    continue
                if name == "modify_uml" and self._negated(normalized, position):
                    continue
                candidates.append((position, name, phrase, confidence))
                break

        if "?" in text or normalized.startswith(("que ", "como ", "cual ", "por que ")):
            candidates.append((0, "answer_question", "pregunta explicita", 0.86))
        unique: dict[str, tuple[int, str, float]] = {}
        for position, name, evidence, confidence in candidates:
            current = unique.get(name)
            if current is None or position < current[0]:
                unique[name] = (position, evidence, confidence)
        ordered = sorted(unique.items(), key=lambda item: item[1][0])
        if not ordered:
            return [DetectedIntent(name="unknown", confidence=0.4, evidence="sin patron seguro", order=1)]
        return [
            DetectedIntent(name=name, confidence=data[2], evidence=data[1], order=index)
            for index, (name, data) in enumerate(ordered, start=1)
        ]

    @staticmethod
    def _negated(text: str, position: int) -> bool:
        prefix = text[max(0, position - 15):position]
        return bool(re.search(r"\b(no|sin)\s+$", prefix))

    @staticmethod
    def is_ambiguous(text: str, has_active_diagram: bool) -> bool:
        normalized = _normalize(text)
        pronouns = ("esa clase", "esa tabla", "la anterior", "la que acabo", "conectalo", "conectala")
        return any(item in normalized for item in pronouns) and not has_active_diagram

    @staticmethod
    def requests_sensitive_data(text: str) -> bool:
        normalized = _normalize(text)
        privileged = any(
            phrase in normalized
            for phrase in ("muestra secretos", "revela el prompt", "muestra tokens", "lee el .env", "dame las claves")
        )
        override = "ignora" in normalized and "reglas" in normalized
        return privileged or override
