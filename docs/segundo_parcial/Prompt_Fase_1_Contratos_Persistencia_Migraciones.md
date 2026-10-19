# PROMPT FASE 1: CONTRATOS, PERSISTENCIA Y MIGRACIONES

## 0. Instruccion maestra

Implementar la Fase 1 de la segunda parte de CASE Inteligente de forma completa, verificable y compatible con todo lo construido durante el primer parcial.

Esta fase debe establecer los contratos y la persistencia que utilizaran posteriormente:

- El motor unico de IA local con Ollama y Qwen.
- La conversacion colaborativa compartida por proyecto.
- La deteccion y ejecucion de una o varias intenciones.
- La especificacion funcional de metodos UML.
- La generacion coordinada de Spring Boot y Flutter.
- El editor y la previsualizacion de estilos Flutter.
- El versionado ampliado del proyecto.
- La bitacora y las notificaciones.
- La aplicacion movil reducida en formato PWA.

No realizar una implementacion superficial, simulada o aislada. Antes de modificar archivos se debe estudiar el repositorio real, identificar las convenciones existentes y reutilizar los modulos, servicios, repositorios, esquemas, migraciones y mecanismos de seguridad disponibles.

Las fases son divisiones tecnicas de una sola implementacion integral. Ninguna fase posterior deberia necesitar reemplazar los contratos definidos aqui; solo podra ampliarlos de manera compatible y versionada.

---

## 1. Rol del implementador

Actuar como arquitecto de software y desarrollador senior responsable de contratos distribuidos, PostgreSQL, FastAPI, SQLAlchemy 2, Pydantic 2, TypeScript, WebSocket, Alembic y pruebas automatizadas.

Reglas obligatorias:

1. Leer primero el codigo existente.
2. Respetar la arquitectura modular por paquetes.
3. Separar modelos, repositorios, servicios, routers y esquemas.
4. Evitar duplicar funcionalidades existentes.
5. Mantener compatibilidad con datos del primer parcial.
6. No revertir cambios locales ajenos a esta fase.
7. No introducir credenciales o secretos.
8. No agregar dependencias sin necesidad real.
9. Incorporar pruebas proporcionales al riesgo.
10. Entregar migraciones, contratos, pruebas y documentacion sincronizados.

---

## 2. Contexto funcional

CASE Inteligente ya permite gestionar usuarios y proyectos, editar UML, importar y exportar XMI, generar UML por texto, voz e imagen, colaborar por WebSocket, guardar versiones, generar Spring Boot y Flutter, previsualizar estilos y recibir notificaciones Web Push.

La segunda parte incorpora una sola IA integral. No existen personalidades separadas. La misma IA explica, recomienda, revisa, coordina, modifica UML o prepara generacion segun una o varias intenciones detectadas en cada solicitud.

La IA trabaja dentro del contexto de un proyecto, reconoce al usuario autenticado, conserva una conversacion compartida y propone acciones estructuradas. Nunca debe escribir directamente en la base de datos sin pasar por servicios, permisos y validadores.

La descripcion funcional de un metodo UML alimentara tanto al generador Spring Boot como al generador Flutter. Esta fase aun no implementa toda esa generacion, pero debe crear un contrato suficientemente expresivo para ambas salidas.

La aplicacion movil sera una vista reducida de CASE: proyectos, diagramas de solo lectura, actividad, versiones, IA y notificaciones. No incluira inicialmente el editor UML completo.

---

## 3. Tecnologias obligatorias

### Backend

- Python y FastAPI en las versiones fijadas por el proyecto.
- SQLAlchemy 2 con `Mapped` y `mapped_column`.
- Pydantic 2.
- PostgreSQL.
- Alembic.
- Pytest.
- Ruff.

### Frontend

- React.
- TypeScript estricto.
- Vite.
- Cliente HTTP y WebSocket existentes.
- Vitest y Testing Library.

### Datos

- UUID nativo para identificadores.
- `TIMESTAMP WITH TIME ZONE` para fechas.
- `JSONB` solo con esquema Pydantic asociado.
- `TEXT` para contenido conversacional.
- `VARCHAR`, restricciones `CHECK`, `UNIQUE`, claves foraneas e indices.

No sustituir PostgreSQL por SQLite para probar JSONB, UUID, restricciones o concurrencia.

---

## 4. Alcance exacto

La fase debe completar:

1. Especificacion funcional persistente para metodos UML.
2. Configuracion persistente de IA por proyecto.
3. Conversacion y mensajes compartidos por proyecto.
4. Acciones estructuradas y recomendaciones persistentes.
5. Configuracion visual Flutter persistente.
6. Contrato versionado para snapshots ampliados.
7. Contratos REST para consultar y mantener estos datos.
8. Contratos WebSocket para eventos de IA.
9. Contratos de lectura para la PWA movil.
10. Migraciones compatibles y reversibles.
11. Tipos TypeScript equivalentes.
12. Pruebas de modelos, servicios, API, seguridad y migraciones.

---

## 5. Fuera de alcance

No implementar todavia:

- Llamadas reales a Ollama.
- Descarga automatica de Qwen.
- Inferencia LLM o streaming real.
- RAG, embeddings o entrenamiento.
- Ejecucion automatica de acciones de IA.
- Generacion completa desde descripciones de metodos.
- Chat visual definitivo.
- Editor visual final de especificaciones.
- Interfaz movil terminada.
- Proveedores cloud como requisito.

Definir contratos preparados para estas capacidades sin simular que ya existen. No crear endpoints que fabriquen respuestas falsas del modelo.

---

## 6. Analisis previo obligatorio

Inspeccionar como minimo:

- `backend/app/core/database/`
- `backend/app/core/security/`
- `backend/app/models.py`
- `backend/app/main.py`
- `backend/app/modules/modelado_uml/`
- `backend/app/modules/proyectos_colaboracion/`
- `backend/app/modules/generacion_software/`
- `backend/app/modules/notificaciones/`
- `backend/app/websocket/`
- `backend/migrations/versions/`
- `backend/tests/`
- `frontend/src/core/api/`
- `frontend/src/core/websocket/`
- Los modulos frontend de proyectos, UML y generacion.

Confirmar:

- Como se verifica membresia y rol de proyecto.
- Como se serializa un diagrama.
- Como se construye `ProjectVersion.snapshot`.
- Como se numeran e identifican eventos colaborativos.
- Como se registran modelos para Alembic.
- Cual es el `head` real de migraciones.
- Como se representan metodos y parametros UML.
- Como se valida y envia `theme_config`.

No crear un mecanismo paralelo si ya existe uno apropiado.

---

## 7. Convenciones de datos

- UUID para todas las entidades nuevas.
- UUID del servidor, excepto claves idempotentes del cliente.
- El autor siempre se obtiene del token autenticado.
- UTC interno e ISO 8601 en API.
- Estados como enums Pydantic y uniones literales TypeScript.
- Cadenas persistidas con `CHECK` cuando el conjunto sea estable.
- Todo JSONB debe incluir validacion y `schema_version` cuando pueda evolucionar.
- Las dependencias sin sentido propio usan `ON DELETE CASCADE`.
- No agregar eliminacion fisica de conversaciones mediante API de usuario.
- No guardar binarios, base64, tokens o secretos en JSONB.

---

## 8. Especificacion funcional de metodos UML

### Decision de modelado

Crear una entidad uno a uno `UmlMethodSpecification` en `uml_method_specifications`. Mantener en `uml_methods` la firma UML basica y guardar la semantica en la nueva tabla.

### Campos minimos

```text
id                      UUID PK
method_id               UUID FK uml_methods.id UNIQUE NOT NULL ON DELETE CASCADE
description             TEXT NULL
operation_kind          VARCHAR(40) NOT NULL DEFAULT 'custom'
exposure                VARCHAR(30) NOT NULL DEFAULT 'internal'
preconditions           JSONB NOT NULL DEFAULT []
postconditions          JSONB NOT NULL DEFAULT []
business_rules          JSONB NOT NULL DEFAULT []
validations             JSONB NOT NULL DEFAULT []
side_effects            JSONB NOT NULL DEFAULT []
required_permissions    JSONB NOT NULL DEFAULT []
related_entities        JSONB NOT NULL DEFAULT []
backend_contract        JSONB NOT NULL DEFAULT {}
frontend_contract       JSONB NOT NULL DEFAULT {}
schema_version          INTEGER NOT NULL DEFAULT 1
created_at              TIMESTAMPTZ NOT NULL
updated_at              TIMESTAMPTZ NOT NULL
```

### `operation_kind`

- `create`
- `read`
- `update`
- `delete`
- `search`
- `calculate`
- `business_action`
- `custom`

### `exposure`

- `internal`: no requiere endpoint ni interfaz directa.
- `api`: requiere contrato backend, no necesariamente control visual.
- `user_action`: requiere backend y evaluacion obligatoria de Flutter.

### Regla, condicion o validacion

```json
{
  "code": "student_must_exist",
  "description": "El estudiante debe existir",
  "severity": "error"
}
```

Normalizar entradas simples a esta estructura. Limitar longitud y cantidad.

### Entidad relacionada

```json
{
  "class_id": "uuid-opcional",
  "class_name": "Estudiante",
  "relation": "input_reference",
  "required": true
}
```

### Contrato backend

```json
{
  "http_method": "POST",
  "path": "/inscripciones",
  "request_dto": "CrearInscripcionRequest",
  "response_dto": "InscripcionResponse",
  "transactional": true,
  "authorization": [],
  "error_codes": ["STUDENT_NOT_FOUND", "DUPLICATE_ENROLLMENT"]
}
```

### Contrato Flutter

```json
{
  "interaction": "form",
  "label": "Inscribir estudiante",
  "placement": "list_primary_action",
  "confirmation_required": false,
  "refresh_targets": ["Inscripcion"],
  "success_message": "Inscripcion registrada",
  "fields": [
    {
      "parameter": "estudianteId",
      "control": "entity_selector",
      "source_entity": "Estudiante",
      "display_fields": ["id", "nombre"]
    }
  ]
}
```

### Validaciones

- Descripcion con maximo definido.
- Codigos en `snake_case`.
- Ruta iniciada en `/`.
- Metodo HTTP restringido.
- Referencias pertenecientes al mismo diagrama.
- Parametros de controles existentes en la firma UML.
- Un `user_action` sin contrato Flutter genera error o advertencia explicita.

### Compatibilidad

- Metodos anteriores sin especificacion siguen funcionando.
- La ausencia de especificacion no impide abrir, validar, exportar ni generar con el comportamiento anterior.
- Crear esquemas de alta, lectura y PATCH parcial.
- Actualizar dentro de una transaccion.

---

## 9. Configuracion de IA por proyecto

Crear `AiProjectSettings` en `ai_project_settings`:

```text
id                          UUID PK
project_id                  UUID FK projects.id UNIQUE NOT NULL ON DELETE CASCADE
enabled                     BOOLEAN NOT NULL DEFAULT true
preferred_provider          VARCHAR(40) NOT NULL DEFAULT 'ollama'
model_name                  VARCHAR(120) NOT NULL
fallback_enabled            BOOLEAN NOT NULL DEFAULT true
require_confirmation        BOOLEAN NOT NULL DEFAULT true
max_context_messages        INTEGER NOT NULL DEFAULT 40
summary_trigger_messages    INTEGER NOT NULL DEFAULT 30
settings_json               JSONB NOT NULL DEFAULT {}
created_by_user_id          UUID FK users.id NOT NULL
updated_by_user_id          UUID FK users.id NOT NULL
created_at                  TIMESTAMPTZ NOT NULL
updated_at                  TIMESTAMPTZ NOT NULL
```

Reglas:

- Proveedores iniciales: `ollama` y `rule_engine`.
- Rangos seguros para limites de contexto.
- No almacenar API keys o secretos.
- No crear campos de personalidad.
- Todo miembro consulta configuracion no sensible.
- Solo creador u organizador modifica proveedor, modelo y politicas.

---

## 10. Conversacion compartida

### `AiConversation`

Tabla `ai_conversations`:

```text
id                          UUID PK
project_id                  UUID FK projects.id UNIQUE NOT NULL ON DELETE CASCADE
status                      VARCHAR(30) NOT NULL DEFAULT 'active'
summary                     TEXT NULL
summary_until_sequence      INTEGER NOT NULL DEFAULT 0
last_message_sequence       INTEGER NOT NULL DEFAULT 0
schema_version              INTEGER NOT NULL DEFAULT 1
created_at                  TIMESTAMPTZ NOT NULL
updated_at                  TIMESTAMPTZ NOT NULL
```

Debe existir una conversacion principal por proyecto. Crear de forma perezosa y segura ante concurrencia.

### `AiMessage`

Tabla `ai_messages`:

```text
id                          UUID PK
conversation_id             UUID FK ai_conversations.id NOT NULL ON DELETE CASCADE
project_id                  UUID FK projects.id NOT NULL ON DELETE CASCADE
author_user_id              UUID FK users.id NULL
role                        VARCHAR(20) NOT NULL
content                     TEXT NOT NULL
sequence_number             INTEGER NOT NULL
client_message_id           UUID NULL
correlation_id              UUID NOT NULL
status                      VARCHAR(30) NOT NULL DEFAULT 'completed'
detected_intents            JSONB NOT NULL DEFAULT []
references_json             JSONB NOT NULL DEFAULT []
metadata_json               JSONB NOT NULL DEFAULT {}
created_at                  TIMESTAMPTZ NOT NULL
updated_at                  TIMESTAMPTZ NOT NULL
```

Roles de protocolo: `user`, `assistant`, `system`, `tool`. No son personalidades.

Estados: `pending`, `streaming`, `completed`, `failed`, `cancelled`.

Restricciones:

- `UNIQUE(conversation_id, sequence_number)`.
- Idempotencia por conversacion, autor y `client_message_id` no nulo.
- Indices por proyecto/secuencia y correlacion.
- Autor obligatorio para mensajes de usuario.
- Secuencia asignada transaccionalmente.
- No usar `MAX + 1` sin bloqueo.
- Rechazar contenido vacio o excesivo.
- No aceptar HTML confiable ni binarios embebidos.

Referencia tipada:

```json
{
  "type": "uml_class",
  "id": "uuid",
  "label": "Inscripcion"
}
```

Validar que cada referencia pertenezca al proyecto.

---

## 11. Intenciones y solicitudes compuestas

Definir estas intenciones iniciales:

- `answer_question`
- `explain_system`
- `explain_uml`
- `recommend`
- `review_uml`
- `validate_uml`
- `modify_uml`
- `generate_uml`
- `specify_method`
- `prepare_generation`
- `summarize_conversation`
- `summarize_project`
- `coordinate_team`
- `unknown`

Definir `AiInteractionRequest` para uso en Fase 2:

```json
{
  "client_message_id": "uuid",
  "content": "Revisa el diagrama, agrega Factura y explica el cambio",
  "diagram_id": "uuid-opcional",
  "base_diagram_version": 12,
  "requested_context": {
    "include_diagram": true,
    "include_recent_messages": true,
    "include_project_versions": false
  }
}
```

Respuesta futura:

```json
{
  "message_id": "uuid",
  "correlation_id": "uuid",
  "status": "completed",
  "detected_intents": ["review_uml", "modify_uml", "explain_uml"],
  "answer": "...",
  "actions": [],
  "recommendations": [],
  "conversation_sequence": 28
}
```

Crear esquemas backend y tipos TypeScript, pero no una respuesta falsa del modelo.

---

## 12. Acciones estructuradas

Crear `AiAction` en `ai_actions`:

```text
id                          UUID PK
project_id                  UUID FK projects.id NOT NULL ON DELETE CASCADE
conversation_id             UUID FK ai_conversations.id NOT NULL ON DELETE CASCADE
source_message_id           UUID FK ai_messages.id NOT NULL ON DELETE CASCADE
requested_by_user_id        UUID FK users.id NOT NULL
action_type                 VARCHAR(80) NOT NULL
target_type                 VARCHAR(80) NULL
target_id                   UUID NULL
payload                     JSONB NOT NULL DEFAULT {}
risk_level                  VARCHAR(20) NOT NULL DEFAULT 'low'
requires_confirmation       BOOLEAN NOT NULL DEFAULT true
status                      VARCHAR(30) NOT NULL DEFAULT 'proposed'
confirmed_by_user_id        UUID FK users.id NULL
confirmed_at                TIMESTAMPTZ NULL
executed_at                 TIMESTAMPTZ NULL
result_json                 JSONB NOT NULL DEFAULT {}
error_message               TEXT NULL
idempotency_key             UUID NOT NULL
created_at                  TIMESTAMPTZ NOT NULL
updated_at                  TIMESTAMPTZ NOT NULL
```

Estados: `proposed`, `confirmed`, `executing`, `applied`, `rejected`, `failed`, `cancelled`.

Riesgos: `low`, `medium`, `high`.

Catalogo inicial:

- Crear, actualizar y eliminar clase.
- Crear, actualizar y eliminar atributo.
- Crear, actualizar y eliminar metodo.
- Crear, actualizar y eliminar relacion.
- Actualizar especificacion de metodo.
- Guardar version.
- Preparar generacion backend.
- Preparar generacion Flutter.

Reglas:

- Clave idempotente unica por proyecto.
- Una accion aplicada no se ejecuta de nuevo.
- Confirmacion y permiso de ejecucion son controles diferentes.
- Acciones destructivas siempre requieren confirmacion.
- Validar `payload` segun `action_type`.
- No implementar ejecutores falsos en esta fase.

---

## 13. Recomendaciones

Crear `AiRecommendation` en `ai_recommendations`:

```text
id                          UUID PK
project_id                  UUID FK projects.id NOT NULL ON DELETE CASCADE
conversation_id             UUID FK ai_conversations.id NOT NULL ON DELETE CASCADE
source_message_id           UUID FK ai_messages.id NOT NULL ON DELETE CASCADE
category                    VARCHAR(50) NOT NULL
severity                    VARCHAR(20) NOT NULL DEFAULT 'info'
title                       VARCHAR(200) NOT NULL
description                 TEXT NOT NULL
references_json             JSONB NOT NULL DEFAULT []
status                      VARCHAR(30) NOT NULL DEFAULT 'open'
resolved_by_user_id         UUID FK users.id NULL
resolved_at                 TIMESTAMPTZ NULL
resolution_note             TEXT NULL
created_at                  TIMESTAMPTZ NOT NULL
updated_at                  TIMESTAMPTZ NOT NULL
```

Categorias: calidad UML, arquitectura, especificacion de metodos, generacion, colaboracion, seguridad y usabilidad.

Severidades: `info`, `warning`, `critical`.

Estados: `open`, `accepted`, `dismissed`, `resolved`.

No confundir recomendacion persistente con notificacion push.

---

## 14. Configuracion Flutter persistente

Crear `FlutterThemeSettings` en `flutter_theme_settings`:

```text
id                          UUID PK
project_id                  UUID FK projects.id UNIQUE NOT NULL ON DELETE CASCADE
config_json                 JSONB NOT NULL
preset_name                 VARCHAR(120) NULL
schema_version              INTEGER NOT NULL DEFAULT 1
created_by_user_id          UUID FK users.id NOT NULL
updated_by_user_id          UUID FK users.id NOT NULL
created_at                  TIMESTAMPTZ NOT NULL
updated_at                  TIMESTAMPTZ NOT NULL
```

Contrato version 1:

```json
{
  "primary_color": "#0F766E",
  "secondary_color": "#14B8A6",
  "background_color": "#F8FAFC",
  "surface_color": "#FFFFFF",
  "button_color": "#0F766E",
  "font_family": "Roboto",
  "border_radius": 12,
  "button_style": "filled",
  "density": "normal"
}
```

Reutilizar la validacion existente. No duplicar normalizadores. Un proyecto antiguo obtiene defaults. Solo editores modifican; todos los miembros leen.

Endpoints sugeridos:

- `GET /projects/{project_id}/flutter-theme`
- `PUT /projects/{project_id}/flutter-theme`

El PUT debe ser idempotente y devolver la configuracion normalizada.

---

## 15. Snapshot versionado

Definir `ProjectSnapshotV2`:

```json
{
  "schema_version": 2,
  "captured_at": "2026-10-15T12:00:00Z",
  "project": {"id": "uuid", "name": "Sistema de ventas"},
  "diagrams": [],
  "flutter_theme": null,
  "generation_settings": {},
  "ai_settings": {
    "enabled": true,
    "preferred_provider": "ollama",
    "model_name": "qwen",
    "fallback_enabled": true,
    "require_confirmation": true
  }
}
```

Reglas:

- No incluir conversaciones, acciones o recomendaciones.
- No incluir secretos, suscripciones push o endpoints privados.
- Incluir solamente configuracion de IA no sensible.
- Tratar snapshots sin version como version 1.
- Implementar adaptador V1 a V2.
- Validar antes de restaurar.
- Mantener copia de seguridad previa a restauracion.
- Una version futura no soportada produce error explicito.

---

## 16. Contrato WebSocket version 2

Sobre comun:

```json
{
  "protocol_version": 2,
  "type": "AI_MESSAGE_CREATED",
  "event_id": "uuid",
  "project_id": "uuid",
  "diagram_id": "uuid-opcional",
  "sequence_number": 125,
  "correlation_id": "uuid",
  "occurred_at": "2026-10-15T12:00:00Z",
  "actor": {
    "user_id": "uuid-opcional",
    "display_name": "Editor UML"
  },
  "payload": {}
}
```

Definir:

- `AI_MESSAGE_CREATED`
- `AI_MESSAGE_STATUS_CHANGED`
- `AI_ACTION_PROPOSED`
- `AI_ACTION_STATUS_CHANGED`
- `AI_RECOMMENDATION_CREATED`
- `AI_CONVERSATION_SUMMARY_UPDATED`
- `FLUTTER_THEME_UPDATED`
- `PROJECT_VERSION_CREATED`
- `PROJECT_VERSION_RESTORED`

Reglas:

- Reutilizar autenticacion y membresia actuales.
- Mantener evento, correlacion y secuencia.
- Clientes ignoran eventos desconocidos sin desconectarse.
- Mantener compatibilidad temporal con version 1.
- Diferenciar streaming temporal de eventos persistentes.

En esta fase se exigen esquemas, tipos y pruebas de serializacion. No es obligatorio emitir eventos de capacidades aun inexistentes.

---

## 17. API REST real

### Configuracion IA

- `GET /projects/{project_id}/ai/settings`
- `PUT /projects/{project_id}/ai/settings`

### Conversacion

- `GET /projects/{project_id}/ai/conversation`
- `GET /projects/{project_id}/ai/messages`

Paginar por secuencia mediante `before_sequence`, `after_sequence` y `limit` acotado. No usar offset para historiales crecientes.

### Acciones y recomendaciones

- `GET /projects/{project_id}/ai/actions`
- `GET /projects/{project_id}/ai/actions/{action_id}`
- `GET /projects/{project_id}/ai/recommendations`

Confirmar, rechazar y ejecutar se dejan para el orquestador, salvo que se implementen ahora con transiciones y permisos completos. No aparentar ejecucion.

### Tema Flutter

- `GET /projects/{project_id}/flutter-theme`
- `PUT /projects/{project_id}/flutter-theme`

Reglas comunes:

- Autenticacion obligatoria.
- Membresia en todas las lecturas.
- Permiso real en mutaciones.
- `response_model` explicito.
- Limites en listados.
- Errores coherentes con el sistema.
- No revelar proyectos privados por diferencias innecesarias de respuesta.

---

## 18. Contratos moviles

Definir respuestas compactas de solo lectura.

### `MobileProjectSummary`

- `id`
- `name`
- `description`
- `project_role`
- `status`
- `diagram_count`
- `member_count`
- `unread_notification_count`
- `updated_at`

### `MobileDiagramSummary`

- `id`
- `project_id`
- `name`
- `diagram_type`
- `class_count`
- `relationship_count`
- `updated_at`
- `updated_by_display_name`

### `MobileDiagramDetail`

- Identidad y nombre.
- Clases con posicion y dimensiones.
- Atributos y metodos visibles.
- Relaciones, direcciones y multiplicidades.
- Version logica o fecha de actualizacion.
- Permisos efectivos de lectura.

Rutas posibles:

- `GET /mobile/projects`
- `GET /mobile/projects/{project_id}/diagrams`
- `GET /mobile/diagrams/{diagram_id}`

Reutilizar servicios y permisos. No duplicar dominio ni exponer escrituras moviles en esta fase.

---

## 19. Arquitectura modular

Crear un modulo coherente, por ejemplo:

```text
backend/app/modules/asistente_proyecto/
    models/
    repositories/
    schemas/
    services/
    routers/
```

La especificacion de metodos permanece bajo `modelado_uml`. La configuracion Flutter permanece bajo `generacion_software`. Las proyecciones moviles reutilizan servicios existentes.

Registrar modelos en `backend/app/models.py` y routers en `backend/app/main.py`.

Repositorios: solo acceso a datos.

Servicios: permisos, normalizacion, transacciones, autor, idempotencia y reglas de estado.

Para secuencias concurrentes usar bloqueo de fila o actualizacion atomica con `RETURNING`. No usar `MAX + 1` sin control.

---

## 20. Esquemas y TypeScript

Pydantic:

- Tipos explicitos.
- Limites de longitud y cantidad.
- `default_factory` para colecciones.
- `from_attributes` en respuestas ORM.
- Esquemas separados para crear, actualizar y responder.
- Contratos internos de snapshot y WebSocket.

TypeScript:

- Configuracion IA.
- Conversacion y mensaje.
- Referencias.
- Intenciones.
- Acciones y recomendaciones.
- Especificacion funcional de metodo.
- Tema Flutter.
- Snapshot V2.
- Eventos WebSocket V2.
- Respuestas moviles.

No usar `any`. Mantener nombres JSON reales del backend. No construir aun las interfaces finales.

---

## 21. Migracion Alembic

Crear una migracion cuyo `down_revision` sea el `head` real.

Debe:

- Crear tablas en orden correcto.
- Crear indices, `UNIQUE` y `CHECK` con nombres estables.
- No eliminar o renombrar columnas anteriores.
- No imponer valores imposibles a filas existentes.
- Incluir downgrade completo.
- Ser compatible con PostgreSQL.

Compatibilidad:

- Metodos existentes no requieren backfill de especificacion.
- Configuracion y conversacion pueden crearse al primer acceso.
- Evitar filas masivas si `get_or_create` es suficiente.
- Documentar cualquier backfill.

Pruebas de migracion:

1. Upgrade desde base vacia.
2. Cargar datos representativos anteriores.
3. Aplicar nueva migracion.
4. Verificar datos antiguos.
5. Crear datos nuevos.
6. Downgrade de una revision.
7. Confirmar que solo se retiran estructuras nuevas.
8. Upgrade otra vez.
9. Generar SQL con `alembic upgrade head --sql`.

No probar downgrade en la base real del usuario.

---

## 22. Seguridad y privacidad

- Autenticacion en toda ruta.
- Membresia antes de leer cualquier recurso.
- Permisos de proyecto antes de mutar.
- Consultas filtradas por proyecto autorizado.
- Nunca obtener un mensaje por UUID sin comprobar proyecto.
- Referencias UML restringidas al proyecto.
- Escapar contenido conversacional en interfaz.
- Limitar mensajes y metadatos.
- No registrar conversaciones completas, JWT o secretos.
- No guardar claves Ollama, Gemini, AWS, VAPID o BD.
- No agregar valores reales a `.env.example`.
- Verificar que `.env` siga ignorado.

Errores de dominio claros:

- Proyecto inaccesible.
- Configuracion invalida.
- Especificacion invalida.
- Referencia externa.
- Mensaje duplicado.
- Transicion invalida.
- Snapshot incompatible.
- Cursor invalido.

Los logs pueden incluir `project_id`, `correlation_id` y `event_id`, nunca contenido sensible completo.

---

## 23. Matriz de pruebas backend

### Modelos

- Relaciones y cascadas.
- Restricciones unicas.
- Defaults.
- Estados permitidos.
- JSONB normalizado.

### Metodos

- Crear y actualizar especificacion.
- Rechazar operacion invalida.
- Rechazar referencia externa.
- Mantener metodo antiguo.
- Serializar contratos Spring y Flutter.

### Configuracion IA

- Crear defaults al primer acceso.
- Evitar duplicados por proyecto.
- Lectura para miembro.
- Escritura restringida.
- Rechazar secretos o campos no permitidos.

### Conversacion

- Una conversacion por proyecto.
- `get_or_create` repetible.
- Secuencia monotona.
- Idempotencia por cliente.
- Paginacion anterior y posterior.
- Limite maximo.
- Aislamiento entre proyectos.
- Autor desde autenticacion.

### Concurrencia

- Dos mensajes simultaneos no comparten secuencia.
- Reintentos no duplican mensajes.
- Acciones aplicadas no se repiten.

### Acciones

- Crear propuesta.
- Validar estados.
- Rechazar transicion imposible.
- Rechazar confirmacion sin permiso.
- Coherencia entre resultado y error.

### Recomendaciones

- Crear y listar.
- Filtrar estado y severidad.
- Resolver con permiso.
- Rechazar referencias externas.

### Tema Flutter

- Defaults de proyecto antiguo.
- Persistencia y normalizacion.
- Rechazo de valores invalidos.
- PUT idempotente.
- Permisos.

### Snapshot

- Leer V1.
- Adaptar V1 a V2.
- Crear V2.
- Excluir conversaciones y secretos.
- Restaurar tema y configuracion.
- Rechazar version futura.

### Movil

- Listar solo proyectos accesibles.
- Resumen compacto correcto.
- Diagrama completo de lectura.
- Sin rutas de escritura movil.

### OpenAPI

- Rutas presentes.
- Esquemas presentes.
- Respuestas tipadas.
- Seguridad declarada.

---

## 24. Pruebas frontend

- Los tipos compilan.
- Adaptadores REST usan rutas y payloads exactos.
- Parser WebSocket acepta version 2.
- Eventos desconocidos no rompen conexion.
- No se introduce `any`.
- Fixtures reflejan JSON real de OpenAPI.
- Lint, pruebas y build de produccion pasan.

---

## 25. Orden obligatorio de trabajo

1. Auditar arquitectura y migraciones.
2. Registrar decisiones de modelado.
3. Definir enums y contratos Pydantic.
4. Implementar modelos SQLAlchemy.
5. Registrar metadata.
6. Crear migracion.
7. Implementar repositorios.
8. Implementar servicios y permisos.
9. Exponer solo endpoints reales.
10. Definir contratos WebSocket.
11. Agregar tipos TypeScript.
12. Implementar pruebas.
13. Probar migraciones en PostgreSQL.
14. Ejecutar suites completas.
15. Revisar OpenAPI y SQL.
16. Escanear secretos y archivos locales.
17. Documentar decisiones reales.

No comenzar por la interfaz. La fuente de verdad son los contratos y la persistencia.

---

## 26. Comandos de verificacion

Backend:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check app tests migrations
.\.venv\Scripts\alembic.exe upgrade head --sql
```

PostgreSQL de prueba:

```powershell
cd backend
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\alembic.exe downgrade -1
.\.venv\Scripts\alembic.exe upgrade head
```

Frontend:

```powershell
cd frontend
npm run lint
npm run test -- --run
npm run build
```

Repositorio:

```powershell
git diff --check
git status --short
```

---

## 27. Documentacion de implementacion

Crear al ejecutar la fase:

```text
docs/segundo_parcial/fase1/
    00_indice_fase1.md
    01_decisiones_modelado.md
    02_contratos_rest.md
    03_contratos_websocket.md
    04_modelo_persistencia.md
    05_migraciones_compatibilidad.md
    06_pruebas_fase1.md
    07_resumen_fase1.md
```

Documentar solo lo realmente implementado. Incluir Mermaid para entidades de IA, especificacion de metodos, snapshot y protocolo WebSocket.

---

## 28. Entregables

- Modelos SQLAlchemy y relaciones.
- Esquemas Pydantic.
- Repositorios y servicios.
- Routers REST reales.
- Contratos WebSocket.
- Migracion con downgrade.
- Registro de modelos y routers.
- Tipos TypeScript.
- Adaptadores frontend minimos.
- Pruebas backend y frontend.
- Documentacion de fase.

No es valido crear solo tablas sin servicios o tipos sin persistencia.

---

## 29. Casos de aceptacion

### Proyecto anterior

Abrir un proyecto previo, consultar metodo sin especificacion, recibir tema por defecto y crear conversacion perezosa. Nada anterior debe fallar.

### Aislamiento

Crear proyectos A y B. Un usuario miembro solo de A no puede leer configuracion, conversacion, acciones, tema o diagramas de B.

### Idempotencia

Enviar dos veces el mismo `client_message_id`. Debe existir un solo mensaje y ambas solicitudes deben identificar el mismo recurso.

### Concurrencia

Insertar dos mensajes simultaneos. Deben recibir secuencias diferentes y orden estable.

### Metodo visible

Crear `inscribirEstudiante(estudianteId, cursoId)`, marcarlo como `business_action` y `user_action`, guardar contratos backend y Flutter y recuperarlos sin perdida.

### Snapshot

Configurar tema e IA, crear conversacion y guardar version. El snapshot incluye tema y configuracion no sensible, pero no mensajes, secretos o suscripciones.

### Migracion reversible

Upgrade, creacion de datos nuevos, downgrade y upgrade. Las tablas del primer parcial permanecen intactas.

---

## 30. Prohibiciones

- No crear personalidades separadas.
- No guardar secretos.
- No aceptar autor desde el cliente.
- No usar secuencias inseguras.
- No incluir conversaciones en snapshots.
- No ejecutar acciones sin permisos.
- No simular Ollama.
- No romper metodos existentes.
- No duplicar validadores Flutter.
- No duplicar permisos.
- No usar JSONB sin esquema.
- No eliminar datos anteriores.
- No probar downgrade en produccion.
- No mezclar interfaces finales de fases posteriores.
- No declarar exito sin ejecutar pruebas.

---

## 31. Lista final de verificacion

- [ ] Arquitectura inspeccionada.
- [ ] Head de Alembic identificado.
- [ ] Especificacion uno a uno para metodos.
- [ ] Configuracion IA sin personalidades.
- [ ] Conversacion compartida.
- [ ] Mensajes con secuencia e idempotencia.
- [ ] Acciones con ciclo de vida.
- [ ] Recomendaciones persistentes.
- [ ] Tema Flutter persistente.
- [ ] Snapshot V2 compatible con V1.
- [ ] Conversaciones y secretos excluidos del snapshot.
- [ ] WebSocket versionado.
- [ ] Contratos moviles.
- [ ] Tipos TypeScript equivalentes.
- [ ] Permisos y aislamiento probados.
- [ ] Concurrencia probada.
- [ ] Upgrade y downgrade probados.
- [ ] OpenAPI correcto.
- [ ] Backend pasa pruebas y lint.
- [ ] Frontend pasa pruebas, lint y build.
- [ ] Sin credenciales.
- [ ] Documentacion consistente.

---

## 32. Informe final requerido

Al terminar la implementacion reportar:

1. Capacidades implementadas.
2. Modulos creados o modificados.
3. Migracion y `down_revision`.
4. Endpoints agregados.
5. Eventos WebSocket definidos.
6. Decisiones de compatibilidad.
7. Pruebas ejecutadas y resultados exactos.
8. Limitaciones reales para la Fase 2.

No afirmar que una prueba se ejecuto si solo se reviso codigo.

---

## 33. Resultado final esperado

CASE Inteligente debe quedar con una base contractual y persistente coherente para toda la segunda parte. Debe poder representar metodos con semantica suficiente para Spring Boot y Flutter, conservar una conversacion compartida, identificar mensajes y futuras acciones, guardar recomendaciones, persistir estilos, producir snapshots versionados y ofrecer datos de lectura para la PWA movil.

La IA real, la generacion semantica completa y las interfaces finales se implementaran en fases posteriores sin redisenar la persistencia ni romper los contratos creados aqui.
