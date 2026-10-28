"""MongoDB infrastructure for the PostgreSQL/MongoDB persistence boundary."""

from app.core.nosql.client import MongoManager, mongo_manager
from app.core.nosql.contracts import MongoCollection

__all__ = ["MongoCollection", "MongoManager", "mongo_manager"]
