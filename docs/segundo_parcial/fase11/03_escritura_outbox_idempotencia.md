# Escritura, Outbox e idempotencia

## Transacción

`enqueue_message_document` ejecuta `flush`, construye el documento validado y añade una mutación Outbox antes del `commit` del servicio llamador. Si PostgreSQL revierte, también desaparece el evento.

Se cubren estos productores:

- mensaje del usuario;
- respuesta del asistente;
- transición a `completed` o `failed`;
- refinamiento funcional de métodos;
- mensaje de sistema por restauración de versión.

## Clave idempotente

```text
ai-message:{message_id}:{content_hash}
```

La misma versión lógica no puede duplicar eventos. Una actualización válida cambia el hash y genera un evento nuevo.

## Orden fuera de secuencia

El worker compara `updated_at`. Un evento sólo reemplaza el documento si no es más antiguo que el almacenado. Por ello un evento `pending` retrasado no puede revertir posteriormente un mensaje `completed`.

## Reconexión

PostgreSQL conserva la restricción de `client_message_id`. Repetir una petición devuelve el mismo mensaje y no crea otro evento ni otra secuencia. Los eventos WebSocket reutilizan el id y la correlación persistidos.

## Fallos

- Mongo no disponible: SQL y Outbox quedan durables.
- Worker interrumpido: el bloqueo expira y otro worker recupera el evento.
- Aplicación repetida: `upsert` produce el mismo documento.
- Recibo duplicado: el índice único lo trata como ejecución ya completada.
- Intentos agotados: el evento pasa a `dead` para intervención explícita.
