# Resumen de la Fase 11

## Implementado

- Mensajes completos como documentos Mongo independientes.
- Hash canónico y validación estricta.
- Lectura Mongo principal con paginación compatible.
- Superposición SQL para lectura inmediata mientras Outbox procesa.
- Fallback reversible por configuración.
- Escritura Outbox en todos los productores de mensajes.
- Protección contra eventos fuera de orden.
- Memoria estructurada en snapshots separados.
- Contexto acotado para chats extensos.
- Migración histórica por lotes con checkpoint compuesto.
- Verificación acotada de conteos, ids y hashes.
- Gate de readiness y orden de despliegue.
- Integración CI con PostgreSQL y MongoDB reales.
- Índice SQL de migración y nuevo head Alembic.

## Estado de almacenamiento

MongoDB es la fuente principal de lectura para mensajes y memoria. PostgreSQL conserva temporalmente una réplica completa, las secuencias y las FK requeridas por acciones/recomendaciones. Esta copia es el rollback controlado hasta la consolidación de fase 14.

## Siguiente fase

La fase 12 puede aplicar el mismo patrón a snapshots y versiones UML inmutables: contrato, migración reiniciable, comparación de hashes, lectura reversible y retiro posterior de duplicación.
