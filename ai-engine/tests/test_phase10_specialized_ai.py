from ai_engine.services import LocalAIService
from ai_engine.services.contracts import (
    CodeGenerationRequest,
    KnowledgeSearchRequest,
    UmlGenerationRequest,
    UmlModificationRequest,
)


def test_specialized_text_generation_uses_dataset_and_rag() -> None:
    service = LocalAIService()

    response = service.text_to_uml(
        UmlGenerationRequest(prompt="Sistema de ventas con clientes, pedidos, productos y facturas")
    )

    class_names = {uml_class.name for uml_class in response.classes}
    assert {"Cliente", "Pedido", "Producto", "Factura"}.issubset(class_names)
    assert response.knowledge_context
    assert response.engine == "local-offline"


def test_local_knowledge_dataset_training_and_evaluation_are_available() -> None:
    service = LocalAIService()

    knowledge = service.search_knowledge(KnowledgeSearchRequest(query="validacion UML relaciones"))
    dataset = service.dataset_summary()
    training = service.training_plan()
    evaluation = service.evaluate_offline()

    assert knowledge
    assert dataset.records >= 4
    assert "QLoRA" in training.techniques
    assert evaluation.offline is True
    assert evaluation.average_score > 0


def test_uml_modification_and_code_guidance_are_offline() -> None:
    service = LocalAIService()
    base = service.text_to_uml(UmlGenerationRequest(prompt="Sistema con cliente y pedido"))

    modified = service.modify_uml(
        UmlModificationRequest(
            instruction="Agregar autenticacion al sistema",
            classes=base.classes,
            relationships=base.relationships,
        )
    )
    code = service.generate_code_guidance(
        CodeGenerationRequest(
            classes=modified.classes,
            relationships=modified.relationships,
            target="spring_boot",
        )
    )

    assert any(uml_class.name == "Usuario" for uml_class in modified.classes)
    assert modified.changes
    assert "controller" in code.architecture
    assert code.engine == "local-offline"
