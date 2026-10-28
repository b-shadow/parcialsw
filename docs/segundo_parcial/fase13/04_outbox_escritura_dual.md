# Outbox y escritura dual

## Garantia transaccional

`mark_uml_project_for_sync` registra el proyecto en `Session.info`. En `before_commit`, despues de `flush`, se construye el documento canonico y se inserta `nosql_outbox_events` sin realizar un segundo commit. Una caida no puede confirmar el cambio SQL sin dejar registrada su entrega a MongoDB.

La clave idempotente usa:

```text
uml-diagram:{diagram_id}:{revision}:{content_hash}
```

## Orden y repeticion

- Una revision antigua recibe comprobante, pero no sobrescribe una nueva.
- La misma revision y hash es una repeticion valida.
- La misma revision con hash distinto es conflicto.
- El comprobante en `nosql_processed_events` evita aplicar dos veces el mismo evento.
- Los reintentos usan backoff y terminan en `dead` despues del limite configurado.

Las eliminaciones tambien se encolan y se ejecutan de forma idempotente por UUID.
