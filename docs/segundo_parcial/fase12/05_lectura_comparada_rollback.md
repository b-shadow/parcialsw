# Lectura comparada y rollback

## Politica

La vista previa y la restauracion usan MongoDB primero. El documento solo es aceptado cuando coinciden:

- `project_id` autorizado;
- `version_number` del registro;
- hash del registro o hash canonico efectivo para legado;
- hash recalculado del contenido validado.

Con `UML_VERSIONS_COMPARE_READS=true` tambien se canonicaliza el JSONB SQL y se compara contra MongoDB.

## Banderas

| Variable | Funcion |
|---|---|
| `UML_VERSIONS_MONGODB_READ_ENABLED` | Activa la fuente documental |
| `UML_VERSIONS_SQL_FALLBACK_ENABLED` | Permite rollback de lectura |
| `UML_VERSIONS_COMPARE_READS` | Detecta divergencias SQL/Mongo |
| `UML_VERSIONS_MIGRATION_REQUIRED` | Bloquea readiness sin checkpoint completo |

Una ausencia o falla usa SQL solo con fallback activo. Una divergencia usa SQL y emite advertencia; sin fallback produce `409`. Una caida de Mongo sin fallback produce `503`. Ninguno de estos casos modifica el proyecto.
