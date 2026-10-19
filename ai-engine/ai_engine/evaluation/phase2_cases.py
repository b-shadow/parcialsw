from ai_engine.orchestration.intent_classifier import IntentClassifier

PHASE2_CASES = [
    ("explica este diagrama", {"explain_uml"}),
    ("revisa y valida el modelo", {"review_uml", "validate_uml"}),
    ("agrega Cliente y relaciona con Pedido", {"modify_uml"}),
    ("genera backend Spring Boot y frontend Flutter", {"prepare_generation"}),
    ("resume el proyecto y recomienda mejoras", {"summarize_project", "recommend"}),
    ("especifica el metodo inscribir", {"specify_method"}),
]


def evaluate_classifier(classifier: IntentClassifier | None = None) -> dict[str, float | int]:
    engine = classifier or IntentClassifier()
    exact = 0
    intent_hits = 0
    expected_total = 0
    for text, expected in PHASE2_CASES:
        actual = {item.name for item in engine.classify(text)}
        exact += int(actual == expected)
        intent_hits += len(actual & expected)
        expected_total += len(expected)
    return {
        "cases": len(PHASE2_CASES),
        "exact_match": exact / len(PHASE2_CASES),
        "intent_recall": intent_hits / expected_total,
    }
