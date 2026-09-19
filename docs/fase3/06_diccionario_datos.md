# Fase 3 - Diccionario de datos

## Campos comunes

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| `id` | UUID | Identificador primario |
| `created_at` | timestamp tz | Fecha de creacion |
| `updated_at` | timestamp tz | Fecha de ultima actualizacion |

## Acceso, usuarios y seguimiento

### `users`

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| `full_name` | varchar(150) | Nombre completo |
| `email` | varchar(180) | Correo unico |
| `password_hash` | varchar(255) | Contrasena cifrada |
| `is_active` | boolean | Estado activo |
| `last_access_at` | timestamp tz | Ultimo acceso |

### `roles`

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| `name` | varchar(50) | Nombre unico del rol |
| `description` | text | Descripcion |
| `is_system` | boolean | Indica rol base del sistema |

### `audit_logs`

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| `user_id` | UUID | Usuario responsable |
| `project_id` | UUID | Proyecto relacionado |
| `module` | varchar(80) | Modulo afectado |
| `action` | varchar(120) | Accion realizada |
| `result` | varchar(40) | Resultado |
| `detail` | text | Detalle legible |
| `metadata_json` | JSONB | Datos complementarios |

## Proyectos y colaboracion

### `projects`

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| `owner_id` | UUID | Propietario inicial |
| `name` | varchar(160) | Nombre del proyecto |
| `description` | text | Descripcion |
| `status` | varchar(40) | Estado |
| `settings` | JSONB | Configuracion |

### `project_members`

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| `project_id` | UUID | Proyecto |
| `user_id` | UUID | Usuario integrante |
| `project_role` | varchar(40) | Rol interno |
| `joined_at` | timestamp tz | Fecha de ingreso |

### `collaboration_events`

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| `project_id` | UUID | Proyecto |
| `diagram_id` | UUID | Diagrama afectado |
| `user_id` | UUID | Usuario emisor |
| `event_type` | varchar(80) | Tipo de evento |
| `element_type` | varchar(80) | Tipo de elemento |
| `element_id` | UUID | Elemento afectado |
| `base_version` | integer | Version base |
| `payload` | JSONB | Datos del evento |

## Modelado UML

### `uml_diagrams`

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| `project_id` | UUID | Proyecto |
| `created_by_user_id` | UUID | Creador |
| `name` | varchar(160) | Nombre |
| `diagram_type` | varchar(50) | Tipo de diagrama |
| `status` | varchar(40) | Estado |
| `current_version` | integer | Version actual |
| `metadata_json` | JSONB | Metadatos |

### `uml_classes`

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| `diagram_id` | UUID | Diagrama |
| `name` | varchar(120) | Nombre de clase |
| `visibility` | varchar(20) | Visibilidad |
| `element_type` | varchar(40) | Clase, interfaz u otro |
| `stereotype` | varchar(80) | Estereotipo |
| `description` | text | Descripcion |

### `uml_attributes`

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| `class_id` | UUID | Clase |
| `name` | varchar(120) | Nombre |
| `data_type` | varchar(120) | Tipo de dato |
| `visibility` | varchar(20) | Visibilidad |
| `initial_value` | varchar(255) | Valor inicial |
| `multiplicity` | varchar(40) | Multiplicidad |
| `is_required` | boolean | Obligatorio |
| `constraints` | JSONB | Restricciones |

### `uml_relationships`

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| `diagram_id` | UUID | Diagrama |
| `source_class_id` | UUID | Clase origen |
| `target_class_id` | UUID | Clase destino |
| `relationship_type` | varchar(50) | Tipo de relacion |
| `source_cardinality` | varchar(40) | Cardinalidad origen |
| `target_cardinality` | varchar(40) | Cardinalidad destino |
| `direction` | varchar(40) | Direccion |
| `label` | varchar(120) | Etiqueta |

## Transformacion y generacion

### `ai_processes`

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| `process_type` | varchar(80) | Texto, voz, imagen, validacion o generacion |
| `model_provider` | varchar(80) | Proveedor local |
| `model_name` | varchar(120) | Modelo usado |
| `input_payload` | JSONB | Entrada |
| `output_payload` | JSONB | Salida |
| `status` | varchar(40) | Estado |

### `generated_backends` y `generated_frontends`

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| `project_id` | UUID | Proyecto origen |
| `transformation_id` | UUID | Transformacion |
| `generated_by_user_id` | UUID | Usuario solicitante |
| `technology` | varchar(80) | Spring Boot o Flutter |
| `language` | varchar(40) | Java o Dart |
| `version_label` | varchar(80) | Version generada |
| `artifact_path` | varchar(500) | Ruta del artefacto |
| `manifest` | JSONB | Manifiesto de archivos |

