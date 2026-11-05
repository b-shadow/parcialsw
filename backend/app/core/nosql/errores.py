class ErrorPersistenciaMongo(RuntimeError):
    """Base error for the NoSQL persistence boundary."""


class ErrorMongoNoDisponible(ErrorPersistenciaMongo):
    """Raised when MongoDB cannot serve a requested operation."""


class ErrorEsquemaMongo(ErrorPersistenciaMongo):
    """Raised when collections, validators, or indexes cannot be prepared."""


class ErrorContratoMongo(ErrorPersistenciaMongo):
    """Raised when an integration event violates a versioned document contract."""
