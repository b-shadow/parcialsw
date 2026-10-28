# Gate de consolidacion

El comando bloqueante es:

```powershell
python -m app.core.nosql.commands.consolidate --minimum-healthy-audits 3
```

El checkpoint `phase14_consolidation_v1` solo queda `completed` cuando:

- las migraciones de mensajes, versiones y diagrama activo terminaron;
- la auditoria operativa no tiene hallazgos;
- Outbox no contiene `pending`, `retry`, `processing` ni `dead`;
- existe la cantidad minima de auditorias saludables en siete dias.

Un fallo registra `failed`, lista bloqueadores y mantiene el backend fuera de readiness cuando `PHASE14_CONSOLIDATION_REQUIRED=true`. El gate nunca repara ni borra datos automaticamente.
