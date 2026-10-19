# Protocolo WebSocket colaborativo

## Conexion

```text
GET /ws/projects/{project_id}
Sec-WebSocket-Protocol: case-v1, case-auth.{JWT}
```

El servidor valida origen, JWT, usuario activo y membresia antes de aceptar. `SESSION_CONNECTED` comunica `connection_id`, `project_sequence` y `conversation_sequence`.

## Sobre v2

```json
{
  "protocol_version": 2,
  "type": "AI_MESSAGE_CREATED",
  "event_id": "uuid",
  "project_id": "uuid",
  "diagram_id": null,
  "sequence_number": 125,
  "conversation_sequence": 34,
  "correlation_id": "uuid",
  "occurred_at": "ISO-8601",
  "persistent": true,
  "actor": { "user_id": "uuid", "display_name": "Ana" },
  "payload": {}
}
```

`sequence_number` ordena todos los eventos durables del proyecto. `conversation_sequence` ordena mensajes. Los eventos efimeros usan secuencia de proyecto cero y `persistent=false`.

## Eventos

| Grupo | Tipos |
| --- | --- |
| Mensajes | `AI_MESSAGE_CREATED`, `AI_MESSAGE_STATUS_CHANGED` |
| Acciones | `AI_ACTION_PROPOSED`, `AI_ACTION_STATUS_CHANGED` |
| Recomendaciones | `AI_RECOMMENDATION_CREATED`, `AI_RECOMMENDATION_STATUS_CHANGED` |
| Memoria | `AI_CONVERSATION_SUMMARY_UPDATED` |
| Proceso | `AI_PROCESSING_STARTED`, `AI_PROCESSING_FINISHED`, `AI_PROCESSING_FAILED` |
| Presencia | `PRESENCE_JOINED`, `PRESENCE_LEFT`, `PRESENCE_SNAPSHOT` |
| Recuperacion | `SYNC_REQUIRED` |

## Heartbeat, presencia y revocacion

El cliente envia `PING` cada 20 segundos. El servidor responde `PONG`, actualiza `last_seen_at` y revalida acceso. `ACTIVE_DIAGRAM` mantiene el diagrama observado. Varias pestanas del mismo usuario se agregan con `connection_count`; solo se emite salida al cerrarse su ultima conexion.

## Reconexion y catch-up

El cliente aplica espera exponencial con variacion, hasta 30 segundos. Al reconectar envia:

```json
{
  "type": "SYNC_STATE",
  "last_project_sequence": 120,
  "last_conversation_sequence": 31
}
```

Si existe una brecha, el servidor envia `SYNC_REQUIRED`. El cliente solicita mensajes posteriores al cursor y eventos de proyecto posteriores a su secuencia, refresca acciones/recomendaciones y actualiza ambos cursores. Los `event_id` recientes se deduplican en memoria. Los comandos de escritura no se reenvian automaticamente.
