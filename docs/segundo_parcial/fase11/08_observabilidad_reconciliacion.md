# Observabilidad y reconciliación

## Señales

- `ai_message_store_drift`: mensaje faltante o hash distinto.
- `MongoDB message read failed`: lectura no disponible y fallback aplicado.
- conteos `processed/completed/retry/dead` del worker.
- reporte JSON del migrador.
- componente `ai_memory_migration` en readiness productivo.

## Consultas

```sql
SELECT status, count(*)
FROM nosql_outbox_events
WHERE aggregate_type IN ('ai_message', 'ai_context_snapshot')
GROUP BY status;
```

```javascript
db.ai_messages.countDocuments({})
db.ai_context_snapshots.countDocuments({})
db.migration_checkpoints.findOne({migration_name: "phase11_ai_memory_v1"})
```

## Respuesta a divergencias

1. Desactivar lectura Mongo si afecta al usuario.
2. Mantener el worker detenido sólo si está generando el problema.
3. Ejecutar `--verify-only` y conservar su JSON.
4. Corregir causa o documento explícitamente.
5. Reanudar migrador desde checkpoint o usar reset idempotente.
6. Verificar de nuevo antes de reactivar lectura.

Los huérfanos no se borran automáticamente; pueden representar evidencia necesaria para recuperar una operación.
