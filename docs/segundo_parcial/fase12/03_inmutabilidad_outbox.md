# Inmutabilidad y Outbox

## Garantia transaccional

`enqueue_version_document` se ejecuta despues del `flush` de `ProjectVersion` y antes del `commit`. El registro y su evento Outbox se confirman o revierten juntos. No existe escritura directa a MongoDB dentro de la peticion.

La clave idempotente tiene la forma:

```text
uml-version:{version_id}:{content_hash}
```

## Regla append-only

El despachador aplica estas decisiones:

1. Si `_id` no existe, inserta el documento validado.
2. Si existe con el mismo hash, confirma la repeticion sin modificarlo.
3. Si existe con otro hash, rechaza el evento y no registra recibo exitoso.
4. Un conflicto en otro indice unico tambien se considera inconsistencia.

El repositorio usado por la migracion implementa la misma regla mediante `insert_immutable`. Las versiones manuales y respaldos previos a restauracion comparten esta proteccion.
