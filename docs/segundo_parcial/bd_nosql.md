# Catalogo de la base de datos MongoDB

MongoDB almacena los agregados documentales de crecimiento o estructura variable.
Los contratos se encuentran en `backend/app/core/nosql/contracts.py` y los
validadores e indices en `backend/app/core/nosql/schema.py`.

## Convenciones comunes

Todos los documentos tienen:

- `_id`: UUID serializado como `string`; clave primaria del documento.
- `schema_version`: entero positivo; actualmente `1`.
- `created_at`: fecha BSON.
- `updated_at`: fecha BSON.

MongoDB no declara claves foraneas. Las relaciones descritas abajo son referencias
logicas verificadas por la aplicacion y por el reconciliador de la fase 14.

## `uml_diagrams`

Fuente de verdad del diagrama activo de cada proyecto.

- Atributos: `_id`, `schema_version`, `created_at`, `updated_at`,
  `project_id UUID-string`, `revision int >= 0`, `content object`,
  `content_hash string SHA-256`.
- Relaciones logicas: `_id -> PostgreSQL uml_diagrams.id` y
  `project_id -> PostgreSQL projects.id`.
- Restriccion: un documento por `project_id`.
- Indices: `project_id` unico y `updated_at DESC`.

### Estructura de `content`

- Diagrama: `id?`, `project_id?`, `name`, `diagram_type`, `status`,
  `current_version`, `description?`, `classes[]`, `relationships[]`, `metadata_json`.
- Clase: `id?`, `name`, `visibility`, `element_type`, `stereotype?`,
  `description?`, `attributes[]`, `methods[]`, `visual`, `metadata_json`.
- Atributo: `id?`, `name`, `data_type`, `visibility`, `initial_value?`,
  `multiplicity?`, `is_required`, `order_index`, `constraints`.
- Metodo: `id?`, `name`, `return_type?`, `visibility`, `order_index`,
  `parameters[]`, `metadata_json`, `specification?`, `readiness?`.
- Parametro: `id?`, `name`, `data_type`, `default_value?`, `order_index`.
- Visual: `id?`, `x`, `y`, `width?`, `height?`, `style`.
- Relacion: `id?`, `source_class_id`, `target_class_id`, `relationship_type`,
  `source_cardinality?`, `target_cardinality?`, `direction`, `label?`,
  `metadata_json`.

Las relaciones UML solo pueden referenciar clases incluidas en el mismo documento.

## `uml_diagram_versions`

Snapshots inmutables utilizados por el historial y la restauracion.

- Atributos: `_id`, `schema_version`, `created_at`, `updated_at`,
  `project_id UUID-string`, `diagram_id UUID-string`, `version_number int >= 1`,
  `project_revision int >= 0`, `snapshot_schema_version int >= 1`,
  `name string`, `description string?`, `kind manual|pre_restore_backup`,
  `snapshot_size_bytes int >= 0`, `content object`, `content_hash SHA-256`,
  `created_by_user_id UUID-string?`.
- Relaciones logicas: `_id -> project_versions.id`, `project_id -> projects.id`,
  `diagram_id -> uml_diagrams.id`, `created_by_user_id -> users.id`.
- Indices: `(diagram_id, version_number)` unico,
  `(project_id, version_number)` unico, `(project_id, created_at DESC)` y
  `content_hash`.

## `ai_messages`

Fuente de verdad del historial completo de conversaciones.

- Atributos: `_id`, `schema_version`, `created_at`, `updated_at`,
  `project_id UUID-string`, `conversation_id UUID-string`,
  `author_user_id UUID-string?`, `role user|assistant|system|tool`,
  `sequence_number int >= 1`, `content string`, `correlation_id UUID-string`,
  `client_message_id UUID-string?`,
  `status pending|streaming|completed|failed|cancelled`, `detected_intents[]`,
  `references_json[]`, `metadata_json object`, `content_hash SHA-256`.
- Relaciones logicas: `project_id -> projects.id`,
  `conversation_id -> ai_conversations.id`, `author_user_id -> users.id`.
- Indices: `(conversation_id, sequence_number)` unico,
  `(project_id, created_at DESC)` y `(conversation_id, client_message_id)` unico
  cuando `client_message_id` existe.

## `ai_context_snapshots`

Resumen y contexto compacto para evitar reconstruir conversaciones extensas.

- Atributos: `_id`, `schema_version`, `created_at`, `updated_at`,
  `project_id UUID-string`, `conversation_id UUID-string`,
  `until_sequence int >= 0`, `summary string`, `context object`,
  `content_hash SHA-256`, `expires_at date?`.
- Relaciones logicas: `project_id -> projects.id` y
  `conversation_id -> ai_conversations.id`.
- Indices: `(conversation_id, until_sequence DESC)` unico y TTL sobre `expires_at`.

## `migration_checkpoints`

Control reiniciable de las migraciones SQL hacia MongoDB y del gate de consolidacion.

- Atributos: `_id`, `schema_version`, `created_at`, `updated_at`,
  `migration_name string`, `status pending|running|completed|failed`,
  `cursor string?`, `processed_count int >= 0`, `failed_count int >= 0`,
  `details object`.
- Relaciones logicas: no pertenece a una entidad funcional; identifica una tarea
  de migracion por nombre.
- Indices: `migration_name` unico y `(status, updated_at)`.

## `nosql_processed_events`

Recibos idempotentes de los eventos publicados desde PostgreSQL.

- Atributos: `_id`, `schema_version`, `created_at`, `updated_at`,
  `idempotency_key string`, `event_id UUID-string`, `collection string`,
  `operation upsert|delete`, `processed_at date`.
- Relaciones logicas: `event_id -> PostgreSQL nosql_outbox_events.id`; `collection`
  identifica la coleccion modificada.
- Indices: `idempotency_key` unico, `event_id` unico y `processed_at DESC`.

## `nosql_operational_audits`

Resultados historicos del reconciliador operativo.

- Atributos: `_id`, `schema_version`, `created_at`, `updated_at`,
  `status healthy|degraded`, `duration_ms int >= 0`, `findings[]`, `metrics object`,
  `collection_reports[]`.
- Relaciones logicas: los hallazgos pueden mencionar IDs de documentos, proyectos,
  diagramas o conversaciones sin imponer una FK.
- Indices: `created_at DESC` y `(status, created_at DESC)`.

## Mapa de integracion

```text
PostgreSQL projects.id
  -> MongoDB uml_diagrams.project_id
  -> MongoDB uml_diagram_versions.project_id
  -> MongoDB ai_messages.project_id
  -> MongoDB ai_context_snapshots.project_id

PostgreSQL uml_diagrams.id
  -> MongoDB uml_diagrams._id
  -> MongoDB uml_diagram_versions.diagram_id

PostgreSQL project_versions.id
  -> MongoDB uml_diagram_versions._id

PostgreSQL ai_conversations.id
  -> MongoDB ai_messages.conversation_id
  -> MongoDB ai_context_snapshots.conversation_id

PostgreSQL nosql_outbox_events.id
  -> MongoDB nosql_processed_events.event_id
```

## Autoridad de datos

| Informacion | Fuente de verdad |
|---|---|
| Usuarios, proyectos, permisos y registros | PostgreSQL |
| Diagrama UML activo y elementos embebidos | MongoDB `uml_diagrams` |
| Versiones inmutables del diagrama | MongoDB `uml_diagram_versions` |
| Mensajes del asistente | MongoDB `ai_messages` |
| Resumen y contexto extenso | MongoDB `ai_context_snapshots` |
| Integraciones documentales asincronas | PostgreSQL `nosql_outbox_events` |
| Idempotencia de consumo | MongoDB `nosql_processed_events` |
