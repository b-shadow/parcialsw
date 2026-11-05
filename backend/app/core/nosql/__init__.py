"""MongoDB infrastructure for the PostgreSQL/MongoDB persistence boundary."""

from app.core.nosql.cliente import GestorMongo, mongo_manager
from app.core.nosql.contratos import ColeccionMongo

__all__ = ["ColeccionMongo", "GestorMongo", "mongo_manager"]
