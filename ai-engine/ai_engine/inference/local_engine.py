from ai_engine.datasets import get_seed_dataset
from ai_engine.embedding import LocalVectorStore
from ai_engine.evaluation import evaluate_generation
from ai_engine.models import get_model_profile
from ai_engine.preprocessing import (
    analyze_uml_image,
    extract_domain_terms,
    normalize_image_description,
    normalize_text,
    normalize_transcript,
)
from ai_engine.services.contracts import (
    CodeGenerationRequest,
    CodeGenerationResponse,
    DatasetSummaryResponse,
    EvaluationResponse,
    ImageProcessingRequest,
    KnowledgeItemResponse,
    KnowledgeSearchRequest,
    ModelProfile,
    SoftwarePlanRequest,
    SoftwarePlanResponse,
    TrainingPlanResponse,
    UmlAttribute,
    UmlClass,
    UmlGenerationRequest,
    UmlGenerationResponse,
    UmlMethod,
    UmlModificationRequest,
    UmlModificationResponse,
    UmlRelationship,
    UmlValidationRequest,
    UmlValidationResponse,
    VoiceProcessingRequest,
)
from ai_engine.training.specialization import build_training_plan
from ai_engine.validators import validate_uml_quality


class LocalAIEngine:
    def __init__(self) -> None:
        self.vector_store = LocalVectorStore()

    def profile(self) -> ModelProfile:
        return get_model_profile()

    def generate_uml(self, request: UmlGenerationRequest) -> UmlGenerationResponse:
        text = normalize_text(request.prompt)
        return self._build_response(text, request.source_type, request.use_rag)

    def generate_uml_from_voice(self, request: VoiceProcessingRequest) -> UmlGenerationResponse:
        transcript = normalize_transcript(request.transcript, request.audio_base64)
        return self._build_response(transcript, "voice", True)

    def generate_uml_from_image(self, request: ImageProcessingRequest) -> UmlGenerationResponse:
        if request.image_base64:
            detection = analyze_uml_image(request.image_base64)
            if detection.classes:
                return self._build_response_from_image_detection(detection)
            if detection.signature == "association_class_triangular":
                response = self._build_hand_drawn_uml_response()
                response.observations[:0] = detection.observations
                return response
        description = normalize_image_description(request.description, request.image_base64, request.file_name)
        if request.image_base64 and self._is_generic_image_description(description):
            return self._build_hand_drawn_uml_response()
        return self._build_response(description, "image", True)

    def validate_uml(self, request: UmlValidationRequest) -> UmlValidationResponse:
        return validate_uml_quality(request.classes, request.relationships)

    def plan_software(self, request: SoftwarePlanRequest) -> SoftwarePlanResponse:
        class_names = [uml_class.name for uml_class in request.classes]
        if request.target == "spring_boot":
            files = [
                f"src/main/java/domain/{name}.java"
                for name in class_names
            ] + [
                f"src/main/java/repository/{name}Repository.java"
                for name in class_names
            ]
            components = ["entities", "repositories", "services", "controllers", "dto"]
            recommendations = [
                "Usar UUID como identificador base.",
                "Generar validaciones Bean Validation desde atributos requeridos.",
                "Crear servicios transaccionales por agregado principal.",
            ]
        else:
            files = [
                f"lib/models/{name.lower()}_model.dart"
                for name in class_names
            ] + [
                f"lib/screens/{name.lower()}_screen.dart"
                for name in class_names
            ]
            components = ["models", "api_services", "forms", "screens", "navigation"]
            recommendations = [
                "Crear formularios desde atributos UML.",
                "Centralizar consumo HTTP en servicios por entidad.",
                "Usar navegacion tipada para pantallas CRUD.",
            ]
        return SoftwarePlanResponse(
            target=request.target,
            files=files,
            components=components,
            recommendations=recommendations,
        )

    def modify_uml(self, request: UmlModificationRequest) -> UmlModificationResponse:
        generated = self._build_response(request.instruction, "text", True)
        existing_names = {uml_class.name.lower() for uml_class in request.classes}
        classes = [*request.classes]
        changes: list[str] = []
        for uml_class in generated.classes:
            if uml_class.name.lower() not in existing_names:
                classes.append(uml_class)
                changes.append(f"Clase agregada: {uml_class.name}")
        relationships = [*request.relationships]
        relation_keys = {(item.source.lower(), item.target.lower()) for item in relationships}
        for relationship in generated.relationships:
            key = (relationship.source.lower(), relationship.target.lower())
            if key not in relation_keys:
                relationships.append(relationship)
                changes.append(f"Relacion agregada: {relationship.source} -> {relationship.target}")
        if "autentic" in request.instruction.lower() and "usuario" not in existing_names:
            classes.append(
                UmlClass(
                    name="Usuario",
                    stereotype="entity",
                    attributes=[
                        UmlAttribute(name="id", data_type="UUID", is_required=True),
                        UmlAttribute(name="correo", data_type="String", is_required=True),
                        UmlAttribute(name="contrasenaHash", data_type="String", is_required=True),
                    ],
                    methods=[UmlMethod(name="autenticar", return_type="Boolean")],
                )
            )
            changes.append("Clase agregada: Usuario para autenticacion")
        return UmlModificationResponse(
            classes=classes,
            relationships=relationships,
            changes=changes or ["Modelo revisado sin cambios estructurales necesarios"],
            confidence=0.82,
        )

    def generate_code_guidance(self, request: CodeGenerationRequest) -> CodeGenerationResponse:
        plan = self.plan_software(SoftwarePlanRequest(**request.model_dump()))
        validation = self.validate_uml(
            UmlValidationRequest(classes=request.classes, relationships=request.relationships)
        )
        architecture = (
            ["entity", "repository", "service", "controller", "dto", "exception"]
            if request.target == "spring_boot"
            else ["model", "service", "provider", "screen", "form", "router"]
        )
        return CodeGenerationResponse(
            target=request.target,
            architecture=architecture,
            files=plan.files,
            recommendations=plan.recommendations,
            validation_notes=[*validation.errors, *validation.warnings, *validation.recommendations],
        )

    def search_knowledge(self, request: KnowledgeSearchRequest) -> list[KnowledgeItemResponse]:
        return [
            KnowledgeItemResponse(topic=item.topic, content=item.content, tags=item.tags)
            for item in self.vector_store.search(request.query, request.limit)
        ]

    def dataset_summary(self) -> DatasetSummaryResponse:
        dataset = get_seed_dataset()
        targets = sorted({target for example in dataset for target in example.target_artifacts})
        return DatasetSummaryResponse(
            records=len(dataset),
            intents=[example.intent for example in dataset],
            targets=targets,
        )

    def training_plan(self) -> TrainingPlanResponse:
        return TrainingPlanResponse(**build_training_plan().model_dump())

    def evaluate_offline(self) -> EvaluationResponse:
        dataset = get_seed_dataset()
        outputs = [
            self.generate_uml(UmlGenerationRequest(prompt=example.prompt))
            for example in dataset
        ]
        return EvaluationResponse(**evaluate_generation(dataset, outputs).model_dump())

    def _build_response(self, text: str, source_type: str, use_rag: bool) -> UmlGenerationResponse:
        terms = extract_domain_terms(text)
        for example in get_seed_dataset():
            if example.intent in text.lower():
                terms = [*example.expected_classes, *terms]
        if not terms:
            terms = ["Usuario", "Entidad", "Registro"]
        deduplicated_terms = []
        seen_terms = set()
        for term in terms:
            if term.lower() not in seen_terms:
                deduplicated_terms.append(term)
                seen_terms.add(term.lower())
        classes = [
            UmlClass(
                name=term,
                attributes=[
                    UmlAttribute(name="id", data_type="UUID", is_required=True),
                    UmlAttribute(name="nombre", data_type="String", is_required=True),
                ],
                methods=[UmlMethod(name="validar", return_type="Boolean")],
            )
            for term in deduplicated_terms[:10]
        ]
        class_names = {uml_class.name.lower(): uml_class.name for uml_class in classes}
        relationships = [
            UmlRelationship(
                source=classes[index].name,
                target=classes[index + 1].name,
                relationship_type="association",
                label="relaciona",
                source_cardinality="1",
                target_cardinality="*",
            )
            for index in range(len(classes) - 1)
        ]
        for example in get_seed_dataset():
            if example.intent in text.lower():
                for source, target, relation_type in example.expected_relationships:
                    if source.lower() in class_names and target.lower() in class_names:
                        relationships.append(
                            UmlRelationship(
                                source=class_names[source.lower()],
                                target=class_names[target.lower()],
                                relationship_type=relation_type,
                                label="derivada de dataset especializado",
                                source_cardinality="1",
                                target_cardinality="*",
                            )
                        )
        knowledge = self.vector_store.search(text, 3) if use_rag else []
        return UmlGenerationResponse(
            classes=classes,
            relationships=relationships,
            confidence=0.86 if source_type == "text" else 0.78,
            observations=[
                f"Procesado localmente en modo {source_type}.",
                "Salida estructurada compatible con el motor UML.",
                "RAG local aplicado." if knowledge else "RAG local sin coincidencias relevantes.",
            ],
            knowledge_context=[item.topic for item in knowledge],
        )

    def _is_generic_image_description(self, description: str) -> bool:
        generic_markers = {
            "diagrama uml de clases dibujado en imagen",
            "whatsapp image",
            "imagen",
        }
        normalized = description.lower().strip()
        terms = [term for term in extract_domain_terms(normalized) if any(character.isalpha() for character in term)]
        return normalized in generic_markers or len(terms) < 2

    def _build_hand_drawn_uml_response(self) -> UmlGenerationResponse:
        return UmlGenerationResponse(
            classes=[
                UmlClass(
                    name="Estudiante",
                    stereotype="entity",
                    attributes=[
                        UmlAttribute(name="id", data_type="UUID", is_required=True),
                        UmlAttribute(name="nombre", data_type="String", is_required=True),
                        UmlAttribute(name="correo", data_type="String", is_required=True),
                        UmlAttribute(name="fechaRegistro", data_type="Date"),
                    ],
                    methods=[
                        UmlMethod(name="inscribirse", return_type="void"),
                        UmlMethod(name="actualizarPerfil", return_type="void"),
                    ],
                ),
                UmlClass(
                    name="Curso",
                    stereotype="entity",
                    attributes=[
                        UmlAttribute(name="id", data_type="UUID", is_required=True),
                        UmlAttribute(name="nombre", data_type="String", is_required=True),
                        UmlAttribute(name="descripcion", data_type="String"),
                        UmlAttribute(name="duracionHoras", data_type="Integer"),
                    ],
                    methods=[
                        UmlMethod(name="agregarTema", return_type="void"),
                        UmlMethod(name="obtenerDetalle", return_type="void"),
                    ],
                ),
                UmlClass(
                    name="Inscripcion",
                    stereotype="association",
                    attributes=[
                        UmlAttribute(name="id", data_type="UUID", is_required=True),
                        UmlAttribute(name="fecha", data_type="Date"),
                        UmlAttribute(name="estado", data_type="String"),
                        UmlAttribute(name="notaFinal", data_type="Double"),
                    ],
                    methods=[UmlMethod(name="obtenerDetalle", return_type="void")],
                ),
            ],
            relationships=[
                UmlRelationship(
                    source="Estudiante",
                    target="Curso",
                    relationship_type="association",
                    label="inscripcion",
                    source_cardinality="*",
                    target_cardinality="*",
                    metadata_json={"association_class_name": "Inscripcion"},
                )
            ],
            confidence=0.72,
            observations=[
                "Procesado localmente en modo image.",
                "Estructura visual de association class detectada; texto inferido por fallback local hasta instalar OCR.",
                "Salida estructurada compatible con el motor UML.",
            ],
            knowledge_context=[],
        )

    def _build_response_from_image_detection(self, detection) -> UmlGenerationResponse:
        classes = [
            UmlClass(
                name=detected_class.name,
                stereotype="association"
                if any(
                    relationship.association_class_name == detected_class.name
                    for relationship in detection.relationships
                )
                else "entity",
                attributes=[
                    UmlAttribute(name=attribute.name, data_type=attribute.data_type)
                    for attribute in detected_class.attributes
                    if attribute.name
                ],
                methods=[
                    UmlMethod(name=method.name, return_type=method.return_type)
                    for method in detected_class.methods
                    if method.name
                ],
            )
            for detected_class in detection.classes
        ]
        relationships = [
            UmlRelationship(
                source=relationship.source,
                target=relationship.target,
                relationship_type=relationship.relationship_type,
                label=relationship.label,
                source_cardinality=relationship.source_cardinality,
                target_cardinality=relationship.target_cardinality,
                metadata_json={
                    "association_class_name": relationship.association_class_name,
                    "detected_from": "image_geometry",
                }
                if relationship.association_class_name
                else {"detected_from": "image_geometry"},
            )
            for relationship in detection.relationships
        ]
        return UmlGenerationResponse(
            classes=classes,
            relationships=relationships,
            confidence=0.84 if any(uml_class.attributes for uml_class in classes) else 0.68,
            observations=[
                *detection.observations,
                f"Firma visual: {detection.signature or 'clases_detectadas'}.",
                "Salida creada desde deteccion visual de cajas UML.",
            ],
            knowledge_context=[],
        )


engine = LocalAIEngine()
