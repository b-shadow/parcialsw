from typing import Any

from fastapi import Request

from app.core.nosql.cliente import GestorMongo


def obtener_gestor_mongo(request: Request) -> GestorMongo:
    return request.app.state.mongo_manager


def obtener_base_mongo(request: Request) -> Any:
    return obtener_gestor_mongo(request).database
