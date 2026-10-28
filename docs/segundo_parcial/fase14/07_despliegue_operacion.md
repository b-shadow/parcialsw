# Despliegue y operacion

## Cadena de arranque

1. PostgreSQL y MongoDB saludables.
2. Alembic hasta `d2f6a7b8c9d0`.
3. Migraciones documentales 11, 12 y 13.
4. `nosql-outbox-drain` hasta cero trabajos.
5. `nosql-reconciliation-check` saludable.
6. `phase14-consolidation` completada.
7. Backend, worker Outbox y reconciliador periodico.

Produccion usa `NOSQL_CONSOLIDATED_MODE=true`, fallbacks SQL desactivados y `PHASE14_CONSOLIDATION_REQUIRED=true`. `/ready` exige checkpoint completado y una auditoria saludable cuya antiguedad no exceda `NOSQL_RECONCILIATION_MAX_AGE_SECONDS`.

Los respaldos se montan en `/storage/backups` mediante el volumen `coordinated_backups`.
