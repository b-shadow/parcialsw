# Diccionario físico de PostgreSQL

Esquema verificado directamente en PostgreSQL con la revisión Alembic `e9a1b3c5d7f8`.
Solo aparecen las tablas y columnas físicas existentes en PostgreSQL.

## Diseño físico de datos

### Volumen y diccionario de datos

Cada tabla muestra sus columnas reales. **Tamaño** indica longitud máxima para `VARCHAR`, tamaño físico de tipos fijos o `Variable` para `TEXT` y `JSONB`. **Nulos** procede de la restricción SQL `NOT NULL`; **Llave** señala únicamente `PK` y `FK` declaradas en PostgreSQL.

### Acceso y usuarios

#### Tabla 1. Diccionario de `usuarios`

Cuentas de acceso al sistema.

| Atributo | Tipo de dato | Descripción | Tamaño | Nulos | Llave |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Identificador del registro. | 16 bytes | No | PK |
| `nombre_completo` | `VARCHAR(150)` | Nombre completo del usuario. | 150 | No | — |
| `correo` | `VARCHAR(180)` | Correo electrónico de acceso. | 180 | No | — |
| `hash_contrasena` | `VARCHAR(255)` | Hash de la contraseña. | 255 | No | — |
| `esta_activo` | `BOOLEAN` | Indica si el registro está activo. | 1 byte | No | — |
| `fecha_ultimo_acceso` | `TIMESTAMPTZ` | Último acceso del usuario. | 8 bytes | Sí | — |
| `fecha_creacion` | `TIMESTAMPTZ` | Fecha de creación del registro. | 8 bytes | No | — |
| `fecha_actualizacion` | `TIMESTAMPTZ` | Fecha de última actualización. | 8 bytes | No | — |

**Unicidad:** UNIQUE(`correo`).

#### Tabla 2. Diccionario de `roles`

Roles globales disponibles para usuarios.

| Atributo | Tipo de dato | Descripción | Tamaño | Nulos | Llave |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Identificador del registro. | 16 bytes | No | PK |
| `nombre` | `VARCHAR(50)` | Nombre del registro. | 50 | No | — |
| `descripcion` | `TEXT` | Descripción del registro. | Variable | Sí | — |
| `es_sistema` | `BOOLEAN` | Indica si es un rol propio del sistema. | 1 byte | No | — |
| `fecha_creacion` | `TIMESTAMPTZ` | Fecha de creación del registro. | 8 bytes | No | — |
| `fecha_actualizacion` | `TIMESTAMPTZ` | Fecha de última actualización. | 8 bytes | No | — |

**Unicidad:** UNIQUE(`nombre`).

#### Tabla 3. Diccionario de `roles_usuario`

Asignación del rol global a cada usuario.

| Atributo | Tipo de dato | Descripción | Tamaño | Nulos | Llave |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Identificador del registro. | 16 bytes | No | PK |
| `usuario_id` | `UUID` | Referencia a `usuarios.id`. | 16 bytes | No | FK |
| `rol_id` | `UUID` | Referencia a `roles.id`. | 16 bytes | No | FK |
| `fecha_creacion` | `TIMESTAMPTZ` | Fecha de creación del registro. | 8 bytes | No | — |
| `fecha_actualizacion` | `TIMESTAMPTZ` | Fecha de última actualización. | 8 bytes | No | — |

**Relaciones:** `rol_id` → `roles.id`; `usuario_id` → `usuarios.id`.

**Unicidad:** UNIQUE(`usuario_id`).

#### Tabla 4. Diccionario de `sesiones_usuario`

Sesiones y tokens de renovación de acceso.

| Atributo | Tipo de dato | Descripción | Tamaño | Nulos | Llave |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Identificador del registro. | 16 bytes | No | PK |
| `usuario_id` | `UUID` | Referencia a `usuarios.id`. | 16 bytes | No | FK |
| `hash_token_renovacion` | `VARCHAR(255)` | Hash del token de renovación. | 255 | Sí | — |
| `direccion_ip` | `VARCHAR(80)` | Dirección IP de la sesión. | 80 | Sí | — |
| `agente_usuario` | `VARCHAR(255)` | Agente del navegador o dispositivo. | 255 | Sí | — |
| `fecha_revocacion` | `TIMESTAMPTZ` | Fecha de revocación. | 8 bytes | Sí | — |
| `fecha_expiracion` | `TIMESTAMPTZ` | Fecha de vencimiento. | 8 bytes | No | — |
| `fecha_creacion` | `TIMESTAMPTZ` | Fecha de creación del registro. | 8 bytes | No | — |
| `fecha_actualizacion` | `TIMESTAMPTZ` | Fecha de última actualización. | 8 bytes | No | — |

**Relaciones:** `usuario_id` → `usuarios.id`.

#### Tabla 5. Diccionario de `registros_auditoria`

Trazas de auditoría por usuario, proyecto y módulo.

| Atributo | Tipo de dato | Descripción | Tamaño | Nulos | Llave |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Identificador del registro. | 16 bytes | No | PK |
| `usuario_id` | `UUID` | Referencia a `usuarios.id`. | 16 bytes | Sí | FK |
| `proyecto_id` | `UUID` | Referencia a `proyectos.id`. | 16 bytes | Sí | FK |
| `modulo` | `VARCHAR(80)` | Módulo que originó la operación. | 80 | No | — |
| `accion` | `VARCHAR(120)` | Acción realizada. | 120 | No | — |
| `resultado` | `VARCHAR(40)` | Resultado de la operación. | 40 | No | — |
| `detalle` | `TEXT` | Detalle adicional de auditoría. | Variable | Sí | — |
| `metadatos_json` | `JSONB` | Metadatos adicionales en JSON. | Variable | No | — |
| `fecha_creacion` | `TIMESTAMPTZ` | Fecha de creación del registro. | 8 bytes | No | — |
| `fecha_actualizacion` | `TIMESTAMPTZ` | Fecha de última actualización. | 8 bytes | No | — |

**Relaciones:** `proyecto_id` → `proyectos.id`; `usuario_id` → `usuarios.id`.

### Proyectos y colaboración

#### Tabla 6. Diccionario de `proyectos`

Identidad, configuración y revisión del proyecto; cada proyecto corresponde a un diagrama de clases en la aplicación.

| Atributo | Tipo de dato | Descripción | Tamaño | Nulos | Llave |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Identificador del registro. | 16 bytes | No | PK |
| `propietario_id` | `UUID` | Referencia a `usuarios.id`. | 16 bytes | No | FK |
| `nombre` | `VARCHAR(160)` | Nombre del registro. | 160 | No | — |
| `descripcion` | `TEXT` | Descripción del registro. | Variable | Sí | — |
| `estado` | `VARCHAR(40)` | Estado actual del proceso o registro. | 40 | No | — |
| `configuracion` | `JSONB` | Configuración general del proyecto. | Variable | No | — |
| `revision` | `INTEGER` | Número de revisión para control de cambios. | 4 bytes | No | — |
| `siguiente_numero_version` | `INTEGER` | Siguiente número de versión del proyecto. | 4 bytes | No | — |
| `fecha_creacion` | `TIMESTAMPTZ` | Fecha de creación del registro. | 8 bytes | No | — |
| `fecha_actualizacion` | `TIMESTAMPTZ` | Fecha de última actualización. | 8 bytes | No | — |

**Relaciones:** `propietario_id` → `usuarios.id`.

#### Tabla 7. Diccionario de `integrantes_proyecto`

Usuarios que participan en un proyecto y su rol local.

| Atributo | Tipo de dato | Descripción | Tamaño | Nulos | Llave |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Identificador del registro. | 16 bytes | No | PK |
| `proyecto_id` | `UUID` | Referencia a `proyectos.id`. | 16 bytes | No | FK |
| `usuario_id` | `UUID` | Referencia a `usuarios.id`. | 16 bytes | No | FK |
| `rol_proyecto` | `VARCHAR(40)` | Rol del integrante dentro del proyecto. | 40 | No | — |
| `fecha_incorporacion` | `TIMESTAMPTZ` | Fecha de incorporación al proyecto. | 8 bytes | Sí | — |
| `fecha_creacion` | `TIMESTAMPTZ` | Fecha de creación del registro. | 8 bytes | No | — |
| `fecha_actualizacion` | `TIMESTAMPTZ` | Fecha de última actualización. | 8 bytes | No | — |

**Relaciones:** `proyecto_id` → `proyectos.id`; `usuario_id` → `usuarios.id`.

**Unicidad:** UNIQUE(`proyecto_id`, `usuario_id`).

#### Tabla 8. Diccionario de `invitaciones_proyecto`

Invitaciones pendientes o resueltas para colaborar.

| Atributo | Tipo de dato | Descripción | Tamaño | Nulos | Llave |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Identificador del registro. | 16 bytes | No | PK |
| `proyecto_id` | `UUID` | Referencia a `proyectos.id`. | 16 bytes | No | FK |
| `usuario_invitador_id` | `UUID` | Referencia a `usuarios.id`. | 16 bytes | No | FK |
| `usuario_invitado_id` | `UUID` | Referencia a `usuarios.id`. | 16 bytes | Sí | FK |
| `correo_invitado` | `VARCHAR(180)` | Correo de la persona invitada. | 180 | No | — |
| `rol_proyecto` | `VARCHAR(40)` | Rol del integrante dentro del proyecto. | 40 | No | — |
| `estado` | `VARCHAR(40)` | Estado actual del proceso o registro. | 40 | No | — |
| `fecha_expiracion` | `TIMESTAMPTZ` | Fecha de vencimiento. | 8 bytes | Sí | — |
| `fecha_respuesta` | `TIMESTAMPTZ` | Fecha de respuesta a la invitación. | 8 bytes | Sí | — |
| `fecha_creacion` | `TIMESTAMPTZ` | Fecha de creación del registro. | 8 bytes | No | — |
| `fecha_actualizacion` | `TIMESTAMPTZ` | Fecha de última actualización. | 8 bytes | No | — |

**Relaciones:** `proyecto_id` → `proyectos.id`; `usuario_invitado_id` → `usuarios.id`; `usuario_invitador_id` → `usuarios.id`.

**Unicidad:** UNIQUE(`proyecto_id`, `lower(correo_invitado::text)`) WHERE `((estado)::text = 'pending'::text)`.

#### Tabla 9. Diccionario de `eventos_colaboracion`

Registro ordenado de eventos colaborativos y de IA.

| Atributo | Tipo de dato | Descripción | Tamaño | Nulos | Llave |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Identificador del registro. | 16 bytes | No | PK |
| `proyecto_id` | `UUID` | Referencia a `proyectos.id`. | 16 bytes | No | FK |
| `diagrama_id` | `UUID` | Referencia a `diagramas_uml.id`. | 16 bytes | Sí | FK |
| `usuario_id` | `UUID` | Referencia a `usuarios.id`. | 16 bytes | No | FK |
| `tipo_evento` | `VARCHAR(80)` | Tipo de evento registrado. | 80 | No | — |
| `tipo_elemento` | `VARCHAR(80)` | Tipo de elemento afectado. | 80 | Sí | — |
| `elemento_id` | `UUID` | Identificador lógico del elemento afectado. | 16 bytes | Sí | — |
| `version_base` | `INTEGER` | Versión del elemento antes del cambio. | 4 bytes | Sí | — |
| `carga_datos` | `JSONB` | Datos del evento o acción en JSON. | Variable | No | — |
| `evento_cliente_id` | `UUID` | Identificador idempotente del evento de cliente. | 16 bytes | No | — |
| `numero_secuencia` | `INTEGER` | Orden del evento en el proyecto o chat. | 4 bytes | No | — |
| `nombre_visible_actor` | `VARCHAR(160)` | Nombre del actor al registrar el evento. | 160 | Sí | — |
| `tipo_recurso` | `VARCHAR(80)` | Tipo de recurso vinculado al evento. | 80 | Sí | — |
| `recurso_id` | `UUID` | Identificador lógico del recurso vinculado. | 16 bytes | Sí | — |
| `correlacion_id` | `UUID` | Identificador para correlacionar eventos. | 16 bytes | Sí | — |
| `causa_id` | `UUID` | Identificador del evento que lo originó. | 16 bytes | Sí | — |
| `clave_resumen` | `VARCHAR(160)` | Clave de resumen de actividad. | 160 | Sí | — |
| `fecha_creacion` | `TIMESTAMPTZ` | Fecha de creación del registro. | 8 bytes | No | — |
| `fecha_actualizacion` | `TIMESTAMPTZ` | Fecha de última actualización. | 8 bytes | No | — |

**Relaciones:** `diagrama_id` → `diagramas_uml.id`; `proyecto_id` → `proyectos.id`; `usuario_id` → `usuarios.id`.

**Unicidad:** UNIQUE(`proyecto_id`, `numero_secuencia`); UNIQUE(`proyecto_id`, `usuario_id`, `evento_cliente_id`).

#### Tabla 10. Diccionario de `versiones_proyecto`

Registro SQL de versiones del proyecto.

| Atributo | Tipo de dato | Descripción | Tamaño | Nulos | Llave |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Identificador del registro. | 16 bytes | No | PK |
| `proyecto_id` | `UUID` | Referencia a `proyectos.id`. | 16 bytes | No | FK |
| `usuario_creador_id` | `UUID` | Referencia a `usuarios.id`. | 16 bytes | No | FK |
| `numero_version` | `INTEGER` | Número de versión dentro del proyecto. | 4 bytes | No | — |
| `nombre` | `VARCHAR(120)` | Nombre del registro. | 120 | No | — |
| `descripcion` | `TEXT` | Descripción del registro. | Variable | Sí | — |
| `instantanea` | `JSONB` | Campo JSON de compatibilidad del registro de versión. | Variable | No | — |
| `estado` | `VARCHAR(40)` | Estado actual del proceso o registro. | 40 | No | — |
| `clase` | `VARCHAR(40)` | Clase de versión o registro. | 40 | No | — |
| `version_esquema_instantanea` | `INTEGER` | Versión del contrato del snapshot. | 4 bytes | No | — |
| `hash_instantanea` | `VARCHAR(64)` | Hash de integridad de la versión. | 64 | No | — |
| `tamano_instantanea_bytes` | `INTEGER` | Tamaño del snapshot en bytes. | 4 bytes | No | — |
| `revision_proyecto` | `INTEGER` | Revisión del proyecto capturada. | 4 bytes | No | — |
| `clave_idempotencia` | `VARCHAR(120)` | Clave para evitar operaciones duplicadas. | 120 | Sí | — |
| `metadatos_json` | `JSONB` | Metadatos adicionales en JSON. | Variable | No | — |
| `almacenamiento_instantanea` | `VARCHAR(20)` | Código de almacenamiento de la versión. | 20 | No | — |
| `fecha_creacion` | `TIMESTAMPTZ` | Fecha de creación del registro. | 8 bytes | No | — |
| `fecha_actualizacion` | `TIMESTAMPTZ` | Fecha de última actualización. | 8 bytes | No | — |

**Relaciones:** `proyecto_id` → `proyectos.id`; `usuario_creador_id` → `usuarios.id`.

**Unicidad:** UNIQUE(`proyecto_id`, `numero_version`); UNIQUE(`proyecto_id`, `usuario_creador_id`, `clave_idempotencia`).

#### Tabla 11. Diccionario de `restauraciones_proyecto`

Operaciones idempotentes de restauración y sus respaldos.

| Atributo | Tipo de dato | Descripción | Tamaño | Nulos | Llave |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Identificador del registro. | 16 bytes | No | PK |
| `proyecto_id` | `UUID` | Referencia a `proyectos.id`. | 16 bytes | No | FK |
| `version_origen_id` | `UUID` | Referencia a `versiones_proyecto.id`. | 16 bytes | No | FK |
| `version_respaldo_id` | `UUID` | Referencia a `versiones_proyecto.id`. | 16 bytes | Sí | FK |
| `usuario_solicitante_id` | `UUID` | Referencia a `usuarios.id`. | 16 bytes | No | FK |
| `clave_idempotencia` | `VARCHAR(120)` | Clave para evitar operaciones duplicadas. | 120 | No | — |
| `estado` | `VARCHAR(24)` | Estado actual del proceso o registro. | 24 | No | — |
| `hash_instantanea_origen` | `VARCHAR(64)` | Hash del snapshot que se va a restaurar. | 64 | No | — |
| `hash_instantanea_anterior` | `VARCHAR(64)` | Hash del estado previo a la restauración. | 64 | No | — |
| `hash_instantanea_posterior` | `VARCHAR(64)` | Hash del estado posterior a la restauración. | 64 | Sí | — |
| `revision_proyecto_anterior` | `INTEGER` | Revisión anterior del proyecto. | 4 bytes | No | — |
| `revision_proyecto_posterior` | `INTEGER` | Revisión posterior del proyecto. | 4 bytes | Sí | — |
| `diagnosticos_json` | `JSONB` | Diagnósticos de la restauración en JSON. | Variable | No | — |
| `fecha_inicio` | `TIMESTAMPTZ` | Inicio de la operación. | 8 bytes | No | — |
| `fecha_finalizacion` | `TIMESTAMPTZ` | Fin de la operación. | 8 bytes | Sí | — |
| `fecha_creacion` | `TIMESTAMPTZ` | Fecha de creación del registro. | 8 bytes | No | — |
| `fecha_actualizacion` | `TIMESTAMPTZ` | Fecha de última actualización. | 8 bytes | No | — |

**Relaciones:** `proyecto_id` → `proyectos.id`; `usuario_solicitante_id` → `usuarios.id`; `version_origen_id` → `versiones_proyecto.id`; `version_respaldo_id` → `versiones_proyecto.id`.

**Unicidad:** UNIQUE(`proyecto_id`, `usuario_solicitante_id`, `clave_idempotencia`).

### Registro UML e intercambio

#### Tabla 12. Diccionario de `diagramas_uml`

Identidad, estado y metadatos SQL del diagrama.

| Atributo | Tipo de dato | Descripción | Tamaño | Nulos | Llave |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Identificador del registro. | 16 bytes | No | PK |
| `proyecto_id` | `UUID` | Referencia a `proyectos.id`. | 16 bytes | No | FK |
| `usuario_creador_id` | `UUID` | Referencia a `usuarios.id`. | 16 bytes | No | FK |
| `nombre` | `VARCHAR(160)` | Nombre del registro. | 160 | No | — |
| `tipo_diagrama` | `VARCHAR(50)` | Tipo de diagrama registrado. | 50 | No | — |
| `estado` | `VARCHAR(40)` | Estado actual del proceso o registro. | 40 | No | — |
| `version_actual` | `INTEGER` | Versión actual del diagrama. | 4 bytes | No | — |
| `descripcion` | `TEXT` | Descripción del registro. | Variable | Sí | — |
| `metadatos_json` | `JSONB` | Metadatos adicionales en JSON. | Variable | No | — |
| `almacenamiento_contenido` | `VARCHAR(20)` | Código de almacenamiento del contenido. | 20 | No | — |
| `fecha_creacion` | `TIMESTAMPTZ` | Fecha de creación del registro. | 8 bytes | No | — |
| `fecha_actualizacion` | `TIMESTAMPTZ` | Fecha de última actualización. | 8 bytes | No | — |

**Relaciones:** `proyecto_id` → `proyectos.id`; `usuario_creador_id` → `usuarios.id`.

#### Tabla 13. Diccionario de `intercambios_xmi`

Historial de importaciones y exportaciones XMI.

| Atributo | Tipo de dato | Descripción | Tamaño | Nulos | Llave |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Identificador del registro. | 16 bytes | No | PK |
| `diagrama_id` | `UUID` | Referencia a `diagramas_uml.id`. | 16 bytes | No | FK |
| `usuario_id` | `UUID` | Referencia a `usuarios.id`. | 16 bytes | No | FK |
| `tipo_intercambio` | `VARCHAR(30)` | Importación o exportación XMI. | 30 | No | — |
| `nombre_herramienta` | `VARCHAR(120)` | Herramienta externa de intercambio. | 120 | Sí | — |
| `nombre_archivo` | `VARCHAR(255)` | Nombre del archivo. | 255 | No | — |
| `ruta_archivo` | `VARCHAR(500)` | Ruta del archivo generado o recibido. | 500 | Sí | — |
| `estado` | `VARCHAR(40)` | Estado actual del proceso o registro. | 40 | No | — |
| `detalle_error` | `TEXT` | Detalle del error si ocurrió. | Variable | Sí | — |
| `metadatos_json` | `JSONB` | Metadatos adicionales en JSON. | Variable | No | — |
| `fecha_creacion` | `TIMESTAMPTZ` | Fecha de creación del registro. | 8 bytes | No | — |
| `fecha_actualizacion` | `TIMESTAMPTZ` | Fecha de última actualización. | 8 bytes | No | — |

**Relaciones:** `diagrama_id` → `diagramas_uml.id`; `usuario_id` → `usuarios.id`.

### Asistente e IA

#### Tabla 14. Diccionario de `conversaciones_ia`

Identidad y metadatos SQL de los chats del proyecto.

| Atributo | Tipo de dato | Descripción | Tamaño | Nulos | Llave |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Identificador del registro. | 16 bytes | No | PK |
| `proyecto_id` | `UUID` | Referencia a `proyectos.id`. | 16 bytes | No | FK |
| `estado` | `VARCHAR(30)` | Estado actual del proceso o registro. | 30 | No | — |
| `resumen` | `TEXT` | Campo de compatibilidad para el resumen del chat. | Variable | Sí | — |
| `resumen_hasta_secuencia` | `INTEGER` | Última secuencia incluida en el resumen. | 4 bytes | No | — |
| `secuencia_ultimo_mensaje` | `INTEGER` | Última secuencia de mensaje del chat. | 4 bytes | No | — |
| `version_esquema` | `INTEGER` | Versión del contrato de datos. | 4 bytes | No | — |
| `titulo` | `VARCHAR(160)` | Título mostrado al usuario. | 160 | No | — |
| `usuario_creador_id` | `UUID` | Referencia a `usuarios.id`. | 16 bytes | Sí | FK |
| `almacenamiento_mensajes` | `VARCHAR(20)` | Código de almacenamiento de mensajes. | 20 | No | — |
| `fecha_creacion` | `TIMESTAMPTZ` | Fecha de creación del registro. | 8 bytes | No | — |
| `fecha_actualizacion` | `TIMESTAMPTZ` | Fecha de última actualización. | 8 bytes | No | — |

**Relaciones:** `proyecto_id` → `proyectos.id`; `usuario_creador_id` → `usuarios.id`.

#### Tabla 15. Diccionario de `acciones_ia`

Propuestas y confirmaciones de cambios del asistente.

| Atributo | Tipo de dato | Descripción | Tamaño | Nulos | Llave |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Identificador del registro. | 16 bytes | No | PK |
| `proyecto_id` | `UUID` | Referencia a `proyectos.id`. | 16 bytes | No | FK |
| `conversacion_id` | `UUID` | Referencia a `conversaciones_ia.id`. | 16 bytes | No | FK |
| `mensaje_origen_id` | `UUID` | Identificador del mensaje que originó el registro; sin FK SQL. | 16 bytes | No | — |
| `usuario_solicitante_id` | `UUID` | Referencia a `usuarios.id`. | 16 bytes | No | FK |
| `tipo_accion` | `VARCHAR(80)` | Tipo de cambio propuesto por la IA. | 80 | No | — |
| `tipo_destino` | `VARCHAR(80)` | Tipo del elemento objetivo. | 80 | Sí | — |
| `destino_id` | `UUID` | Identificador lógico del elemento objetivo. | 16 bytes | Sí | — |
| `carga_datos` | `JSONB` | Datos del evento o acción en JSON. | Variable | No | — |
| `nivel_riesgo` | `VARCHAR(20)` | Nivel de riesgo de la propuesta. | 20 | No | — |
| `requiere_confirmacion` | `BOOLEAN` | Indica si la propuesta requiere aprobación. | 1 byte | No | — |
| `estado` | `VARCHAR(30)` | Estado actual del proceso o registro. | 30 | No | — |
| `usuario_confirmador_id` | `UUID` | Referencia a `usuarios.id`. | 16 bytes | Sí | FK |
| `fecha_confirmacion` | `TIMESTAMPTZ` | Fecha de aprobación de la acción. | 8 bytes | Sí | — |
| `fecha_ejecucion` | `TIMESTAMPTZ` | Fecha de ejecución de la acción. | 8 bytes | Sí | — |
| `resultado_json` | `JSONB` | Resultado de ejecutar la acción en JSON. | Variable | No | — |
| `mensaje_error` | `TEXT` | Mensaje de error de la acción. | Variable | Sí | — |
| `clave_idempotencia` | `UUID` | Clave para evitar operaciones duplicadas. | 16 bytes | No | — |
| `fecha_creacion` | `TIMESTAMPTZ` | Fecha de creación del registro. | 8 bytes | No | — |
| `fecha_actualizacion` | `TIMESTAMPTZ` | Fecha de última actualización. | 8 bytes | No | — |

**Relaciones:** `conversacion_id` → `conversaciones_ia.id`; `proyecto_id` → `proyectos.id`; `usuario_confirmador_id` → `usuarios.id`; `usuario_solicitante_id` → `usuarios.id`.

**Unicidad:** UNIQUE(`proyecto_id`, `clave_idempotencia`).

#### Tabla 16. Diccionario de `recomendaciones_ia`

Recomendaciones emitidas por el asistente y su resolución.

| Atributo | Tipo de dato | Descripción | Tamaño | Nulos | Llave |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Identificador del registro. | 16 bytes | No | PK |
| `proyecto_id` | `UUID` | Referencia a `proyectos.id`. | 16 bytes | No | FK |
| `conversacion_id` | `UUID` | Referencia a `conversaciones_ia.id`. | 16 bytes | No | FK |
| `mensaje_origen_id` | `UUID` | Identificador del mensaje que originó el registro; sin FK SQL. | 16 bytes | No | — |
| `categoria` | `VARCHAR(50)` | Categoría de la recomendación o preferencia. | 50 | No | — |
| `severidad` | `VARCHAR(20)` | Severidad del aviso o recomendación. | 20 | No | — |
| `titulo` | `VARCHAR(200)` | Título mostrado al usuario. | 200 | No | — |
| `descripcion` | `TEXT` | Descripción del registro. | Variable | No | — |
| `referencias_json` | `JSONB` | Referencias de la recomendación en JSON. | Variable | No | — |
| `estado` | `VARCHAR(30)` | Estado actual del proceso o registro. | 30 | No | — |
| `usuario_resolutor_id` | `UUID` | Referencia a `usuarios.id`. | 16 bytes | Sí | FK |
| `fecha_resolucion` | `TIMESTAMPTZ` | Fecha de resolución de la recomendación. | 8 bytes | Sí | — |
| `nota_resolucion` | `TEXT` | Motivo o nota de resolución. | Variable | Sí | — |
| `fecha_creacion` | `TIMESTAMPTZ` | Fecha de creación del registro. | 8 bytes | No | — |
| `fecha_actualizacion` | `TIMESTAMPTZ` | Fecha de última actualización. | 8 bytes | No | — |

**Relaciones:** `conversacion_id` → `conversaciones_ia.id`; `proyecto_id` → `proyectos.id`; `usuario_resolutor_id` → `usuarios.id`.

#### Tabla 17. Diccionario de `procesos_ia`

Trazas de ejecuciones de IA.

| Atributo | Tipo de dato | Descripción | Tamaño | Nulos | Llave |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Identificador del registro. | 16 bytes | No | PK |
| `usuario_id` | `UUID` | Referencia a `usuarios.id`. | 16 bytes | No | FK |
| `proyecto_id` | `UUID` | Referencia a `proyectos.id`. | 16 bytes | Sí | FK |
| `diagrama_id` | `UUID` | Referencia a `diagramas_uml.id`. | 16 bytes | Sí | FK |
| `tipo_proceso` | `VARCHAR(80)` | Tipo de procesamiento de IA. | 80 | No | — |
| `proveedor_modelo` | `VARCHAR(80)` | Proveedor que ejecutó el modelo. | 80 | No | — |
| `nombre_modelo` | `VARCHAR(120)` | Nombre del modelo de IA. | 120 | Sí | — |
| `carga_entrada` | `JSONB` | Entrada registrada para la ejecución de IA. | Variable | No | — |
| `carga_salida` | `JSONB` | Salida registrada de la ejecución de IA. | Variable | No | — |
| `estado` | `VARCHAR(40)` | Estado actual del proceso o registro. | 40 | No | — |
| `detalle_error` | `TEXT` | Detalle del error si ocurrió. | Variable | Sí | — |
| `fecha_creacion` | `TIMESTAMPTZ` | Fecha de creación del registro. | 8 bytes | No | — |
| `fecha_actualizacion` | `TIMESTAMPTZ` | Fecha de última actualización. | 8 bytes | No | — |

**Relaciones:** `diagrama_id` → `diagramas_uml.id`; `proyecto_id` → `proyectos.id`; `usuario_id` → `usuarios.id`.

### Generación de software

#### Tabla 18. Diccionario de `transformaciones_uml`

Transformaciones derivadas del diagrama para generar software; no son el contenido UML canónico.

| Atributo | Tipo de dato | Descripción | Tamaño | Nulos | Llave |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Identificador del registro. | 16 bytes | No | PK |
| `proyecto_id` | `UUID` | Referencia a `proyectos.id`. | 16 bytes | No | FK |
| `diagrama_id` | `UUID` | Referencia a `diagramas_uml.id`. | 16 bytes | No | FK |
| `usuario_solicitante_id` | `UUID` | Referencia a `usuarios.id`. | 16 bytes | No | FK |
| `version_origen` | `VARCHAR(80)` | Versión de origen de la transformación. | 80 | Sí | — |
| `plataforma_destino` | `VARCHAR(80)` | Plataforma objetivo de generación. | 80 | No | — |
| `modelo_intermedio` | `JSONB` | Modelo intermedio derivado para generar código; no es el diagrama canónico. | Variable | No | — |
| `estado` | `VARCHAR(40)` | Estado actual del proceso o registro. | 40 | No | — |
| `detalle_error` | `TEXT` | Detalle del error si ocurrió. | Variable | Sí | — |
| `fecha_creacion` | `TIMESTAMPTZ` | Fecha de creación del registro. | 8 bytes | No | — |
| `fecha_actualizacion` | `TIMESTAMPTZ` | Fecha de última actualización. | 8 bytes | No | — |

**Relaciones:** `diagrama_id` → `diagramas_uml.id`; `proyecto_id` → `proyectos.id`; `usuario_solicitante_id` → `usuarios.id`.

#### Tabla 19. Diccionario de `backends_generados`

Versiones de backend generadas y sus artefactos.

| Atributo | Tipo de dato | Descripción | Tamaño | Nulos | Llave |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Identificador del registro. | 16 bytes | No | PK |
| `proyecto_id` | `UUID` | Referencia a `proyectos.id`. | 16 bytes | No | FK |
| `transformacion_id` | `UUID` | Referencia a `transformaciones_uml.id`. | 16 bytes | No | FK |
| `usuario_generador_id` | `UUID` | Referencia a `usuarios.id`. | 16 bytes | No | FK |
| `nombre` | `VARCHAR(160)` | Nombre del registro. | 160 | No | — |
| `tecnologia` | `VARCHAR(80)` | Tecnología del artefacto generado. | 80 | No | — |
| `lenguaje` | `VARCHAR(40)` | Lenguaje de programación generado. | 40 | No | — |
| `motor_base_datos` | `VARCHAR(80)` | Motor de base de datos del backend generado. | 80 | No | — |
| `etiqueta_version` | `VARCHAR(80)` | Etiqueta visible de la versión generada. | 80 | No | — |
| `estado` | `VARCHAR(40)` | Estado actual del proceso o registro. | 40 | No | — |
| `ruta_artefacto` | `VARCHAR(500)` | Ruta del artefacto descargable. | 500 | Sí | — |
| `manifiesto` | `JSONB` | Manifiesto del resultado de generación en JSON. | Variable | No | — |
| `detalle_error` | `TEXT` | Detalle del error si ocurrió. | Variable | Sí | — |
| `fecha_creacion` | `TIMESTAMPTZ` | Fecha de creación del registro. | 8 bytes | No | — |
| `fecha_actualizacion` | `TIMESTAMPTZ` | Fecha de última actualización. | 8 bytes | No | — |

**Relaciones:** `proyecto_id` → `proyectos.id`; `transformacion_id` → `transformaciones_uml.id`; `usuario_generador_id` → `usuarios.id`.

#### Tabla 20. Diccionario de `frontends_generados`

Versiones Flutter generadas y backend de origen.

| Atributo | Tipo de dato | Descripción | Tamaño | Nulos | Llave |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Identificador del registro. | 16 bytes | No | PK |
| `proyecto_id` | `UUID` | Referencia a `proyectos.id`. | 16 bytes | No | FK |
| `transformacion_id` | `UUID` | Referencia a `transformaciones_uml.id`. | 16 bytes | No | FK |
| `usuario_generador_id` | `UUID` | Referencia a `usuarios.id`. | 16 bytes | No | FK |
| `backend_id` | `UUID` | Referencia a `backends_generados.id`. | 16 bytes | Sí | FK |
| `nombre` | `VARCHAR(160)` | Nombre del registro. | 160 | No | — |
| `tecnologia` | `VARCHAR(80)` | Tecnología del artefacto generado. | 80 | No | — |
| `lenguaje` | `VARCHAR(40)` | Lenguaje de programación generado. | 40 | No | — |
| `etiqueta_version` | `VARCHAR(80)` | Etiqueta visible de la versión generada. | 80 | No | — |
| `estado` | `VARCHAR(40)` | Estado actual del proceso o registro. | 40 | No | — |
| `ruta_artefacto` | `VARCHAR(500)` | Ruta del artefacto descargable. | 500 | Sí | — |
| `manifiesto` | `JSONB` | Manifiesto del resultado de generación en JSON. | Variable | No | — |
| `detalle_error` | `TEXT` | Detalle del error si ocurrió. | Variable | Sí | — |
| `fecha_creacion` | `TIMESTAMPTZ` | Fecha de creación del registro. | 8 bytes | No | — |
| `fecha_actualizacion` | `TIMESTAMPTZ` | Fecha de última actualización. | 8 bytes | No | — |

**Relaciones:** `backend_id` → `backends_generados.id`; `proyecto_id` → `proyectos.id`; `transformacion_id` → `transformaciones_uml.id`; `usuario_generador_id` → `usuarios.id`.

#### Tabla 21. Diccionario de `artefactos_generados`

Archivos descargables producidos por la generación.

| Atributo | Tipo de dato | Descripción | Tamaño | Nulos | Llave |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Identificador del registro. | 16 bytes | No | PK |
| `proyecto_id` | `UUID` | Referencia a `proyectos.id`. | 16 bytes | No | FK |
| `backend_generado_id` | `UUID` | Referencia a `backends_generados.id`. | 16 bytes | Sí | FK |
| `frontend_generado_id` | `UUID` | Referencia a `frontends_generados.id`. | 16 bytes | Sí | FK |
| `tipo_artefacto` | `VARCHAR(60)` | Tipo de archivo generado. | 60 | No | — |
| `nombre_archivo` | `VARCHAR(255)` | Nombre del archivo. | 255 | No | — |
| `ruta_archivo` | `VARCHAR(500)` | Ruta del archivo generado o recibido. | 500 | No | — |
| `suma_verificacion` | `VARCHAR(128)` | Suma de verificación del archivo. | 128 | Sí | — |
| `metadatos_json` | `JSONB` | Metadatos adicionales en JSON. | Variable | No | — |
| `fecha_creacion` | `TIMESTAMPTZ` | Fecha de creación del registro. | 8 bytes | No | — |
| `fecha_actualizacion` | `TIMESTAMPTZ` | Fecha de última actualización. | 8 bytes | No | — |

**Relaciones:** `backend_generado_id` → `backends_generados.id`; `frontend_generado_id` → `frontends_generados.id`; `proyecto_id` → `proyectos.id`.

#### Tabla 22. Diccionario de `generaciones_coordinadas`

Estado de la generación coordinada de backend y frontend.

| Atributo | Tipo de dato | Descripción | Tamaño | Nulos | Llave |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Identificador del registro. | 16 bytes | No | PK |
| `proyecto_id` | `UUID` | Referencia a `proyectos.id`. | 16 bytes | No | FK |
| `transformacion_id` | `UUID` | Referencia a `transformaciones_uml.id`. | 16 bytes | No | FK |
| `usuario_solicitante_id` | `UUID` | Referencia a `usuarios.id`. | 16 bytes | No | FK |
| `backend_id` | `UUID` | Referencia a `backends_generados.id`. | 16 bytes | Sí | FK |
| `frontend_id` | `UUID` | Referencia a `frontends_generados.id`. | 16 bytes | Sí | FK |
| `solicitud_cliente_id` | `VARCHAR(120)` | Identificador idempotente de la solicitud. | 120 | No | — |
| `nombre` | `VARCHAR(160)` | Nombre del registro. | 160 | No | — |
| `estado` | `VARCHAR(40)` | Estado actual del proceso o registro. | 40 | No | — |
| `etapa` | `VARCHAR(40)` | Etapa actual del proceso de generación. | 40 | No | — |
| `hash_plan` | `VARCHAR(64)` | Hash del plan de generación. | 64 | Sí | — |
| `plan_json` | `JSONB` | Plan de generación en JSON. | Variable | No | — |
| `diagnosticos` | `JSONB` | Diagnósticos de generación en JSON. | Variable | No | — |
| `manifiesto` | `JSONB` | Manifiesto del resultado de generación en JSON. | Variable | No | — |
| `ruta_artefacto` | `VARCHAR(500)` | Ruta del artefacto descargable. | 500 | Sí | — |
| `detalle_error` | `TEXT` | Detalle del error si ocurrió. | Variable | Sí | — |
| `fecha_creacion` | `TIMESTAMPTZ` | Fecha de creación del registro. | 8 bytes | No | — |
| `fecha_actualizacion` | `TIMESTAMPTZ` | Fecha de última actualización. | 8 bytes | No | — |

**Relaciones:** `backend_id` → `backends_generados.id`; `frontend_id` → `frontends_generados.id`; `proyecto_id` → `proyectos.id`; `transformacion_id` → `transformaciones_uml.id`; `usuario_solicitante_id` → `usuarios.id`.

**Unicidad:** UNIQUE(`transformacion_id`, `usuario_solicitante_id`, `solicitud_cliente_id`).

#### Tabla 23. Diccionario de `temas_flutter_predefinidos`

Temas Flutter reutilizables del proyecto.

| Atributo | Tipo de dato | Descripción | Tamaño | Nulos | Llave |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Identificador del registro. | 16 bytes | No | PK |
| `proyecto_id` | `UUID` | Referencia a `proyectos.id`. | 16 bytes | No | FK |
| `nombre` | `VARCHAR(120)` | Nombre del registro. | 120 | No | — |
| `configuracion_json` | `JSONB` | Configuración visual Flutter en JSON. | Variable | No | — |
| `version_esquema` | `INTEGER` | Versión del contrato de datos. | 4 bytes | No | — |
| `usuario_creador_id` | `UUID` | Referencia a `usuarios.id`. | 16 bytes | No | FK |
| `usuario_actualizador_id` | `UUID` | Referencia a `usuarios.id`. | 16 bytes | No | FK |
| `fecha_creacion` | `TIMESTAMPTZ` | Fecha de creación del registro. | 8 bytes | No | — |
| `fecha_actualizacion` | `TIMESTAMPTZ` | Fecha de última actualización. | 8 bytes | No | — |

**Relaciones:** `proyecto_id` → `proyectos.id`; `usuario_actualizador_id` → `usuarios.id`; `usuario_creador_id` → `usuarios.id`.

**Unicidad:** UNIQUE(`proyecto_id`, `lower(nombre::text)`).

### Notificaciones

#### Tabla 24. Diccionario de `notificaciones`

Avisos dirigidos a usuarios.

| Atributo | Tipo de dato | Descripción | Tamaño | Nulos | Llave |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Identificador del registro. | 16 bytes | No | PK |
| `usuario_destinatario_id` | `UUID` | Referencia a `usuarios.id`. | 16 bytes | No | FK |
| `proyecto_id` | `UUID` | Referencia a `proyectos.id`. | 16 bytes | Sí | FK |
| `usuario_actor_id` | `UUID` | Referencia a `usuarios.id`. | 16 bytes | Sí | FK |
| `tipo` | `VARCHAR(80)` | Tipo de notificación. | 80 | No | — |
| `severidad` | `VARCHAR(16)` | Severidad del aviso o recomendación. | 16 | No | — |
| `titulo` | `VARCHAR(180)` | Título mostrado al usuario. | 180 | No | — |
| `cuerpo` | `VARCHAR(500)` | Contenido de la notificación. | 500 | No | — |
| `tipo_recurso` | `VARCHAR(80)` | Tipo de recurso vinculado al evento. | 80 | Sí | — |
| `recurso_id` | `UUID` | Identificador lógico del recurso vinculado. | 16 bytes | Sí | — |
| `enlace_directo` | `JSONB` | Destino de navegación de la notificación en JSON. | Variable | No | — |
| `clave_deduplicacion` | `VARCHAR(200)` | Clave para no duplicar el aviso. | 200 | No | — |
| `clave_grupo` | `VARCHAR(200)` | Clave de agrupación de avisos. | 200 | Sí | — |
| `fecha_suceso` | `TIMESTAMPTZ` | Fecha del suceso notificado. | 8 bytes | No | — |
| `fecha_lectura` | `TIMESTAMPTZ` | Fecha de lectura del aviso. | 8 bytes | Sí | — |
| `fecha_clic` | `TIMESTAMPTZ` | Fecha de apertura del aviso. | 8 bytes | Sí | — |
| `fecha_archivo` | `TIMESTAMPTZ` | Fecha de archivo del aviso. | 8 bytes | Sí | — |
| `fecha_creacion` | `TIMESTAMPTZ` | Fecha de creación del registro. | 8 bytes | No | — |
| `fecha_actualizacion` | `TIMESTAMPTZ` | Fecha de última actualización. | 8 bytes | No | — |

**Relaciones:** `proyecto_id` → `proyectos.id`; `usuario_actor_id` → `usuarios.id`; `usuario_destinatario_id` → `usuarios.id`.

**Unicidad:** UNIQUE(`usuario_destinatario_id`, `clave_deduplicacion`).

#### Tabla 25. Diccionario de `bandeja_salida_notificaciones`

Entregas pendientes o completadas de avisos.

| Atributo | Tipo de dato | Descripción | Tamaño | Nulos | Llave |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Identificador del registro. | 16 bytes | No | PK |
| `notificacion_id` | `UUID` | Referencia a `notificaciones.id`. | 16 bytes | No | FK |
| `canal` | `VARCHAR(32)` | Canal de entrega de la notificación. | 32 | No | — |
| `estado` | `VARCHAR(24)` | Estado actual del proceso o registro. | 24 | No | — |
| `numero_intentos` | `INTEGER` | Número de intentos de entrega o publicación. | 4 bytes | No | — |
| `fecha_disponible` | `TIMESTAMPTZ` | Fecha desde la que se puede procesar. | 8 bytes | No | — |
| `fecha_bloqueo` | `TIMESTAMPTZ` | Fecha en que un trabajador tomó el registro. | 8 bytes | Sí | — |
| `bloqueado_por` | `VARCHAR(120)` | Trabajador que tomó el registro. | 120 | Sí | — |
| `codigo_ultimo_error` | `VARCHAR(120)` | Código del último fallo de entrega. | 120 | Sí | — |
| `fecha_entrega` | `TIMESTAMPTZ` | Fecha de entrega de la notificación. | 8 bytes | Sí | — |
| `fecha_creacion` | `TIMESTAMPTZ` | Fecha de creación del registro. | 8 bytes | No | — |
| `fecha_actualizacion` | `TIMESTAMPTZ` | Fecha de última actualización. | 8 bytes | No | — |

**Relaciones:** `notificacion_id` → `notificaciones.id`.

**Unicidad:** UNIQUE(`notificacion_id`, `canal`).

#### Tabla 26. Diccionario de `preferencias_notificaciones`

Preferencias de notificación por usuario y proyecto.

| Atributo | Tipo de dato | Descripción | Tamaño | Nulos | Llave |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Identificador del registro. | 16 bytes | No | PK |
| `usuario_id` | `UUID` | Referencia a `usuarios.id`. | 16 bytes | No | FK |
| `proyecto_id` | `UUID` | Referencia a `proyectos.id`. | 16 bytes | Sí | FK |
| `categoria` | `VARCHAR(80)` | Categoría de la recomendación o preferencia. | 80 | No | — |
| `habilitado_en_aplicacion` | `BOOLEAN` | Permite notificaciones dentro de la aplicación. | 1 byte | No | — |
| `push_habilitado` | `BOOLEAN` | Permite notificaciones push. | 1 byte | No | — |
| `silenciado_hasta` | `TIMESTAMPTZ` | Silencio de avisos hasta esta fecha. | 8 bytes | Sí | — |
| `fecha_creacion` | `TIMESTAMPTZ` | Fecha de creación del registro. | 8 bytes | No | — |
| `fecha_actualizacion` | `TIMESTAMPTZ` | Fecha de última actualización. | 8 bytes | No | — |

**Relaciones:** `proyecto_id` → `proyectos.id`; `usuario_id` → `usuarios.id`.

**Unicidad:** UNIQUE(`usuario_id`, `categoria`) WHERE `(proyecto_id IS NULL)`; UNIQUE(`usuario_id`, `proyecto_id`, `categoria`).

#### Tabla 27. Diccionario de `suscripciones_push`

Suscripciones push de navegadores y dispositivos.

| Atributo | Tipo de dato | Descripción | Tamaño | Nulos | Llave |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Identificador del registro. | 16 bytes | No | PK |
| `usuario_id` | `UUID` | Referencia a `usuarios.id`. | 16 bytes | No | FK |
| `punto_acceso` | `VARCHAR(2048)` | URL de suscripción push. | 2048 | No | — |
| `p256dh` | `TEXT` | Clave pública de cifrado push. | Variable | No | — |
| `autenticacion` | `TEXT` | Secreto de autenticación push. | Variable | No | — |
| `codificacion_contenido` | `VARCHAR(40)` | Codificación del contenido push. | 40 | No | — |
| `agente_usuario` | `VARCHAR(512)` | Agente del navegador o dispositivo. | 512 | Sí | — |
| `fecha_expiracion` | `TIMESTAMPTZ` | Fecha de vencimiento. | 8 bytes | Sí | — |
| `esta_activo` | `BOOLEAN` | Indica si el registro está activo. | 1 byte | No | — |
| `numero_fallos` | `INTEGER` | Número de fallos de entrega push. | 4 bytes | No | — |
| `fecha_ultimo_exito` | `TIMESTAMPTZ` | Última entrega push correcta. | 8 bytes | Sí | — |
| `fecha_creacion` | `TIMESTAMPTZ` | Fecha de creación del registro. | 8 bytes | No | — |
| `fecha_actualizacion` | `TIMESTAMPTZ` | Fecha de última actualización. | 8 bytes | No | — |

**Relaciones:** `usuario_id` → `usuarios.id`.

**Unicidad:** UNIQUE(`punto_acceso`).

### Infraestructura SQL

#### Tabla 28. Diccionario de `bandeja_salida_nosql`

Tabla SQL de eventos transaccionales pendientes de publicación.

| Atributo | Tipo de dato | Descripción | Tamaño | Nulos | Llave |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Identificador del registro. | 16 bytes | No | PK |
| `tipo_agregado` | `VARCHAR(80)` | Tipo de agregado asociado al evento SQL. | 80 | No | — |
| `agregado_id` | `UUID` | Identificador del agregado asociado al evento SQL. | 16 bytes | No | — |
| `tipo_evento` | `VARCHAR(100)` | Tipo de evento registrado. | 100 | No | — |
| `carga_datos` | `JSONB` | Datos del evento o acción en JSON. | Variable | No | — |
| `clave_idempotencia` | `VARCHAR(200)` | Clave para evitar operaciones duplicadas. | 200 | No | — |
| `estado` | `VARCHAR(24)` | Estado actual del proceso o registro. | 24 | No | — |
| `numero_intentos` | `INTEGER` | Número de intentos de entrega o publicación. | 4 bytes | No | — |
| `fecha_disponible` | `TIMESTAMPTZ` | Fecha desde la que se puede procesar. | 8 bytes | No | — |
| `fecha_bloqueo` | `TIMESTAMPTZ` | Fecha en que un trabajador tomó el registro. | 8 bytes | Sí | — |
| `bloqueado_por` | `VARCHAR(120)` | Trabajador que tomó el registro. | 120 | Sí | — |
| `fecha_procesamiento` | `TIMESTAMPTZ` | Fecha de publicación satisfactoria. | 8 bytes | Sí | — |
| `ultimo_error` | `TEXT` | Descripción del último error de publicación. | Variable | Sí | — |
| `fecha_creacion` | `TIMESTAMPTZ` | Fecha de creación del registro. | 8 bytes | No | — |
| `fecha_actualizacion` | `TIMESTAMPTZ` | Fecha de última actualización. | 8 bytes | No | — |

**Unicidad:** UNIQUE(`clave_idempotencia`).

### Control de migraciones

#### Tabla 29. Diccionario de `alembic_version`

Revisión de migraciones Alembic aplicada a PostgreSQL.

| Atributo | Tipo de dato | Descripción | Tamaño | Nulos | Llave |
| --- | --- | --- | --- | --- | --- |
| `version_num` | `VARCHAR(32)` | Revisión Alembic aplicada. | 32 | No | PK |
