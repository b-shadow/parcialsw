import asyncio
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from ai_engine.providers.errores import ErrorContextoDemasiadoGrande

from app.modules.asistente_proyecto.schemas.esquemas_asistente import ContextoSolicitado
from app.modules.asistente_proyecto.services.constructor_contexto import ConstructorContextoProyecto


def test_project_context_enforces_budget_instead_of_silently_ignoring_it(monkeypatch) -> None:
    db = Mock()
    db.get.return_value = None
    constructor = ConstructorContextoProyecto(db)
    constructor.assistant.listar_acciones = Mock(return_value=[])
    constructor.assistant.listar_recomendaciones = Mock(
        return_value=[
            SimpleNamespace(
                id=uuid4(),
                title=f"Recomendación {index}",
                description="x" * 2000,
                category="modelado",
                severity="media",
                references_json=[],
            )
            for index in range(50)
        ]
    )

    async def sin_memoria(*_args):
        return None

    monkeypatch.setattr(constructor, "_memoria_conversaciones_proyecto", sin_memoria)

    with pytest.raises(ErrorContextoDemasiadoGrande):
        asyncio.run(
            constructor.construir(
                project=SimpleNamespace(id=uuid4(), name="Proyecto", description="Prueba"),
                member=SimpleNamespace(project_role="EDITOR"),
                user_id=uuid4(),
                conversation=SimpleNamespace(id=uuid4()),
                settings=SimpleNamespace(require_confirmation=True),
                diagram_id=None,
                requested=ContextoSolicitado(
                    include_diagram=False,
                    include_recent_messages=False,
                    include_project_versions=False,
                ),
            )
        )
