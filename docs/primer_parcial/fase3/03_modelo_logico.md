# Fase 3 - Modelo logico

## Acceso, usuarios y seguimiento

| Tabla | Clave primaria | Claves foraneas | Proposito |
| --- | --- | --- | --- |
| `users` | `id` | - | Usuarios registrados |
| `roles` | `id` | - | Roles globales |
| `user_roles` | `id` | `user_id`, `role_id` | Relacion N:M usuario-rol |
| `user_sessions` | `id` | `user_id` | Sesiones y refresh tokens |
| `audit_logs` | `id` | `user_id`, `project_id` | Bitacora transversal |

Restricciones:

- `users.email` unico.
- `roles.name` unico.
- `user_roles(user_id, role_id)` unico.

## Proyectos y colaboracion

| Tabla | Clave primaria | Claves foraneas | Proposito |
| --- | --- | --- | --- |
| `projects` | `id` | `owner_id` | Proyectos colaborativos |
| `project_members` | `id` | `project_id`, `user_id` | Integrantes por proyecto |
| `project_permissions` | `id` | `member_id` | Permisos internos |
| `project_invitations` | `id` | `project_id`, `invited_by_user_id`, `invited_user_id` | Invitaciones |
| `project_versions` | `id` | `project_id`, `created_by_user_id` | Snapshots/versiones |
| `collaboration_events` | `id` | `project_id`, `diagram_id`, `user_id` | Eventos colaborativos |

Restricciones:

- `project_members(project_id, user_id)` unico.
- `project_permissions(member_id, permission_code)` unico.
- `project_versions(project_id, version_number)` unico.

## Modelado UML inteligente

| Tabla | Clave primaria | Claves foraneas | Proposito |
| --- | --- | --- | --- |
| `uml_diagrams` | `id` | `project_id`, `created_by_user_id` | Diagramas UML |
| `uml_classes` | `id` | `diagram_id` | Clases UML |
| `uml_attributes` | `id` | `class_id` | Atributos de clase |
| `uml_methods` | `id` | `class_id` | Metodos de clase |
| `uml_parameters` | `id` | `method_id` | Parametros de metodos |
| `uml_relationships` | `id` | `diagram_id`, `source_class_id`, `target_class_id` | Relaciones entre clases |
| `uml_visual_elements` | `id` | `diagram_id` | Posicion y estilo visual |
| `xmi_exchanges` | `id` | `diagram_id`, `user_id` | Importaciones/exportaciones |

Restricciones:

- `uml_visual_elements(diagram_id, element_type, element_id)` unico.

## Transformacion y generacion

| Tabla | Clave primaria | Claves foraneas | Proposito |
| --- | --- | --- | --- |
| `ai_processes` | `id` | `user_id`, `project_id`, `diagram_id` | Procesos IA |
| `uml_transformations` | `id` | `project_id`, `diagram_id`, `requested_by_user_id` | Modelo intermedio |
| `generated_backends` | `id` | `project_id`, `transformation_id`, `generated_by_user_id` | Backend Spring Boot |
| `generated_frontends` | `id` | `project_id`, `transformation_id`, `generated_by_user_id`, `backend_id` | Frontend Flutter |
| `generated_artifacts` | `id` | `project_id`, `generated_backend_id`, `generated_frontend_id` | Archivos exportables |

