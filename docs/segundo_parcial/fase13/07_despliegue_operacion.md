# Despliegue y operacion

## Orden productivo

1. PostgreSQL y MongoDB saludables.
2. `database-migrations` aplica Alembic.
3. Migraciones de memoria IA y versiones UML.
4. `uml-diagram-migration` migra y verifica contenido activo.
5. Backend y worker Outbox arrancan solo tras finalizar el paso anterior.

`/ready` exige el checkpoint de fase 13 cuando `UML_DIAGRAMS_MIGRATION_REQUIRED=true`.

## Variables

```text
UML_DIAGRAMS_MONGODB_READ_ENABLED=true
UML_DIAGRAMS_SQL_FALLBACK_ENABLED=true
UML_DIAGRAMS_COMPARE_READS=true
UML_DIAGRAMS_DUAL_WRITE_ENABLED=true
UML_DIAGRAMS_MIGRATION_BATCH_SIZE=100
UML_DIAGRAMS_MIGRATION_REQUIRED=true
```

## Operacion

Se deben vigilar eventos Outbox `retry/dead`, divergencias de hash, documentos atrasados, latencia de MongoDB y estado del checkpoint. La comparacion de lectura registra deriva sin exponer el contenido del usuario en logs.
