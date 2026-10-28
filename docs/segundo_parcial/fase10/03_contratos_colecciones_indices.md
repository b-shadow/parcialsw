# Contratos, colecciones e índices

## Convención común

```json
{
  "_id": "uuid",
  "schema_version": 1,
  "created_at": "BSON date UTC",
  "updated_at": "BSON date UTC"
}
```

Los modelos Pydantic rechazan campos desconocidos. MongoDB aplica validadores `$jsonSchema` en nivel `strict` y acción `error`. El bootstrap usa `create_collection`, `collMod` y `create_indexes`, por lo que es repetible.

## Colecciones

### `uml_diagrams`

Contiene `project_id`, `revision`, `content` y `content_hash`. Índices:

- único por `project_id`;
- descendente por `updated_at`.

### `uml_diagram_versions`

Contiene `project_id`, `diagram_id`, `version_number`, `content`, `content_hash` y autor opcional. Índices:

- único `(diagram_id, version_number)`;
- `(project_id, created_at desc)`.

### `ai_messages`

Contiene proyecto, conversación, autor, rol, secuencia, contenido, correlación, id cliente, metadatos y hash. Índices:

- único `(conversation_id, sequence_number)`;
- `(project_id, created_at desc)`;
- único parcial `(conversation_id, client_message_id)` cuando el id existe.

### `ai_context_snapshots`

Almacena resúmenes y contexto acotado por conversación. Índices:

- único `(conversation_id, until_sequence)`;
- TTL en `expires_at`.

### `migration_checkpoints`

Registra nombre, estado, cursor, procesados, fallidos y detalles. Índices:

- único por `migration_name`;
- `(status, updated_at)`.

### `nosql_processed_events`

Conserva recibos de Outbox. Índices únicos por `idempotency_key` y `event_id`, más índice temporal por `processed_at`.

## Versionado

`schema_version=1` es obligatorio. Una evolución incompatible debe añadir un nuevo modelo y un migrador reiniciable; no se modifica silenciosamente el significado de una versión existente.

## Tamaño

Archivos, imágenes UML y artefactos ZIP quedan fuera de BSON. El contenido grande se separa por mensaje o versión para evitar documentos con crecimiento ilimitado.
