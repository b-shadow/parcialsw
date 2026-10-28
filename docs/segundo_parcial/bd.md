# Catalogo de la base de datos PostgreSQL

Este documento describe el esquema cargado por `backend/app/models.py` y las
migraciones Alembic vigentes hasta `d2f6a7b8c9d0`.

## Convenciones

- Todas las tablas tienen `id UUID PK`, `created_at TIMESTAMPTZ` y
  `updated_at TIMESTAMPTZ` mediante los mixins comunes.
- `?` indica que el atributo acepta `NULL`.
- `FK -> tabla.columna` indica una clave foranea.
- `JSONB` representa estructuras variables validadas por la aplicacion.
- MongoDB es la unica fuente de verdad del contenido UML, snapshots, mensajes y
  contexto. PostgreSQL conserva solo registros administrativos y referencias
  logicas hacia los documentos.

## Acceso y usuarios

### `users`

- Atributos: `full_name VARCHAR(150)`, `email VARCHAR(180)`,
  `password_hash VARCHAR(255)`, `is_active BOOLEAN`, `last_access_at TIMESTAMPTZ?`.
- Relaciones: es propietario de proyectos y puede aparecer como autor, miembro,
  invitado, actor, destinatario o solicitante en los modulos restantes.

### `roles`

- Atributos: `name VARCHAR(50)`, `description TEXT?`, `is_system BOOLEAN`.
- Relaciones: `roles 1 -- N user_roles`.

### `user_roles`

- Atributos: `user_id UUID FK -> users.id`, `role_id UUID FK -> roles.id`.
- Restriccion: un solo registro de rol por usuario (`UNIQUE user_id`).
- Relaciones: resuelve la asociacion entre usuarios y roles globales.

### `user_sessions`

- Atributos: `user_id UUID FK -> users.id`, `refresh_token_hash VARCHAR(255)?`,
  `ip_address VARCHAR(80)?`, `user_agent VARCHAR(255)?`, `revoked_at TIMESTAMPTZ?`,
  `expires_at TIMESTAMPTZ`.
- Relaciones: `users 1 -- N user_sessions`.

### `audit_logs`

- Atributos: `user_id UUID? FK -> users.id`, `project_id UUID? FK -> projects.id`,
  `module VARCHAR(80)`, `action VARCHAR(120)`, `result VARCHAR(40)`, `detail TEXT?`,
  `metadata_json JSONB`.
- Relaciones: cada registro puede estar asociado con un usuario y un proyecto.

## Proyectos y colaboracion

### `projects`

- Atributos: `owner_id UUID FK -> users.id`, `name VARCHAR(160)`,
  `description TEXT?`, `status VARCHAR(40)`, `settings JSONB`, `revision INTEGER`,
  `next_version_number INTEGER`.
- Relaciones: un usuario posee muchos proyectos; cada proyecto agrupa miembros,
  permisos, invitaciones, diagramas, chats, versiones, generaciones y eventos.

### `project_members`

- Atributos: `project_id UUID FK -> projects.id`, `user_id UUID FK -> users.id`,
  `project_role VARCHAR(40)`, `joined_at TIMESTAMPTZ?`.
- Restriccion: `UNIQUE(project_id, user_id)`.
- Relaciones: tabla asociativa entre proyectos y usuarios; tiene permisos
  particulares en `project_permissions`.

### `project_permissions`

- Atributos: `member_id UUID FK -> project_members.id`,
  `permission_code VARCHAR(80)`, `is_allowed BOOLEAN`.
- Restriccion: `UNIQUE(member_id, permission_code)`.
- Relaciones: `project_members 1 -- N project_permissions`.

### `project_invitations`

- Atributos: `project_id UUID FK -> projects.id`,
  `invited_by_user_id UUID FK -> users.id`, `invited_user_id UUID? FK -> users.id`,
  `invited_email VARCHAR(180)`, `project_role VARCHAR(40)`, `status VARCHAR(40)`,
  `expires_at TIMESTAMPTZ?`, `responded_at TIMESTAMPTZ?`.
- Relaciones: pertenece a un proyecto, identifica al emisor y opcionalmente al
  usuario destinatario ya registrado.

### `collaboration_events`

- Atributos: `project_id UUID FK -> projects.id`,
  `diagram_id UUID? FK -> uml_diagrams.id`, `user_id UUID FK -> users.id`,
  `client_event_id UUID`, `sequence_number INTEGER`, `event_type VARCHAR(80)`,
  `element_type VARCHAR(80)?`, `element_id UUID?`, `base_version INTEGER?`,
  `payload JSONB`, `actor_display_name VARCHAR(160)?`, `resource_type VARCHAR(80)?`,
  `resource_id UUID?`, `correlation_id UUID?`, `causation_id UUID?`,
  `summary_key VARCHAR(160)?`.
- Restricciones: secuencia unica por proyecto y evento de cliente unico por
  `project_id`, `user_id` y `client_event_id`.
- Relaciones: registra acciones colaborativas de un usuario sobre un proyecto y,
  opcionalmente, su diagrama.

### `project_versions`

- Atributos: `project_id UUID FK -> projects.id`,
  `created_by_user_id UUID FK -> users.id`, `version_number INTEGER`,
  `name VARCHAR(120)`, `description TEXT?`, `snapshot JSONB` reservado vacio,
  `status VARCHAR(40)`,
  `kind VARCHAR(40)`, `snapshot_schema_version INTEGER`, `snapshot_hash VARCHAR(64)`,
  `snapshot_size_bytes INTEGER`, `project_revision INTEGER`,
  `idempotency_key VARCHAR(120)?`, `metadata_json JSONB`,
  `snapshot_storage VARCHAR(20) = 'mongodb'`.
- Restricciones: version unica por proyecto e idempotencia por proyecto/usuario.
- Relaciones: registro SQL de una version; el snapshot canonico se almacena en
  MongoDB `uml_diagram_versions`. En modo consolidado `snapshot` permanece `{}`.

### `project_restore_operations`

- Atributos: `project_id UUID FK -> projects.id`,
  `source_version_id UUID FK -> project_versions.id`,
  `backup_version_id UUID? FK -> project_versions.id`,
  `requested_by_user_id UUID FK -> users.id`, `idempotency_key VARCHAR(120)`,
  `status VARCHAR(24)`, `source_snapshot_hash VARCHAR(64)`,
  `before_snapshot_hash VARCHAR(64)`, `after_snapshot_hash VARCHAR(64)?`,
  `project_revision_before INTEGER`, `project_revision_after INTEGER?`,
  `diagnostics_json JSONB`, `started_at TIMESTAMPTZ`, `completed_at TIMESTAMPTZ?`.
- Restriccion: operacion idempotente por proyecto, usuario y clave.
- Relaciones: enlaza proyecto, version restaurada, respaldo preventivo y usuario.

## Modelado UML

### `uml_diagrams`

- Atributos: `project_id UUID FK -> projects.id`,
  `created_by_user_id UUID FK -> users.id`, `name VARCHAR(160)`,
  `diagram_type VARCHAR(50)`, `status VARCHAR(40)`, `current_version INTEGER`,
  `description TEXT?`, `metadata_json JSONB`,
  `content_storage VARCHAR(20) = 'mongodb'`.
- Relaciones: cada proyecto posee su registro de diagrama; el contenido completo
  esta en MongoDB `uml_diagrams`.

### `xmi_exchanges`

- Atributos: `diagram_id UUID FK -> uml_diagrams.id`,
  `user_id UUID FK -> users.id`, `exchange_type VARCHAR(30)`,
  `tool_name VARCHAR(120)?`, `file_name VARCHAR(255)`, `file_path VARCHAR(500)?`,
  `status VARCHAR(40)`, `error_detail TEXT?`, `metadata_json JSONB`.
- Relaciones: registra cada importacion o exportacion XMI de un diagrama y usuario.

## Asistente e IA

### `ai_conversations`

- Atributos: `title VARCHAR(160)`, `created_by_user_id UUID? FK -> users.id`,
  `project_id UUID FK -> projects.id`, `status VARCHAR(30)`,
  `summary TEXT?` reservado vacio,
  `summary_until_sequence INTEGER`, `last_message_sequence INTEGER`,
  `schema_version INTEGER`, `message_storage VARCHAR(20) = 'mongodb'`.
- Relaciones: `projects 1 -- N ai_conversations`; los mensajes canonicos estan en
  MongoDB y se identifican mediante `conversation_id`.

### `ai_project_settings`

- Atributos: `project_id UUID FK -> projects.id`, `enabled BOOLEAN`,
  `preferred_provider VARCHAR(40)`, `model_name VARCHAR(120)`,
  `fallback_enabled BOOLEAN`, `require_confirmation BOOLEAN`,
  `max_context_messages INTEGER`, `summary_trigger_messages INTEGER`,
  `settings_json JSONB`, `created_by_user_id UUID FK -> users.id`,
  `updated_by_user_id UUID FK -> users.id`.
- Restriccion: `UNIQUE(project_id)`, configuracion uno a uno por proyecto.

### `ai_actions`

- Atributos: `project_id UUID FK -> projects.id`,
  `conversation_id UUID FK -> ai_conversations.id`,
  `source_message_id UUID` referencia logica a MongoDB `ai_messages._id`,
  `requested_by_user_id UUID FK -> users.id`, `action_type VARCHAR(80)`,
  `target_type VARCHAR(80)?`, `target_id UUID?`, `payload JSONB`,
  `risk_level VARCHAR(20)`, `requires_confirmation BOOLEAN`, `status VARCHAR(30)`,
  `confirmed_by_user_id UUID? FK -> users.id`, `confirmed_at TIMESTAMPTZ?`,
  `executed_at TIMESTAMPTZ?`, `result_json JSONB`, `error_message TEXT?`,
  `idempotency_key UUID`.
- Restriccion: clave idempotente unica por proyecto.
- Relaciones: una accion nace de un mensaje y puede ser confirmada por otro usuario.

### `ai_recommendations`

- Atributos: `project_id UUID FK -> projects.id`,
  `conversation_id UUID FK -> ai_conversations.id`,
  `source_message_id UUID` referencia logica a MongoDB `ai_messages._id`,
  `severity VARCHAR(20)`, `title VARCHAR(200)`, `description TEXT`,
  `references_json JSONB`, `status VARCHAR(30)`,
  `resolved_by_user_id UUID? FK -> users.id`, `resolved_at TIMESTAMPTZ?`,
  `resolution_note TEXT?`.
- Relaciones: recomendacion asociada al proyecto, chat y mensaje documental que la origino.

## Tablas retiradas en `d2f6a7b8c9d0`

La migracion destructiva elimina `uml_classes`, `uml_attributes`, `uml_methods`,
`uml_method_specifications`, `uml_parameters`, `uml_relationships`,
`uml_visual_elements` y `ai_messages`. Sus datos existen exclusivamente en las
colecciones `uml_diagrams` y `ai_messages`. Alembic excluye deliberadamente esos
nombres del autogenerado para impedir su recreacion accidental.

### `ai_processes`

- Atributos: `user_id UUID FK -> users.id`, `project_id UUID? FK -> projects.id`,
  `diagram_id UUID? FK -> uml_diagrams.id`, `process_type VARCHAR(80)`,
  `model_provider VARCHAR(80)`, `model_name VARCHAR(120)?`, `input_payload JSONB`,
  `output_payload JSONB`, `status VARCHAR(40)`, `error_detail TEXT?`.
- Relaciones: traza una ejecucion de IA y sus recursos relacionados.

## Generacion de software

### `uml_transformations`

- Atributos: `project_id UUID FK -> projects.id`,
  `diagram_id UUID FK -> uml_diagrams.id`, `requested_by_user_id UUID FK -> users.id`,
  `source_version VARCHAR(80)?`, `target_platform VARCHAR(80)`,
  `intermediate_model JSONB`, `status VARCHAR(40)`, `error_detail TEXT?`.
- Relaciones: transforma un diagrama para alimentar una generacion.

### `generated_backends`

- Atributos: `project_id UUID FK -> projects.id`,
  `transformation_id UUID FK -> uml_transformations.id`,
  `generated_by_user_id UUID FK -> users.id`, `name VARCHAR(160)`,
  `technology VARCHAR(80)`, `language VARCHAR(40)`, `database_engine VARCHAR(80)`,
  `version_label VARCHAR(80)`, `status VARCHAR(40)`, `artifact_path VARCHAR(500)?`,
  `manifest JSONB`, `error_detail TEXT?`.
- Relaciones: pertenece a un proyecto y transformacion; puede ser utilizado por
  multiples frontends y artefactos.

### `generated_frontends`

- Atributos: `project_id UUID FK -> projects.id`,
  `transformation_id UUID FK -> uml_transformations.id`,
  `generated_by_user_id UUID FK -> users.id`,
  `backend_id UUID? FK -> generated_backends.id`, `name VARCHAR(160)`,
  `technology VARCHAR(80)`, `language VARCHAR(40)`, `version_label VARCHAR(80)`,
  `status VARCHAR(40)`, `artifact_path VARCHAR(500)?`, `manifest JSONB`,
  `error_detail TEXT?`.
- Relaciones: puede declarar para que version de backend fue generado.

### `generated_artifacts`

- Atributos: `project_id UUID FK -> projects.id`,
  `generated_backend_id UUID? FK -> generated_backends.id`,
  `generated_frontend_id UUID? FK -> generated_frontends.id`,
  `artifact_type VARCHAR(60)`, `file_name VARCHAR(255)`, `file_path VARCHAR(500)`,
  `checksum VARCHAR(128)?`, `metadata_json JSONB`.
- Relaciones: archivo descargable perteneciente a una generacion backend o frontend.

### `coordinated_generations`

- Atributos: `project_id UUID FK -> projects.id`,
  `transformation_id UUID FK -> uml_transformations.id`,
  `requested_by_user_id UUID FK -> users.id`,
  `backend_id UUID? FK -> generated_backends.id`,
  `frontend_id UUID? FK -> generated_frontends.id`, `client_request_id VARCHAR(120)`,
  `name VARCHAR(160)`, `status VARCHAR(40)`, `stage VARCHAR(40)`,
  `plan_hash VARCHAR(64)?`, `plan_json JSONB`, `diagnostics JSONB`, `manifest JSONB`,
  `artifact_path VARCHAR(500)?`, `error_detail TEXT?`.
- Restriccion: solicitud unica por transformacion, usuario y `client_request_id`.
- Relaciones: orquesta y enlaza la generacion coordinada de backend y frontend.

### `flutter_theme_settings`

- Atributos: `project_id UUID FK -> projects.id`, `config_json JSONB`,
  `preset_name VARCHAR(120)?`, `schema_version INTEGER`, `revision INTEGER`,
  `created_by_user_id UUID FK -> users.id`, `updated_by_user_id UUID FK -> users.id`.
- Restriccion: `UNIQUE(project_id)`, configuracion activa uno a uno por proyecto.

### `flutter_theme_presets`

- Atributos: `project_id UUID FK -> projects.id`, `name VARCHAR(120)`,
  `config_json JSONB`, `schema_version INTEGER`,
  `created_by_user_id UUID FK -> users.id`, `updated_by_user_id UUID FK -> users.id`.
- Relaciones: un proyecto puede almacenar multiples presets de tema.

## Notificaciones

### `notifications`

- Atributos: `recipient_user_id UUID FK -> users.id`,
  `project_id UUID? FK -> projects.id`, `actor_user_id UUID? FK -> users.id`,
  `type VARCHAR(80)`, `severity VARCHAR(16)`, `title VARCHAR(180)`,
  `body VARCHAR(500)`, `resource_type VARCHAR(80)?`, `resource_id UUID?`,
  `deep_link JSONB`, `dedup_key VARCHAR(200)`, `group_key VARCHAR(200)?`,
  `occurred_at TIMESTAMPTZ`, `read_at TIMESTAMPTZ?`, `clicked_at TIMESTAMPTZ?`,
  `archived_at TIMESTAMPTZ?`.
- Restriccion: `UNIQUE(recipient_user_id, dedup_key)`.
- Relaciones: enlaza destinatario, actor y proyecto; tiene entregas en Outbox.

### `notification_outbox`

- Atributos: `notification_id UUID FK -> notifications.id`, `channel VARCHAR(32)`,
  `status VARCHAR(24)`, `attempt_count INTEGER`, `available_at TIMESTAMPTZ`,
  `locked_at TIMESTAMPTZ?`, `locked_by VARCHAR(120)?`,
  `last_error_code VARCHAR(120)?`, `delivered_at TIMESTAMPTZ?`.
- Restriccion: `UNIQUE(notification_id, channel)`.
- Relaciones: `notifications 1 -- N notification_outbox`.

### `notification_preferences`

- Atributos: `user_id UUID FK -> users.id`, `project_id UUID? FK -> projects.id`,
  `category VARCHAR(80)`, `in_app_enabled BOOLEAN`, `push_enabled BOOLEAN`,
  `muted_until TIMESTAMPTZ?`.
- Restriccion: `UNIQUE(user_id, project_id, category)`.
- Relaciones: preferencia global o particular de un proyecto para un usuario.

### `push_subscriptions`

- Atributos: `user_id UUID FK -> users.id`, `endpoint VARCHAR(2048)`, `p256dh TEXT`,
  `auth TEXT`, `content_encoding VARCHAR(40)`, `user_agent VARCHAR(512)?`,
  `expires_at TIMESTAMPTZ?`, `is_active BOOLEAN`, `failure_count INTEGER`,
  `last_success_at TIMESTAMPTZ?`.
- Restriccion: `UNIQUE(endpoint)`.
- Relaciones: un usuario puede registrar multiples dispositivos o navegadores.

## Integracion PostgreSQL-MongoDB

### `nosql_outbox_events`

- Atributos: `aggregate_type VARCHAR(80)`, `aggregate_id UUID`,
  `event_type VARCHAR(100)`, `payload JSONB`, `idempotency_key VARCHAR(200)`,
  `status VARCHAR(24)`, `attempt_count INTEGER`, `available_at TIMESTAMPTZ`,
  `locked_at TIMESTAMPTZ?`, `locked_by VARCHAR(120)?`,
  `processed_at TIMESTAMPTZ?`, `last_error TEXT?`.
- Restricciones: `UNIQUE(idempotency_key)` y estado limitado a `pending`,
  `processing`, `completed`, `retry` o `dead`.
- Relaciones: no usa FK deliberadamente; identifica el agregado mediante
  `aggregate_type` y `aggregate_id` y publica mutaciones idempotentes en MongoDB.

## Relaciones principales resumidas

```text
users 1 -> N projects -> 1 uml_diagrams
projects N <-> N users mediante project_members
project_members 1 -> N project_permissions
projects 1 -> N ai_conversations -> MongoDB ai_messages
uml_diagrams 1 -> 1 MongoDB uml_diagrams.content
projects 1 -> N project_versions -> N project_restore_operations
project_versions 1 -> 1 MongoDB uml_diagram_versions
uml_transformations 1 -> N generated_backends/generated_frontends
notifications 1 -> N notification_outbox
```
