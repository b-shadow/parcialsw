from pydantic import BaseModel, Field

from ai_engine.datasets import DatasetExample
from ai_engine.services.contracts import UmlGenerationResponse


class EvaluationReport(BaseModel):
    dataset_size: int
    class_precision: float = Field(ge=0, le=1)
    relationship_precision: float = Field(ge=0, le=1)
    average_score: float = Field(ge=0, le=1)
    offline: bool = True


def evaluate_generation(examples: list[DatasetExample], outputs: list[UmlGenerationResponse]) -> EvaluationReport:
    if not examples or not outputs:
        return EvaluationReport(dataset_size=0, class_precision=0, relationship_precision=0, average_score=0)

    class_scores: list[float] = []
    relationship_scores: list[float] = []
    for example, output in zip(examples, outputs, strict=False):
        expected_classes = {name.lower() for name in example.expected_classes}
        generated_classes = {uml_class.name.lower() for uml_class in output.classes}
        expected_relations = {
            (source.lower(), target.lower()) for source, target, _ in example.expected_relationships
        }
        generated_relations = {
            (relationship.source.lower(), relationship.target.lower())
            for relationship in output.relationships
        }
        class_scores.append(len(expected_classes & generated_classes) / max(len(expected_classes), 1))
        relationship_scores.append(
            len(expected_relations & generated_relations) / max(len(expected_relations), 1)
        )

    class_precision = sum(class_scores) / len(class_scores)
    relationship_precision = sum(relationship_scores) / len(relationship_scores)
    return EvaluationReport(
        dataset_size=len(examples),
        class_precision=round(class_precision, 4),
        relationship_precision=round(relationship_precision, 4),
        average_score=round((class_precision + relationship_precision) / 2, 4),
    )
