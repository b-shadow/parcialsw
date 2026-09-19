# Fase 3 - Diseno de base de datos

## Objetivo

Definir e implementar la base de persistencia inicial para soportar usuarios, proyectos colaborativos, modelos UML, versiones, eventos, procesos IA y generaciones automaticas.

## Enfoque

Se adopta una estrategia hibrida:

- Tablas normalizadas para entidades principales y relaciones criticas.
- `JSONB` para configuraciones dinamicas, snapshots, payloads de eventos, manifiestos y metadatos flexibles.
- UUID como identificador primario en todas las entidades de dominio.
- Timestamps `created_at` y `updated_at` en todas las tablas principales.
- Indices en campos de busqueda frecuente, estados, tipos y claves foraneas.

## Paquetes funcionales cubiertos

### Gestion de acceso, usuarios y seguimiento

Tablas:

- `users`
- `roles`
- `user_roles`
- `user_sessions`
- `audit_logs`

### Gestion de proyectos y colaboracion

Tablas:

- `projects`
- `project_members`
- `project_permissions`
- `project_invitations`
- `project_versions`
- `collaboration_events`

### Modelado UML inteligente

Tablas:

- `uml_diagrams`
- `uml_classes`
- `uml_attributes`
- `uml_methods`
- `uml_parameters`
- `uml_relationships`
- `uml_visual_elements`
- `xmi_exchanges`

### Transformacion y generacion automatica

Tablas:

- `ai_processes`
- `uml_transformations`
- `generated_backends`
- `generated_frontends`
- `generated_artifacts`

## Reglas principales

- Un usuario puede tener varios roles globales.
- Un proyecto pertenece a un usuario propietario.
- Un proyecto tiene multiples integrantes.
- Un integrante tiene rol interno por proyecto.
- Los permisos internos son asignables por integrante.
- Un proyecto puede tener multiples versiones.
- Un proyecto puede tener multiples diagramas UML.
- Un diagrama contiene clases, relaciones y elementos visuales.
- Una clase contiene atributos y metodos.
- Un metodo contiene parametros.
- Las relaciones conectan clases origen y destino.
- Los procesos IA y de generacion se registran con estado y payload.
- Los artefactos generados quedan separados del modelo UML origen.

