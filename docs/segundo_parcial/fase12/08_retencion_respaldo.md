# Retencion y respaldo

## Politica

- Las versiones manuales validas no caducan automaticamente.
- Los respaldos `pre_restore_backup` tampoco se eliminan durante las fases 12 y 13.
- No existe TTL en `uml_diagram_versions`.
- Cualquier futura depuracion requiere estado archivado, auditoria y respaldo coordinado.
- Las imagenes, XMI y artefactos ZIP permanecen fuera de BSON.

## Respaldo coordinado

Un punto recuperable debe incluir PostgreSQL, `uml_diagram_versions`, `nosql_processed_events` y checkpoints. Se registra la misma hora de corte y se verifica luego que cada `project_versions.id` tenga un `_id` documental con hash coincidente.

El rollback operativo cambia las banderas de lectura a SQL; no elimina documentos Mongo ni columnas JSONB. El retiro del JSONB queda fuera de esta fase y solo puede decidirse tras la estabilizacion de la Fase 13.
