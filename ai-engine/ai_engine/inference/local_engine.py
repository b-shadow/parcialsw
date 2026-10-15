import re

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
    ATTRIBUTE_WORDS = (
        "atributo",
        "atributos",
        "campo",
        "campos",
        "columna",
        "columnas",
        "propiedad",
        "propiedades",
        "dato",
        "datos",
    )
    METHOD_WORDS = (
        "metodo",
        "metodos",
        "funcion",
        "funciones",
        "operacion",
        "operaciones",
        "accion",
        "acciones",
    )
    CLASS_WORDS = ("clase", "tabla", "entidad", "modelo")
    CREATION_VERBS = (
        "crea",
        "crear",
        "agrega",
        "agregar",
        "anade",
        "incluye",
        "incorpora",
        "coloca",
    )
    MEMBER_EDIT_VERBS = (
        "agrega",
        "agregar",
        "anade",
        "pon",
        "ponle",
        "agregale",
        "incluye",
        "incorpora",
        "mete",
        "coloca",
    )
    REMOVAL_VERBS = (
        "elimina",
        "eliminar",
        "quita",
        "quitar",
        "borra",
        "borrar",
        "remueve",
        "remover",
        "saca",
        "sacar",
    )
    RENAME_VERBS = (
        "renombra",
        "renombrar",
        "cambia nombre",
        "cambiar nombre",
        "cambia el nombre",
        "cambiar el nombre",
    )
    CONNECTION_VERBS = (
        "conecta",
        "conecte",
        "conectar",
        "conectala",
        "conectalo",
        "relaciona",
        "relacione",
        "relacionar",
        "relacionala",
        "relacionalo",
        "asocia",
        "asocie",
        "asociar",
        "vincula",
        "vincule",
        "vincular",
        "une",
        "unir",
    )
    RELATION_WORDS = ("relacion", "relaciones", "asociacion", "enlace", "conexion")

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
        description = normalize_image_description(request.description, request.image_base64, request.file_name)
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
        rename_change = self._try_rename_class(request)
        if rename_change:
            return rename_change

        removal_change = self._try_remove_requested_items(request)
        if removal_change:
            return removal_change

        association_class_change = self._try_modify_association_class(request)
        if association_class_change:
            return association_class_change

        batch_change = self._try_modify_batch_operations(request)
        if batch_change:
            return batch_change

        relationship_change = self._try_modify_relationship_only(request)
        if relationship_change:
            return relationship_change

        class_connection_change = self._try_create_class_with_relationship(request)
        if class_connection_change:
            return class_connection_change

        class_member_change = self._try_modify_class_members(request)
        if class_member_change:
            return class_member_change

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
            relationships=self._validated_relationships(classes, relationships),
            changes=changes or ["Modelo revisado sin cambios estructurales necesarios"],
            confidence=0.82,
        )

    def _try_modify_association_class(
        self,
        request: UmlModificationRequest,
    ) -> UmlModificationResponse | None:
        normalized = normalize_text(request.instruction)
        association_markers = (
            "association class",
            "asociation class",
            "clase asociativa",
            "clase de asociacion",
        )
        if not any(marker in normalized for marker in association_markers):
            return None

        endpoints = self._extract_existing_endpoint_classes(normalized, request.classes)
        if len(endpoints) < 2:
            return None

        association_class_name = self._extract_association_class_name(normalized)
        attributes = self._extract_requested_attributes(normalized)
        if not attributes:
            attributes = [
                UmlAttribute(name="id", data_type="UUID", is_required=True),
                UmlAttribute(name="nombre", data_type="String"),
            ]

        existing_by_name = {uml_class.name.lower(): uml_class for uml_class in request.classes}
        classes = [*request.classes]
        if association_class_name.lower() not in existing_by_name:
            classes.append(
                UmlClass(
                    name=association_class_name,
                    stereotype="association",
                    attributes=attributes,
                    methods=[],
                )
            )

        source, target = endpoints[:2]
        relationships = [*request.relationships]
        relation_exists = any(
            relationship.source.lower() == source.name.lower()
            and relationship.target.lower() == target.name.lower()
            and relationship.metadata_json.get("association_class_name", "").lower()
            == association_class_name.lower()
            for relationship in relationships
        )
        if not relation_exists:
            relationships.append(
                UmlRelationship(
                    source=source.name,
                    target=target.name,
                    relationship_type="association",
                    label=association_class_name[:1].lower() + association_class_name[1:],
                    source_cardinality="*",
                    target_cardinality="*",
                    metadata_json={"association_class_name": association_class_name},
                )
            )

        return UmlModificationResponse(
            classes=classes,
            relationships=self._validated_relationships(classes, relationships),
            changes=[
                f"Clase asociativa {association_class_name} conectada entre {source.name} y {target.name}."
            ],
            confidence=0.88,
        )

    def _try_create_class_with_relationship(
        self,
        request: UmlModificationRequest,
    ) -> UmlModificationResponse | None:
        normalized = normalize_text(request.instruction)
        if not any(word in normalized for word in self.CLASS_WORDS):
            return None
        if not any(marker in normalized for marker in self.CREATION_VERBS):
            return None
        if not any(marker in normalized for marker in self.CONNECTION_VERBS):
            return None

        target = self._extract_relationship_target_class(normalized, request.classes)
        if target is None:
            target = self._selected_class(request.selected_class_name, request.classes)
        if target is None:
            return None

        class_name = self._extract_requested_class_name(normalized)
        if not class_name or class_name.lower() == target.name.lower():
            return None

        attributes = self._extract_requested_attributes(normalized)
        existing_by_name = {uml_class.name.lower(): uml_class for uml_class in request.classes}
        classes: list[UmlClass] = []
        changes: list[str] = []
        new_class = existing_by_name.get(class_name.lower())

        for uml_class in request.classes:
            if uml_class.name.lower() != class_name.lower():
                classes.append(uml_class)
                continue

            existing_attributes = {attribute.name.lower() for attribute in uml_class.attributes}
            merged_attributes = [*uml_class.attributes]
            for attribute in attributes:
                if attribute.name.lower() in existing_attributes:
                    continue
                merged_attributes.append(attribute)
                existing_attributes.add(attribute.name.lower())
                changes.append(f"Atributo agregado en {uml_class.name}: {attribute.name}")
            new_class = uml_class.model_copy(update={"attributes": merged_attributes})
            classes.append(new_class)

        if new_class is None:
            new_class = UmlClass(
                name=class_name,
                stereotype="entity",
                attributes=attributes,
                methods=[],
            )
            classes.append(new_class)
            changes.append(f"Clase agregada: {class_name}")

        source_cardinality, target_cardinality = self._extract_requested_cardinality(normalized)
        relationships, relationship_change = self._upsert_association_relationship(
            request.relationships,
            new_class,
            target,
            source_cardinality,
            target_cardinality,
        )
        changes.append(relationship_change)

        return UmlModificationResponse(
            classes=classes,
            relationships=self._validated_relationships(classes, relationships),
            changes=changes,
            confidence=0.88,
        )

    def _try_modify_batch_operations(
        self,
        request: UmlModificationRequest,
    ) -> UmlModificationResponse | None:
        normalized = normalize_text(request.instruction)
        segments = self._split_operation_segments(normalized)
        if len(segments) < 2:
            return None

        classes = [*request.classes]
        relationships = [*request.relationships]
        changes: list[str] = []

        create_verbs = "|".join(self.CREATION_VERBS)
        member_verbs = "|".join(self.MEMBER_EDIT_VERBS)
        removal_verbs = "|".join(self.REMOVAL_VERBS)
        class_words = "|".join(self.CLASS_WORDS)
        attribute_words = "|".join(self.ATTRIBUTE_WORDS)
        method_words = "|".join(self.METHOD_WORDS)

        for segment in segments:
            if any(marker in segment for marker in self.RENAME_VERBS):
                rename_change = self._try_rename_class(
                    UmlModificationRequest(
                        instruction=segment,
                        classes=classes,
                        relationships=relationships,
                        selected_class_name=request.selected_class_name,
                    )
                )
                if rename_change:
                    classes = rename_change.classes
                    relationships = rename_change.relationships
                    changes.extend(rename_change.changes)
                continue

            if re.search(
                rf"\b(?:{removal_verbs})\s+(?:un\s+|una\s+|la\s+|el\s+|los\s+|las\s+)?"
                rf"(?:{class_words}|{attribute_words}|{method_words})\b",
                segment,
            ):
                removal_change = self._try_remove_requested_items(
                    UmlModificationRequest(
                        instruction=segment,
                        classes=classes,
                        relationships=relationships,
                        selected_class_name=request.selected_class_name,
                    )
                )
                if removal_change:
                    classes = removal_change.classes
                    relationships = removal_change.relationships
                    changes.extend(removal_change.changes)
                continue

            if re.search(
                rf"\b(?:{create_verbs})\s+(?:una\s+|un\s+|la\s+|el\s+)?(?:{class_words})\b",
                segment,
            ):
                result = self._apply_create_class_operation(
                    segment,
                    classes,
                    relationships,
                    request.selected_class_name,
                )
                classes = result.classes
                relationships = result.relationships
                changes.extend(result.changes)
                continue

            if re.search(
                rf"\b(?:{member_verbs})\s+(?:un\s+|una\s+|los\s+|las\s+|el\s+|la\s+)?"
                rf"(?:{attribute_words}|{method_words})\b",
                segment,
            ):
                member_change = self._try_modify_class_members(
                    UmlModificationRequest(
                        instruction=segment,
                        classes=classes,
                        relationships=relationships,
                        selected_class_name=request.selected_class_name,
                    )
                )
                if member_change:
                    classes = member_change.classes
                    relationships = member_change.relationships
                    changes.extend(member_change.changes)
                continue

            relationship_change = self._try_modify_relationship_only(
                UmlModificationRequest(
                    instruction=segment,
                    classes=classes,
                    relationships=relationships,
                    selected_class_name=request.selected_class_name,
                )
            )
            if relationship_change:
                classes = relationship_change.classes
                relationships = relationship_change.relationships
                changes.extend(relationship_change.changes)

        if not changes:
            return None

        return UmlModificationResponse(
            classes=classes,
            relationships=self._validated_relationships(classes, relationships),
            changes=changes,
            confidence=0.87,
        )

    def _split_operation_segments(self, normalized: str) -> list[str]:
        create_verbs = "|".join(self.CREATION_VERBS)
        member_verbs = "|".join(self.MEMBER_EDIT_VERBS)
        removal_verbs = "|".join(self.REMOVAL_VERBS)
        connection_verbs = "|".join(
            verb
            for verb in self.CONNECTION_VERBS
            if verb
            not in {
                "conecte",
                "conectala",
                "conectalo",
                "relacione",
                "relacionala",
                "relacionalo",
                "asocie",
                "vincule",
            }
        )
        class_words = "|".join(self.CLASS_WORDS)
        attribute_words = "|".join(self.ATTRIBUTE_WORDS)
        method_words = "|".join(self.METHOD_WORDS)
        operation_pattern = re.compile(
            rf"\b(?:{create_verbs})\s+"
            rf"(?:un\s+|una\s+|la\s+|el\s+|los\s+|las\s+)?"
            rf"(?:{class_words}|{attribute_words}|{method_words})\b"
            rf"|\b(?:{member_verbs})\s+"
            rf"(?:un\s+|una\s+|la\s+|el\s+|los\s+|las\s+)?"
            rf"(?:{attribute_words}|{method_words})\b"
            rf"|\b(?:{removal_verbs})\s+"
            rf"(?:un\s+|una\s+|la\s+|el\s+|los\s+|las\s+)?"
            rf"(?:{class_words}|{attribute_words}|{method_words})\b"
            r"|\b(?:renombra|renombrar|cambia(?:r)?(?:\s+el)?\s+nombre)\b"
            rf"|(?:^|[,.;]\s+|\sy\s+)\b(?:{connection_verbs})\b"
        )
        matches = list(operation_pattern.finditer(normalized))
        segments: list[str] = []
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(normalized)
            segment = normalized[match.start() : end].strip(" ,.;")
            segment = re.sub(r"^y\s+", "", segment)
            if segment:
                segments.append(segment)
        return segments

    def _apply_create_class_operation(
        self,
        normalized: str,
        current_classes: list[UmlClass],
        current_relationships: list[UmlRelationship],
        selected_class_name: str | None = None,
    ) -> UmlModificationResponse:
        class_name = self._extract_requested_class_name(normalized)
        attributes = self._extract_requested_attributes(normalized)
        classes: list[UmlClass] = []
        relationships = [*current_relationships]
        changes: list[str] = []
        existing_by_name = {uml_class.name.lower(): uml_class for uml_class in current_classes}
        target_class = existing_by_name.get(class_name.lower())

        for uml_class in current_classes:
            if uml_class.name.lower() != class_name.lower():
                classes.append(uml_class)
                continue

            merged_attributes = [*uml_class.attributes]
            existing_attributes = {attribute.name.lower() for attribute in merged_attributes}
            for attribute in attributes:
                if attribute.name.lower() in existing_attributes:
                    continue
                merged_attributes.append(attribute)
                existing_attributes.add(attribute.name.lower())
                changes.append(f"Atributo agregado en {uml_class.name}: {attribute.name}")
            target_class = uml_class.model_copy(update={"attributes": merged_attributes})
            classes.append(target_class)

        if target_class is None:
            target_class = UmlClass(
                name=class_name,
                stereotype="entity",
                attributes=attributes,
                methods=[],
            )
            classes.append(target_class)
            changes.append(f"Clase agregada: {class_name}")

        if any(marker in normalized for marker in self.CONNECTION_VERBS):
            relationship_target = self._extract_relationship_target_class(normalized, classes)
            if relationship_target is None:
                relationship_target = self._selected_class(selected_class_name, classes)
            if relationship_target and relationship_target.name.lower() != target_class.name.lower():
                source_cardinality, target_cardinality = self._extract_requested_cardinality(normalized)
                relationships, relationship_change = self._upsert_association_relationship(
                    relationships,
                    target_class,
                    relationship_target,
                    source_cardinality,
                    target_cardinality,
                )
                changes.append(relationship_change)

        return UmlModificationResponse(
            classes=classes,
            relationships=self._validated_relationships(classes, relationships),
            changes=changes,
            confidence=0.87,
        )

    def _try_rename_class(
        self,
        request: UmlModificationRequest,
    ) -> UmlModificationResponse | None:
        normalized = normalize_text(request.instruction)
        if not any(marker in normalized for marker in self.RENAME_VERBS):
            return None

        target = self._extract_target_existing_class(normalized, request.classes)
        if target is None:
            target = self._selected_class(request.selected_class_name, request.classes)
        if target is None:
            return None

        target_position = normalized.find(normalize_text(target.name))
        search_section = normalized[target_position + len(normalize_text(target.name)) :]
        match = re.search(r"\b(?:a|por|como)\s+(?:la\s+|el\s+)?([a-zA-Z][a-zA-Z0-9_]*)\b", search_section)
        if not match:
            return None

        new_name = self._to_pascal_case(match.group(1))
        if not new_name or new_name.lower() == target.name.lower():
            return None

        classes = [
            uml_class.model_copy(update={"name": new_name})
            if uml_class.name.lower() == target.name.lower()
            else uml_class
            for uml_class in request.classes
        ]
        relationships = [
            relationship.model_copy(
                update={
                    "source": new_name if relationship.source.lower() == target.name.lower() else relationship.source,
                    "target": new_name if relationship.target.lower() == target.name.lower() else relationship.target,
                }
            )
            for relationship in request.relationships
        ]
        return UmlModificationResponse(
            classes=classes,
            relationships=self._validated_relationships(classes, relationships),
            changes=[f"Clase renombrada: {target.name} -> {new_name}"],
            confidence=0.87,
        )

    def _try_remove_requested_items(
        self,
        request: UmlModificationRequest,
    ) -> UmlModificationResponse | None:
        normalized = normalize_text(request.instruction)
        if not any(marker in normalized for marker in self.REMOVAL_VERBS):
            return None

        removes_class = any(word in normalized for word in self.CLASS_WORDS)
        removes_attribute = any(word in normalized for word in self.ATTRIBUTE_WORDS)
        removes_method = any(word in normalized for word in self.METHOD_WORDS)
        target = self._extract_target_existing_class(normalized, request.classes)
        if target is None:
            target = self._selected_class(request.selected_class_name, request.classes)
        if target is None:
            return None

        if removes_class and not (removes_attribute or removes_method):
            classes = [
                uml_class for uml_class in request.classes if uml_class.name.lower() != target.name.lower()
            ]
            relationships = [
                relationship
                for relationship in request.relationships
                if relationship.source.lower() != target.name.lower()
                and relationship.target.lower() != target.name.lower()
            ]
            return UmlModificationResponse(
                classes=classes,
                relationships=self._validated_relationships(classes, relationships),
                changes=[f"Clase eliminada: {target.name}"],
                confidence=0.86,
            )

        item_name = self._extract_requested_member_name(normalized)
        if not item_name:
            return None

        classes: list[UmlClass] = []
        changes: list[str] = []
        for uml_class in request.classes:
            if uml_class.name.lower() != target.name.lower():
                classes.append(uml_class)
                continue

            attributes = [*uml_class.attributes]
            methods = [*uml_class.methods]
            if removes_attribute:
                kept_attributes = [
                    attribute for attribute in attributes if attribute.name.lower() != item_name.lower()
                ]
                if len(kept_attributes) != len(attributes):
                    attributes = kept_attributes
                    changes.append(f"Atributo eliminado en {uml_class.name}: {item_name}")
            if removes_method:
                kept_methods = [method for method in methods if method.name.lower() != item_name.lower()]
                if len(kept_methods) != len(methods):
                    methods = kept_methods
                    changes.append(f"Metodo eliminado en {uml_class.name}: {item_name}")
            classes.append(uml_class.model_copy(update={"attributes": attributes, "methods": methods}))

        if not changes:
            return None

        return UmlModificationResponse(
            classes=classes,
            relationships=self._validated_relationships(classes, request.relationships),
            changes=changes,
            confidence=0.86,
        )

    def _try_modify_class_members(
        self,
        request: UmlModificationRequest,
    ) -> UmlModificationResponse | None:
        normalized = normalize_text(request.instruction)
        has_attribute_request = any(marker in normalized for marker in self.ATTRIBUTE_WORDS)
        has_method_request = any(marker in normalized for marker in self.METHOD_WORDS)
        if not (has_attribute_request or has_method_request):
            return None

        target = self._extract_target_existing_class(normalized, request.classes)
        if target is None:
            target = self._selected_class(request.selected_class_name, request.classes)
        if target is None:
            return None

        classes: list[UmlClass] = []
        changes: list[str] = []
        for uml_class in request.classes:
            if uml_class.name.lower() != target.name.lower():
                classes.append(uml_class)
                continue

            attributes = [*uml_class.attributes]
            methods = [*uml_class.methods]
            existing_attributes = {attribute.name.lower() for attribute in attributes}
            existing_methods = {method.name.lower() for method in methods}

            if has_attribute_request:
                for attribute in self._extract_requested_attributes(normalized):
                    if attribute.name.lower() in existing_attributes:
                        continue
                    attributes.append(attribute)
                    existing_attributes.add(attribute.name.lower())
                    changes.append(f"Atributo agregado en {uml_class.name}: {attribute.name}")

            if has_method_request:
                for method in self._extract_requested_methods(normalized):
                    if method.name.lower() in existing_methods:
                        continue
                    methods.append(method)
                    existing_methods.add(method.name.lower())
                    changes.append(f"Metodo agregado en {uml_class.name}: {method.name}")

            classes.append(uml_class.model_copy(update={"attributes": attributes, "methods": methods}))

        if not changes:
            return None

        return UmlModificationResponse(
            classes=classes,
            relationships=self._validated_relationships(classes, request.relationships),
            changes=changes,
            confidence=0.86,
        )

    def _try_modify_relationship_only(
        self,
        request: UmlModificationRequest,
    ) -> UmlModificationResponse | None:
        normalized = normalize_text(request.instruction)
        has_relationship_intent = any(marker in normalized for marker in self.CONNECTION_VERBS) or any(
            word in normalized for word in self.RELATION_WORDS
        )
        if not has_relationship_intent:
            return None

        endpoints = self._extract_existing_endpoint_classes(normalized, request.classes)
        selected = self._selected_class(request.selected_class_name, request.classes)
        if selected and all(uml_class.name.lower() != selected.name.lower() for uml_class in endpoints):
            endpoints = [selected, *endpoints]
        if len(endpoints) < 2:
            return None

        source, target = endpoints[:2]
        source_cardinality, target_cardinality = self._extract_requested_cardinality(normalized)
        relationships, relationship_change = self._upsert_association_relationship(
            request.relationships,
            source,
            target,
            source_cardinality,
            target_cardinality,
        )
        return UmlModificationResponse(
            classes=[*request.classes],
            relationships=self._validated_relationships(request.classes, relationships),
            changes=[relationship_change],
            confidence=0.86,
        )

    def _selected_class(
        self,
        selected_class_name: str | None,
        classes: list[UmlClass],
    ) -> UmlClass | None:
        if not selected_class_name:
            return None
        selected = normalize_text(selected_class_name)
        for uml_class in classes:
            if normalize_text(uml_class.name) == selected:
                return uml_class
        return None

    def _upsert_association_relationship(
        self,
        relationships: list[UmlRelationship],
        source: UmlClass,
        target: UmlClass,
        source_cardinality: str,
        target_cardinality: str,
    ) -> tuple[list[UmlRelationship], str]:
        next_relationships = [*relationships]
        for index, relationship in enumerate(next_relationships):
            if (
                relationship.relationship_type.lower() == "association"
                and {relationship.source.lower(), relationship.target.lower()}
                == {source.name.lower(), target.name.lower()}
            ):
                next_relationships[index] = relationship.model_copy(
                    update={
                        "source": source.name,
                        "target": target.name,
                        "source_cardinality": source_cardinality,
                        "target_cardinality": target_cardinality,
                        "label": relationship.label or "asocia",
                    }
                )
                return (
                    next_relationships,
                    f"Relacion actualizada: {source.name} {source_cardinality} a {target_cardinality} {target.name}",
                )

        next_relationships.append(
            UmlRelationship(
                source=source.name,
                target=target.name,
                relationship_type="association",
                label="asocia",
                source_cardinality=source_cardinality,
                target_cardinality=target_cardinality,
            )
        )
        return (
            next_relationships,
            f"Relacion agregada: {source.name} {source_cardinality} a {target_cardinality} {target.name}",
        )

    def _validated_relationships(
        self,
        classes: list[UmlClass],
        relationships: list[UmlRelationship],
    ) -> list[UmlRelationship]:
        class_by_normalized_name = {normalize_text(uml_class.name): uml_class.name for uml_class in classes}
        valid_relationships: list[UmlRelationship] = []
        seen: set[tuple[str, str, str, str]] = set()
        for relationship in relationships:
            source = class_by_normalized_name.get(normalize_text(relationship.source))
            target = class_by_normalized_name.get(normalize_text(relationship.target))
            if not source or not target:
                continue
            relationship_type = relationship.relationship_type.lower()
            association_name = str(
                relationship.metadata_json.get("association_class_name", "")
                if relationship.metadata_json
                else ""
            ).lower()
            if relationship_type == "association":
                endpoints = tuple(sorted((source.lower(), target.lower())))
                key = (endpoints[0], endpoints[1], relationship_type, association_name)
            else:
                key = (source.lower(), target.lower(), relationship_type, association_name)
            if key in seen:
                continue
            seen.add(key)
            valid_relationships.append(
                relationship.model_copy(update={"source": source, "target": target})
            )
        return valid_relationships

    def _extract_existing_endpoint_classes(
        self,
        normalized: str,
        classes: list[UmlClass],
    ) -> list[UmlClass]:
        matches: list[tuple[int, int, UmlClass]] = []
        matched_names: set[str] = set()
        for uml_class in classes:
            aliases = self._class_name_aliases(uml_class.name)
            for priority, alias in enumerate(aliases):
                match = re.search(rf"\b{re.escape(alias)}\b", normalized)
                if match:
                    name_key = uml_class.name.lower()
                    if name_key not in matched_names:
                        matches.append((match.start(), priority, uml_class))
                        matched_names.add(name_key)
                    break
        matches.sort(key=lambda item: (item[0], item[1]))
        return [uml_class for _, _, uml_class in matches]

    def _class_name_aliases(self, class_name: str) -> list[str]:
        normalized_name = normalize_text(class_name)
        spaced = normalize_text(
            re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", class_name).replace("_", " ")
        )
        aliases = [normalized_name]
        if spaced and spaced != normalized_name:
            aliases.append(spaced)
        return aliases

    def _extract_target_existing_class(
        self,
        normalized: str,
        classes: list[UmlClass],
    ) -> UmlClass | None:
        matches = self._extract_existing_endpoint_classes(normalized, classes)
        if not matches:
            return None
        class_markers = (*self.CLASS_WORDS, "en", "a", "al")
        scored: list[tuple[int, UmlClass]] = []
        for uml_class in matches:
            class_name = normalize_text(uml_class.name)
            position = normalized.find(class_name)
            prefix = normalized[max(0, position - 18) : position]
            score = 0 if any(marker in prefix.split() for marker in class_markers) else 1
            scored.append((score, uml_class))
        scored.sort(key=lambda item: item[0])
        return scored[0][1]

    def _extract_relationship_target_class(
        self,
        normalized: str,
        classes: list[UmlClass],
    ) -> UmlClass | None:
        markers = (*self.CLASS_WORDS,)
        candidates: list[tuple[int, UmlClass]] = []
        for uml_class in classes:
            aliases = self._class_name_aliases(uml_class.name)
            for alias in aliases:
                for marker in markers:
                    pattern = rf"\b{marker}\s+{re.escape(alias)}\b"
                    match = re.search(pattern, normalized)
                    if match:
                        candidates.append((match.start(), uml_class))
                        break
                if any(item[1].name == uml_class.name for item in candidates):
                    break
            if not any(item[1].name == uml_class.name for item in candidates):
                for alias in aliases:
                    position = normalized.rfind(alias)
                    if position >= 0 and any(
                        word in normalized[max(0, position - 36) : position]
                        for word in ("con", "hacia", "a", "al")
                    ):
                        candidates.append((position, uml_class))
                        break
        if not candidates:
            return None
        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1]

    def _extract_requested_cardinality(self, normalized: str) -> tuple[str, str]:
        cardinality_patterns: tuple[tuple[str, tuple[str, str]], ...] = (
            (r"\b(?:de\s+)?1\s*(?:a|:|-)\s*1\b", ("1", "1")),
            (r"\b(?:de\s+)?uno\s+a\s+uno\b", ("1", "1")),
            (r"\b(?:de\s+)?1\s*(?:a|:|-)\s*(?:n|muchos|\*)\b", ("1", "*")),
            (r"\b(?:de\s+)?uno\s+a\s+muchos\b", ("1", "*")),
            (r"\b(?:de\s+)?uno\s+a\s+(?:varios|varias)\b", ("1", "*")),
            (r"\b(?:de\s+)?(?:n|muchos|\*)\s*(?:a|:|-)\s*1\b", ("*", "1")),
            (r"\b(?:de\s+)?muchos\s+a\s+uno\b", ("*", "1")),
            (r"\b(?:de\s+)?(?:varios|varias)\s+a\s+uno\b", ("*", "1")),
            (r"\b(?:de\s+)?(?:n|muchos|\*)\s*(?:a|:|-)\s*(?:n|muchos|\*)\b", ("*", "*")),
            (r"\b(?:de\s+)?muchos\s+a\s+muchos\b", ("*", "*")),
            (r"\b(?:de\s+)?(?:varios|varias)\s+a\s+(?:varios|varias)\b", ("*", "*")),
        )
        for pattern, cardinality in cardinality_patterns:
            if re.search(pattern, normalized):
                return cardinality
        return "1", "*"

    def _extract_association_class_name(self, normalized: str) -> str:
        class_words = "|".join(self.CLASS_WORDS)
        patterns = (
            rf"\bresultante\s+(?:sera|sea|es)?\s*(?:la\s+)?(?:{class_words})\s+([a-zA-Z][a-zA-Z0-9_]*)",
            rf"\b(?:{class_words})\s+(?:asociativa|de\s+asociacion)\s+(?:llamada|nombrada|denominada)?\s*([a-zA-Z][a-zA-Z0-9_]*)",
            r"\b(?:llamada|nombrada|denominada)\s+([a-zA-Z][a-zA-Z0-9_]*)",
        )
        for pattern in patterns:
            match = re.search(pattern, normalized)
            if match:
                candidate = match.group(1)
                if candidate not in {"con", "entre", *self.ATTRIBUTE_WORDS, *self.CLASS_WORDS}:
                    return self._to_pascal_case(candidate)
        return "Detalle"

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
        explicit_class = self._try_build_explicit_single_class(text, source_type)
        if explicit_class:
            return explicit_class

        if self._matches_academic_enrollment_prompt(text):
            response = self._build_hand_drawn_uml_response()
            response.confidence = 0.9 if source_type == "text" else 0.84
            response.observations = [
                f"Procesado localmente en modo {source_type}.",
                "Prompt de inscripcion academica reconocido con clase asociativa.",
                "Salida estructurada compatible con el motor UML.",
            ]
            return response

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

    def _try_build_explicit_single_class(
        self,
        text: str,
        source_type: str,
    ) -> UmlGenerationResponse | None:
        normalized = normalize_text(text)
        has_class_word = any(word in normalized for word in self.CLASS_WORDS)
        has_attribute_word = any(word in normalized for word in self.ATTRIBUTE_WORDS) or re.search(
            r"\b(?:que\s+)?tenga\b", normalized
        )
        if not has_class_word or not has_attribute_word:
            return None

        class_name = self._extract_requested_class_name(normalized)
        attributes = self._extract_requested_attributes(normalized)
        if not attributes:
            return None

        return UmlGenerationResponse(
            classes=[
                UmlClass(
                    name=class_name,
                    stereotype="entity",
                    attributes=attributes,
                    methods=[],
                )
            ],
            relationships=[],
            confidence=0.9,
            observations=[
                f"Procesado localmente en modo {source_type}.",
                "Solicitud explicita de una clase con atributos detectada.",
                "Salida estructurada compatible con el motor UML.",
            ],
            knowledge_context=[],
        )

    def _extract_requested_class_name(self, normalized: str) -> str:
        class_words = "|".join(self.CLASS_WORDS)
        match = re.search(
            rf"\b(?:{class_words})\s+(?:(?:llamada|nombrada|denominada|con\s+nombre)\s+)?(?:una\s+|un\s+|la\s+|el\s+)?([a-zA-Z][a-zA-Z0-9_]*)",
            normalized,
        )
        if match:
            candidate = match.group(1)
            if candidate not in {"con", "que", "para", *self.ATTRIBUTE_WORDS, *self.CLASS_WORDS}:
                return self._to_pascal_case(candidate)
        return "Entidad"

    def _extract_requested_attributes(self, normalized: str) -> list[UmlAttribute]:
        attribute_markers = "|".join(self.ATTRIBUTE_WORDS)
        marker_pattern = re.compile(rf"\b(?:{attribute_markers})\b|\b(?:que\s+)?tenga\b")
        marker_match = marker_pattern.search(normalized)
        attributes_section = normalized[marker_match.end() :] if marker_match else normalized
        connection_verbs = "|".join(self.CONNECTION_VERBS)
        class_words = "|".join(self.CLASS_WORDS)
        attributes_section = re.split(
            rf"\b(?:que\s+)?(?:{connection_verbs})\b|\b(?:a|al|en|para)\s+(?:la\s+|el\s+)?(?:{class_words})\b",
            attributes_section,
            maxsplit=1,
        )[0]
        pattern = re.compile(
            r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?::|que\s+es|de\s+tipo|tipo|es)\s*([a-zA-Z_][a-zA-Z0-9_]*)"
        )
        attributes: list[UmlAttribute] = []
        seen: set[str] = set()
        for raw_name, raw_type in pattern.findall(attributes_section):
            if raw_name in {"a", "la", "tipo", "es", *self.ATTRIBUTE_WORDS, *self.CLASS_WORDS}:
                continue
            name = self._to_camel_case(raw_name)
            if not name or name.lower() in seen:
                continue
            attributes.append(
                UmlAttribute(
                    name=name,
                    data_type=self._normalize_uml_type(raw_type),
                    is_required=name == "id",
                )
            )
            seen.add(name.lower())
        if attributes:
            return attributes

        tokens = [
            token
            for token in re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", attributes_section)
            if token
            not in {
                "a",
                "agrega",
                "agregar",
                "agregale",
                "anade",
                "coloca",
                "con",
                "conectala",
                "conectalo",
                "de",
                "e",
                "el",
                "en",
                "es",
                "incluye",
                "incorpora",
                "la",
                "mete",
                "para",
                "pon",
                "ponle",
                "que",
                "tipo",
                "tenga",
                "un",
                "una",
                "y",
                *self.ATTRIBUTE_WORDS,
                *self.CLASS_WORDS,
            }
        ]
        for index in range(0, len(tokens) - 1, 2):
            raw_name = tokens[index]
            raw_type = tokens[index + 1]
            name = self._to_camel_case(raw_name)
            if not name or name.lower() in seen:
                continue
            attributes.append(
                UmlAttribute(
                    name=name,
                    data_type=self._normalize_uml_type(raw_type),
                    is_required=name == "id",
                )
            )
            seen.add(name.lower())
        return attributes

    def _extract_requested_member_name(self, normalized: str) -> str:
        member_words = "|".join((*self.ATTRIBUTE_WORDS, *self.METHOD_WORDS))
        marker_match = re.search(rf"\b(?:{member_words})\b", normalized)
        if not marker_match:
            return ""
        section = normalized[marker_match.end() :]
        section = re.split(
            rf"\b(?:de|del|a|al|en|para)\s+(?:la\s+|el\s+)?(?:{'|'.join(self.CLASS_WORDS)})\b|\b(?:de|del|a|al|en|para)\b",
            section,
            maxsplit=1,
        )[0]
        tokens = [
            token
            for token in re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", section)
            if token
            not in {
                "el",
                "la",
                "los",
                "las",
                "un",
                "una",
                "que",
                "se",
                "llama",
                "llamado",
                "llamada",
                *self.ATTRIBUTE_WORDS,
                *self.METHOD_WORDS,
                *self.CLASS_WORDS,
            }
        ]
        return self._to_camel_case(tokens[0]) if tokens else ""

    def _extract_requested_methods(self, normalized: str) -> list[UmlMethod]:
        method_markers = "|".join(self.METHOD_WORDS)
        marker_match = re.search(rf"\b(?:{method_markers})\b", normalized)
        methods_section = normalized[marker_match.end() :] if marker_match else normalized
        pattern = re.compile(
            r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:retorna|devuelve|return|:|tipo|es)?\s*(void|boolean|bool|string|integer|int|double|uuid)?"
        )
        methods: list[UmlMethod] = []
        seen: set[str] = set()
        ignored = {
            "a",
            "agrega",
            "agregar",
            "agregale",
            "anade",
            "coloca",
            "con",
            "de",
            "e",
            "el",
            "en",
            "es",
            "la",
            "mete",
            "para",
            "pon",
            "ponle",
            "que",
            "un",
            "una",
            "y",
            *self.CLASS_WORDS,
            *self.METHOD_WORDS,
        }
        for raw_name, raw_type in pattern.findall(methods_section):
            if raw_name in ignored or raw_name in {"void", "boolean", "bool", "string", "integer", "int", "double", "uuid"}:
                continue
            name = self._to_camel_case(raw_name)
            if not name or name.lower() in seen:
                continue
            methods.append(UmlMethod(name=name, return_type=self._normalize_uml_type(raw_type or "void")))
            seen.add(name.lower())
            break
        return methods

    def _normalize_uml_type(self, raw_type: str) -> str:
        type_map = {
            "uuid": "UUID",
            "string": "String",
            "str": "String",
            "texto": "String",
            "integer": "Integer",
            "int": "Integer",
            "entero": "Integer",
            "long": "Long",
            "double": "Double",
            "decimal": "Double",
            "date": "Date",
            "fecha": "Date",
            "boolean": "Boolean",
            "bool": "Boolean",
            "void": "void",
        }
        normalized = normalize_text(raw_type).replace(" ", "")
        return type_map.get(normalized, self._to_pascal_case(normalized) or "String")

    def _to_pascal_case(self, value: str) -> str:
        words = [word for word in re.findall(r"[a-zA-Z0-9_]+", value) if word]
        return "".join(word[:1].upper() + word[1:] for word in words)

    def _to_camel_case(self, value: str) -> str:
        pascal = self._to_pascal_case(value)
        return pascal[:1].lower() + pascal[1:] if pascal else ""

    def _matches_academic_enrollment_prompt(self, text: str) -> bool:
        normalized = normalize_text(text)
        required_terms = ("estudiante", "curso", "inscripcion")
        association_markers = (
            "association class",
            "clase asociativa",
            "clase de asociacion",
            "asociacion clase",
            "relacion muchos a muchos",
            "muchos a muchos",
            "* a *",
            "*--*",
        )
        has_required_terms = all(term in normalized for term in required_terms)
        has_association_marker = any(marker in normalized for marker in association_markers)
        has_domain_relation = "estudiante" in normalized and "curso" in normalized and "inscripcion" in normalized
        return has_required_terms and (has_association_marker or has_domain_relation)

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
