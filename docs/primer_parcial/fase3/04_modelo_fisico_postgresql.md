# Fase 3 - Modelo fisico PostgreSQL

## Convenciones

- Claves primarias: `UUID`.
- Fechas: `TIMESTAMP WITH TIME ZONE`.
- Estados y tipos: `VARCHAR`.
- Datos flexibles: `JSONB`.
- Texto largo: `TEXT`.
- Indices en claves foraneas, estados, tipos y campos de consulta.

## Tipos principales

| Uso | Tipo PostgreSQL |
| --- | --- |
| Identificador | `UUID` |
| Nombre corto | `VARCHAR(120-180)` |
| Estado | `VARCHAR(40)` |
| Descripcion | `TEXT` |
| Configuracion dinamica | `JSONB` |
| Fecha/hora | `TIMESTAMP WITH TIME ZONE` |
| Booleano | `BOOLEAN` |
| Orden/version | `INTEGER` |
| Coordenadas | `DOUBLE PRECISION` |

## Indices clave

- `ix_users_email`
- `ix_roles_name`
- `ix_projects_owner_id`
- `ix_projects_status`
- `ix_project_members_project_id`
- `ix_project_members_user_id`
- `ix_project_permissions_permission_code`
- `ix_collaboration_events_project_id`
- `ix_collaboration_events_event_type`
- `ix_uml_diagrams_project_id`
- `ix_uml_classes_diagram_id`
- `ix_uml_relationships_source_class_id`
- `ix_uml_relationships_target_class_id`
- `ix_ai_processes_process_type`
- `ix_uml_transformations_status`
- `ix_generated_backends_status`
- `ix_generated_frontends_status`
- `ix_generated_artifacts_artifact_type`

## Script fisico

El script completo generado por Alembic esta en:

- `docs/fase3/sql/001_modelo_persistencia_inicial.sql`

Los datos iniciales estan en:

- `docs/fase3/sql/002_datos_iniciales.sql`

