# Fuente de verdad y retiro SQL

| Dato | Fuente de verdad | Registro relacionado |
|---|---|---|
| Proyecto, propietario, miembros y permisos | PostgreSQL | `projects`, `project_members` |
| Identidad y revision del diagrama | PostgreSQL | `uml_diagrams` |
| Clases, miembros, relaciones y visuales | MongoDB | `uml_diagrams._id` |
| Registro de conversacion y secuencia | PostgreSQL | `ai_conversations` |
| Mensajes y contexto | MongoDB | `ai_messages`, `ai_context_snapshots` |
| Metadatos de version | PostgreSQL | `project_versions` |
| Snapshot inmutable | MongoDB | `uml_diagram_versions` |

La migracion `c1e5f6a7b8c9` agrega `content_storage`, `message_storage` y `snapshot_storage`, restringidos a `mongodb`. Esto hace auditable la autoridad por registro. La migracion `d2f6a7b8c9d0` completa el retiro fisico.

El retiro se ejecuta en dos niveles:

1. Retiro funcional: editor, historial, versiones, mensajes y memoria escriben y leen contenido en MongoDB.
2. Retiro fisico: se eliminan las siete tablas UML de contenido y `ai_messages`; las FK de acciones y recomendaciones pasan a referencias logicas indexadas.
3. Vaciado de duplicados: `project_versions.snapshot` queda `{}` y `ai_conversations.summary` queda `NULL` en modo consolidado.

La doble escritura y los fallbacks SQL quedan desactivados. `NOSQL_CONSOLIDATED_MODE=true` usa repositorios documentales directos; el Outbox permanece para integraciones operativas, no como copia de contenido funcional.
