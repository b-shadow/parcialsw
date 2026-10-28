# Fase 11 - Conversaciones y memoria de IA en MongoDB

## Objetivo

Trasladar mensajes, referencias, metadatos y memoria extensa del asistente a MongoDB sin perder permisos, orden, idempotencia, paginación ni posibilidad de volver temporalmente a PostgreSQL.

## Documentos

1. [Arquitectura funcional](01_arquitectura_funcional.md)
2. [Modelo documental de mensajes](02_modelo_documental_mensajes.md)
3. [Escritura, Outbox e idempotencia](03_escritura_outbox_idempotencia.md)
4. [Migración histórica y checkpoints](04_migracion_historica_checkpoints.md)
5. [Lectura, paginación y rollback](05_lectura_paginacion_rollback.md)
6. [Memoria y contexto](06_memoria_contexto.md)
7. [Despliegue y operación](07_despliegue_operacion.md)
8. [Observabilidad y reconciliación](08_observabilidad_reconciliacion.md)
9. [Pruebas y trazabilidad](09_pruebas_trazabilidad.md)
10. [Resumen](10_resumen_fase11.md)
11. [Acta de cierre](11_acta_cierre_fase11.md)

## Fuentes ejecutables

- `backend/app/modules/asistente_proyecto/services/conversation_document_store.py`
- `backend/app/core/nosql/commands/migrate_ai_memory.py`
- `backend/app/core/nosql/outbox.py`
- `backend/tests/test_phase11_ai_memory_mongodb.py`
- `backend/tests/test_phase11_ai_memory_integration.py`
- `backend/migrations/versions/f8b2c3d4e5f6_phase11_ai_memory_migration_index.py`
