from ai_engine.inference.health import check_health
from ai_engine.preprocessing import analyze_uml_image
from ai_engine.services import LocalAIService
from ai_engine.services.contracts import (
    ImageProcessingRequest,
    SoftwarePlanRequest,
    UmlAttribute,
    UmlClass,
    UmlGenerationRequest,
    UmlMethod,
    UmlModificationRequest,
    UmlRelationship,
    UmlValidationRequest,
    VoiceProcessingRequest,
)


def test_ai_engine_health_is_offline() -> None:
    health = check_health()

    assert health["status"] == "ok"
    assert health["mode"] == "local-offline"
    assert health["offline"] is True


def test_text_voice_and_image_generate_structured_uml() -> None:
    service = LocalAIService()

    text = service.text_to_uml(
        UmlGenerationRequest(prompt="Crear sistema de biblioteca con libros, usuarios y prestamos")
    )
    voice = service.voice_to_uml(VoiceProcessingRequest(transcript="Sistema academico con cursos y docentes"))
    image = service.image_to_uml(ImageProcessingRequest(description="Diagrama UML con Cliente y Pedido"))

    assert text.classes
    assert voice.classes
    assert image.classes
    assert text.engine == "local-offline"
    assert text.confidence > 0


def test_image_detector_identifies_association_class_geometry() -> None:
    import base64

    import cv2
    import numpy as np

    image = np.full((720, 960, 3), 255, dtype=np.uint8)
    cv2.rectangle(image, (70, 70), (370, 280), (0, 0, 0), 4)
    cv2.line(image, (70, 120), (370, 120), (0, 0, 0), 3)
    cv2.line(image, (70, 220), (370, 220), (0, 0, 0), 3)
    cv2.rectangle(image, (590, 70), (890, 280), (0, 0, 0), 4)
    cv2.line(image, (590, 120), (890, 120), (0, 0, 0), 3)
    cv2.line(image, (590, 220), (890, 220), (0, 0, 0), 3)
    cv2.rectangle(image, (330, 420), (650, 650), (0, 0, 0), 4)
    cv2.line(image, (330, 470), (650, 470), (0, 0, 0), 3)
    cv2.line(image, (330, 590), (650, 590), (0, 0, 0), 3)
    ok, encoded = cv2.imencode(".jpg", image)

    assert ok
    detection = analyze_uml_image(base64.b64encode(encoded.tobytes()).decode("ascii"))

    assert len(detection.boxes) == 3
    assert detection.signature == "association_class_triangular"
    assert [uml_class.name for uml_class in detection.classes] == [
        "Clase1",
        "Clase2",
        "Clase3",
    ]
    assert [attribute.name for attribute in detection.classes[0].attributes] == ["id", "nombre"]
    assert detection.relationships[0].source == "Clase1"
    assert detection.relationships[0].target == "Clase2"
    assert detection.relationships[0].association_class_name == "Clase3"
    assert not {"Estudiante", "Curso", "Inscripcion"}.intersection(
        {uml_class.name for uml_class in detection.classes}
    )


def test_text_generates_single_class_with_requested_attributes() -> None:
    service = LocalAIService()

    response = service.text_to_uml(
        UmlGenerationRequest(
            prompt="generar una clase con atributos id que es UUID y nombre que es string"
        )
    )

    assert [uml_class.name for uml_class in response.classes] == ["Entidad"]
    assert [(attribute.name, attribute.data_type) for attribute in response.classes[0].attributes] == [
        ("id", "UUID"),
        ("nombre", "String"),
    ]
    assert response.relationships == []


def test_text_and_voice_generate_academic_association_class() -> None:
    service = LocalAIService()
    prompt = (
        "Crea un diagrama UML con Estudiante, Curso e Inscripcion. "
        "Estudiante y Curso tienen una relacion muchos a muchos. "
        "Usa Inscripcion como clase asociativa de la relacion entre Estudiante y Curso. "
        "La multiplicidad en ambos extremos debe ser *."
    )

    text = service.text_to_uml(UmlGenerationRequest(prompt=prompt))
    voice = service.voice_to_uml(VoiceProcessingRequest(transcript=prompt))

    for response in (text, voice):
        assert [uml_class.name for uml_class in response.classes] == [
            "Estudiante",
            "Curso",
            "Inscripcion",
        ]
        assert [attribute.name for attribute in response.classes[2].attributes] == [
            "id",
            "fecha",
            "estado",
            "notaFinal",
        ]
        assert response.relationships[0].source == "Estudiante"
        assert response.relationships[0].target == "Curso"
        assert response.relationships[0].source_cardinality == "*"
        assert response.relationships[0].target_cardinality == "*"
        assert response.relationships[0].metadata_json["association_class_name"] == "Inscripcion"


def test_modify_existing_uml_adds_association_class() -> None:
    service = LocalAIService()

    response = service.modify_uml(
        UmlModificationRequest(
            instruction=(
                "entre la clase Estudiante y Curso haz una association class y en la "
                "resultante sera clase Detalle con atributos nombre string y id UUID"
            ),
            classes=[
                UmlClass(name="Estudiante", attributes=[UmlAttribute(name="id", data_type="UUID")]),
                UmlClass(name="Curso", attributes=[UmlAttribute(name="id", data_type="UUID")]),
            ],
            relationships=[
                UmlRelationship(source="Estudiante", target="Curso", relationship_type="association")
            ],
        )
    )

    detalle = next(uml_class for uml_class in response.classes if uml_class.name == "Detalle")
    assert detalle.stereotype == "association"
    assert [(attribute.name, attribute.data_type) for attribute in detalle.attributes] == [
        ("nombre", "String"),
        ("id", "UUID"),
    ]
    assert response.relationships[-1].metadata_json["association_class_name"] == "Detalle"
    assert response.relationships[-1].source == "Estudiante"
    assert response.relationships[-1].target == "Curso"


def test_modify_existing_uml_adds_attribute_to_named_class() -> None:
    service = LocalAIService()

    response = service.modify_uml(
        UmlModificationRequest(
            instruction="agrega atributo fecha Date a la clase Estudiante",
            classes=[
                UmlClass(name="Estudiante", attributes=[UmlAttribute(name="id", data_type="UUID")]),
                UmlClass(name="Curso", attributes=[UmlAttribute(name="id", data_type="UUID")]),
            ],
        )
    )

    estudiante = next(uml_class for uml_class in response.classes if uml_class.name == "Estudiante")
    assert ("fecha", "Date") in [
        (attribute.name, attribute.data_type) for attribute in estudiante.attributes
    ]
    assert not any(uml_class.name == "Entidad" for uml_class in response.classes)
    assert response.changes == ["Atributo agregado en Estudiante: fecha"]


def test_modify_existing_uml_creates_class_and_one_to_one_relationship_with_table() -> None:
    service = LocalAIService()

    response = service.modify_uml(
        UmlModificationRequest(
            instruction=(
                "crea clase Perfil con los atributos id UUID y biografia String "
                "que conecte de 1 a 1 con la tabla Usuario"
            ),
            classes=[
                UmlClass(name="Usuario", attributes=[UmlAttribute(name="id", data_type="UUID")]),
            ],
        )
    )

    perfil = next(uml_class for uml_class in response.classes if uml_class.name == "Perfil")
    assert [(attribute.name, attribute.data_type) for attribute in perfil.attributes] == [
        ("id", "UUID"),
        ("biografia", "String"),
    ]
    assert response.relationships[-1].source == "Perfil"
    assert response.relationships[-1].target == "Usuario"
    assert response.relationships[-1].source_cardinality == "1"
    assert response.relationships[-1].target_cardinality == "1"


def test_modify_existing_uml_processes_multiple_operations_in_one_instruction() -> None:
    service = LocalAIService()

    response = service.modify_uml(
        UmlModificationRequest(
            instruction=(
                "crea clase Perfil con los atributos id UUID y biografia String que conecte de 1 a 1 "
                "con la tabla Usuario, agrega atributo activo Boolean a la clase Usuario y crea clase "
                "Preferencia con los atributos id UUID y tema String que conecte de 1 a muchos con la tabla Perfil"
            ),
            classes=[
                UmlClass(name="Usuario", attributes=[UmlAttribute(name="id", data_type="UUID")]),
            ],
        )
    )

    usuario = next(uml_class for uml_class in response.classes if uml_class.name == "Usuario")
    perfil = next(uml_class for uml_class in response.classes if uml_class.name == "Perfil")
    preferencia = next(uml_class for uml_class in response.classes if uml_class.name == "Preferencia")

    assert ("activo", "Boolean") in [
        (attribute.name, attribute.data_type) for attribute in usuario.attributes
    ]
    assert [(attribute.name, attribute.data_type) for attribute in perfil.attributes] == [
        ("id", "UUID"),
        ("biografia", "String"),
    ]
    assert [(attribute.name, attribute.data_type) for attribute in preferencia.attributes] == [
        ("id", "UUID"),
        ("tema", "String"),
    ]
    assert [
        (
            relationship.source,
            relationship.target,
            relationship.source_cardinality,
            relationship.target_cardinality,
        )
        for relationship in response.relationships
    ] == [
        ("Perfil", "Usuario", "1", "1"),
        ("Preferencia", "Perfil", "1", "*"),
    ]


def test_modify_existing_uml_understands_voice_field_synonyms() -> None:
    service = LocalAIService()

    response = service.modify_uml(
        UmlModificationRequest(
            instruction="ponle el campo telefono String a la clase Cliente",
            classes=[
                UmlClass(name="Cliente", attributes=[UmlAttribute(name="id", data_type="UUID")]),
            ],
        )
    )

    cliente = next(uml_class for uml_class in response.classes if uml_class.name == "Cliente")
    assert ("telefono", "String") in [
        (attribute.name, attribute.data_type) for attribute in cliente.attributes
    ]
    assert response.changes == ["Atributo agregado en Cliente: telefono"]


def test_modify_existing_uml_creates_relationship_from_voice_instruction() -> None:
    service = LocalAIService()

    response = service.modify_uml(
        UmlModificationRequest(
            instruction="conecta Cliente con Pedido de uno a muchos",
            classes=[
                UmlClass(name="Cliente", attributes=[UmlAttribute(name="id", data_type="UUID")]),
                UmlClass(name="Pedido", attributes=[UmlAttribute(name="id", data_type="UUID")]),
            ],
        )
    )

    assert response.relationships[-1].source == "Cliente"
    assert response.relationships[-1].target == "Pedido"
    assert response.relationships[-1].source_cardinality == "1"
    assert response.relationships[-1].target_cardinality == "*"


def test_modify_existing_uml_creates_table_with_fields_and_relationship_synonyms() -> None:
    service = LocalAIService()

    response = service.modify_uml(
        UmlModificationRequest(
            instruction=(
                "crea la tabla Factura que tenga id UUID y total Double "
                "y conectala de uno a muchos con la entidad Cliente"
            ),
            classes=[
                UmlClass(name="Cliente", attributes=[UmlAttribute(name="id", data_type="UUID")]),
            ],
        )
    )

    factura = next(uml_class for uml_class in response.classes if uml_class.name == "Factura")
    assert [(attribute.name, attribute.data_type) for attribute in factura.attributes] == [
        ("id", "UUID"),
        ("total", "Double"),
    ]
    assert response.relationships[-1].source == "Factura"
    assert response.relationships[-1].target == "Cliente"
    assert response.relationships[-1].source_cardinality == "1"
    assert response.relationships[-1].target_cardinality == "*"


def test_modify_existing_uml_processes_mixed_voice_batch_instruction() -> None:
    service = LocalAIService()

    response = service.modify_uml(
        UmlModificationRequest(
            instruction=(
                "ponle campo telefono String a Cliente, conecta Cliente con Pedido de uno a muchos "
                "y crea tabla Pago con campos id UUID y monto Double que conecte de uno a uno con Pedido"
            ),
            classes=[
                UmlClass(name="Cliente", attributes=[UmlAttribute(name="id", data_type="UUID")]),
                UmlClass(name="Pedido", attributes=[UmlAttribute(name="id", data_type="UUID")]),
            ],
        )
    )

    cliente = next(uml_class for uml_class in response.classes if uml_class.name == "Cliente")
    pago = next(uml_class for uml_class in response.classes if uml_class.name == "Pago")
    assert ("telefono", "String") in [
        (attribute.name, attribute.data_type) for attribute in cliente.attributes
    ]
    assert [(attribute.name, attribute.data_type) for attribute in pago.attributes] == [
        ("id", "UUID"),
        ("monto", "Double"),
    ]
    assert [
        (
            relationship.source,
            relationship.target,
            relationship.source_cardinality,
            relationship.target_cardinality,
        )
        for relationship in response.relationships
    ] == [
        ("Cliente", "Pedido", "1", "*"),
        ("Pago", "Pedido", "1", "1"),
    ]


def test_modify_existing_uml_renames_class_and_updates_relationships() -> None:
    service = LocalAIService()

    response = service.modify_uml(
        UmlModificationRequest(
            instruction="renombra la clase Cliente a Comprador",
            classes=[
                UmlClass(name="Cliente", attributes=[UmlAttribute(name="id", data_type="UUID")]),
                UmlClass(name="Pedido", attributes=[UmlAttribute(name="id", data_type="UUID")]),
            ],
            relationships=[
                UmlRelationship(source="Cliente", target="Pedido", relationship_type="association")
            ],
        )
    )

    assert any(uml_class.name == "Comprador" for uml_class in response.classes)
    assert not any(uml_class.name == "Cliente" for uml_class in response.classes)
    assert response.relationships[0].source == "Comprador"
    assert response.relationships[0].target == "Pedido"


def test_modify_existing_uml_removes_attribute_from_voice_instruction() -> None:
    service = LocalAIService()

    response = service.modify_uml(
        UmlModificationRequest(
            instruction="quita campo telefono de Cliente",
            classes=[
                UmlClass(
                    name="Cliente",
                    attributes=[
                        UmlAttribute(name="id", data_type="UUID"),
                        UmlAttribute(name="telefono", data_type="String"),
                    ],
                ),
            ],
        )
    )

    cliente = next(uml_class for uml_class in response.classes if uml_class.name == "Cliente")
    assert ("telefono", "String") not in [
        (attribute.name, attribute.data_type) for attribute in cliente.attributes
    ]
    assert response.changes == ["Atributo eliminado en Cliente: telefono"]


def test_modify_existing_uml_uses_selected_class_for_implicit_attribute_edit() -> None:
    service = LocalAIService()

    response = service.modify_uml(
        UmlModificationRequest(
            instruction="ponle campo correo String",
            selected_class_name="Cliente",
            classes=[
                UmlClass(name="Cliente", attributes=[UmlAttribute(name="id", data_type="UUID")]),
                UmlClass(name="Pedido", attributes=[UmlAttribute(name="id", data_type="UUID")]),
            ],
        )
    )

    cliente = next(uml_class for uml_class in response.classes if uml_class.name == "Cliente")
    pedido = next(uml_class for uml_class in response.classes if uml_class.name == "Pedido")
    assert ("correo", "String") in [
        (attribute.name, attribute.data_type) for attribute in cliente.attributes
    ]
    assert ("correo", "String") not in [
        (attribute.name, attribute.data_type) for attribute in pedido.attributes
    ]


def test_modify_existing_uml_uses_selected_class_for_implicit_relationship() -> None:
    service = LocalAIService()

    response = service.modify_uml(
        UmlModificationRequest(
            instruction="conectala con Pedido de uno a varios",
            selected_class_name="Cliente",
            classes=[
                UmlClass(name="Cliente", attributes=[UmlAttribute(name="id", data_type="UUID")]),
                UmlClass(name="Pedido", attributes=[UmlAttribute(name="id", data_type="UUID")]),
            ],
        )
    )

    assert response.relationships == [
        UmlRelationship(
            source="Cliente",
            target="Pedido",
            relationship_type="association",
            label="asocia",
            source_cardinality="1",
            target_cardinality="*",
        )
    ]


def test_modify_existing_uml_matches_spoken_compound_class_names() -> None:
    service = LocalAIService()

    response = service.modify_uml(
        UmlModificationRequest(
            instruction="conecta detalle pedido con linea pago de uno a uno",
            classes=[
                UmlClass(name="DetallePedido", attributes=[UmlAttribute(name="id", data_type="UUID")]),
                UmlClass(name="LineaPago", attributes=[UmlAttribute(name="id", data_type="UUID")]),
            ],
        )
    )

    assert response.relationships[-1].source == "DetallePedido"
    assert response.relationships[-1].target == "LineaPago"
    assert response.relationships[-1].source_cardinality == "1"
    assert response.relationships[-1].target_cardinality == "1"


def test_modify_existing_uml_updates_existing_relationship_without_duplicate() -> None:
    service = LocalAIService()

    response = service.modify_uml(
        UmlModificationRequest(
            instruction="conecta Pedido con Cliente de muchos a uno",
            classes=[
                UmlClass(name="Cliente", attributes=[UmlAttribute(name="id", data_type="UUID")]),
                UmlClass(name="Pedido", attributes=[UmlAttribute(name="id", data_type="UUID")]),
            ],
            relationships=[
                UmlRelationship(
                    source="Cliente",
                    target="Pedido",
                    relationship_type="association",
                    source_cardinality="1",
                    target_cardinality="*",
                )
            ],
        )
    )

    assert len(response.relationships) == 1
    assert response.relationships[0].source == "Pedido"
    assert response.relationships[0].target == "Cliente"
    assert response.relationships[0].source_cardinality == "*"
    assert response.relationships[0].target_cardinality == "1"


def test_modify_existing_uml_discards_relationships_to_missing_classes() -> None:
    service = LocalAIService()

    response = service.modify_uml(
        UmlModificationRequest(
            instruction="ponle campo correo String a Cliente",
            classes=[
                UmlClass(name="Cliente", attributes=[UmlAttribute(name="id", data_type="UUID")]),
            ],
            relationships=[
                UmlRelationship(source="Cliente", target="Fantasma", relationship_type="association")
            ],
        )
    )

    assert response.relationships == []


def test_ai_validation_and_software_plan() -> None:
    service = LocalAIService()
    uml = service.text_to_uml(UmlGenerationRequest(prompt="Crear sistema con cliente y pedido"))

    validation = service.validate_uml(
        UmlValidationRequest(classes=uml.classes, relationships=uml.relationships)
    )
    spring = service.software_plan(
        SoftwarePlanRequest(classes=uml.classes, relationships=uml.relationships, target="spring_boot")
    )
    flutter = service.software_plan(
        SoftwarePlanRequest(classes=uml.classes, relationships=uml.relationships, target="flutter")
    )

    assert validation.score > 0
    assert any(file.endswith(".java") for file in spring.files)
    assert any(file.endswith(".dart") for file in flutter.files)


def test_ai_validation_allows_empty_methods_and_rejects_invalid_uml_details() -> None:
    service = LocalAIService()
    valid = service.validate_uml(
        UmlValidationRequest(
            classes=[
                UmlClass(
                    name="Cliente",
                    attributes=[UmlAttribute(name="id", data_type="UUID")],
                    methods=[],
                )
            ]
        )
    )
    invalid = service.validate_uml(
        UmlValidationRequest(
            classes=[
                UmlClass(
                    name="Cliente",
                    attributes=[
                        UmlAttribute(name="correo", data_type="String"),
                        UmlAttribute(name="CORREO", data_type="String"),
                    ],
                    methods=[
                        UmlMethod(name="guardar", return_type="void"),
                        UmlMethod(name="GUARDAR", return_type="void"),
                    ],
                )
            ],
            relationships=[
                UmlRelationship(
                    source="Cliente",
                    target="Fantasma",
                    relationship_type="association",
                    source_cardinality="muchos",
                )
            ],
        )
    )

    assert valid.errors == []
    assert not any("metodo" in item.lower() for item in valid.recommendations)
    assert any("Multiplicidad invalida" in error for error in invalid.errors)
    assert any("destino inexistente" in error for error in invalid.errors)
    assert any("Atributos duplicados" in warning for warning in invalid.warnings)
    assert any("Metodos duplicados" in warning for warning in invalid.warnings)
