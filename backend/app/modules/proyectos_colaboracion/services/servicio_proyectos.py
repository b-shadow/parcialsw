import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4, uuid5

from fastapi import HTTPException, status
from pydantic import ValidationError
from pymongo.errors import PyMongoError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config.configuracion import settings
from app.core.nosql.errores import ErrorMongoNoDisponible
from app.modules.acceso_usuarios.models import Usuario
from app.modules.acceso_usuarios.services.servicio_auditoria import ServicioAuditoria
from app.modules.modelado_uml.models import DiagramaUML
from app.modules.modelado_uml.services.almacen_diagrama_activo import (
    marcar_proyecto_uml_para_sincronizar,
)
from app.modules.notificaciones.schemas.notificacion import EnlaceProfundoNotificacion
from app.modules.notificaciones.services.servicio_notificaciones import (
    EventoNotificacionDominio,
    ServicioNotificaciones,
)
from app.modules.proyectos_colaboracion.models import (
    EventoColaboracion,
    IntegranteProyecto,
    InvitacionProyecto,
    Proyecto,
    RestauracionProyecto,
    VersionProyecto,
)
from app.modules.proyectos_colaboracion.repositories.repositorio_integrantes import (
    RepositorioIntegrantes,
)
from app.modules.proyectos_colaboracion.repositories.repositorio_proyectos import (
    RepositorioProyectos,
)
from app.modules.proyectos_colaboracion.schemas.instantanea import (
    InstantaneaConfiguracionIA,
    InstantaneaProyecto,
    InstantaneaProyectoV2,
    InstantaneaTemaFlutter,
    actualizar_instantanea_v1_a_v2,
    analizar_instantanea_proyecto,
    hash_instantanea_sha256,
    normalizar_instantanea_proyecto,
)
from app.modules.proyectos_colaboracion.schemas.proyecto import (
    SolicitudActualizacionProyecto,
    SolicitudActualizarIntegrante,
    SolicitudAgregarIntegrante,
    SolicitudCreacionProyecto,
    SolicitudCreacionVersion,
    SolicitudRestauracion,
)
from app.modules.proyectos_colaboracion.services.almacen_documentos_versiones import (
    AlmacenDocumentosVersionesUML,
    encolar_documento_version,
    persistir_documento_version,
)
from app.modules.proyectos_colaboracion.services.guardia_mutaciones_proyecto import (
    GuardiaMutacionesProyecto,
)
from app.modules.proyectos_colaboracion.validators.validador_proyecto import (
    asegurar_permiso_proyecto,
    asegurar_proyecto_existente,
    permisos_integrante,
)

EVENT_ALIASES = {
    "CREATE_CLASS": "UML_CLASS_CREATED",
    "UPDATE_CLASS": "UML_CLASS_UPDATED",
    "DELETE_CLASS": "UML_CLASS_DELETED",
    "CREATE_ATTRIBUTE": "UML_ATTRIBUTE_CREATED",
    "UPDATE_ATTRIBUTE": "UML_ATTRIBUTE_UPDATED",
    "DELETE_ATTRIBUTE": "UML_ATTRIBUTE_DELETED",
    "CREATE_METHOD": "UML_METHOD_CREATED",
    "UPDATE_METHOD": "UML_METHOD_UPDATED",
    "DELETE_METHOD": "UML_METHOD_DELETED",
    "CREATE_RELATION": "UML_RELATIONSHIP_CREATED",
    "CREATE_RELATIONSHIP": "UML_RELATIONSHIP_CREATED",
    "UPDATE_RELATIONSHIP": "UML_RELATIONSHIP_UPDATED",
    "DELETE_RELATIONSHIP": "UML_RELATIONSHIP_DELETED",
    "MOVE_ELEMENT": "UML_ELEMENT_MOVED",
    "AI_UPDATE_DIAGRAM": "AI_ACTIONS_APPLIED",
    "RESTORE_VERSION": "PROJECT_VERSION_RESTORED",
}

logger = logging.getLogger(__name__)


def _optional_uuid(value: object) -> UUID | None:
    try:
        return UUID(str(value)) if value else None
    except (TypeError, ValueError):
        return None


class ServicioProyectos:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = RepositorioProyectos(db)
        self.members = RepositorioIntegrantes(db)
        self.audit = ServicioAuditoria(db)
        self.mutations = GuardiaMutacionesProyecto(db)
        self.version_documents = AlmacenDocumentosVersionesUML()

    def crear_proyecto(self, payload: SolicitudCreacionProyecto, owner_id: UUID) -> Proyecto:
        project = self.projects.add(
            Proyecto(
                owner_id=owner_id,
                name=payload.name.strip(),
                description=payload.description,
                settings=payload.settings,
            )
        )
        self.members.add(
            IntegranteProyecto(
                project_id=project.id,
                user_id=owner_id,
                project_role="ORGANIZADOR",
                joined_at=datetime.now(UTC),
            )
        )
        diagram = DiagramaUML(
            project_id=project.id,
            created_by_user_id=owner_id,
            name=project.name,
            diagram_type="class",
            description=project.description,
            metadata_json={"project_diagram": True},
        )
        if settings.nosql_consolidated_mode:
            from app.modules.modelado_uml.repositories.repositorio_mongo_uml import (
                RepositorioMongoUML,
            )

            RepositorioMongoUML(self.db).agregar_diagrama(diagram)
        else:
            self.db.add(diagram)
        marcar_proyecto_uml_para_sincronizar(self.db, project.id)
        self.audit.record(
            module="proyectos_colaboracion",
            action="CREATE_PROJECT",
            user_id=owner_id,
            project_id=project.id,
        )
        self.db.commit()
        self.db.refresh(project)
        return project

    def listar_proyectos(self, user_id: UUID) -> list[Proyecto]:
        return self.projects.listar_por_usuario(user_id)

    def obtener_proyecto(self, project_id: UUID, user_id: UUID) -> Proyecto:
        project = asegurar_proyecto_existente(self.projects.get(project_id))
        asegurar_proyecto_existente(project)
        self._require_member(project_id, user_id)
        return project

    def mi_participacion(self, project_id: UUID, user_id: UUID) -> dict:
        member = self.members.obtener_participacion(project_id, user_id)
        if member is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "PERMISSION_DENIED", "message": "Sin acceso al proyecto"},
            )
        perms = permisos_integrante(self.db, member)
        return {
            "project_id": project_id,
            "user_id": user_id,
            "project_role": member.project_role,
            "permissions": sorted(perms),
        }

    def actualizar_proyecto(
        self, project_id: UUID, payload: SolicitudActualizacionProyecto, user_id: UUID
    ) -> Proyecto:
        project = self.mutations.acquire(project_id)
        asegurar_permiso_proyecto(self.db, project_id, user_id, "project.update")
        values = payload.model_dump(exclude_unset=True)
        if "settings" in values:
            values["settings"] = {**(project.settings or {}), **(values["settings"] or {})}
        changed = any(
            field in {"name", "description", "settings"} and getattr(project, field) != value
            for field, value in values.items()
        )
        if changed:
            self.mutations.avanzar(project)
        for field, value in values.items():
            setattr(project, field, value)
        diagram = self.db.scalar(
            select(DiagramaUML)
            .where(DiagramaUML.project_id == project_id)
            .order_by(DiagramaUML.created_at)
            .limit(1)
        )
        if diagram is not None:
            if "name" in values:
                diagram.name = project.name
            if "description" in values:
                diagram.description = project.description
            if changed and ({"name", "description"} & values.keys()):
                marcar_proyecto_uml_para_sincronizar(self.db, project.id)
        self.audit.record(
            module="proyectos_colaboracion",
            action="UPDATE_PROJECT",
            user_id=user_id,
            project_id=project_id,
        )
        self.db.commit()
        self.db.refresh(project)
        return project

    def archivar_proyecto(self, project_id: UUID, user_id: UUID) -> Proyecto:
        return self.actualizar_proyecto(
            project_id,
            SolicitudActualizacionProyecto(status="archived"),
            user_id,
        )

    def agregar_integrante(
        self, project_id: UUID, payload: SolicitudAgregarIntegrante, user_id: UUID
    ) -> IntegranteProyecto:
        asegurar_proyecto_existente(self.projects.get(project_id))
        asegurar_permiso_proyecto(self.db, project_id, user_id, "members.manage")
        existing = self.members.obtener_participacion(project_id, payload.user_id)
        if existing is not None:
            return existing
        member = self.members.add(
            IntegranteProyecto(
                project_id=project_id,
                user_id=payload.user_id,
                project_role=payload.project_role,
                joined_at=datetime.now(UTC),
            )
        )
        self.audit.record(
            module="proyectos_colaboracion",
            action="ADD_PROJECT_MEMBER",
            user_id=user_id,
            project_id=project_id,
            metadata={"member_user_id": str(payload.user_id)},
        )
        self._evento_actividad(
            project_id=project_id,
            user_id=user_id,
            event_type="PROJECT_MEMBER_ADDED",
            resource_type="project_member",
            resource_id=member.id,
            summary_key="activity.member_added",
            payload={"member_id": str(member.id), "project_role": member.project_role},
        )
        ServicioNotificaciones(self.db).record(
            EventoNotificacionDominio(
                type="PROJECT_MEMBER_ADDED",
                category="access",
                title="Nuevo proyecto compartido",
                body=f"Te agregaron al proyecto como {member.project_role}.",
                recipient_user_ids={member.user_id},
                dedup_entity_id=member.id,
                project_id=project_id,
                actor_user_id=user_id,
                resource_type="project_member",
                resource_id=member.id,
                deep_link=EnlaceProfundoNotificacion(
                    route_name="project_management", params={"project_id": str(project_id)}
                ),
            )
        )
        self.db.commit()
        self.db.refresh(member)
        return member

    def agregar_integrante_desde_invitacion(self, invitation: InvitacionProyecto, user_id: UUID) -> IntegranteProyecto:
        asegurar_proyecto_existente(self.projects.get(invitation.project_id))
        existing = self.members.obtener_participacion(invitation.project_id, user_id)
        if existing is not None:
            return existing
        member = self.members.add(
            IntegranteProyecto(
                project_id=invitation.project_id,
                user_id=user_id,
                project_role=invitation.project_role,
                joined_at=datetime.now(UTC),
            )
        )
        self.audit.record(
            module="proyectos_colaboracion",
            action="ADD_PROJECT_MEMBER",
            user_id=invitation.invited_by_user_id,
            project_id=invitation.project_id,
            metadata={
                "member_user_id": str(user_id),
                "origin": "invitation",
                "invitation_id": str(invitation.id),
            },
        )
        self._evento_actividad(
            project_id=invitation.project_id,
            user_id=invitation.invited_by_user_id,
            event_type="PROJECT_MEMBER_ADDED",
            resource_type="project_member",
            resource_id=member.id,
            summary_key="activity.member_added",
            payload={
                "member_id": str(member.id),
                "project_role": member.project_role,
                "origin": "invitation",
            },
        )
        ServicioNotificaciones(self.db).record(
            EventoNotificacionDominio(
                type="PROJECT_MEMBER_ADDED",
                category="access",
                title="Nuevo proyecto compartido",
                body=f"Te agregaron al proyecto como {member.project_role}.",
                recipient_user_ids={member.user_id},
                dedup_entity_id=member.id,
                project_id=invitation.project_id,
                actor_user_id=invitation.invited_by_user_id,
                resource_type="project_member",
                resource_id=member.id,
                deep_link=EnlaceProfundoNotificacion(
                    route_name="project_management",
                    params={"project_id": str(invitation.project_id)},
                ),
            )
        )
        self.db.commit()
        self.db.refresh(member)
        return member

    def listar_integrantes(self, project_id: UUID, user_id: UUID) -> list[IntegranteProyecto]:
        self._require_member(project_id, user_id)
        return self.members.listar_por_proyecto(project_id)

    def listar_candidatos_integrantes(self, project_id: UUID, user_id: UUID) -> list[Usuario]:
        asegurar_proyecto_existente(self.projects.get(project_id))
        asegurar_permiso_proyecto(self.db, project_id, user_id, "members.manage")
        member_user_ids = {
            member.user_id for member in self.members.listar_por_proyecto(project_id)
        }
        return list(
            self.db.scalars(
                select(Usuario)
                .where(Usuario.is_active.is_(True), Usuario.id.not_in(member_user_ids))
                .order_by(Usuario.full_name, Usuario.email)
            )
        )

    def actualizar_integrante(
        self, project_id: UUID, member_id: UUID, payload: SolicitudActualizarIntegrante, user_id: UUID
    ) -> IntegranteProyecto:
        project = asegurar_proyecto_existente(self.projects.get(project_id))
        asegurar_permiso_proyecto(self.db, project_id, user_id, "members.manage")
        member = self.members.get(member_id)
        if member is None or member.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Miembro de proyecto no encontrado",
            )
        if member.user_id == project.owner_id and payload.project_role != "ORGANIZADOR":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El propietario debe conservar rol ORGANIZADOR",
            )
        if member.project_role == "ORGANIZADOR" and payload.project_role != "ORGANIZADOR":
            organizers = [
                item
                for item in self.members.listar_por_proyecto(project_id)
                if item.project_role == "ORGANIZADOR"
            ]
            if len(organizers) <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El proyecto debe conservar al menos un organizador",
                )
        member.project_role = payload.project_role
        self.audit.record(
            module="proyectos_colaboracion",
            action="UPDATE_PROJECT_MEMBER",
            user_id=user_id,
            project_id=project_id,
            metadata={"member_id": str(member_id), "project_role": payload.project_role},
        )
        self._evento_actividad(
            project_id=project_id,
            user_id=user_id,
            event_type="PROJECT_MEMBER_ROLE_CHANGED",
            resource_type="project_member",
            resource_id=member.id,
            summary_key="activity.member_role_changed",
            payload={"member_id": str(member.id), "project_role": member.project_role},
        )
        ServicioNotificaciones(self.db).record(
            EventoNotificacionDominio(
                type="PROJECT_MEMBER_ROLE_CHANGED",
                category="access",
                title="Rol de proyecto actualizado",
                body=f"Tu rol ahora es {member.project_role}.",
                recipient_user_ids={member.user_id},
                dedup_entity_id=f"{member.id}:{member.project_role}",
                project_id=project_id,
                actor_user_id=user_id,
                resource_type="project_member",
                resource_id=member.id,
                deep_link=EnlaceProfundoNotificacion(
                    route_name="project_management", params={"project_id": str(project_id)}
                ),
            )
        )
        self.db.commit()
        self.db.refresh(member)
        return member

    def quitar_integrante(self, project_id: UUID, member_id: UUID, user_id: UUID) -> UUID:
        project = asegurar_proyecto_existente(self.projects.get(project_id))
        asegurar_permiso_proyecto(self.db, project_id, user_id, "members.manage")
        member = self.members.get(member_id)
        if member is None or member.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Miembro de proyecto no encontrado",
            )
        if member.user_id == project.owner_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede quitar al propietario del proyecto",
            )
        if member.project_role == "ORGANIZADOR":
            organizers = [
                item
                for item in self.members.listar_por_proyecto(project_id)
                if item.project_role == "ORGANIZADOR"
            ]
            if len(organizers) <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El proyecto debe conservar al menos un organizador",
                )
        removed_user_id = member.user_id
        removed_member_id = member.id
        self.members.delete(member)
        self.audit.record(
            module="proyectos_colaboracion",
            action="REMOVE_PROJECT_MEMBER",
            user_id=user_id,
            project_id=project_id,
            metadata={"member_id": str(member_id)},
        )
        self._evento_actividad(
            project_id=project_id,
            user_id=user_id,
            event_type="PROJECT_MEMBER_REMOVED",
            resource_type="project_member",
            resource_id=removed_member_id,
            summary_key="activity.member_removed",
            payload={"member_id": str(removed_member_id)},
        )
        ServicioNotificaciones(self.db).record(
            EventoNotificacionDominio(
                type="PROJECT_MEMBER_REMOVED",
                category="access",
                title="Acceso retirado",
                body="Ya no formas parte de este proyecto.",
                recipient_user_ids={removed_user_id},
                dedup_entity_id=removed_member_id,
                project_id=project_id,
                actor_user_id=user_id,
                resource_type="project",
                resource_id=project_id,
                deep_link=EnlaceProfundoNotificacion(route_name="projects"),
            )
        )
        self.db.commit()
        return removed_user_id

    def crear_version(
        self,
        project_id: UUID,
        payload: SolicitudCreacionVersion,
        user_id: UUID,
        idempotency_key: str | None = None,
    ) -> VersionProyecto:
        project = self.mutations.acquire(project_id)
        asegurar_permiso_proyecto(self.db, project_id, user_id, "versions.create")
        if (
            payload.expected_project_revision is not None
            and payload.expected_project_revision != project.revision
        ):
            self._error_dominio(
                409, "PROJECT_REVISION_CONFLICT", "El proyecto cambio antes de guardar la version"
            )
        if idempotency_key:
            existing = self.db.scalar(
                select(VersionProyecto).where(
                    VersionProyecto.project_id == project_id,
                    VersionProyecto.created_by_user_id == user_id,
                    VersionProyecto.idempotency_key == idempotency_key,
                )
            )
            if existing:
                return existing
        snapshot = self._construir_instantanea_proyecto(project_id, user_id)
        snapshot_hash = hash_instantanea_sha256(snapshot)
        previous = self.db.scalar(
            select(VersionProyecto)
            .where(
                VersionProyecto.project_id == project_id,
                VersionProyecto.kind == "manual",
            )
            .order_by(VersionProyecto.version_number.desc())
            .limit(1)
        )
        if previous and previous.snapshot_hash == snapshot_hash and not payload.allow_duplicate:
            self._error_dominio(
                409, "VERSION_DUPLICATE_CONTENT", "No hay cambios desde la ultima version"
            )
        version = self._crear_registro_version(
            project=project,
            project_id=project_id,
            user_id=user_id,
            name=payload.name,
            description=payload.description,
            snapshot={} if settings.nosql_consolidated_mode else snapshot,
            kind="manual",
            idempotency_key=idempotency_key,
        )
        self._evento_actividad(
            project_id=project_id,
            user_id=user_id,
            event_type="PROJECT_VERSION_CREATED",
            resource_type="project_version",
            resource_id=version.id,
            summary_key="activity.version_created",
            payload={"version_id": str(version.id), "version_number": version.version_number},
        )
        recipients = self._ids_integrantes_activos(project_id)
        ServicioNotificaciones(self.db).record(
            EventoNotificacionDominio(
                type="PROJECT_VERSION_CREATED",
                category="versions",
                title="Version de proyecto guardada",
                body=f"Se guardo la version {version.version_number}: {version.name}.",
                recipient_user_ids=recipients,
                dedup_entity_id=version.id,
                project_id=project_id,
                actor_user_id=user_id,
                severity="success",
                resource_type="project_version",
                resource_id=version.id,
                deep_link=EnlaceProfundoNotificacion(
                    route_name="project_collaborative",
                    params={"project_id": str(project_id)},
                    query={"panel": "versions", "version_id": str(version.id)},
                ),
                push_default=False,
            )
        )
        self.audit.record(
            module="proyectos_colaboracion",
            action="CREATE_PROJECT_VERSION",
            user_id=user_id,
            project_id=project_id,
            metadata={"version_number": version.version_number},
        )
        self.db.commit()
        self.db.refresh(version)
        return version

    def listar_versiones(self, project_id: UUID, user_id: UUID) -> list[dict]:
        asegurar_proyecto_existente(self.projects.get(project_id))
        asegurar_permiso_proyecto(self.db, project_id, user_id, "project.read")
        return [
            {
                **self._diccionario_version(version),
                "created_by_name": user_name,
            }
            for version, user_name in self.projects.listar_versiones(project_id)
        ]

    async def vista_previa_restauracion(self, project_id: UUID, version_id: UUID, user_id: UUID) -> dict:
        project = asegurar_proyecto_existente(self.projects.get(project_id))
        asegurar_permiso_proyecto(self.db, project_id, user_id, "project.read")
        version = self.projects.obtener_version(version_id)
        if version is None or version.project_id != project_id:
            self._error_dominio(404, "VERSION_NOT_FOUND", "Version del proyecto no encontrada")
        raw_snapshot, warnings = await self._cargar_instantanea_version(version, project)
        snapshot = self._analizar_instantanea(raw_snapshot, project)
        current = InstantaneaProyectoV2.model_validate(
            self._construir_instantanea_proyecto(project_id, user_id)
        )
        target_stats = self._estadisticas_instantanea(snapshot)
        current_stats = self._estadisticas_instantanea(current)
        return {
            "version": self._diccionario_version(version),
            "current_revision": project.revision,
            "effective_schema_version": snapshot.schema_version,
            "summary": target_stats,
            "differences": {
                key: target_stats[key] - current_stats[key]
                for key in ("diagrams", "classes", "attributes", "methods", "relationships")
            },
            "warnings": [
                *warnings,
                *(["snapshot_v1_adapted"] if raw_snapshot.get("schema_version", 1) == 1 else []),
            ],
        }

    def listar_cambios(
        self,
        project_id: UUID,
        user_id: UUID,
        limit: int,
        after_sequence: int | None = None,
    ) -> list[dict]:
        asegurar_proyecto_existente(self.projects.get(project_id))
        self._require_member(project_id, user_id)
        records = (
            self.projects.listar_cambios_posteriores(project_id, after_sequence, limit)
            if after_sequence is not None
            else self.projects.listar_cambios(project_id, limit)
        )
        return [
            {
                "id": event.id,
                "project_id": event.project_id,
                "diagram_id": event.diagram_id,
                "user_id": event.user_id,
                "user_name": user_name,
                "client_event_id": event.client_event_id,
                "sequence_number": event.sequence_number,
                "event_type": event.event_type,
                "element_type": event.element_type,
                "element_id": event.element_id,
                "base_version": event.base_version,
                "payload": event.payload,
                "created_at": event.created_at,
            }
            for event, user_name in records
        ]

    def listar_actividad(
        self,
        project_id: UUID,
        user_id: UUID,
        *,
        before_sequence: int | None,
        limit: int,
        event_types: set[str] | None = None,
    ) -> dict:
        asegurar_proyecto_existente(self.projects.get(project_id))
        self._require_member(project_id, user_id)
        rows = self.projects.listar_actividad_anterior(project_id, before_sequence, limit, event_types)
        has_more = len(rows) > limit
        visible = rows[:limit]
        items = [self._diccionario_evento(event, user_name) for event, user_name in visible]
        return {
            "items": items,
            "next_cursor": items[-1]["sequence_number"] if has_more and items else None,
            "has_more": has_more,
            "latest_sequence": self.projects.secuencia_evento_actual(project_id),
        }

    async def restaurar_version(
        self,
        project_id: UUID,
        version_id: UUID,
        user_id: UUID,
        *,
        idempotency_key: str,
        payload: SolicitudRestauracion | None = None,
    ) -> dict:
        project = self.mutations.acquire(project_id)
        asegurar_permiso_proyecto(self.db, project_id, user_id, "versions.restore")
        version = self.projects.obtener_version(version_id)
        if version is None or version.project_id != project.id:
            self._error_dominio(404, "VERSION_NOT_FOUND", "Version del proyecto no encontrada")
        existing_operation = self.db.scalar(
            select(RestauracionProyecto).where(
                RestauracionProyecto.project_id == project_id,
                RestauracionProyecto.requested_by_user_id == user_id,
                RestauracionProyecto.idempotency_key == idempotency_key,
            )
        )
        if existing_operation:
            if existing_operation.source_version_id != version_id:
                self._error_dominio(
                    409, "IDEMPOTENCY_KEY_REUSED", "La clave ya se uso para otra version"
                )
            if existing_operation.status != "completed":
                self._error_dominio(409, "RESTORE_IN_PROGRESS", "La restauracion ya esta en curso")
            backup = self.projects.obtener_version(existing_operation.backup_version_id)
            restored_ids = [
                UUID(value)
                for value in existing_operation.diagnostics_json.get("restored_diagram_ids", [])
            ]
            return self._resultado_restauracion(
                existing_operation,
                version,
                backup,
                restored_ids,
                idempotent_replay=True,
            )
        if (
            payload
            and payload.expected_project_revision is not None
            and payload.expected_project_revision != project.revision
        ):
            self._error_dominio(
                409, "PROJECT_REVISION_CONFLICT", "El proyecto cambio antes de restaurar"
            )
        raw_snapshot, _ = await self._cargar_instantanea_version(version, project)
        snapshot = self._analizar_instantanea(raw_snapshot, project)
        before_snapshot = self._construir_instantanea_proyecto(project_id, user_id)
        before_hash = hash_instantanea_sha256(before_snapshot)
        operation = RestauracionProyecto(
            project_id=project_id,
            source_version_id=version.id,
            requested_by_user_id=user_id,
            idempotency_key=idempotency_key,
            status="validating",
            source_snapshot_hash=hash_instantanea_sha256(snapshot),
            before_snapshot_hash=before_hash,
            project_revision_before=project.revision,
            diagnostics_json={},
            started_at=datetime.now(UTC),
        )
        self.db.add(operation)
        self.db.flush()

        backup = self._crear_registro_version(
            project=project,
            project_id=project_id,
            user_id=user_id,
            name=f"Respaldo antes de restaurar v{version.version_number}",
            description="Snapshot automatico de seguridad previo a la restauracion.",
            snapshot=before_snapshot,
            kind="pre_restore_backup",
            metadata={
                "restore_operation_id": str(operation.id),
                "source_version_id": str(version.id),
            },
        )
        operation.backup_version_id = backup.id
        from app.modules.modelado_uml.services.servicio_uml import ServicioUML

        restored_ids = ServicioUML(self.db).restaurar_instantanea_proyecto(
            project_id, snapshot.model_dump(mode="json"), user_id
        )
        self._restaurar_configuracion_instantanea(project, snapshot, user_id)
        project.revision += 1
        marcar_proyecto_uml_para_sincronizar(self.db, project_id)
        after_snapshot = self._construir_instantanea_proyecto(project_id, user_id)
        operation.status = "completed"
        operation.after_snapshot_hash = hash_instantanea_sha256(after_snapshot)
        operation.project_revision_after = project.revision
        operation.diagnostics_json = {
            "restored_diagram_ids": [str(item) for item in restored_ids],
        }
        operation.completed_at = datetime.now(UTC)
        from app.core.config.configuracion import settings
        from app.core.nosql.contratos import DocumentoMensajeIA
        from app.modules.asistente_proyecto.models import MensajeIA
        from app.modules.asistente_proyecto.repositories.repositorio_asistente import (
            RepositorioAsistente,
        )
        from app.modules.asistente_proyecto.services.almacen_documentos_conversacion import (
            AlmacenSincronoDocumentosConversacion,
            encolar_documento_mensaje,
            hash_contenido_mensaje,
        )

        conversation = RepositorioAsistente(self.db).obtener_conversacion(project_id, for_update=True)
        if conversation is not None:
            conversation.last_message_sequence += 1
            message_values = {
                "conversation_id": conversation.id,
                "project_id": project_id,
                "author_user_id": None,
                "role": "system",
                "content": f"El proyecto fue restaurado a la version {version.version_number}.",
                "sequence_number": conversation.last_message_sequence,
                "client_message_id": None,
                "correlation_id": operation.id,
                "status": "completed",
                "detected_intents": [],
                "references_json": [
                    {
                        "type": "project_version",
                        "id": str(version.id),
                        "label": f"Version {version.version_number}",
                    }
                ],
                "metadata_json": {"restore_operation_id": str(operation.id)},
            }
            if settings.nosql_consolidated_mode:
                system_message = DocumentoMensajeIA(
                    _id=uuid4(), content_hash="0" * 64, **message_values
                )
                system_message.content_hash = hash_contenido_mensaje(system_message)
                AlmacenSincronoDocumentosConversacion().upsert(system_message)
            else:
                system_message = MensajeIA(**message_values)
                self.db.add(system_message)
                encolar_documento_mensaje(self.db, system_message)
        restore_event = self._evento_actividad(
            project_id=project_id,
            user_id=user_id,
            event_type="PROJECT_VERSION_RESTORED",
            resource_type="project_restore_operation",
            resource_id=operation.id,
            correlation_id=operation.id,
            summary_key="activity.version_restored",
            payload={
                "source_version_id": str(version.id),
                "source_version_number": version.version_number,
                "backup_version_id": str(backup.id),
                "backup_version_number": backup.version_number,
                "project_revision": project.revision,
            },
        )
        ServicioNotificaciones(self.db).record(
            EventoNotificacionDominio(
                type="PROJECT_VERSION_RESTORED",
                category="versions",
                title="Proyecto restaurado",
                body=f"El proyecto fue restaurado a la version {version.version_number}.",
                recipient_user_ids=self._ids_integrantes_activos(project_id),
                dedup_entity_id=operation.id,
                project_id=project_id,
                actor_user_id=user_id,
                severity="warning",
                resource_type="project_restore_operation",
                resource_id=operation.id,
                deep_link=EnlaceProfundoNotificacion(
                    route_name="project_collaborative",
                    params={"project_id": str(project_id)},
                    query={"panel": "versions", "version_id": str(version.id)},
                ),
            )
        )
        self.audit.record(
            module="proyectos_colaboracion",
            action="RESTORE_PROJECT_VERSION",
            user_id=user_id,
            project_id=project_id,
            metadata={
                "restored_version": version.version_number,
                "backup_version": backup.version_number,
            },
        )
        self.db.commit()
        self.db.refresh(version)
        self.db.refresh(backup)
        return self._resultado_restauracion(operation, version, backup, restored_ids, restore_event)

    def registrar_evento_colaboracion(
        self,
        *,
        project_id: UUID,
        diagram_id: UUID | None,
        user_id: UUID,
        client_event_id: UUID,
        event_type: str,
        element_type: str | None,
        element_id: UUID | None,
        base_version: int | None,
        payload: dict,
    ) -> tuple[EventoColaboracion, bool]:
        self._require_member(project_id, user_id)
        if diagram_id is not None:
            from app.modules.modelado_uml.models import DiagramaUML

            diagram = self.db.get(DiagramaUML, diagram_id)
            if diagram is None or diagram.project_id != project_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El diagrama no pertenece al proyecto colaborativo",
                )
        existing = self.projects.obtener_evento_por_id_cliente(project_id, user_id, client_event_id)
        if existing is not None:
            return existing, False
        project = self.mutations.acquire(project_id)
        event = EventoColaboracion(
            project_id=project_id,
            diagram_id=diagram_id,
            user_id=user_id,
            client_event_id=client_event_id,
            sequence_number=self.projects.siguiente_secuencia_evento(project_id),
            event_type=EVENT_ALIASES.get(event_type, event_type),
            element_type=element_type,
            element_id=element_id,
            base_version=base_version,
            payload=payload,
            resource_type=element_type,
            resource_id=element_id,
            correlation_id=_optional_uuid(payload.get("correlation_id")),
            summary_key=f"activity.{EVENT_ALIASES.get(event_type, event_type).casefold()}",
        )
        project.revision += 1
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event, True

    @staticmethod
    def _diccionario_evento(event: EventoColaboracion, user_name: str) -> dict:
        return {
            "id": event.id,
            "project_id": event.project_id,
            "diagram_id": event.diagram_id,
            "user_id": event.user_id,
            "user_name": event.actor_display_name or user_name,
            "client_event_id": event.client_event_id,
            "sequence_number": event.sequence_number,
            "event_type": event.event_type,
            "element_type": event.element_type,
            "element_id": event.element_id,
            "base_version": event.base_version,
            "payload": event.payload,
            "created_at": event.created_at,
            "resource_type": event.resource_type,
            "resource_id": event.resource_id,
            "correlation_id": event.correlation_id,
            "causation_id": event.causation_id,
            "summary_key": event.summary_key,
        }

    def _crear_registro_version(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        name: str,
        description: str | None,
        snapshot: dict,
        project: Proyecto | None = None,
        kind: str = "manual",
        idempotency_key: str | None = None,
        metadata: dict | None = None,
    ) -> VersionProyecto:
        project = project or self.mutations.acquire(project_id)
        parsed = InstantaneaProyectoV2.model_validate(snapshot)
        canonical = normalizar_instantanea_proyecto(parsed)
        if len(canonical) > settings.project_snapshot_max_bytes:
            self._error_dominio(
                413, "SNAPSHOT_TOO_LARGE", "El snapshot excede el limite configurado"
            )
        version = VersionProyecto(
            project_id=project_id,
            created_by_user_id=user_id,
            version_number=project.siguiente_numero_version,
            name=name,
            description=description,
            snapshot=snapshot,
            status="available",
            kind=kind,
            snapshot_schema_version=parsed.schema_version,
            snapshot_hash=hash_instantanea_sha256(parsed),
            snapshot_size_bytes=len(canonical),
            project_revision=project.revision,
            idempotency_key=idempotency_key,
            metadata_json=metadata or {},
        )
        project.siguiente_numero_version += 1
        self.db.add(version)
        self.db.flush()
        diagram_id = self._id_diagrama_instantanea(snapshot, project_id)
        if settings.nosql_consolidated_mode:
            persistir_documento_version(version, diagram_id=diagram_id, content=snapshot)
        else:
            encolar_documento_version(self.db, version, diagram_id=diagram_id)
        return version

    def _id_diagrama_instantanea(self, snapshot: dict, project_id: UUID) -> UUID:
        for item in snapshot.get("diagrams", []):
            diagram_id = _optional_uuid(item.get("id"))
            if diagram_id is not None:
                return diagram_id
        diagram_id = self.db.scalar(
            select(DiagramaUML.id)
            .where(DiagramaUML.project_id == project_id)
            .order_by(DiagramaUML.created_at, DiagramaUML.id)
            .limit(1)
        )
        if diagram_id is None:
            self._error_dominio(
                409,
                "PROJECT_DIAGRAM_MISSING",
                "El proyecto no tiene un diagrama asociado para versionar",
            )
        return diagram_id

    async def _cargar_instantanea_version(
        self, version: VersionProyecto, project: Proyecto
    ) -> tuple[dict, list[str]]:
        warnings: list[str] = []
        try:
            document = await self.version_documents.obtener_seguro(version.id)
        except (ErrorMongoNoDisponible, PyMongoError):
            self._error_dominio(
                503,
                "VERSION_DOCUMENT_UNAVAILABLE",
                "El almacenamiento documental de versiones no esta disponible",
            )
        if document is None:
            if not settings.uml_versions_sql_fallback_enabled:
                self._error_dominio(
                    503,
                    "VERSION_DOCUMENT_UNAVAILABLE",
                    "El snapshot documental no esta disponible",
                )
            return dict(version.snapshot), ["mongodb_snapshot_fallback_sql"]

        registry_hash = version.snapshot_hash if len(version.snapshot_hash or "") == 64 else ""
        document_valid = (
            document.project_id == project.id
            and document.version_number == version.version_number
            and document.content_hash == registry_hash
        )
        if document_valid:
            try:
                parsed = self._analizar_instantanea(document.content, project)
                document_valid = hash_instantanea_sha256(parsed) == document.content_hash
            except HTTPException:
                document_valid = False

        if settings.uml_versions_compare_reads:
            sql_parsed = self._analizar_instantanea(version.snapshot, project)
            effective_sql_hash = hash_instantanea_sha256(sql_parsed)
        else:
            effective_sql_hash = registry_hash
        if settings.uml_versions_compare_reads and effective_sql_hash != document.content_hash:
            document_valid = False
            logger.error(
                "UML version SQL/MongoDB hash divergence",
                extra={"version_id": str(version.id), "project_id": str(project.id)},
            )

        if document_valid:
            return dict(document.content), warnings
        if settings.uml_versions_sql_fallback_enabled:
            warnings.append("mongodb_snapshot_hash_mismatch_fallback_sql")
            return dict(version.snapshot), warnings
        self._error_dominio(
            409,
            "VERSION_DOCUMENT_DIVERGED",
            "El snapshot documental no coincide con su registro relacional",
        )
        raise AssertionError("unreachable")

    def _construir_instantanea_proyecto(self, project_id: UUID, user_id: UUID) -> dict:
        from app.modules.asistente_proyecto.repositories.repositorio_asistente import (
            RepositorioAsistente,
        )
        from app.modules.generacion_software.repositories.repositorio_temas import RepositorioTemas
        from app.modules.modelado_uml.services.servicio_uml import ServicioUML

        project = asegurar_proyecto_existente(self.projects.get(project_id))
        uml_service = ServicioUML(self.db)
        diagrams = uml_service.uml.listar_diagramas_por_proyecto(project_id)
        theme = RepositorioTemas(self.db).get(project_id)
        ai_settings = RepositorioAsistente(self.db).obtener_configuracion(project_id)
        snapshot = InstantaneaProyectoV2(
            captured_at=datetime.now(UTC),
            project=InstantaneaProyecto(
                id=project.id,
                name=project.name,
                description=project.description,
            ),
            diagrams=[
                uml_service._construir_modelo_interno(diagram).model_dump(mode="json")
                for diagram in diagrams
            ],
            flutter_theme=(
                InstantaneaTemaFlutter(
                    config=theme.config_json,
                    preset_name=theme.preset_name,
                    schema_version=theme.schema_version,
                    revision=theme.revision,
                )
                if theme
                else None
            ),
            generation_settings=project.settings.get("generation_settings", {}),
            ai_settings=(
                InstantaneaConfiguracionIA(
                    enabled=ai_settings.enabled,
                    preferred_provider=ai_settings.preferred_provider,
                    model_name=ai_settings.model_name,
                    fallback_enabled=ai_settings.fallback_enabled,
                    require_confirmation=ai_settings.require_confirmation,
                )
                if ai_settings
                else None
            ),
        )
        return snapshot.model_dump(mode="json")

    def _restaurar_configuracion_instantanea(
        self,
        project: Proyecto,
        snapshot: InstantaneaProyectoV2,
        user_id: UUID,
    ) -> None:
        from app.modules.asistente_proyecto.schemas.esquemas_asistente import (
            ActualizacionConfiguracionIAProyecto,
        )

        project.name = snapshot.project.name
        project.description = snapshot.project.description
        project.settings = {
            **project.settings,
            "generation_settings": snapshot.generation_settings,
        }
        if snapshot.flutter_theme:
            theme_values = snapshot.flutter_theme
            old_theme = (project.settings or {}).get("flutter_theme", {})
            now = datetime.now(UTC).isoformat()
            project.settings = {
                **(project.settings or {}),
                "flutter_theme": {
                    "id": old_theme.get("id", str(uuid5(project.id, "flutter-theme"))),
                    "config_json": theme_values.config.model_dump(mode="json"),
                    "preset_name": theme_values.preset_name,
                    "schema_version": theme_values.schema_version,
                    "revision": max(old_theme.get("revision", 0) + 1, theme_values.revision),
                    "created_by_user_id": old_theme.get("created_by_user_id", str(user_id)),
                    "updated_by_user_id": str(user_id),
                    "created_at": old_theme.get("created_at", now),
                    "updated_at": now,
                },
            }
        if snapshot.ai_settings:
            old = (project.settings or {}).get("ai", {})
            ai_values = ActualizacionConfiguracionIAProyecto(
                **{
                    **{key: value for key, value in old.items() if key in ActualizacionConfiguracionIAProyecto.model_fields},
                    **snapshot.ai_settings.model_dump(),
                }
            ).model_dump()
            project.settings = {
                **(project.settings or {}),
                "ai": {
                    **old,
                    **ai_values,
                    "id": old.get("id", str(uuid5(project.id, "ai-settings"))),
                    "created_by_user_id": old.get("created_by_user_id", str(user_id)),
                    "created_at": old.get("created_at", datetime.now(UTC).isoformat()),
                    "updated_by_user_id": str(user_id),
                    "updated_at": datetime.now(UTC).isoformat(),
                },
            }

    @staticmethod
    def _diccionario_version(version: VersionProyecto) -> dict:
        return {
            "id": version.id,
            "project_id": version.project_id,
            "created_by_user_id": version.created_by_user_id,
            "version_number": version.version_number,
            "name": version.name,
            "description": version.description,
            "snapshot": version.snapshot,
            "status": version.status,
            "created_at": version.created_at,
            "created_by_name": None,
            "kind": version.kind,
            "snapshot_schema_version": version.snapshot_schema_version,
            "snapshot_hash": version.snapshot_hash,
            "snapshot_size_bytes": version.snapshot_size_bytes,
            "project_revision": version.project_revision,
        }

    def _asegurar_gestor_versiones(self, project: Proyecto, user_id: UUID) -> None:
        if project.owner_id == user_id:
            return
        member = self.members.obtener_participacion(project.id, user_id)
        if member is None or member.project_role != "ORGANIZADOR":
            self._error_dominio(
                403, "VERSION_MANAGE_FORBIDDEN", "Se requiere ser propietario u organizador"
            )

    @staticmethod
    def _error_dominio(http_status: int, code: str, message: str) -> None:
        raise HTTPException(status_code=http_status, detail={"code": code, "message": message})

    def _analizar_instantanea(self, raw: dict, project: Proyecto) -> InstantaneaProyectoV2:
        try:
            if raw.get("schema_version", 1) == 1:
                current = InstantaneaProyectoV2.model_validate(
                    self._construir_instantanea_proyecto(project.id, project.owner_id)
                )
                upgraded, _ = actualizar_instantanea_v1_a_v2(
                    raw,
                    InstantaneaProyecto(
                        id=project.id, name=project.name, description=project.description
                    ),
                    generation_settings=current.generation_settings,
                    flutter_theme=current.flutter_theme,
                    ai_settings=current.ai_settings,
                )
                return upgraded
            return analizar_instantanea_proyecto(
                raw,
                InstantaneaProyecto(id=project.id, name=project.name, description=project.description),
            )
        except (ValueError, ValidationError) as exc:
            code = (
                "SNAPSHOT_VERSION_UNSUPPORTED" if "no soportada" in str(exc) else "SNAPSHOT_INVALID"
            )
            self._error_dominio(409 if code.endswith("UNSUPPORTED") else 422, code, str(exc))
        raise AssertionError("unreachable")

    def _ids_integrantes_activos(self, project_id: UUID) -> set[UUID]:
        return set(
            self.db.scalars(
                select(IntegranteProyecto.user_id).where(IntegranteProyecto.project_id == project_id)
            )
        )

    def _evento_actividad(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        event_type: str,
        resource_type: str,
        resource_id: UUID,
        summary_key: str,
        payload: dict,
        correlation_id: UUID | None = None,
    ) -> EventoColaboracion:
        event = EventoColaboracion(
            project_id=project_id,
            diagram_id=None,
            user_id=user_id,
            client_event_id=uuid4(),
            sequence_number=self.projects.siguiente_secuencia_evento(project_id),
            event_type=event_type,
            element_type=resource_type,
            element_id=resource_id,
            base_version=None,
            payload=payload,
            resource_type=resource_type,
            resource_id=resource_id,
            correlation_id=correlation_id,
            summary_key=summary_key,
        )
        self.db.add(event)
        self.db.flush()
        return event

    @staticmethod
    def _estadisticas_instantanea(snapshot: InstantaneaProyectoV2) -> dict[str, int]:
        totals = {
            "diagrams": len(snapshot.diagrams),
            "classes": 0,
            "attributes": 0,
            "methods": 0,
            "relationships": 0,
        }
        for diagram in snapshot.diagrams:
            classes = diagram.get("classes", [])
            totals["classes"] += len(classes)
            totals["attributes"] += sum(len(item.get("attributes", [])) for item in classes)
            totals["methods"] += sum(len(item.get("methods", [])) for item in classes)
            totals["relationships"] += len(diagram.get("relationships", []))
        return totals

    def _resultado_restauracion(
        self,
        operation: RestauracionProyecto,
        version: VersionProyecto,
        backup: VersionProyecto | None,
        restored_ids: list[UUID],
        event: EventoColaboracion | None = None,
        *,
        idempotent_replay: bool = False,
    ) -> dict:
        if backup is None:
            self._error_dominio(409, "RESTORE_FAILED", "No se encontro el respaldo de restauracion")
        return {
            "restored_version": self._diccionario_version(version),
            "backup_version": self._diccionario_version(backup),
            "restored_diagram_ids": restored_ids,
            "restore_operation_id": operation.id,
            "project_revision": operation.project_revision_after
            or operation.project_revision_before,
            "event_sequence": event.sequence_number if event else None,
            "event_id": event.id if event else None,
            "client_event_id": event.client_event_id if event else None,
            "idempotent_replay": idempotent_replay,
        }

    def _require_member(self, project_id: UUID, user_id: UUID) -> IntegranteProyecto:
        from app.modules.proyectos_colaboracion.validators.validador_proyecto import (
            asegurar_participacion,
        )

        return asegurar_participacion(self.members.obtener_participacion(project_id, user_id))
