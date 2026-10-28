# Consistencia, Outbox y reconciliación

## Problema evitado

PostgreSQL y MongoDB no comparten una transacción distribuida. Escribir primero en uno y luego en otro puede dejar datos divergentes si el segundo paso falla.

## Outbox transaccional

La migración `e7a1b2c3d4e5` crea `nosql_outbox_events`. El servicio productor añade el evento a la misma sesión SQL del cambio de negocio y no ejecuta `commit` por cuenta propia.

Estados:

```text
pending -> processing -> completed
                   \-> retry -> processing
                   \-> dead
```

El worker:

- reclama filas con `FOR UPDATE SKIP LOCKED`;
- recupera bloqueos de más de cinco minutos;
- usa backoff exponencial con variación;
- limita intentos;
- libera el bloqueo después de cada resultado;
- registra un recibo Mongo único.

Si el proceso cae después de aplicar un `upsert` y antes del recibo, repetir la operación produce el mismo documento. Para ello el contrato prohíbe operaciones incrementales genéricas.

## Uso productor

```python
mutation = MongoMutation(
    collection=MongoCollection.UML_DIAGRAMS,
    operation="upsert",
    document_id=diagram_id,
    document=document,
)
NoSqlOutboxService(db).enqueue(
    aggregate_type="uml_diagram",
    aggregate_id=diagram_id,
    mutation=mutation,
    idempotency_key=f"uml:{diagram_id}:revision:{revision}",
)
db.commit()
```

## Reconciliación

`ReconciliationService` compara:

- cantidad SQL y Mongo;
- identificadores huérfanos en Mongo;
- faltantes SQL cuando se activa `--require-complete`;
- `content_hash` esperado cuando el migrador lo suministra.

Comando:

```bash
cd backend
python -m app.core.nosql.commands.reconcile
python -m app.core.nosql.commands.reconcile --require-complete
python -m app.core.nosql.commands.reconcile --hash-manifest expected-hashes.json
```

El manifiesto tiene la forma `{"uml_diagrams": {"uuid": "sha256"}}`; permite comparar hashes calculados por un migrador sin acoplar el reconciliador al formato SQL de una fase concreta.

Códigos: `0` consistente, `1` almacén no disponible y `2` divergencia. La herramienta nunca repara automáticamente.
