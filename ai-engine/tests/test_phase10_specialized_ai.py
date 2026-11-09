from ai_engine.services import ServicioIALocal
from ai_engine.services.contratos import (
    SolicitudBusquedaConocimiento,
    SolicitudGeneracionCodigo,
    SolicitudGeneracionUML,
    SolicitudModificacionUML,
)


def test_specialized_text_generation_uses_dataset_and_rag() -> None:
    service = ServicioIALocal()

    response = service.texto_a_uml(
        SolicitudGeneracionUML(prompt="Sistema de ventas con clientes, pedidos, productos y facturas")
    )

    class_names = {uml_class.name for uml_class in response.classes}
    assert {"Cliente", "Pedido", "Producto", "Factura"}.issubset(class_names)
    assert response.knowledge_context
    assert response.engine == "local-offline"


def test_sales_description_keeps_only_named_concepts_without_generic_members() -> None:
    response = ServicioIALocal().texto_a_uml(
        SolicitudGeneracionUML(prompt="Sistema de ventas con clientes, productos, pedidos y pagos")
    )

    names = {item.name for item in response.classes}
    assert names == {"Venta", "Cliente", "Producto", "Pedido", "Pago"}
    assert all(not item.attributes and not item.methods for item in response.classes)
    assert {(item.source, item.target) for item in response.relationships} == {
        ("Cliente", "Pedido"),
        ("Pedido", "Producto"),
        ("Pedido", "Pago"),
    }
    assert all(
        item.source_cardinality is None and item.target_cardinality is None
        for item in response.relationships
    )


def test_local_knowledge_dataset_training_and_evaluation_are_available() -> None:
    service = ServicioIALocal()

    knowledge = service.buscar_conocimiento(SolicitudBusquedaConocimiento(query="validacion UML relaciones"))
    dataset = service.resumen_datos()
    training = service.plan_entrenamiento()
    evaluation = service.evaluar_sin_conexion()

    assert knowledge
    assert dataset.records >= 4
    assert "QLoRA" in training.techniques
    assert evaluation.offline is True
    assert evaluation.average_score > 0


def test_uml_modification_and_code_guidance_are_offline() -> None:
    service = ServicioIALocal()
    base = service.texto_a_uml(SolicitudGeneracionUML(prompt="Sistema con cliente y pedido"))

    modified = service.modificar_uml(
        SolicitudModificacionUML(
            instruction="Agregar autenticacion al sistema",
            classes=base.classes,
            relationships=base.relationships,
        )
    )
    code = service.generar_orientacion_codigo(
        SolicitudGeneracionCodigo(
            classes=modified.classes,
            relationships=modified.relationships,
            target="spring_boot",
        )
    )

    assert any(uml_class.name == "Usuario" for uml_class in modified.classes)
    assert modified.changes
    assert "controller" in code.architecture
    assert code.engine == "local-offline"
