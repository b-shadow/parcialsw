# Metricas y alertas

## Metricas registradas

- latencia de `ping` a MongoDB;
- revision maxima atrasada;
- tamano BSON maximo;
- documentos, almacenamiento y promedio por coleccion;
- indices disponibles y operaciones por indice mediante `$indexStats`;
- topologia, replica set, hosts y capacidad de escritura;
- eventos Outbox por estado;
- duracion total de la auditoria.

## Umbrales

```text
NOSQL_ALERT_PENDING_OUTBOX=100
NOSQL_ALERT_DEAD_OUTBOX=1
NOSQL_ALERT_MAX_DOCUMENT_BYTES=12000000
NOSQL_ALERT_MAX_REVISION_LAG=0
```

Los hallazgos generan estado `degraded`, salida distinta de cero en ejecucion unica y log estructurado `nosql_reconciliation_alert`. Compose reinicia el worker continuo y `/ready` rechaza auditorias degradadas o antiguas.
