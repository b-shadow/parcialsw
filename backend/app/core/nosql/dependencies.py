from typing import Any

from fastapi import Request

from app.core.nosql.client import MongoManager


def get_mongo_manager(request: Request) -> MongoManager:
    return request.app.state.mongo_manager


def get_mongo_database(request: Request) -> Any:
    return get_mongo_manager(request).database
