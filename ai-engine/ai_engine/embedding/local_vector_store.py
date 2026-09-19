from dataclasses import dataclass
from math import sqrt
from re import findall


@dataclass(frozen=True)
class KnowledgeItem:
    topic: str
    content: str
    tags: list[str]


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in findall(r"[a-zA-ZáéíóúÁÉÍÓÚñÑ0-9_]+", text)]


def _vector(text: str) -> dict[str, float]:
    vector: dict[str, float] = {}
    for token in _tokens(text):
        vector[token] = vector.get(token, 0.0) + 1.0
    return vector


def _cosine(left: dict[str, float], right: dict[str, float]) -> float:
    numerator = sum(value * right.get(token, 0.0) for token, value in left.items())
    left_norm = sqrt(sum(value * value for value in left.values()))
    right_norm = sqrt(sum(value * value for value in right.values()))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


class LocalVectorStore:
    def __init__(self, items: list[KnowledgeItem] | None = None) -> None:
        self.items = items or _default_knowledge()
        self._vectors = [_vector(f"{item.topic} {item.content} {' '.join(item.tags)}") for item in self.items]

    def search(self, query: str, limit: int = 3) -> list[KnowledgeItem]:
        query_vector = _vector(query)
        scored = [
            (_cosine(query_vector, item_vector), item)
            for item_vector, item in zip(self._vectors, self.items, strict=True)
        ]
        return [item for score, item in sorted(scored, key=lambda value: value[0], reverse=True)[:limit] if score > 0]


def _default_knowledge() -> list[KnowledgeItem]:
    return [
        KnowledgeItem(
            topic="diagramas de clases",
            content="Una clase UML debe tener nombre singular, atributos tipados y operaciones coherentes.",
            tags=["uml", "clase", "atributos", "metodos"],
        ),
        KnowledgeItem(
            topic="relaciones UML",
            content="Usar asociacion para colaboracion, composicion para ciclo de vida contenido y herencia para especializacion.",
            tags=["association", "composition", "inheritance", "cardinalidad"],
        ),
        KnowledgeItem(
            topic="spring boot",
            content="El backend generado mantiene capas entity, repository, service, controller y dto con validaciones.",
            tags=["java", "spring", "rest", "postgresql"],
        ),
        KnowledgeItem(
            topic="flutter",
            content="El frontend generado organiza modelos, servicios, providers, rutas y formularios por entidad.",
            tags=["dart", "provider", "mobile", "crud"],
        ),
        KnowledgeItem(
            topic="calidad de diseno",
            content="Un modelo mantenible evita clases vacias, relaciones duplicadas y nombres ambiguos.",
            tags=["cohesion", "acoplamiento", "validacion"],
        ),
    ]
