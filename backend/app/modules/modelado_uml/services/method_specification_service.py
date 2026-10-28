import re
from dataclasses import dataclass
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config.settings import settings
from app.modules.acceso_usuarios.services.audit_service import AuditService
from app.modules.asistente_proyecto.models import AiAction
from app.modules.asistente_proyecto.repositories.assistant_repository import AssistantRepository
from app.modules.asistente_proyecto.schemas.assistant import AiMessageCreateInternal
from app.modules.asistente_proyecto.services.assistant_service import AssistantContractService
from app.modules.modelado_uml.models import UmlMethodSpecification
from app.modules.modelado_uml.repositories.uml_repository import UmlRepository
from app.modules.modelado_uml.schemas.method_specification import (
    BackendMethodContract,
    FlutterFieldContract,
    FlutterMethodContract,
    MethodDiagnostic,
    MethodSpecificationEnvelope,
    MethodSpecificationProposalResponse,
    MethodSpecificationRefineRequest,
    MethodSpecificationValidationResponse,
    RelatedEntityReference,
    UmlMethodSpecificationBase,
    UmlMethodSpecificationCreate,
    UmlMethodSpecificationPatch,
    UmlMethodSpecificationResponse,
)
from app.modules.modelado_uml.services.active_diagram_store import mark_uml_project_for_sync
from app.modules.proyectos_colaboracion.repositories.member_repository import MemberRepository
from app.modules.proyectos_colaboracion.services.project_mutation_guard import ProjectMutationGuard
from app.modules.proyectos_colaboracion.validators.project_validator import ensure_membership


@dataclass
class MethodContext:
    method: object
    uml_class: object
    diagram: object
    member: object


class MethodSpecificationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        if settings.nosql_consolidated_mode:
            from app.modules.modelado_uml.repositories.mongo_uml_repository import (
                MongoUmlRepository,
            )

            self.uml = MongoUmlRepository(db)
        else:
            self.uml = UmlRepository(db)
        self.members = MemberRepository(db)
        self.audit = AuditService(db)
        self.mutations = ProjectMutationGuard(db)

    def event_context(self, method_id: UUID, user_id: UUID) -> MethodContext:
        return self._context(method_id, user_id)

    def get(self, method_id: UUID, user_id: UUID) -> MethodSpecificationEnvelope:
        context = self._context(method_id, user_id)
        specification = self.uml.get_method_specification(context.method.id)
        return MethodSpecificationEnvelope(
            specification=(
                UmlMethodSpecificationResponse.model_validate(specification)
                if specification
                else None
            ),
            readiness=self.validate_model(context, specification, strict=False),
        )

    def put(
        self,
        method_id: UUID,
        payload: UmlMethodSpecificationCreate,
        user_id: UUID,
        *,
        expected_revision: int | None = None,
        create_only: bool = False,
        commit: bool = True,
    ) -> UmlMethodSpecification:
        context = self._context(method_id, user_id, require_edit=True)
        self.mutations.advance(self.mutations.acquire(context.diagram.project_id))
        mark_uml_project_for_sync(self.db, context.diagram.project_id)
        current = self.uml.get_method_specification_for_update(context.method.id)
        if create_only and current is not None:
            self._conflict(current.revision)
        if current is None and expected_revision not in {None, 0}:
            self._conflict(0)
        if current is not None and expected_revision != current.revision:
            self._conflict(current.revision)
        normalized = UmlMethodSpecificationCreate.model_validate(payload.model_dump())
        self._assert_structural_references(context, normalized)
        old_revision = current.revision if current else 0
        values = self._persistence_values(normalized)
        if current is None:
            current = self.uml.add_method_specification(
                UmlMethodSpecification(method_id=context.method.id, revision=1, **values)
            )
            action = "CREATE_METHOD_SPECIFICATION"
        else:
            for key, value in values.items():
                setattr(current, key, value)
            current.revision += 1
            action = "UPDATE_METHOD_SPECIFICATION"
        self._audit(context, user_id, action, old_revision, current.revision, list(values))
        if commit:
            try:
                self.db.commit()
            except IntegrityError:
                self.db.rollback()
                concurrent = self.uml.get_method_specification(context.method.id)
                self._conflict(concurrent.revision if concurrent else 0)
            if not settings.nosql_consolidated_mode:
                self.db.refresh(current)
        else:
            self.db.flush()
        return current

    def patch(
        self,
        method_id: UUID,
        payload: UmlMethodSpecificationPatch,
        user_id: UUID,
        *,
        expected_revision: int,
    ) -> UmlMethodSpecification:
        context = self._context(method_id, user_id, require_edit=True)
        self.mutations.advance(self.mutations.acquire(context.diagram.project_id))
        mark_uml_project_for_sync(self.db, context.diagram.project_id)
        current = self.uml.get_method_specification_for_update(context.method.id)
        if current is None:
            raise HTTPException(status_code=404, detail="Especificacion de metodo no encontrada")
        if current.revision != expected_revision:
            self._conflict(current.revision)
        merged = {
            **self._model_from_orm(current).model_dump(),
            **payload.model_dump(exclude_unset=True),
        }
        try:
            validated = UmlMethodSpecificationBase.model_validate(merged)
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=exc.errors()) from exc
        self._assert_structural_references(context, validated)
        changed = list(payload.model_dump(exclude_unset=True))
        for key, value in self._persistence_values(validated).items():
            setattr(current, key, value)
        old_revision = current.revision
        current.revision += 1
        self._audit(
            context, user_id, "UPDATE_METHOD_SPECIFICATION", old_revision, current.revision, changed
        )
        self.db.commit()
        if not settings.nosql_consolidated_mode:
            self.db.refresh(current)
        return current

    def delete(self, method_id: UUID, user_id: UUID, *, expected_revision: int) -> MethodContext:
        context = self._context(method_id, user_id, require_edit=True)
        self.mutations.advance(self.mutations.acquire(context.diagram.project_id))
        mark_uml_project_for_sync(self.db, context.diagram.project_id)
        current = self.uml.get_method_specification_for_update(context.method.id)
        if current is None:
            raise HTTPException(status_code=404, detail="Especificacion de metodo no encontrada")
        if current.revision != expected_revision:
            self._conflict(current.revision)
        self._audit(
            context,
            user_id,
            "DELETE_METHOD_SPECIFICATION",
            current.revision,
            0,
            ["specification"],
        )
        self.uml.delete_method_specification(current)
        self.db.commit()
        return context

    def validate(
        self, method_id: UUID, user_id: UUID, *, strict: bool
    ) -> MethodSpecificationValidationResponse:
        context = self._context(method_id, user_id)
        return self.validate_model(
            context,
            self.uml.get_method_specification(context.method.id),
            strict=strict,
        )

    def validate_model(
        self,
        context: MethodContext,
        specification: UmlMethodSpecification | UmlMethodSpecificationBase | None,
        *,
        strict: bool,
        proposed: bool = False,
    ) -> MethodSpecificationValidationResponse:
        if specification is None:
            return MethodSpecificationValidationResponse(
                status="legacy", ready_for_generation=False
            )
        model = (
            specification
            if isinstance(specification, UmlMethodSpecificationBase)
            else self._model_from_orm(specification)
        )
        errors: list[MethodDiagnostic] = []
        warnings: list[MethodDiagnostic] = []

        def issue(code: str, path: str, message: str, suggestion: str, blocking=True):
            target = errors if blocking else warnings
            target.append(
                MethodDiagnostic(
                    code=code,
                    severity="error" if blocking else "warning",
                    path=path,
                    message=message,
                    suggestion=suggestion,
                )
            )

        substantive = bool(
            model.description
            or model.operation_kind != "custom"
            or model.backend_contract
            or model.frontend_contract
            or model.preconditions
            or model.business_rules
        )
        if not substantive:
            return MethodSpecificationValidationResponse(status="empty", ready_for_generation=False)
        if not model.description:
            issue(
                "missing_description",
                "description",
                "Falta la descripcion funcional",
                "Describa el resultado observable del metodo",
                strict,
            )
        if context.method.visibility == "private" and model.exposure != "internal":
            issue(
                "private_method_exposed",
                "exposure",
                "Un metodo privado no puede exponerse",
                "Cambie la visibilidad o use exposicion internal",
            )
        if model.exposure in {"api", "user_action"} and model.backend_contract is None:
            issue(
                "missing_backend_contract",
                "backend_contract",
                "La operacion expuesta necesita contrato backend",
                "Defina metodo HTTP y ruta",
                strict,
            )
        if model.exposure == "user_action" and model.frontend_contract is None:
            issue(
                "missing_flutter_contract",
                "frontend_contract",
                "La accion visible necesita contrato Flutter",
                "Defina interaccion, etiqueta y campos",
                strict,
            )
        if model.exposure == "internal" and (model.backend_contract or model.frontend_contract):
            issue(
                "internal_with_public_contract",
                "exposure",
                "El metodo interno conserva contratos publicos",
                "Limpie los contratos o cambie la exposicion",
                False,
            )
        self._validate_rule_collections(model, context, issue)
        self._validate_related_entities(model, context, issue)
        self._validate_backend(model, context, issue)
        self._validate_flutter(model, context, issue, strict)
        if (
            model.operation_kind == "delete"
            and model.frontend_contract
            and not model.frontend_contract.confirmation_required
        ):
            issue(
                "delete_requires_confirmation",
                "frontend_contract.confirmation_required",
                "Una eliminacion visible requiere confirmacion",
                "Active la confirmacion",
            )
        readiness = (
            "invalid"
            if errors
            else ("needs_review" if proposed else ("ready" if strict else "draft"))
        )
        return MethodSpecificationValidationResponse(
            status=readiness,
            ready_for_generation=not errors and strict,
            errors=errors,
            warnings=warnings,
        )

    def refine(
        self, method_id: UUID, payload: MethodSpecificationRefineRequest, user_id: UUID
    ) -> tuple[MethodSpecificationProposalResponse, AiAction, MethodContext]:
        context = self._context(method_id, user_id)
        current = self.uml.get_method_specification(context.method.id)
        revision = current.revision if current else 0
        if payload.base_revision != revision:
            self._conflict(revision)
        patch, unresolved, assumptions = self._infer_patch(context, payload.instruction, current)
        base = self._model_from_orm(current) if current else UmlMethodSpecificationBase()
        merged = UmlMethodSpecificationBase.model_validate(
            {**base.model_dump(), **patch.model_dump(exclude_unset=True)}
        )
        self._assert_structural_references(context, merged)
        validation = self.validate_model(context, merged, strict=True, proposed=True)
        contracts = AssistantContractService(self.db)
        conversation = contracts.get_conversation(context.diagram.project_id, user_id)
        correlation_id = uuid4()
        user_message, created = contracts.create_message(
            context.diagram.project_id,
            user_id,
            AiMessageCreateInternal(
                role="user",
                content=payload.instruction,
                client_message_id=payload.client_message_id,
                correlation_id=correlation_id,
            ),
        )
        if not created:
            existing_action = AssistantRepository(self.db).get_action_by_idempotency(
                context.diagram.project_id, payload.client_message_id
            )
            if existing_action is None:
                raise HTTPException(status_code=409, detail="El refinamiento ya esta en proceso")
            stored_payload = {
                key: value for key, value in existing_action.payload.items() if key != "_plan"
            }
            stored_patch = UmlMethodSpecificationPatch.model_validate(stored_payload)
            return (
                MethodSpecificationProposalResponse(
                    action_id=existing_action.id,
                    method_id=context.method.id,
                    base_revision=revision,
                    summary=f"Propuesta funcional para {context.method.name}",
                    patch=stored_patch,
                    changed_fields=list(stored_patch.model_fields_set),
                    unresolved_references=unresolved,
                    assumptions=assumptions,
                    validation=validation,
                    provider="rule_engine",
                ),
                existing_action,
                context,
            )
        assistant_message, _ = contracts.create_message(
            context.diagram.project_id,
            user_id,
            AiMessageCreateInternal(
                role="assistant",
                content=f"Prepare una propuesta para {context.method.name}. Revisa los campos antes de aplicarla.",
                correlation_id=correlation_id,
                status="completed",
                references=[],
                metadata_json={"provider": "rule_engine", "phase": 4},
            ),
        )
        action = AiAction(
            project_id=context.diagram.project_id,
            conversation_id=conversation.id,
            source_message_id=assistant_message.id,
            requested_by_user_id=user_id,
            action_type="update_method_specification",
            target_type="uml_method",
            target_id=context.method.id,
            payload={
                **merged.model_dump(mode="json", exclude_none=True),
                "_plan": {
                    "diagram_id": str(context.diagram.id),
                    "base_spec_revision": revision,
                    "client_message_id": str(payload.client_message_id),
                },
            },
            risk_level="medium",
            requires_confirmation=True,
            status="proposed",
            idempotency_key=payload.client_message_id,
        )
        self.db.add(action)
        self.audit.record(
            module="modelado_uml",
            action="REFINE_METHOD_SPECIFICATION",
            user_id=user_id,
            project_id=context.diagram.project_id,
            metadata={
                "diagram_id": str(context.diagram.id),
                "class_id": str(context.uml_class.id),
                "method_id": str(context.method.id),
                "correlation_id": str(correlation_id),
                "base_revision": revision,
                "provider": "rule_engine",
            },
        )
        user_message.status = "completed"
        contracts.repository.save_message(user_message)
        self.db.commit()
        self.db.refresh(action)
        changed = list(patch.model_dump(exclude_unset=True))
        return (
            MethodSpecificationProposalResponse(
                action_id=action.id,
                method_id=context.method.id,
                base_revision=revision,
                summary=f"Propuesta funcional para {context.method.name}",
                patch=patch,
                changed_fields=changed,
                unresolved_references=unresolved,
                assumptions=assumptions,
                validation=validation,
                provider="rule_engine",
            ),
            action,
            context,
        )

    def _context(
        self, method_id: UUID, user_id: UUID, *, require_edit: bool = False
    ) -> MethodContext:
        method = self.uml.get_method(method_id)
        if method is None:
            raise HTTPException(status_code=404, detail="Metodo UML no encontrado")
        uml_class = self.uml.get_class(method.class_id)
        diagram = self.uml.get_diagram(uml_class.diagram_id) if uml_class else None
        if diagram is None:
            raise HTTPException(status_code=404, detail="Metodo UML no encontrado")
        member = ensure_membership(self.members.get_membership(diagram.project_id, user_id))
        if require_edit and member.project_role not in {"EDITOR", "ORGANIZADOR"}:
            raise HTTPException(status_code=403, detail="Se requiere permiso de edicion UML")
        return MethodContext(method, uml_class, diagram, member)

    def _assert_structural_references(
        self, context: MethodContext, payload: UmlMethodSpecificationBase
    ) -> None:
        result = self.validate_model(context, payload, strict=False)
        structural = {
            "unknown_related_entity",
            "foreign_related_entity",
            "unknown_parameter",
            "foreign_parameter",
            "unknown_attribute",
            "unknown_source_entity",
            "unknown_display_field",
            "unknown_refresh_target",
            "ambiguous_entity",
        }
        failures = [item for item in result.errors if item.code in structural]
        if failures:
            raise HTTPException(
                status_code=422, detail=[item.model_dump(mode="json") for item in failures]
            )

    @staticmethod
    def _model_from_orm(specification: UmlMethodSpecification) -> UmlMethodSpecificationBase:
        return UmlMethodSpecificationBase.model_validate(
            {key: getattr(specification, key) for key in UmlMethodSpecificationBase.model_fields}
        )

    @staticmethod
    def _persistence_values(payload: UmlMethodSpecificationBase) -> dict:
        values = payload.model_dump(mode="json")
        values["backend_contract"] = values["backend_contract"] or {}
        values["frontend_contract"] = values["frontend_contract"] or {}
        return values

    @staticmethod
    def _conflict(current_revision: int) -> None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "stale_revision", "current_revision": current_revision},
        )

    def _audit(self, context, user_id, action, old_revision, new_revision, fields):
        self.audit.record(
            module="modelado_uml",
            action=action,
            user_id=user_id,
            project_id=context.diagram.project_id,
            metadata={
                "diagram_id": str(context.diagram.id),
                "class_id": str(context.uml_class.id),
                "method_id": str(context.method.id),
                "changed_fields": fields,
                "previous_revision": old_revision,
                "revision": new_revision,
            },
        )

    @staticmethod
    def _validate_rule_collections(model, context, issue):
        parameters = {str(item.id): item for item in context.method.parameters}
        parameter_names = {item.name.casefold() for item in context.method.parameters}
        attributes = {str(item.id): item for item in context.uml_class.attributes}
        for collection_name in ("preconditions", "postconditions", "business_rules", "validations"):
            items = getattr(model, collection_name)
            seen: set[str] = set()
            for index, item in enumerate(items):
                if item.code in seen:
                    issue(
                        "duplicate_rule_code",
                        f"{collection_name}[{index}].code",
                        "El codigo esta repetido",
                        "Use un codigo unico",
                    )
                seen.add(item.code)
                target = item.target
                if target and target.kind == "parameter":
                    if target.id and str(target.id) not in parameters:
                        issue(
                            "foreign_parameter",
                            f"{collection_name}[{index}].target.id",
                            "El parametro no pertenece al metodo",
                            "Seleccione un parametro de la firma",
                        )
                    elif not target.id and target.name.casefold() not in parameter_names:
                        issue(
                            "unknown_parameter",
                            f"{collection_name}[{index}].target.name",
                            "El parametro no existe",
                            "Seleccione un parametro de la firma",
                        )
                if (
                    target
                    and target.kind == "attribute"
                    and target.id
                    and str(target.id) not in attributes
                ):
                    issue(
                        "unknown_attribute",
                        f"{collection_name}[{index}].target.id",
                        "El atributo no pertenece a la clase",
                        "Seleccione un atributo de la clase",
                    )

    def _validate_related_entities(self, model, context, issue):
        classes = self.uml.list_classes(context.diagram.id)
        by_id = {item.id: item for item in classes}
        by_name: dict[str, list] = {}
        for item in classes:
            by_name.setdefault(item.name.casefold(), []).append(item)
        parameter_ids = {item.id for item in context.method.parameters}
        for index, entity in enumerate(model.related_entities):
            if entity.class_id and entity.class_id not in by_id:
                issue(
                    "foreign_related_entity",
                    f"related_entities[{index}].class_id",
                    "La clase no pertenece al diagrama",
                    "Seleccione una clase del diagrama",
                )
            elif not entity.class_id:
                matches = by_name.get(entity.class_name.casefold(), [])
                if not matches:
                    issue(
                        "unknown_related_entity",
                        f"related_entities[{index}].class_name",
                        "La clase indicada no existe",
                        "Seleccione una clase existente",
                    )
                elif len(matches) > 1:
                    issue(
                        "ambiguous_entity",
                        f"related_entities[{index}].class_name",
                        "El nombre coincide con varias clases",
                        "Seleccione la clase mediante su ID",
                    )
            if entity.source_parameter_id and entity.source_parameter_id not in parameter_ids:
                issue(
                    "foreign_parameter",
                    f"related_entities[{index}].source_parameter_id",
                    "El parametro no pertenece al metodo",
                    "Seleccione un parametro de la firma",
                )

    @staticmethod
    def _validate_backend(model, context, issue):
        contract = model.backend_contract
        if not contract:
            return
        parameter_names = {item.name for item in context.method.parameters}
        route_parameters = set(re.findall(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", contract.path))
        for name in sorted(route_parameters - parameter_names):
            issue(
                "unknown_path_parameter",
                "backend_contract.path",
                f"El parametro de ruta {name} no existe",
                "Agregue el parametro a la firma o corrija la ruta",
            )
        if contract.http_method == "GET" and model.operation_kind in {
            "create",
            "update",
            "delete",
            "business_action",
        }:
            issue(
                "unsafe_get_operation",
                "backend_contract.http_method",
                "GET no puede representar una operacion mutante",
                "Use POST, PUT, PATCH o DELETE",
            )
        if model.operation_kind == "create" and contract.status_codes.success not in {
            200,
            201,
            202,
        }:
            issue(
                "invalid_create_status",
                "backend_contract.status_codes.success",
                "El estado de creacion no es coherente",
                "Use 201 o un estado 2xx documentado",
                False,
            )

    def _validate_flutter(self, model, context, issue, strict):
        contract = model.frontend_contract
        if not contract:
            return
        parameters = {item.id: item for item in context.method.parameters}
        by_name = {item.name.casefold(): item for item in context.method.parameters}
        classes = {item.id: item for item in self.uml.list_classes(context.diagram.id)}
        covered: set[UUID] = set()
        for index, field in enumerate(contract.fields):
            parameter = (
                parameters.get(field.parameter_id)
                if field.parameter_id
                else by_name.get(field.parameter.casefold())
            )
            if parameter is None:
                issue(
                    "unknown_parameter",
                    f"frontend_contract.fields[{index}].parameter",
                    "El campo no referencia un parametro real",
                    "Seleccione un parametro del metodo",
                )
                continue
            covered.add(parameter.id)
            if field.control == "entity_selector":
                source = classes.get(field.source_entity_id) if field.source_entity_id else None
                if source is None:
                    issue(
                        "unknown_source_entity",
                        f"frontend_contract.fields[{index}].source_entity_id",
                        "El selector no referencia una clase real",
                        "Seleccione una clase fuente",
                    )
                elif any(
                    name.casefold() not in {a.name.casefold() for a in source.attributes}
                    for name in field.display_fields
                ):
                    issue(
                        "unknown_display_field",
                        f"frontend_contract.fields[{index}].display_fields",
                        "Un campo visible no existe en la entidad fuente",
                        "Use atributos existentes",
                    )
            expected = self._control_for_type(parameter.data_type)
            if expected and field.control != expected and field.control != "entity_selector":
                issue(
                    "control_type_mismatch",
                    f"frontend_contract.fields[{index}].control",
                    f"El tipo {parameter.data_type} normalmente usa {expected}",
                    "Revise el control seleccionado",
                    False,
                )
        if strict and model.exposure == "user_action":
            missing = [item.name for item in context.method.parameters if item.id not in covered]
            if missing:
                issue(
                    "unmapped_parameters",
                    "frontend_contract.fields",
                    f"Faltan controles para: {', '.join(missing)}",
                    "Mapee cada parametro visible",
                )
        for index, target_id in enumerate(contract.refresh_targets):
            if target_id not in classes:
                issue(
                    "unknown_refresh_target",
                    f"frontend_contract.refresh_targets[{index}]",
                    "El objetivo de refresco no existe",
                    "Seleccione una clase del diagrama",
                )

    @staticmethod
    def _control_for_type(data_type: str) -> str | None:
        normalized = data_type.casefold()
        if normalized in {"string", "char", "text"}:
            return "text_input"
        if normalized in {"integer", "int", "long"}:
            return "number_input"
        if normalized in {"double", "float", "decimal"}:
            return "decimal_input"
        if normalized in {"boolean", "bool"}:
            return "switch"
        if normalized in {"date", "localdate"}:
            return "date_picker"
        if normalized in {"datetime", "localdatetime", "timestamp"}:
            return "date_time_picker"
        return None

    def _infer_patch(self, context, instruction: str, current):
        text = instruction.casefold()
        operation = "custom"
        for kind, words in {
            "create": ("crear", "registrar", "agregar"),
            "read": ("obtener", "consultar detalle"),
            "search": ("listar", "buscar", "filtrar"),
            "update": ("actualizar", "editar", "cambiar"),
            "delete": ("eliminar", "borrar"),
            "calculate": ("calcular", "totalizar", "promediar"),
            "business_action": ("aprobar", "inscribir", "cerrar", "pagar"),
        }.items():
            if any(word in text for word in words):
                operation = kind
                break
        visible = any(
            word in text for word in ("formulario", "boton", "usuario", "pantalla", "lista")
        )
        exposure = "user_action" if visible else ("internal" if "intern" in text else "api")
        classes = self.uml.list_classes(context.diagram.id)
        class_by_name = {item.name.casefold(): item for item in classes}
        fields = []
        unresolved = []
        related = []
        for parameter in context.method.parameters:
            control = self._control_for_type(parameter.data_type) or "text_input"
            source_name = re.sub(r"(?:_?id)$", "", parameter.name, flags=re.IGNORECASE)
            source = class_by_name.get(source_name.casefold())
            if parameter.data_type.casefold() == "uuid" and source:
                control = "entity_selector"
                related.append(
                    RelatedEntityReference(
                        class_id=source.id,
                        class_name=source.name,
                        relation="input_reference",
                        required=True,
                        source_parameter_id=parameter.id,
                    )
                )
            elif parameter.data_type.casefold() == "uuid" and "id" in parameter.name.casefold():
                unresolved.append(f"No se pudo resolver la entidad para {parameter.name}")
            fields.append(
                FlutterFieldContract(
                    parameter_id=parameter.id,
                    parameter=parameter.name,
                    control=control,
                    source_entity_id=source.id if source else None,
                    source_entity=source.name if source else None,
                    display_fields=[a.name for a in source.attributes[:2]] if source else [],
                )
            )
        path_name = re.sub(r"[^a-z0-9]+", "-", context.method.name.casefold()).strip("-")
        method = (
            "GET"
            if operation in {"read", "search", "calculate"}
            else ("DELETE" if operation == "delete" else "POST")
        )
        backend = (
            None
            if exposure == "internal"
            else BackendMethodContract(
                http_method=method,
                path=f"/{path_name}",
                transactional=operation in {"create", "update", "delete", "business_action"},
                status_codes={"success": 201 if operation == "create" else 200},
            )
        )
        flutter = None
        if exposure == "user_action":
            flutter = FlutterMethodContract(
                interaction="form" if fields else "button",
                label=context.method.name.replace("_", " ").capitalize(),
                confirmation_required=operation == "delete",
                fields=fields,
            )
        return (
            UmlMethodSpecificationPatch(
                description=instruction.strip(),
                operation_kind=operation,
                exposure=exposure,
                related_entities=related,
                backend_contract=backend,
                frontend_contract=flutter,
            ),
            unresolved,
            ["La clasificacion se infirio de la instruccion y debe ser revisada."],
        )
