# Resumen de la Fase 12

La fase incorpora `uml_diagram_versions` como almacenamiento principal del contenido de versiones UML. Cada nueva version y cada respaldo previo a restauracion generan un evento Outbox dentro de la transaccion SQL. El worker valida e inserta el documento sin permitir modificaciones posteriores.

Las operaciones de vista previa y restauracion son Mongo-first, comparan hashes y mantienen rollback SQL configurable. El migrador historico es paginado, reiniciable, compatible con snapshots v1/v2 y produce un reporte de faltantes, huerfanos y divergencias.

Produccion incluye una tarea de migracion previa al backend, readiness obligatorio, indices BSON/SQL, variables operativas y CI con ambos motores reales. El contrato del frontend no cambia y el contenido editable permanece en PostgreSQL hasta la Fase 13.
