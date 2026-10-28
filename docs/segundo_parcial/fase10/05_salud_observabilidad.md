# Salud y observabilidad

## Liveness

`GET /health` conserva el contrato anterior:

```json
{"status": "ok", "component": "backend"}
```

Sólo indica que el proceso HTTP responde.

## Readiness

`GET /ready` comprueba ambos almacenes y evita ocultar un error del servidor como CORS:

```json
{
  "status": "ok",
  "components": {
    "postgresql": {"status": "available", "required": true},
    "mongodb": {
      "status": "available",
      "required": true,
      "database": "case_inteligente_nosql"
    }
  }
}
```

PostgreSQL no disponible siempre produce `503`. MongoDB produce `503` cuando `MONGODB_REQUIRED=true`; en transición puede informarse no disponible sin retirar el backend del balanceador.

## Señales operativas

- log `MongoDB is unavailable` con clase de error, sin URI ni credenciales;
- salida estructurada del worker con procesados, completados, reintentos y muertos;
- reporte JSON del reconciliador;
- health checks de contenedor para PostgreSQL y MongoDB;
- tabla Outbox consultable por estado, disponibilidad y agregado.

## Consultas de diagnóstico

```sql
SELECT status, count(*)
FROM nosql_outbox_events
GROUP BY status;
```

```javascript
db.nosql_processed_events.countDocuments({})
db.uml_diagrams.getIndexes()
```

No se incluyen secretos, contenido de conversaciones ni documentos UML completos en logs.
