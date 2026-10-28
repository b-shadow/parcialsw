# Reconciliacion y huerfanos

## Ejecucion

```powershell
python -m app.core.nosql.commands.reconcile --operational --require-complete
python -m app.core.nosql.commands.reconcile --operational --watch --interval-seconds 300
```

La auditoria detecta:

- documentos sin registro SQL y registros sin documento;
- referencias a proyecto, diagrama o conversacion inexistentes;
- relaciones UML hacia clases inexistentes;
- hashes UML invalidos y documentos no parseables;
- revisiones Mongo atrasadas respecto a PostgreSQL;
- secuencias de mensajes duplicadas;
- backlog y eventos muertos de Outbox;
- nodos Mongo no escribibles y documentos sobredimensionados.

Cada corrida se guarda en `nosql_operational_audits`, con duracion, hallazgos, metricas y estado de colecciones. En modo consolidado los mensajes se validan contra su conversacion y proyecto, no contra la tabla heredada `ai_messages`.
