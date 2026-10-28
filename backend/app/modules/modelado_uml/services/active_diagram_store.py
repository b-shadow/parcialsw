from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from pydantic import ValidationError
from pymongo.errors import PyMongoError
from sqlalchemy import event, select
from sqlalchemy.orm import Session

from app.core.config.settings import settings
from app.core.nosql.contracts import MongoCollection, MongoMutation, UmlDiagramDocument
from app.core.nosql.errors import MongoUnavailableError
from app.core.nosql.outbox import NoSqlOutboxService
from app.core.nosql.reconciliation import canonical_sha256
from app.core.nosql.sync_client import SyncMongoManager, sync_mongo_manager
from app.modules.modelado_uml.engine.internal_model import (
    UmlAttributeModel,
    UmlClassModel,
    UmlDiagramModel,
    UmlMethodModel,
    UmlParameterModel,
    UmlRelationshipModel,
    UmlVisualModel,
)
from app.modules.modelado_uml.models import UmlDiagram
from app.modules.modelado_uml.repositories.uml_repository import UmlRepository
from app.modules.proyectos_colaboracion.models import Project

logger = logging.getLogger(__name__)
SYNC_PROJECTS_KEY = "uml_document_sync_projects"
DELETE_DIAGRAMS_KEY = "uml_document_delete_diagrams"


def canonical_uml_content(model: UmlDiagramModel | dict[str, Any]) -> dict[str, Any]:
    content = (
        model.model_dump(mode="json")
        if isinstance(model, UmlDiagramModel)
        else UmlDiagramModel.model_validate(model).model_dump(mode="json")
    )
    for uml_class in content.get("classes", []):
        uml_class["attributes"] = sorted(
            uml_class.get("attributes", []),
            key=lambda item: (item.get("order_index", 0), str(item.get("id") or "")),
        )
        uml_class["methods"] = sorted(
            uml_class.get("methods", []),
            key=lambda item: (item.get("order_index", 0), str(item.get("id") or "")),
        )
        for method in uml_class["methods"]:
            method["parameters"] = sorted(
                method.get("parameters", []),
                key=lambda item: (item.get("order_index", 0), str(item.get("id") or "")),
            )
    content["classes"] = sorted(
        content.get("classes", []),
        key=lambda item: (str(item.get("name") or "").casefold(), str(item.get("id") or "")),
    )
    content["relationships"] = sorted(
        content.get("relationships", []), key=lambda item: str(item.get("id") or "")
    )
    return content


def build_sql_diagram_model(db: Session, diagram: UmlDiagram) -> UmlDiagramModel:
    uml = UmlRepository(db)
    visuals = {item.element_id: item for item in uml.list_visual_elements(diagram.id)}
    classes = []
    for uml_class in uml.list_classes(diagram.id):
        visual = visuals.get(uml_class.id)
        classes.append(
            UmlClassModel(
                id=str(uml_class.id),
                name=uml_class.name,
                visibility=uml_class.visibility,
                element_type=uml_class.element_type,
                stereotype=uml_class.stereotype,
                description=uml_class.description,
                attributes=[
                    UmlAttributeModel(
                        id=str(item.id),
                        name=item.name,
                        data_type=item.data_type,
                        visibility=item.visibility,
                        initial_value=item.initial_value,
                        multiplicity=item.multiplicity,
                        is_required=item.is_required,
                        order_index=item.order_index,
                        constraints=item.constraints,
                    )
                    for item in uml_class.attributes
                ],
                methods=[
                    UmlMethodModel(
                        id=str(method.id),
                        name=method.name,
                        return_type=method.return_type,
                        visibility=method.visibility,
                        order_index=method.order_index,
                        metadata_json=method.metadata_json,
                        specification=(
                            {
                                "description": method.specification.description,
                                "operation_kind": method.specification.operation_kind,
                                "exposure": method.specification.exposure,
                                "preconditions": method.specification.preconditions,
                                "postconditions": method.specification.postconditions,
                                "business_rules": method.specification.business_rules,
                                "validations": method.specification.validations,
                                "side_effects": method.specification.side_effects,
                                "required_permissions": method.specification.required_permissions,
                                "related_entities": method.specification.related_entities,
                                "backend_contract": method.specification.backend_contract,
                                "frontend_contract": method.specification.frontend_contract,
                                "schema_version": method.specification.schema_version,
                                "revision": method.specification.revision,
                            }
                            if method.specification
                            else None
                        ),
                        parameters=[
                            UmlParameterModel(
                                id=str(parameter.id),
                                name=parameter.name,
                                data_type=parameter.data_type,
                                default_value=parameter.default_value,
                                order_index=parameter.order_index,
                            )
                            for parameter in method.parameters
                        ],
                    )
                    for method in uml_class.methods
                ],
                visual=UmlVisualModel(
                    id=str(visual.id) if visual else None,
                    x=visual.position_x if visual else 0,
                    y=visual.position_y if visual else 0,
                    width=visual.width if visual else None,
                    height=visual.height if visual else None,
                    style=visual.style if visual else {},
                ),
                metadata_json=uml_class.metadata_json,
            )
        )
    relationships = [
        UmlRelationshipModel(
            id=str(item.id),
            source_class_id=str(item.source_class_id),
            target_class_id=str(item.target_class_id),
            relationship_type=item.relationship_type,
            source_cardinality=item.source_cardinality,
            target_cardinality=item.target_cardinality,
            direction=item.direction,
            label=item.label,
            metadata_json=item.metadata_json,
        )
        for item in uml.list_relationships(diagram.id)
    ]
    return UmlDiagramModel(
        id=str(diagram.id),
        project_id=str(diagram.project_id),
        name=diagram.name,
        diagram_type=diagram.diagram_type,
        status=diagram.status,
        current_version=diagram.current_version,
        description=diagram.description,
        classes=classes,
        relationships=relationships,
        metadata_json=diagram.metadata_json,
    )


def diagram_document_from_sql(
    db: Session, diagram: UmlDiagram, *, revision: int
) -> UmlDiagramDocument:
    content = canonical_uml_content(build_sql_diagram_model(db, diagram))
    now = datetime.now(UTC)
    return UmlDiagramDocument(
        _id=diagram.id,
        project_id=diagram.project_id,
        revision=revision,
        content=content,
        content_hash=canonical_sha256(content),
        created_at=diagram.created_at or now,
        updated_at=now,
    )


def mark_uml_project_for_sync(db: Session, project_id: UUID) -> None:
    if settings.uml_diagrams_dual_write_enabled or settings.nosql_consolidated_mode:
        db.info.setdefault(SYNC_PROJECTS_KEY, set()).add(project_id)


def mark_uml_diagram_for_delete(db: Session, diagram_id: UUID) -> None:
    if settings.uml_diagrams_dual_write_enabled or settings.nosql_consolidated_mode:
        db.info.setdefault(DELETE_DIAGRAMS_KEY, set()).add(diagram_id)


@event.listens_for(Session, "before_commit")
def enqueue_marked_uml_documents(db: Session) -> None:
    project_ids = set(db.info.pop(SYNC_PROJECTS_KEY, set()))
    deleted_ids = set(db.info.pop(DELETE_DIAGRAMS_KEY, set()))
    if not project_ids and not deleted_ids:
        return
    db.flush()
    if settings.nosql_consolidated_mode:
        _persist_canonical_documents(db, project_ids, deleted_ids)
        return
    outbox = NoSqlOutboxService(db)
    for project_id in project_ids:
        project = db.get(Project, project_id)
        if project is None:
            continue
        diagrams = list(db.scalars(select(UmlDiagram).where(UmlDiagram.project_id == project_id)))
        for diagram in diagrams:
            document = diagram_document_from_sql(db, diagram, revision=project.revision)
            outbox.enqueue(
                aggregate_type="uml_diagram",
                aggregate_id=diagram.id,
                mutation=MongoMutation(
                    collection=MongoCollection.UML_DIAGRAMS,
                    operation="upsert",
                    document_id=diagram.id,
                    document=document.to_mongo(),
                ),
                idempotency_key=(
                    f"uml-diagram:{diagram.id}:{document.revision}:{document.content_hash}"
                ),
            )
    for diagram_id in deleted_ids:
        outbox.enqueue(
            aggregate_type="uml_diagram",
            aggregate_id=diagram_id,
            mutation=MongoMutation(
                collection=MongoCollection.UML_DIAGRAMS,
                operation="delete",
                document_id=diagram_id,
            ),
            idempotency_key=f"uml-diagram:{diagram_id}:delete",
        )


def _persist_canonical_documents(
    db: Session, project_ids: set[UUID], deleted_ids: set[UUID]
) -> None:
    """Write canonical UML aggregates directly; SQL no longer carries content."""
    from app.modules.modelado_uml.repositories.mongo_uml_repository import (
        MongoUmlRepository,
    )

    repository = MongoUmlRepository(db)
    collection = repository.documents.database[MongoCollection.UML_DIAGRAMS.value]
    now = datetime.now(UTC)
    for project_id in project_ids:
        project = db.get(Project, project_id)
        if project is None:
            continue
        for diagram in db.scalars(select(UmlDiagram).where(UmlDiagram.project_id == project_id)):
            model = repository.model(diagram)
            content = canonical_uml_content(model)
            previous = collection.find_one({"_id": str(diagram.id)}, {"created_at": 1})
            document = UmlDiagramDocument(
                _id=diagram.id,
                project_id=diagram.project_id,
                revision=project.revision,
                content=content,
                content_hash=canonical_sha256(content),
                created_at=(previous or {}).get("created_at") or diagram.created_at or now,
                updated_at=now,
            )
            collection.replace_one({"_id": str(diagram.id)}, document.to_mongo(), upsert=True)
    for diagram_id in deleted_ids:
        collection.delete_one({"_id": str(diagram_id)})


class ActiveUmlDocumentStore:
    def __init__(self, manager: SyncMongoManager = sync_mongo_manager, *, database=None) -> None:
        self.manager = manager
        self._database = database

    @property
    def database(self):
        return self._database if self._database is not None else self.manager.database

    def get(self, diagram_id: UUID) -> UmlDiagramDocument | None:
        document = self.database[MongoCollection.UML_DIAGRAMS.value].find_one(
            {"_id": str(diagram_id)}
        )
        return UmlDiagramDocument.model_validate(document) if document else None

    def model_for(self, db: Session, diagram: UmlDiagram) -> UmlDiagramModel:
        if not settings.uml_diagrams_mongodb_read_enabled:
            return build_sql_diagram_model(db, diagram)

        def sql_fallback() -> UmlDiagramModel:
            return build_sql_diagram_model(db, diagram)

        try:
            document = self.get(diagram.id)
        except (MongoUnavailableError, PyMongoError, ValidationError):
            if settings.uml_diagrams_sql_fallback_enabled:
                return sql_fallback()
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "UML_DOCUMENT_UNAVAILABLE",
                    "message": "El documento UML no esta disponible",
                },
            ) from None
        if document is None:
            if settings.uml_diagrams_sql_fallback_enabled:
                return sql_fallback()
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "UML_DOCUMENT_MISSING",
                    "message": "El documento UML no existe",
                },
            )
        try:
            content = canonical_uml_content(document.content)
            valid = (
                document.project_id == diagram.project_id
                and str(content.get("id")) == str(diagram.id)
                and document.content_hash == canonical_sha256(content)
            )
        except (TypeError, ValueError, ValidationError):
            valid = False
            content = {}
        project_revision = db.scalar(
            select(Project.revision).where(Project.id == diagram.project_id)
        )
        if project_revision is not None and document.revision < project_revision:
            logger.info(
                "MongoDB UML document is behind SQL outbox projection",
                extra={
                    "diagram_id": str(diagram.id),
                    "document_revision": document.revision,
                    "project_revision": project_revision,
                },
            )
            if settings.uml_diagrams_sql_fallback_enabled:
                return sql_fallback()
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "UML_DOCUMENT_REVISION_LAG",
                    "message": "El documento UML tiene una sincronizacion pendiente",
                },
            )
        if not valid:
            if settings.uml_diagrams_sql_fallback_enabled:
                return sql_fallback()
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "UML_DOCUMENT_INVALID",
                    "message": "El documento UML no supera integridad",
                },
            )
        if settings.uml_diagrams_compare_reads:
            sql_model = sql_fallback()
            sql_hash = canonical_sha256(canonical_uml_content(sql_model))
            if sql_hash != document.content_hash:
                logger.error(
                    "Active UML SQL/MongoDB divergence",
                    extra={"diagram_id": str(diagram.id), "project_id": str(diagram.project_id)},
                )
        return UmlDiagramModel.model_validate(content)
