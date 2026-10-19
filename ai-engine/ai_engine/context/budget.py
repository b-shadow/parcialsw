import json

from pydantic import BaseModel

from ai_engine.context.contracts import AiProjectContext
from ai_engine.providers.errors import ContextTooLargeError


class ContextBudgetResult(BaseModel):
    context: AiProjectContext
    chars: int
    reduced: bool
    removed_messages: int = 0
    removed_versions: int = 0


class ContextBudget:
    def __init__(self, max_chars: int = 50000) -> None:
        if max_chars < 2000:
            raise ValueError("El presupuesto de contexto minimo es 2000 caracteres")
        self.max_chars = max_chars

    def apply(self, context: AiProjectContext) -> ContextBudgetResult:
        candidate = context.model_copy(deep=True)
        initial_messages = len(candidate.recent_messages)
        initial_versions = len(candidate.available_versions)

        while self._size(candidate) > self.max_chars and candidate.available_versions:
            candidate.available_versions.pop()
        while self._size(candidate) > self.max_chars and candidate.recent_messages:
            candidate.recent_messages.pop(0)
        if self._size(candidate) > self.max_chars and candidate.active_diagram:
            for uml_class in candidate.active_diagram.classes:
                if isinstance(uml_class, dict):
                    uml_class.pop("metadata_json", None)
                    uml_class.pop("description", None)
            for relation in candidate.active_diagram.relationships:
                if isinstance(relation, dict):
                    relation.pop("metadata_json", None)
        if self._size(candidate) > self.max_chars:
            raise ContextTooLargeError("El proyecto excede el presupuesto aun sin metadatos secundarios")
        reduced = (
            len(candidate.recent_messages) != initial_messages
            or len(candidate.available_versions) != initial_versions
            or candidate != context
        )
        candidate.context_reduced = reduced
        return ContextBudgetResult(
            context=candidate,
            chars=self._size(candidate),
            reduced=reduced,
            removed_messages=initial_messages - len(candidate.recent_messages),
            removed_versions=initial_versions - len(candidate.available_versions),
        )

    @staticmethod
    def _size(context: AiProjectContext) -> int:
        return len(json.dumps(context.model_dump(mode="json"), ensure_ascii=False))
