"""Pruebas de la IA consciente del equipo y coordinación de integrantes (V2.2)."""

from datetime import UTC, datetime
from uuid import uuid4

from ai_engine.context.contracts import (
    ActorContext,
    AiProjectContext,
    ContextConstraints,
    ProjectContext,
    TeamActivityItem,
)
from ai_engine.orchestration.intent_classifier import IntentClassifier
from ai_engine.providers.rule_engine_provider import RuleEngineProvider


def _base_context() -> AiProjectContext:
    return AiProjectContext(
        project=ProjectContext(
            id=uuid4(),
            name="Sistema de Ventas",
            description="Proyecto colaborativo",
        ),
        actor=ActorContext(
            id=uuid4(),
            display_name="Carlos",
            project_role="EDITOR",
            permissions=["diagrams.edit", "ai.prompt"],
        ),
        constraints=ContextConstraints(),
    )


def test_classify_que_hizo_cada_uno_detects_coordinate_team() -> None:
    classifier = IntentClassifier()
    intents = classifier.classify("¿Qué hizo cada uno?")
    assert intents, "Debe detectar al menos una intención"
    assert intents[0].name == "coordinate_team"
    assert intents[0].confidence >= 0.9

    # Variaciones de preguntas del equipo
    variations = [
        "quien cambio las clases",
        "quien modifico el modelo",
        "resumen del equipo",
        "que esta haciendo cada uno",
        "reparte las tareas",
        "organiza el trabajo",
    ]
    for query in variations:
        detected = classifier.classify(query)
        names = [item.name for item in detected]
        assert "coordinate_team" in names, f"'{query}' debe detectar coordinate_team"


def test_rule_engine_names_both_members_and_their_actions() -> None:
    context = _base_context()
    context.team_activity = [
        TeamActivityItem(
            user_id=uuid4(),
            display_name="Ana",
            actions=["creó Producto y Categoria", "relacionó Producto con Categoria"],
            last_at=datetime.now(UTC),
        ),
        TeamActivityItem(
            user_id=uuid4(),
            display_name="Beto",
            actions=["creó Factura", "agregó atributo total"],
            last_at=datetime.now(UTC),
        ),
    ]

    provider = RuleEngineProvider()
    intents = IntentClassifier().classify("¿Qué hizo cada uno?")
    result = provider.complete("¿Qué hizo cada uno?", context, intents)

    assert "Ana" in result.answer
    assert "creó Producto y Categoria" in result.answer
    assert "relacionó Producto con Categoria" in result.answer
    assert "Beto" in result.answer
    assert "creó Factura" in result.answer


def test_two_members_touching_same_class_suggests_coordination() -> None:
    context = _base_context()
    context.team_activity = [
        TeamActivityItem(
            user_id=uuid4(),
            display_name="Ana",
            actions=["creó Producto y Categoria"],
            last_at=datetime.now(UTC),
        ),
        TeamActivityItem(
            user_id=uuid4(),
            display_name="Beto",
            actions=["modificó Producto y agregó precio"],
            last_at=datetime.now(UTC),
        ),
    ]

    provider = RuleEngineProvider()
    intents = IntentClassifier().classify("¿Qué hizo cada uno?")
    result = provider.complete("¿Qué hizo cada uno?", context, intents)

    # Debe contener sugerencia de coordinación
    lower_answer = result.answer.lower()
    assert "coordin" in lower_answer or "repart" in lower_answer
    assert "producto" in lower_answer


def test_ai_project_context_without_team_activity_backwards_compatible() -> None:
    # Valida compatibilidad hacia atrás cuando no se pasa team_activity
    context = _base_context()
    assert context.team_activity == []

    # El motor de reglas responde apropiadamente si está vacío
    provider = RuleEngineProvider()
    intents = IntentClassifier().classify("¿Qué hizo cada uno?")
    result = provider.complete("¿Qué hizo cada uno?", context, intents)
    assert "no hay actividad" in result.answer.lower()
