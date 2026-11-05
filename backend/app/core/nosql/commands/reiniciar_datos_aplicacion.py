from __future__ import annotations

import argparse
import asyncio
import json
from uuid import UUID

from sqlalchemy import delete, inspect, select, text

import app.models  # noqa: F401
from app.core.database.sesion import SessionLocal
from app.core.nosql.cliente import mongo_manager
from app.modules.acceso_usuarios.models import Rol, RolUsuario, Usuario

PRESERVED_TABLES = frozenset({"roles", "usuarios", "roles_usuario"})
CONFIRMATION = "RESET"


def _select_admin(db, admin_email: str | None) -> tuple[Usuario, Rol]:
    statement = (
        select(Usuario, Rol)
        .join(RolUsuario, RolUsuario.user_id == Usuario.id)
        .join(Rol, Rol.id == RolUsuario.role_id)
        .where(Rol.name == "ADMINISTRADOR", Usuario.is_active.is_(True))
        .order_by(Usuario.created_at, Usuario.id)
    )
    if admin_email:
        statement = statement.where(Usuario.email == admin_email.strip().lower())
    result = db.execute(statement).first()
    if result is None:
        target = admin_email or "an active ADMINISTRADOR user"
        raise RuntimeError(f"cannot reset data: {target} was not found")
    return result[0], result[1]


def preflight_admin(admin_email: str | None = None) -> dict[str, str]:
    with SessionLocal() as db:
        admin, admin_role = _select_admin(db, admin_email)
        return {
            "admin_id": str(admin.id),
            "admin_role_id": str(admin_role.id),
            "admin_email": admin.email,
        }


def reset_postgresql(identity: dict[str, str]) -> dict[str, str]:
    with SessionLocal() as db:
        admin_id = UUID(identity["admin_id"])
        admin_role_id = UUID(identity["admin_role_id"])

        connection = db.connection()
        table_names = [
            name
            for name in inspect(connection).get_table_names()
            if name not in PRESERVED_TABLES and name != "alembic_version"
        ]
        if table_names:
            preparer = connection.dialect.identifier_preparer
            quoted = ", ".join(preparer.quote(name) for name in table_names)
            db.execute(text(f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE"))

        db.execute(delete(RolUsuario).where(RolUsuario.user_id != admin_id))
        db.execute(
            delete(RolUsuario).where(
                RolUsuario.user_id == admin_id,
                RolUsuario.role_id != admin_role_id,
            )
        )
        db.execute(delete(Usuario).where(Usuario.id != admin_id))
        db.commit()
        return {"admin_id": str(admin_id), "admin_email": identity["admin_email"]}


async def reset_mongodb() -> dict[str, int]:
    health = await mongo_manager.connect(bootstrap=True)
    if not health.available:
        raise RuntimeError("cannot reset data: MongoDB is unavailable")
    deleted: dict[str, int] = {}
    for collection_name in await mongo_manager.database.list_collection_names():
        result = await mongo_manager.database[collection_name].delete_many({})
        deleted[collection_name] = result.deleted_count
    return deleted


async def run(admin_email: str | None) -> dict:
    try:
        identity = preflight_admin(admin_email)
        health = await mongo_manager.connect(bootstrap=True)
        if not health.available:
            raise RuntimeError("cannot reset data: MongoDB is unavailable")
        mongo_result = await reset_mongodb()
        postgres_result = reset_postgresql(identity)
        return {"status": "completed", "postgresql": postgres_result, "mongodb": mongo_result}
    finally:
        await mongo_manager.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Delete application data while preserving one administrator account"
    )
    parser.add_argument("--admin-email", help="administrator account to preserve")
    parser.add_argument("--confirm", required=True)
    args = parser.parse_args()
    if args.confirm != CONFIRMATION:
        raise SystemExit(f"Refusing destructive reset; use --confirm {CONFIRMATION}")
    print(json.dumps(asyncio.run(run(args.admin_email)), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
