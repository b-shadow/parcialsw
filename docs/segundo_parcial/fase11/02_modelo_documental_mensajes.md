# Modelo documental de mensajes

## Documento `ai_messages`

```json
{
  "_id": "uuid-del-mensaje",
  "schema_version": 1,
  "project_id": "uuid-del-proyecto",
  "conversation_id": "uuid-del-chat",
  "author_user_id": "uuid-o-null",
  "role": "user|assistant|system|tool",
  "content": "texto",
  "sequence_number": 12,
  "client_message_id": "uuid-o-null",
  "correlation_id": "uuid",
  "status": "completed",
  "detected_intents": [],
  "references_json": [],
  "metadata_json": {},
  "content_hash": "sha256",
  "created_at": "BSON date UTC",
  "updated_at": "BSON date UTC"
}
```

No se pierde ningún campo expuesto previamente por `AiMessageResponse`.

## Índices

- único `(conversation_id, sequence_number)`;
- único parcial `(conversation_id, client_message_id)` cuando el cliente envía id;
- `(project_id, created_at desc)`;
- índice SQL `(created_at, id)` para migración por cursor estable.

## Hash canónico

`content_hash` incluye identidad, proyecto, conversación, autor, rol, contenido, secuencia, ids de cliente/correlación, estado, intenciones, referencias y metadatos. No incluye fechas ni el propio hash, evitando cambios por serialización temporal.

## Límites

Cada mensaje es un documento independiente. Ningún historial se incrusta en una conversación, por lo que su crecimiento no acerca un único documento al límite BSON ni obliga a cargar el chat completo.
