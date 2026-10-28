from uuid import NAMESPACE_URL, UUID, uuid5

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core.config.settings import settings
from app.modules.acceso_usuarios.services.audit_service import AuditService
from app.modules.generacion_software.repositories.generation_repository import GenerationRepository
from app.modules.modelado_uml.engine.internal_model import (
    UmlDiagramModel,
)
from app.modules.modelado_uml.engine.text_parser import build_uml_from_text
from app.modules.modelado_uml.engine.validator import validate_internal_model
from app.modules.modelado_uml.engine.xmi import export_xmi, import_xmi
from app.modules.modelado_uml.models import (
    UmlAttribute,
    UmlClass,
    UmlDiagram,
    UmlMethod,
    UmlParameter,
    UmlRelationship,
    UmlVisualElement,
    XmiExchange,
)
from app.modules.modelado_uml.repositories.uml_repository import UmlRepository
from app.modules.modelado_uml.schemas.uml import (
    DiagramCreateRequest,
    DiagramModelResponse,
    MoveElementRequest,
    TextToUmlRequest,
    UmlAttributeCreateRequest,
    UmlAttributeUpdateRequest,
    UmlClassCreateRequest,
    UmlClassUpdateRequest,
    UmlMethodCreateRequest,
    UmlMethodUpdateRequest,
    UmlParameterCreateRequest,
    UmlParameterUpdateRequest,
    UmlRelationshipCreateRequest,
    UmlRelationshipUpdateRequest,
    UmlValidationResponse,
    XmiExportResponse,
    XmiImportRequest,
)
from app.modules.modelado_uml.services.active_diagram_store import (
    ActiveUmlDocumentStore,
    build_sql_diagram_model,
    mark_uml_diagram_for_delete,
    mark_uml_project_for_sync,
)
from app.modules.modelado_uml.validators.uml_validator import (
    ensure_class_belongs_to_diagram,
    ensure_class_exists,
    ensure_diagram_exists,
)
from app.modules.proyectos_colaboracion.models import CollaborationEvent
from app.modules.proyectos_colaboracion.repositories.member_repository import MemberRepository
from app.modules.proyectos_colaboracion.services.project_mutation_guard import ProjectMutationGuard
from app.modules.proyectos_colaboracion.validators.project_validator import (
    ensure_membership,
    ensure_project_permission,
)


class UmlService:
    def __init__(self, db: Session) -> None:
        self.db = db
        if settings.nosql_consolidated_mode:
            from app.modules.modelado_uml.repositories.mongo_uml_repository import (
                MongoUmlRepository,
            )

            self.uml = MongoUmlRepository(db)
        else:
            self.uml = UmlRepository(db)
        self.generations = GenerationRepository(db)
        self.members = MemberRepository(db)
        self.audit = AuditService(db)
        self.mutations = ProjectMutationGuard(db)
        self.documents = ActiveUmlDocumentStore()

    def create_diagram(self, payload: DiagramCreateRequest, user_id: UUID) -> UmlDiagram:
        ensure_project_permission(self.db, payload.project_id, user_id, "uml.edit")
        existing = self.uml.list_diagrams_by_project(payload.project_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "PROJECT_DIAGRAM_ALREADY_EXISTS",
                    "message": "El proyecto ya tiene su diagrama de clases",
                    "diagram_id": str(existing[0].id),
                },
            )
        self._begin_mutation(payload.project_id)
        diagram = self.uml.add_diagram(
            UmlDiagram(
                project_id=payload.project_id,
                created_by_user_id=user_id,
                name=payload.name,
                diagram_type="class",
                description=payload.description,
                metadata_json=payload.metadata_json,
            )
        )
        self.audit.record(
            module="modelado_uml",
            action="CREATE_DIAGRAM",
            user_id=user_id,
            project_id=payload.project_id,
            metadata={"diagram_id": str(diagram.id)},
        )
        self.db.commit()
        self._refresh(diagram)
        return diagram

    def list_diagrams(self, project_id: UUID, user_id: UUID) -> list[UmlDiagram]:
        ensure_membership(self.members.get_membership(project_id, user_id))
        return self.uml.list_diagrams_by_project(project_id)

    def delete_diagram(self, diagram_id: UUID, user_id: UUID) -> None:
        diagram = ensure_diagram_exists(self.uml.get_diagram(diagram_id))
        ensure_membership(self.members.get_membership(diagram.project_id, user_id))
        self._begin_mutation(diagram.project_id)
        mark_uml_diagram_for_delete(self.db, diagram.id)
        self.generations.delete_generation_tree_by_diagram(diagram_id)
        self.uml.delete_visual_elements_by_diagram(diagram_id)
        self.uml.delete_relationships_by_diagram(diagram_id)
        self.uml.delete_classes_by_diagram(diagram_id)
        self.uml.delete_xmi_exchanges_by_diagram(diagram_id)
        self._detach_collaboration_events(diagram_id)
        self.uml.delete_diagram(diagram)
        self.audit.record(
            module="modelado_uml",
            action="DELETE_DIAGRAM",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"diagram_id": str(diagram_id)},
        )
        self.db.commit()

    def _ensure_unique_class_name(
        self, diagram_id: UUID, name: str, exclude_id: UUID | None = None
    ) -> None:
        normalized_target = name.strip().casefold()
        existing_classes = self.uml.list_classes(diagram_id)
        for cls in existing_classes:
            if exclude_id and cls.id == exclude_id:
                continue
            if cls.name.strip().casefold() == normalized_target:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "CLASS_NAME_DUPLICATED",
                        "message": "Ya existe una clase con ese nombre en el diagrama",
                    },
                )

    def create_class(
        self, diagram_id: UUID, payload: UmlClassCreateRequest, user_id: UUID
    ) -> UmlClass:
        diagram = ensure_diagram_exists(self.uml.get_diagram(diagram_id))
        ensure_project_permission(self.db, diagram.project_id, user_id, "uml.edit")
        self._ensure_unique_class_name(diagram_id, payload.name)
        self._begin_mutation(diagram.project_id)
        uml_class = self.uml.add_class(
            UmlClass(
                diagram_id=diagram_id,
                name=payload.name,
                visibility=payload.visibility,
                element_type=payload.element_type,
                stereotype=payload.stereotype,
                description=payload.description,
                metadata_json=payload.metadata_json,
            )
        )
        self.uml.add_visual_element(
            UmlVisualElement(
                diagram_id=diagram_id,
                element_type="class",
                element_id=uml_class.id,
                position_x=payload.position_x,
                position_y=payload.position_y,
            )
        )
        self.audit.record(
            module="modelado_uml",
            action="CREATE_CLASS",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"diagram_id": str(diagram_id), "class_id": str(uml_class.id)},
        )
        self.db.commit()
        self._refresh(uml_class)
        return uml_class

    def list_classes(self, diagram_id: UUID, user_id: UUID) -> list[UmlClass]:
        diagram = ensure_diagram_exists(self.uml.get_diagram(diagram_id))
        ensure_membership(self.members.get_membership(diagram.project_id, user_id))
        return self.uml.list_classes(diagram_id)

    def get_diagram_model(self, diagram_id: UUID, user_id: UUID) -> DiagramModelResponse:
        diagram = ensure_diagram_exists(self.uml.get_diagram(diagram_id))
        ensure_membership(self.members.get_membership(diagram.project_id, user_id))
        model = self._build_internal_model(diagram)
        class_details = []
        for item in model.classes:
            class_id = UUID(item.id) if item.id else uuid5(NAMESPACE_URL, item.name)
            visual_id = (
                UUID(item.visual.id)
                if item.visual.id
                else uuid5(NAMESPACE_URL, f"visual:{diagram_id}:{class_id}")
            )
            class_details.append(
                {
                    **item.model_dump(exclude={"attributes", "methods", "visual"}),
                    "id": class_id,
                    "diagram_id": diagram_id,
                    "attributes": [
                        {**attribute.model_dump(), "id": UUID(attribute.id), "class_id": class_id}
                        for attribute in item.attributes
                        if attribute.id
                    ],
                    "methods": [
                        {
                            **method.model_dump(
                                exclude={"parameters", "specification", "readiness"}
                            ),
                            "id": UUID(method.id),
                            "class_id": class_id,
                            "parameters": [
                                {
                                    **parameter.model_dump(),
                                    "id": UUID(parameter.id),
                                    "method_id": UUID(method.id),
                                }
                                for parameter in method.parameters
                                if parameter.id
                            ],
                        }
                        for method in item.methods
                        if method.id
                    ],
                    "visual": {
                        "id": visual_id,
                        "diagram_id": diagram_id,
                        "element_type": "class",
                        "element_id": class_id,
                        "position_x": item.visual.x,
                        "position_y": item.visual.y,
                        "width": item.visual.width,
                        "height": item.visual.height,
                        "style": item.visual.style,
                    },
                }
            )
        return DiagramModelResponse.model_validate(
            {
                "diagram": {
                    "id": diagram.id,
                    "project_id": diagram.project_id,
                    "created_by_user_id": diagram.created_by_user_id,
                    "name": model.name,
                    "diagram_type": model.diagram_type,
                    "status": model.status,
                    "current_version": model.current_version,
                    "description": model.description,
                    "metadata_json": model.metadata_json,
                    "created_at": diagram.created_at,
                },
                "classes": class_details,
                "relationships": [
                    {
                        **item.model_dump(),
                        "id": UUID(item.id),
                        "diagram_id": diagram_id,
                        "source_class_id": UUID(item.source_class_id),
                        "target_class_id": UUID(item.target_class_id),
                    }
                    for item in model.relationships
                    if item.id
                ],
            }
        )

    def update_class(
        self, class_id: UUID, payload: UmlClassUpdateRequest, user_id: UUID
    ) -> UmlClass:
        uml_class = ensure_class_exists(self.uml.get_class(class_id))
        diagram = ensure_diagram_exists(self.uml.get_diagram(uml_class.diagram_id))
        ensure_project_permission(self.db, diagram.project_id, user_id, "uml.edit")
        if payload.name is not None:
            self._ensure_unique_class_name(diagram.id, payload.name, exclude_id=class_id)
        self._begin_mutation(diagram.project_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(uml_class, field, value)
        self.audit.record(
            module="modelado_uml",
            action="UPDATE_CLASS",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"class_id": str(class_id)},
        )
        self.db.commit()
        self._refresh(uml_class)
        return uml_class

    def delete_class(self, class_id: UUID, user_id: UUID) -> None:
        uml_class = ensure_class_exists(self.uml.get_class(class_id))
        diagram = ensure_diagram_exists(self.uml.get_diagram(uml_class.diagram_id))
        ensure_project_permission(self.db, diagram.project_id, user_id, "uml.edit")
        self._begin_mutation(diagram.project_id)
        for relationship in self.uml.list_relationships_for_class(class_id):
            self.uml.delete_visual_element(diagram.id, "relationship", relationship.id)
            self.uml.delete_relationship(relationship)
        self.db.flush()
        self.uml.delete_visual_element(diagram.id, "class", class_id)
        self.uml.delete_class(uml_class)
        self.audit.record(
            module="modelado_uml",
            action="DELETE_CLASS",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"class_id": str(class_id)},
        )
        self.db.commit()

    def add_attribute(
        self, class_id: UUID, payload: UmlAttributeCreateRequest, user_id: UUID
    ) -> UmlAttribute:
        uml_class = ensure_class_exists(self.uml.get_class(class_id))
        diagram = ensure_diagram_exists(self.uml.get_diagram(uml_class.diagram_id))
        ensure_project_permission(self.db, diagram.project_id, user_id, "uml.edit")
        self._begin_mutation(diagram.project_id)
        attribute = self.uml.add_attribute(UmlAttribute(class_id=class_id, **payload.model_dump()))
        self.audit.record(
            module="modelado_uml",
            action="CREATE_ATTRIBUTE",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"class_id": str(class_id), "attribute_id": str(attribute.id)},
        )
        self.db.commit()
        self._refresh(attribute)
        return attribute

    def update_attribute(
        self, attribute_id: UUID, payload: UmlAttributeUpdateRequest, user_id: UUID
    ) -> UmlAttribute:
        from fastapi import HTTPException, status

        attribute = self.uml.get_attribute(attribute_id)
        if attribute is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Atributo UML no encontrado"
            )
        uml_class = ensure_class_exists(self.uml.get_class(attribute.class_id))
        diagram = ensure_diagram_exists(self.uml.get_diagram(uml_class.diagram_id))
        ensure_project_permission(self.db, diagram.project_id, user_id, "uml.edit")
        self._begin_mutation(diagram.project_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(attribute, field, value)
        self.audit.record(
            module="modelado_uml",
            action="UPDATE_ATTRIBUTE",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"attribute_id": str(attribute_id), "class_id": str(attribute.class_id)},
        )
        self.db.commit()
        self._refresh(attribute)
        return attribute

    def delete_attribute(self, attribute_id: UUID, user_id: UUID) -> None:
        from fastapi import HTTPException, status

        attribute = self.uml.get_attribute(attribute_id)
        if attribute is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Atributo UML no encontrado"
            )
        uml_class = ensure_class_exists(self.uml.get_class(attribute.class_id))
        diagram = ensure_diagram_exists(self.uml.get_diagram(uml_class.diagram_id))
        ensure_project_permission(self.db, diagram.project_id, user_id, "uml.edit")
        self._begin_mutation(diagram.project_id)
        self.uml.delete_attribute(attribute)
        self.audit.record(
            module="modelado_uml",
            action="DELETE_ATTRIBUTE",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"attribute_id": str(attribute_id), "class_id": str(uml_class.id)},
        )
        self.db.commit()

    def add_method(
        self, class_id: UUID, payload: UmlMethodCreateRequest, user_id: UUID
    ) -> UmlMethod:
        uml_class = ensure_class_exists(self.uml.get_class(class_id))
        diagram = ensure_diagram_exists(self.uml.get_diagram(uml_class.diagram_id))
        ensure_project_permission(self.db, diagram.project_id, user_id, "uml.edit")
        self._begin_mutation(diagram.project_id)
        method = self.uml.add_method(UmlMethod(class_id=class_id, **payload.model_dump()))
        self.audit.record(
            module="modelado_uml",
            action="CREATE_METHOD",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"class_id": str(class_id), "method_id": str(method.id)},
        )
        self.db.commit()
        self._refresh(method)
        return method

    def update_method(
        self, method_id: UUID, payload: UmlMethodUpdateRequest, user_id: UUID
    ) -> UmlMethod:
        from fastapi import HTTPException, status

        method = self.uml.get_method(method_id)
        if method is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Metodo UML no encontrado"
            )
        uml_class = ensure_class_exists(self.uml.get_class(method.class_id))
        diagram = ensure_diagram_exists(self.uml.get_diagram(uml_class.diagram_id))
        ensure_project_permission(self.db, diagram.project_id, user_id, "uml.edit")
        self._begin_mutation(diagram.project_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(method, field, value)
        self.audit.record(
            module="modelado_uml",
            action="UPDATE_METHOD",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"method_id": str(method_id), "class_id": str(method.class_id)},
        )
        self.db.commit()
        self._refresh(method)
        return method

    def delete_method(self, method_id: UUID, user_id: UUID) -> None:
        from fastapi import HTTPException, status

        method = self.uml.get_method(method_id)
        if method is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Metodo UML no encontrado"
            )
        uml_class = ensure_class_exists(self.uml.get_class(method.class_id))
        diagram = ensure_diagram_exists(self.uml.get_diagram(uml_class.diagram_id))
        ensure_project_permission(self.db, diagram.project_id, user_id, "uml.edit")
        self._begin_mutation(diagram.project_id)
        self.uml.delete_method(method)
        self.audit.record(
            module="modelado_uml",
            action="DELETE_METHOD",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"method_id": str(method_id), "class_id": str(uml_class.id)},
        )
        self.db.commit()

    def add_parameter(
        self, method_id: UUID, payload: UmlParameterCreateRequest, user_id: UUID
    ) -> UmlParameter:
        method = self.uml.get_method(method_id)
        if method is None:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Metodo UML no encontrado"
            )
        uml_class = ensure_class_exists(self.uml.get_class(method.class_id))
        diagram = ensure_diagram_exists(self.uml.get_diagram(uml_class.diagram_id))
        ensure_project_permission(self.db, diagram.project_id, user_id, "uml.edit")
        self._begin_mutation(diagram.project_id)
        self._validate_parameter(method, payload.name, payload.data_type, payload.default_value)
        parameter = self.uml.add_parameter(
            UmlParameter(method_id=method_id, **payload.model_dump())
        )
        self.audit.record(
            module="modelado_uml",
            action="CREATE_PARAMETER",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"method_id": str(method_id), "parameter_id": str(parameter.id)},
        )
        self.db.commit()
        self._refresh(parameter)
        return parameter

    def update_parameter(
        self, parameter_id: UUID, payload: UmlParameterUpdateRequest, user_id: UUID
    ) -> UmlParameter:
        parameter = self.uml.get_parameter(parameter_id)
        if parameter is None:
            raise HTTPException(status_code=404, detail="Parametro UML no encontrado")
        method = self.uml.get_method(parameter.method_id)
        uml_class = ensure_class_exists(self.uml.get_class(method.class_id))
        diagram = ensure_diagram_exists(self.uml.get_diagram(uml_class.diagram_id))
        ensure_project_permission(self.db, diagram.project_id, user_id, "uml.edit")
        self._begin_mutation(diagram.project_id)
        values = payload.model_dump(exclude_unset=True)
        self._validate_parameter(
            method,
            values.get("name", parameter.name),
            values.get("data_type", parameter.data_type),
            values.get("default_value", parameter.default_value),
            exclude_id=parameter.id,
        )
        for field, value in values.items():
            setattr(parameter, field, value)
        self.audit.record(
            module="modelado_uml",
            action="UPDATE_PARAMETER",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"method_id": str(method.id), "parameter_id": str(parameter.id)},
        )
        self.db.commit()
        self._refresh(parameter)
        return parameter

    def delete_parameter(self, parameter_id: UUID, user_id: UUID) -> None:
        parameter = self.uml.get_parameter(parameter_id)
        if parameter is None:
            raise HTTPException(status_code=404, detail="Parametro UML no encontrado")
        method = self.uml.get_method(parameter.method_id)
        uml_class = ensure_class_exists(self.uml.get_class(method.class_id))
        diagram = ensure_diagram_exists(self.uml.get_diagram(uml_class.diagram_id))
        ensure_project_permission(self.db, diagram.project_id, user_id, "uml.edit")
        self._begin_mutation(diagram.project_id)
        specification = self.uml.get_method_specification(method.id)
        if specification and self._parameter_is_referenced(
            specification, parameter.id, parameter.name
        ):
            raise HTTPException(
                status_code=409,
                detail="El parametro esta referenciado por la especificacion funcional",
            )
        self.uml.delete_parameter(parameter)
        self.audit.record(
            module="modelado_uml",
            action="DELETE_PARAMETER",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"method_id": str(method.id), "parameter_id": str(parameter.id)},
        )
        self.db.commit()

    def _validate_parameter(
        self,
        method,
        name: str,
        data_type: str,
        default_value: str | None,
        *,
        exclude_id: UUID | None = None,
    ) -> None:
        if any(
            item.id != exclude_id and item.name.casefold() == name.casefold()
            for item in method.parameters
        ):
            raise HTTPException(
                status_code=409, detail="El metodo ya contiene un parametro con ese nombre"
            )
        normalized = data_type.casefold()
        if default_value not in {None, ""}:
            compatible = True
            try:
                if normalized in {"int", "integer", "long"}:
                    int(default_value)
                elif normalized in {"float", "double", "decimal"}:
                    float(default_value)
                elif normalized in {"bool", "boolean"}:
                    compatible = default_value.casefold() in {"true", "false"}
            except ValueError:
                compatible = False
            if not compatible:
                raise HTTPException(
                    status_code=422, detail="El valor por defecto no coincide con el tipo"
                )

    @staticmethod
    def _parameter_is_referenced(specification, parameter_id: UUID, name: str) -> bool:
        serialized = str(
            {
                "preconditions": specification.preconditions,
                "postconditions": specification.postconditions,
                "business_rules": specification.business_rules,
                "validations": specification.validations,
                "related_entities": specification.related_entities,
                "frontend_contract": specification.frontend_contract,
            }
        )
        return (
            str(parameter_id) in serialized
            or f"'{name}'" in serialized
            or f'"{name}"' in serialized
        )

    def create_relationship(
        self, diagram_id: UUID, payload: UmlRelationshipCreateRequest, user_id: UUID
    ) -> UmlRelationship:
        diagram = ensure_diagram_exists(self.uml.get_diagram(diagram_id))
        ensure_project_permission(self.db, diagram.project_id, user_id, "uml.edit")
        self._begin_mutation(diagram.project_id)
        source = ensure_class_exists(self.uml.get_class(payload.source_class_id))
        target = ensure_class_exists(self.uml.get_class(payload.target_class_id))
        ensure_class_belongs_to_diagram(source, diagram_id)
        ensure_class_belongs_to_diagram(target, diagram_id)
        relationship = self.uml.add_relationship(
            UmlRelationship(diagram_id=diagram_id, **payload.model_dump())
        )
        self.audit.record(
            module="modelado_uml",
            action="CREATE_RELATION",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"relationship_id": str(relationship.id)},
        )
        self.db.commit()
        self._refresh(relationship)
        return relationship

    def update_relationship(
        self, relationship_id: UUID, payload: UmlRelationshipUpdateRequest, user_id: UUID
    ) -> UmlRelationship:
        relationship = self.uml.get_relationship(relationship_id)
        if relationship is None:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Relacion UML no encontrada"
            )
        diagram = ensure_diagram_exists(self.uml.get_diagram(relationship.diagram_id))
        ensure_project_permission(self.db, diagram.project_id, user_id, "uml.edit")
        self._begin_mutation(diagram.project_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(relationship, field, value)
        self.audit.record(
            module="modelado_uml",
            action="UPDATE_RELATION",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"relationship_id": str(relationship_id)},
        )
        self.db.commit()
        self._refresh(relationship)
        return relationship

    def delete_relationship(self, relationship_id: UUID, user_id: UUID) -> None:
        relationship = self.uml.get_relationship(relationship_id)
        if relationship is None:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Relacion UML no encontrada"
            )
        diagram = ensure_diagram_exists(self.uml.get_diagram(relationship.diagram_id))
        ensure_project_permission(self.db, diagram.project_id, user_id, "uml.edit")
        self._begin_mutation(diagram.project_id)
        self.uml.delete_visual_element(diagram.id, "relationship", relationship_id)
        self.uml.delete_relationship(relationship)
        self.audit.record(
            module="modelado_uml",
            action="DELETE_RELATION",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"relationship_id": str(relationship_id)},
        )
        self.db.commit()

    def move_element(
        self, diagram_id: UUID, payload: MoveElementRequest, user_id: UUID
    ) -> UmlVisualElement:
        diagram = ensure_diagram_exists(self.uml.get_diagram(diagram_id))
        ensure_project_permission(self.db, diagram.project_id, user_id, "uml.edit")
        self._begin_mutation(diagram.project_id)
        visual = self.uml.get_visual_element(diagram_id, payload.element_type, payload.element_id)
        if visual is None:
            visual = self.uml.add_visual_element(
                UmlVisualElement(
                    diagram_id=diagram_id,
                    element_type=payload.element_type,
                    element_id=payload.element_id,
                    position_x=payload.position_x,
                    position_y=payload.position_y,
                    width=payload.width,
                    height=payload.height,
                    style=payload.style,
                )
            )
        else:
            visual.position_x = payload.position_x
            visual.position_y = payload.position_y
            visual.width = payload.width
            visual.height = payload.height
            visual.style = payload.style
        self.audit.record(
            module="modelado_uml",
            action="MOVE_ELEMENT",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"element_type": payload.element_type, "element_id": str(payload.element_id)},
        )
        self.db.commit()
        self._refresh(visual)
        return visual

    def validate_diagram(self, diagram_id: UUID, user_id: UUID) -> UmlValidationResponse:
        diagram = ensure_diagram_exists(self.uml.get_diagram(diagram_id))
        ensure_membership(self.members.get_membership(diagram.project_id, user_id))
        model = self._build_internal_model(diagram)
        errors, warnings, recommendations = validate_internal_model(model)
        return UmlValidationResponse(
            diagram_id=diagram_id,
            errors=errors,
            warnings=warnings,
            recommendations=recommendations,
        )

    def export_diagram_xmi(self, diagram_id: UUID, user_id: UUID) -> XmiExportResponse:
        diagram = ensure_diagram_exists(self.uml.get_diagram(diagram_id))
        ensure_membership(self.members.get_membership(diagram.project_id, user_id))
        content = export_xmi(self._build_internal_model(diagram))
        file_name = f"{diagram.name.lower().replace(' ', '-')}.xml"
        self.uml.add_xmi_exchange(
            XmiExchange(
                diagram_id=diagram_id,
                user_id=user_id,
                exchange_type="export",
                tool_name="Enterprise Architect",
                file_name=file_name,
                status="completed",
                metadata_json={"format": "xmi"},
            )
        )
        self.audit.record(
            module="modelado_uml",
            action="EXPORT_XMI",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"diagram_id": str(diagram_id), "file_name": file_name},
        )
        self.db.commit()
        return XmiExportResponse(diagram_id=diagram_id, file_name=file_name, content=content)

    def import_diagram_xmi(self, payload: XmiImportRequest, user_id: UUID) -> UmlDiagram:
        ensure_project_permission(self.db, payload.project_id, user_id, "uml.edit")
        existing = self.uml.list_diagrams_by_project(payload.project_id)
        if existing:
            return self.import_diagram_xmi_into_existing(existing[0].id, payload, user_id)
        self._begin_mutation(payload.project_id)
        model = import_xmi(payload.content, payload.name)
        diagram = self._persist_internal_model(model, payload.project_id, user_id)
        self.uml.add_xmi_exchange(
            XmiExchange(
                diagram_id=diagram.id,
                user_id=user_id,
                exchange_type="import",
                tool_name=payload.tool_name,
                file_name=payload.file_name,
                status="completed",
                metadata_json={"class_count": len(model.classes)},
            )
        )
        self.audit.record(
            module="modelado_uml",
            action="IMPORT_XMI",
            user_id=user_id,
            project_id=payload.project_id,
            metadata={"diagram_id": str(diagram.id), "file_name": payload.file_name},
        )
        self.db.commit()
        self._refresh(diagram)
        return diagram

    def import_diagram_xmi_into_existing(
        self, diagram_id: UUID, payload: XmiImportRequest, user_id: UUID
    ) -> UmlDiagram:
        diagram = ensure_diagram_exists(self.uml.get_diagram(diagram_id))
        ensure_project_permission(self.db, diagram.project_id, user_id, "uml.edit")
        if diagram.project_id != payload.project_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="El diagrama no pertenece al proyecto indicado",
            )
        self._begin_mutation(diagram.project_id)
        model = import_xmi(payload.content, payload.name)

        self.generations.delete_generation_tree_by_diagram(diagram_id)
        self.uml.delete_visual_elements_by_diagram(diagram_id)
        self.uml.delete_relationships_by_diagram(diagram_id)
        self.uml.delete_classes_by_diagram(diagram_id)
        self.db.flush()

        diagram.name = payload.name
        diagram.diagram_type = model.diagram_type
        diagram.status = model.status
        diagram.current_version = model.current_version
        diagram.description = model.description
        diagram.metadata_json = {
            **diagram.metadata_json,
            **model.metadata_json,
            "imported_file_name": payload.file_name,
        }
        self._populate_existing_diagram_from_model(diagram, model)
        self.uml.add_xmi_exchange(
            XmiExchange(
                diagram_id=diagram.id,
                user_id=user_id,
                exchange_type="import",
                tool_name=payload.tool_name,
                file_name=payload.file_name,
                status="completed",
                metadata_json={"class_count": len(model.classes), "mode": "replace"},
            )
        )
        self.audit.record(
            module="modelado_uml",
            action="IMPORT_XMI_REPLACE_DIAGRAM",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"diagram_id": str(diagram.id), "file_name": payload.file_name},
        )
        self.db.commit()
        self._refresh(diagram)
        return diagram

    def generate_from_prompt(self, payload: TextToUmlRequest, user_id: UUID) -> UmlDiagram:
        ensure_project_permission(self.db, payload.project_id, user_id, "uml.edit")
        self._begin_mutation(payload.project_id)
        model = build_uml_from_text(payload.prompt, payload.name)
        existing = self.uml.list_diagrams_by_project(payload.project_id)
        if existing:
            diagram = existing[0]
            self.generations.delete_generation_tree_by_diagram(diagram.id)
            self.uml.delete_visual_elements_by_diagram(diagram.id)
            self.uml.delete_relationships_by_diagram(diagram.id)
            self.uml.delete_classes_by_diagram(diagram.id)
            self.db.flush()
            diagram.name = model.name
            diagram.diagram_type = model.diagram_type
            diagram.status = model.status
            diagram.current_version += 1
            diagram.description = model.description
            diagram.metadata_json = {
                **diagram.metadata_json,
                **model.metadata_json,
                "source_type": payload.source_type,
                "source_prompt": payload.prompt,
            }
            self._populate_existing_diagram_from_model(diagram, model)
        else:
            diagram = self._persist_internal_model(
                model,
                payload.project_id,
                user_id,
                metadata={"source_type": payload.source_type, "source_prompt": payload.prompt},
            )
        self.audit.record(
            module="modelado_uml",
            action="GENERATE_UML_FROM_SOURCE",
            user_id=user_id,
            project_id=payload.project_id,
            metadata={"diagram_id": str(diagram.id), "source_type": payload.source_type},
        )
        self.db.commit()
        self._refresh(diagram)
        return diagram

    def restore_project_snapshot(
        self, project_id: UUID, snapshot: dict, user_id: UUID
    ) -> list[UUID]:
        ensure_membership(self.members.get_membership(project_id, user_id))
        try:
            snapshot_models = [
                UmlDiagramModel.model_validate(item) for item in snapshot.get("diagrams", [])
            ]
            desired_ids = [UUID(model.id) for model in snapshot_models if model.id]
            if len(desired_ids) != len(snapshot_models):
                raise ValueError("Todos los diagramas del snapshot deben tener identificador")
            if len(set(desired_ids)) != len(desired_ids):
                raise ValueError("El snapshot contiene diagramas duplicados")
            if any(
                model.project_id and UUID(model.project_id) != project_id
                for model in snapshot_models
            ):
                raise ValueError("El snapshot pertenece a otro proyecto")
        except (TypeError, ValueError, ValidationError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="El snapshot de la version no es valido",
            ) from exc

        current_diagrams = {
            str(diagram.id): diagram for diagram in self.uml.list_diagrams_by_project(project_id)
        }
        snapshot_ids = {str(diagram_id) for diagram_id in desired_ids}

        for diagram_id, diagram in current_diagrams.items():
            self.generations.delete_generation_tree_by_diagram(diagram.id)
            if diagram_id not in snapshot_ids:
                self.uml.delete_visual_elements_by_diagram(diagram.id)
                self.uml.delete_relationships_by_diagram(diagram.id)
                self.uml.delete_classes_by_diagram(diagram.id)
                self.uml.delete_xmi_exchanges_by_diagram(diagram.id)
                self._detach_collaboration_events(diagram.id)
                self.uml.delete_diagram(diagram)

        self.db.flush()
        restored_ids: list[UUID] = []
        for model, desired_id in zip(snapshot_models, desired_ids, strict=True):
            diagram = current_diagrams.get(str(desired_id))
            if diagram is None:
                diagram = self.uml.add_diagram(
                    UmlDiagram(
                        id=desired_id,
                        project_id=project_id,
                        created_by_user_id=user_id,
                        name=model.name,
                        diagram_type=model.diagram_type,
                        status=model.status,
                        current_version=model.current_version + 1,
                        description=model.description,
                        metadata_json=model.metadata_json,
                    )
                )
            else:
                previous_revision = diagram.current_version
                self.uml.delete_visual_elements_by_diagram(diagram.id)
                self.uml.delete_relationships_by_diagram(diagram.id)
                self.uml.delete_classes_by_diagram(diagram.id)
                self.db.flush()
                diagram.name = model.name
                diagram.diagram_type = model.diagram_type
                diagram.status = model.status
                diagram.current_version = previous_revision + 1
                diagram.description = model.description
                diagram.metadata_json = model.metadata_json

            self._populate_existing_diagram_from_model(diagram, model)
            restored_ids.append(diagram.id)

        return restored_ids

    def _begin_mutation(self, project_id: UUID) -> None:
        project = self.mutations.acquire(project_id)
        self.mutations.advance(project)
        mark_uml_project_for_sync(self.db, project_id)

    def _refresh(self, item) -> None:
        if not settings.nosql_consolidated_mode or isinstance(item, UmlDiagram):
            self.db.refresh(item)

    def _detach_collaboration_events(self, diagram_id: UUID) -> None:
        self.db.execute(
            update(CollaborationEvent)
            .where(CollaborationEvent.diagram_id == diagram_id)
            .values(diagram_id=None)
        )

    def _build_internal_model(self, diagram: UmlDiagram) -> UmlDiagramModel:
        if settings.nosql_consolidated_mode:
            return self.uml.model(diagram)
        return self.documents.model_for(self.db, diagram)

    def _build_sql_internal_model(self, diagram: UmlDiagram) -> UmlDiagramModel:
        if settings.nosql_consolidated_mode:
            return self.uml.model(diagram)
        return build_sql_diagram_model(self.db, diagram)

    def _persist_internal_model(
        self,
        model: UmlDiagramModel,
        project_id: UUID,
        user_id: UUID,
        metadata: dict | None = None,
    ) -> UmlDiagram:
        diagram = self.uml.add_diagram(
            UmlDiagram(
                project_id=project_id,
                created_by_user_id=user_id,
                name=model.name,
                diagram_type=model.diagram_type,
                status=model.status,
                current_version=model.current_version,
                description=model.description,
                metadata_json={**model.metadata_json, **(metadata or {})},
            )
        )
        self._populate_existing_diagram_from_model(diagram, model)
        return diagram

    def _populate_existing_diagram_from_model(
        self, diagram: UmlDiagram, model: UmlDiagramModel
    ) -> None:
        id_by_external_ref: dict[str, UUID] = {}
        for uml_class_model in model.classes:
            uml_class = self.uml.add_class(
                UmlClass(
                    diagram_id=diagram.id,
                    name=uml_class_model.name,
                    visibility=uml_class_model.visibility,
                    element_type=uml_class_model.element_type,
                    stereotype=uml_class_model.stereotype,
                    description=uml_class_model.description,
                    metadata_json=uml_class_model.metadata_json,
                )
            )
            if uml_class_model.id:
                id_by_external_ref[uml_class_model.id] = uml_class.id
            id_by_external_ref[uml_class_model.name] = uml_class.id
            self.uml.add_visual_element(
                UmlVisualElement(
                    diagram_id=diagram.id,
                    element_type="class",
                    element_id=uml_class.id,
                    position_x=uml_class_model.visual.x,
                    position_y=uml_class_model.visual.y,
                    width=uml_class_model.visual.width,
                    height=uml_class_model.visual.height,
                    style=uml_class_model.visual.style,
                )
            )
            for attribute_model in uml_class_model.attributes:
                self.uml.add_attribute(
                    UmlAttribute(
                        class_id=uml_class.id, **attribute_model.model_dump(exclude={"id"})
                    )
                )
            for method_model in uml_class_model.methods:
                method = self.uml.add_method(
                    UmlMethod(
                        class_id=uml_class.id,
                        **method_model.model_dump(
                            exclude={"id", "parameters", "specification", "readiness"}
                        ),
                    )
                )
                if method_model.specification:
                    from app.modules.modelado_uml.models import UmlMethodSpecification
                    from app.modules.modelado_uml.schemas.method_specification import (
                        UmlMethodSpecificationBase,
                    )

                    try:
                        raw_values = dict(method_model.specification)
                        revision = max(1, int(raw_values.pop("revision", 1)))
                        raw_values.pop("readiness", None)
                        specification_values = UmlMethodSpecificationBase.model_validate(
                            raw_values
                        ).model_dump(mode="json")
                        specification_values["backend_contract"] = (
                            specification_values["backend_contract"] or {}
                        )
                        specification_values["frontend_contract"] = (
                            specification_values["frontend_contract"] or {}
                        )
                        self.uml.add_method_specification(
                            UmlMethodSpecification(
                                method_id=method.id,
                                revision=revision,
                                **specification_values,
                            )
                        )
                    except (TypeError, ValueError, ValidationError):
                        pass
                for parameter_model in method_model.parameters:
                    self.uml.add_parameter(
                        UmlParameter(
                            method_id=method.id, **parameter_model.model_dump(exclude={"id"})
                        )
                    )
        for relationship_model in model.relationships:
            source_id = id_by_external_ref.get(relationship_model.source_class_id)
            target_id = id_by_external_ref.get(relationship_model.target_class_id)
            if source_id and target_id:
                metadata_json = dict(relationship_model.metadata_json)
                association_class_id = metadata_json.get("association_class_id")
                if association_class_id in id_by_external_ref:
                    metadata_json["association_class_id"] = str(
                        id_by_external_ref[association_class_id]
                    )
                self.uml.add_relationship(
                    UmlRelationship(
                        diagram_id=diagram.id,
                        source_class_id=source_id,
                        target_class_id=target_id,
                        relationship_type=relationship_model.relationship_type,
                        source_cardinality=relationship_model.source_cardinality,
                        target_cardinality=relationship_model.target_cardinality,
                        direction=relationship_model.direction,
                        label=relationship_model.label,
                        metadata_json=metadata_json,
                    )
                )
