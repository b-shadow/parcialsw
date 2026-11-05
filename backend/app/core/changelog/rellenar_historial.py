"""Comando para reconstruir el registro de cambios (Redis Stream) desde audit_logs."""

import argparse
import sys
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.changelog.contratos import CambioPendiente
from app.core.changelog.servicio import ServicioRegistroCambios
from app.core.database.sesion import SessionLocal
from app.core.redis.cliente import clave_redis, obtener_redis
from app.modules.acceso_usuarios.models import RegistroAuditoria
from app.modules.proyectos_colaboracion.models import Proyecto


def backfill_project(db: Session, project_id: UUID) -> int:
    """Borra el Stream del proyecto y lo reconstruye desde audit_logs en orden cronológico."""
    client = obtener_redis()
    if client is not None:
        stream_key = clave_redis("changelog", "project", str(project_id))
        try:
            client.delete(stream_key)
        except Exception:
            pass

    logs = list(
        db.scalars(
            select(RegistroAuditoria)
            .where(RegistroAuditoria.project_id == project_id)
            .order_by(RegistroAuditoria.created_at.asc(), RegistroAuditoria.id.asc())
        )
    )

    if not logs:
        return 0

    service = ServicioRegistroCambios()
    changes: list[CambioPendiente] = []
    for log in logs:
        meta = log.metadata_json or {}
        ent_type = None
        ent_id = None
        for key in (
            "class_id",
            "relationship_id",
            "method_id",
            "attribute_id",
            "parameter_id",
            "diagram_id",
            "preset_id",
            "version_id",
            "member_id",
            "invitation_id",
        ):
            if key in meta:
                ent_type = key.replace("_id", "")
                ent_id = str(meta[key])
                break

        diag_id = None
        if "diagram_id" in meta:
            try:
                diag_id = UUID(str(meta["diagram_id"]))
            except Exception:
                pass

        changes.append(
            CambioPendiente(
                project_id=project_id,
                actor_user_id=log.user_id,
                source="system" if log.user_id is None else "ui",
                module=log.module,
                action=log.action,
                entity_type=ent_type,
                entity_id=ent_id,
                diagram_id=diag_id,
                metadata=meta,
            )
        )

    return service.append_many(changes)


def main() -> None:
    parser = argparse.ArgumentParser(description="Reconstruye Streams de Redis desde audit_logs.")
    parser.add_argument("--project", type=str, help="ID del proyecto UUID")
    parser.add_argument("--all", action="store_true", help="Reconstruir todos los proyectos")
    args = parser.parse_args()

    with SessionLocal() as db:
        if args.project:
            proj_id = UUID(args.project)
            count = backfill_project(db, proj_id)
            print(f"Reconstruidas {count} entradas para el proyecto {proj_id}")
        elif args.all:
            projects = db.scalars(select(Proyecto)).all()
            total = 0
            for p in projects:
                total += backfill_project(db, p.id)
            print(f"Reconstruidas {total} entradas en total para {len(projects)} proyectos")
        else:
            parser.print_help()
            sys.exit(1)


if __name__ == "__main__":
    main()
