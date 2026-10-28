class MongoPersistenceError(RuntimeError):
    """Base error for the NoSQL persistence boundary."""


class MongoUnavailableError(MongoPersistenceError):
    """Raised when MongoDB cannot serve a requested operation."""


class MongoSchemaError(MongoPersistenceError):
    """Raised when collections, validators, or indexes cannot be prepared."""


class MongoContractError(MongoPersistenceError):
    """Raised when an integration event violates a versioned document contract."""
