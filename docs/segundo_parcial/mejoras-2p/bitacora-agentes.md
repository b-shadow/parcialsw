# Bitácora de Agentes — Mejoras 2.º Parcial

Registro cronológico de tareas ejecutadas por los agentes A1, A2, A3 y A4 en el proyecto CASE Inteligente (`parcialsw`).

---


## Ola 1 · Rebanadas Base

### [A3] V1.6 · Backend UML: validación de valores y XMI sin pérdida
- **Fecha:** 2026-10-20
- **Cambios realizados:**
  - `schemas/uml.py`: validadores y constantes Pydantic para `element_type` (`class`, `interface`, `enum`, `abstract_class`), `visibility` (`public`, `private`, `protected`, `package`), y `relationship_type` (`association`, `inheritance`, `aggregation`, `composition`, `dependency`, `realization`, `implementation`), respondiendo con 422 y mensajes claros en español.
  - `engine/xmi.py`:
    - En exportación: serialización de `isAbstract='true'` para clases abstractas, estereotipos `interface` y `enumeration`, visibilidades extendidas (`protected`, `package`), y elementos `UML:Dependency` y `UML:Abstraction` con sus respectivos tagged values de Enterprise Architect. Conservación de `aggregation='shared'` y `aggregation='composite'` en extremos de asociación.
    - En importación: lectura de `aggregation` en `AssociationEnd` preservando `composition` y `aggregation`; resolución segura de `UML:Dependency` y `UML:Abstraction` previniendo errores 500 (`AttributeError`); mapeo de `isAbstract` y estereotipos directos a `element_type`.
  - Escrita suite `backend/tests/test_mejoras_v1_editor_xmi.py` con 5 pruebas exhaustivas (validación 201/422, roundtrip completo con todos los elementos y visibilidades, importación real de `exportar.xml`, y prevención de error 500 en dependencias y abstracciones).
  - Suite completa del backend: 130 pasadas, 3 omitidas, 0 fallos.

### [A3] V1.5 · Editor: interfaz, enum, abstracta, dependencia, realización y visibilidades
- **Fecha:** 2026-10-20
- **Cambios realizados:**
  - `uml.ts`: ampliados tipos `UmlElementType` (`class`, `interface`, `enum`, `abstract_class`), `UmlVisibility` (`public`, `private`, `protected`, `package`), y `UmlRelationshipType` (`association`, `inheritance`, `aggregation`, `composition`, `dependency`, `realization`).
  - `ElementTypeSelect.tsx`: componente accesible para alternar el tipo de clasificador desde el panel de propiedades.
  - `JointUmlCanvas.tsx`:
    - Marcador visual `«interface»` y `«enumeration»` sobre el nombre de la clase.
    - Nombre de clase en cursiva (`italic`) para clases abstractas.
    - Omitido compartimento de métodos para clasificadores tipo `enum`.
    - Soporte completo para 4 visibilidades (`+`, `-`, `#`, `~`) en atributos y métodos.
    - Nuevos marcadores SVG y estilos de línea: dependencia (flecha abierta punteada) y realización (triángulo hueco punteado).
    - Prop `lockedElements` que renderiza borde ámbar punteado y píldora `🔒 {nombre} editando`.
  - `UmlEditorPage.tsx`:
    - Incorporadas herramientas de paleta `dependency` y `realization`.
    - Selector `ElementTypeSelect` en el panel de propiedades.
    - Modo literales y ocultamiento de métodos cuando el elemento seleccionado es `enum`.
  - `JointUmlCanvas.test.tsx`:
    - 5 nuevas pruebas unitarias: `interfaz muestra «interface» sobre el nombre`, `clase abstracta muestra el nombre en cursiva`, `visibilidades se dibujan como + - # ~`, `realización usa línea punteada con marcador de triángulo hueco`, y `lockedElements con la clase -> muestra candado con el nombre`.
  - Documentado en `docs/segundo_parcial/mejoras-2p/editor-uml.md`.
  - Pruebas Vitest: 61 pasadas; ESLint y Build de TypeScript en verde con código 0.

### [A2] V1.4 · Hook de permisos y PermissionGate en el frontend
- **Fecha:** 2026-10-20
- **Cambios realizados:**
  - Implementado `frontend/src/core/permissions/useProjectPermissions.ts`:
    - Cache en Zustand con TTL de 60 segundos indexado por `projectId`.
    - Deduplicación de peticiones en vuelo concurrentes para un mismo `projectId`.
    - Hook `useProjectPermissions(projectId)` que expone `{ role, can, loading, refresh }`.
    - Mientras `loading` está activo o no hay membresía, `can(code)` retorna `false`.
    - Método `refresh()` para invalidación forzada (ej. ante 403 PERMISSION_DENIED).
  - Implementado `frontend/src/core/permissions/PermissionGate.tsx`:
    - Componente declarativo que renderiza `children` solo cuando `can(code)` es `true`, renderizando `fallback` en caso contrario o mientras carga.
  - Escrita suite `frontend/src/core/permissions/useProjectPermissions.test.tsx`:
    - 4 pruebas unitarias: `mientras carga -> can() devuelve false`, `respuesta EDITOR -> can('uml.edit') true y can('members.manage') false`, `dos componentes con el mismo projectId -> una sola petición`, y `PermissionGate oculta children sin permiso y muestra fallback`.
  - Documentado en `docs/segundo_parcial/mejoras-2p/permisos.md`.
  - Vitest: 56 pruebas pasadas; ESLint y Build de TypeScript en verde con código 0.

### [A2] V1.3 · Permisos por rol aplicados en el backend (incluye Lector)
- **Fecha:** 2026-10-20
- **Cambios realizados:**
  - `permissions.py`: formalizados `PERMISSION_CODES` (11 códigos), `PROJECT_ROLES` (`ORGANIZADOR`, `EDITOR`, `LECTOR`), `ROLE_DEFAULTS` y cálculo de `effective_permissions`.
  - `project_validator.py`: implementados `ensure_project_permission(db, project_id, user_id, code)` y `member_permissions(db, member)`, manteniendo `ensure_organizer(member)` para compatibilidad con código existente.
  - `project_service.py`: método `my_membership(project_id, user_id)` retornando `{project_id, user_id, project_role, permissions}`, soporte de rol `LECTOR` en altas/ediciones de miembros, validación de códigos autorizados en `set_permission` (422 si inválido), y permisos `project.update`, `members.manage`, `versions.create`, `versions.restore`.
  - `projects.py`: expuesto `GET /{project_id}/members/me` posicionado antes de `{member_id}` para prevenir colisiones de ruta en FastAPI.
  - Servicios protegidos con permisos específicos:
    - `uml_service.py`: protegido con `uml.edit` en mutaciones (crear/editar/borrar clases, atributos, métodos, relaciones, posiciones, paquetes).
    - `action_execution_service.py`: protegido con `ai.confirm_actions` en confirmar/rechazar acciones propuestas por la IA.
    - `assistant_service.py`: protegido con `ai.settings` en configuración de IA y `ai.chat` en envío de mensajes.
    - `generation_service.py`: protegido con `generation.run` en disparar generación coordinada.
    - `theme_service.py`: protegido con `theme.edit` en crear/actualizar estilos y presets.
    - `method_specification_service.py`: protegido con `uml.edit` al guardar especificaciones.
  - Escrita suite `backend/tests/test_mejoras_v1_permisos.py` con 6 casos exhaustivos verificando permisos por rol y LECTOR.
  - Suite completa del backend: 124 pasadas, 3 omitidas, 0 fallos.

### [A1] V1.2 · Panel «Registro de cambios» en el espacio colaborativo
- **Fecha:** 2026-10-20
- **Cambios realizados:**
  - Implementado `frontend/src/modules/gestion_proyectos_colaboracion/services/changeLogService.ts` con método `list(projectId, params)`.
  - Creado `frontend/src/modules/gestion_proyectos_colaboracion/components/ChangeLogPanel.tsx` según `maqueta.html#registro`:
    - Timeline con avatar (`Avatar` de V0.5), nombre, summary, relative time (`Intl.RelativeTimeFormat 'es'`) y chips semánticos (`StatusBadge` con variantes `neutral`, `info`, `success`, `ai`).
    - Agrupación por días («Hoy», «Ayer», fecha formateada).
    - Filtro de integrantes con select poblado dinámicamente y filtros de tipo de cambio por chips («Todo», «Clases», «Relaciones», «IA», «Versiones», «Generación»).
    - Banner de advertencia «Registro en modo respaldo» cuando `source === 'postgres_fallback'`.
    - Paginación continua con botón «Cargar más» usando `next_cursor` como `before_id`.
    - Suscripción WebSocket a eventos `CHANGE_LOGGED` para anteponer entradas en tiempo real sin duplicar por `id`, y recarga con debounce en eventos `UML_EVENT`, `AI_ACTION_STATUS_CHANGED` y `PROJECT_VERSION_*`.
    - Integración de `EmptyState` y `Skeleton` para los diferentes estados de carga y vacío.
  - Actualizado `ProjectWorkspacePage.tsx` para integrar las pestañas «Chats del proyecto» y «Registro de cambios» acordes a la maqueta con soporte de `?tab=changelog`.
  - Escrita suite `frontend/src/modules/gestion_proyectos_colaboracion/components/ChangeLogPanel.test.tsx` (5/5 pruebas pasando).
  - Pruebas frontend completas: 52 pasadas, 0 fallos; lint y build limpios con código 0.

### [A1] V1.1 · Registro de cambios NoSQL con Redis Streams
- **Fecha:** 2026-10-20
- **Cambios realizados:**
  - Implementado `app/core/changelog/service.py` con `ChangeLogService`:
    - Escritura asíncrona no bloqueante en Redis Streams (`XADD` con límite `redis_change_log_maxlen`) en `case:changelog:project:{id}`.
    - Lectura paginada (`XREVRANGE`) con filtros por tipo de evento y miembro.
    - Respaldo / fallback automático contra PostgreSQL (`audit_logs`) cuando Redis no está disponible o para eventos históricos anteriores a la creación del stream.
  - Implementados hooks SQLAlchemy en `app/core/changelog/hooks.py` conectados tras cada commit para auditar automáticamente cambios de diagramas, clases, relaciones y miembros.
  - Creado script de retrollenado `app/core/changelog/backfill.py` (`backfill_project_changelog`).
  - Integrado hook en `AuditService.log_action` para replicar acciones de auditoría en Redis Streams.
  - Completado router `app/modules/proyectos_colaboracion/routers/change_log.py` con endpoint `GET /projects/{project_id}/change-log`.
  - Documentada la arquitectura en `docs/segundo_parcial/mejoras-2p/redis.md`.
  - Escrita suite `backend/tests/test_mejoras_v1_registro_cambios.py` (4/4 pruebas pasando).


### [A1] V0.1 · Migración única: timestamps, proveedor Gemini e índice de invitaciones
- **Fecha:** 2026-10-20
- **Rama:** `feat/m2p-a1-plataforma`
- **Cambios realizados:**
  - Creada migración Alembic `f1a2b3c4d5e6_mejoras_2p_base.py` con `down_revision = 'da4e5f6a7b8c'`.
  - Añadido `server_default=sa.text('now()')` en `coordinated_generations.created_at/updated_at` y `flutter_theme_presets.created_at/updated_at`.
  - Actualizado check constraint `ck_ai_project_settings_provider` para admitir `'ollama'`, `'gemini'` y `'rule_engine'`.
  - Creado índice parcial único `uq_project_invitations_pending` sobre `(project_id, lower(invited_email))` donde `status = 'pending'`.
  - Escrita prueba `test_mejoras_v0_migracion.py` con soporte para `CASE_TEST_DATABASE_URL` (skip seguro si no está definida).
  - Verificado `alembic heads` mostrando exactamente una cabeza: `f1a2b3c4d5e6`.

### [A1] V0.2 · Redis opcional: configuración, cliente y salud
- **Fecha:** 2026-10-20
- **Cambios realizados:**
  - Añadidos parámetros de configuración en `app/core/config/settings.py` (`redis_enabled`, `redis_url`, `redis_key_prefix`, `redis_change_log_maxlen`, `element_lock_ttl_seconds`, `ai_proactive_*`, `gemini_*`).
  - Creado cliente síncrono/asíncrono perezoso en `app/core/redis/client.py` con funciones `get_redis`, `get_async_redis`, `redis_key`, `redis_status` y `set_test_client`.
  - Creado `app/core/workers.py` con `start_background_workers` conectado al ciclo de vida `lifespan` de FastAPI.
  - Actualizado endpoint `/ready` en `app/main.py` para reportar el estado de Redis sin degradar el servicio si Redis está deshabilitado.
  - Actualizados `docker-compose.yml`, `docker-compose.prod.yml` y `backend/.env.example`.
  - Agregadas dependencias `redis` y `fakeredis` a `backend/pyproject.toml`.
  - Escrita suite `tests/test_mejoras_v0_redis.py` pasando 4/4 con `fakeredis`.

### [A1] V0.3 · Contratos compartidos: registro, permisos, eventos y tipos TS
- **Fecha:** 2026-10-20
- **Cambios realizados:**
  - Creado `app/core/changelog/contracts.py` con `PendingChange`, `ChangeLogEntry`, `ChangeLogPage`, `ACTION_LABELS` (45 acciones de auditoría) y `build_summary`.
  - Creado `app/core/changelog/hooks.py` con `install_change_log_hooks` y `queue_change`.
  - Creado `app/modules/proyectos_colaboracion/permissions.py` con `PERMISSION_CODES`, `PROJECT_ROLES` (`ORGANIZADOR`, `EDITOR`, `LECTOR`), `ROLE_DEFAULTS` y `effective_permissions`.
  - Añadidos eventos `'ELEMENT_LOCKED'`, `'ELEMENT_UNLOCKED'`, `'LOCK_REJECTED'`, `'CHANGE_LOGGED'` a `WsEventTypeV2` en backend y `ProjectSocketEventV2` en frontend.
  - Creado `frontend/src/core/contracts/mejoras2p.ts` y actualizado `phase1.ts`.

### [A1] V0.4 · Correcciones rápidas, routers vacíos y CLAUDE.md
- **Fecha:** 2026-10-20
- **Cambios realizados:**
  - Actualizada directiva Permissions-Policy con `microphone=(self)` en `frontend/nginx.conf` y `backend/app/core/security/headers.py`.
  - Corregida prueba de CORS en `backend/tests/test_second_part_phase9_quality_gates.py` usando `settings.cors_origins[0]`.
  - Implementado `_ensure_unique_class_name` en `UmlService` lanzando `409 CLASS_NAME_DUPLICATED` en `create_class` y `update_class`.
  - Creados routers vacíos `change_log.py` e `invitations.py` y registrados en `app/main.py`.
  - Creado `CLAUDE.md` en la raíz del monorepo.
  - Escrita suite `backend/tests/test_mejoras_v0_contratos.py` (6 pruebas pasando al 100%).
  - Configurado `--basetemp` en `pyproject.toml` para evitar el límite de MAX_PATH de Windows en pruebas de generación.
  - Suite completa del backend: 114 pasadas, 3 omitidas, 0 fallos.

### [A1] V0.5 · Componentes compartidos de interfaz según la maqueta
- **Fecha:** 2026-10-20
- **Cambios realizados:**
  - Creado `Toaster.tsx` y store zustand `useToast` con helpers `toast.success`, `toast.warning`, `toast.error`, auto-cierre a los 4s y límite de 4 avisos.
  - Creado `ConfirmDialog.tsx` y hook `useConfirm` con `ConfirmDialogHost` accesible (`role='dialog'`), soporte de escape y cierre exterior.
  - Creado `Avatar.tsx` y `PresenceStack` con colores estables por `userId` e icono robot para IA (`kind='ai'`).
  - Actualizado `StatusBadge.tsx` con tonos `'info'` y `'ai'`, soporte para `dot` y forma de píldora.
  - Creados `EmptyState.tsx` y `Skeleton.tsx` con soporte de modo oscuro y accesibilidad (`motion-safe:animate-pulse`).
  - Montados `<Toaster />` y `<ConfirmDialogHost />` en `AppLayout.tsx`.
  - Creada suite `sharedComponents.test.tsx` (6 pruebas pasando al 100%).
  - Suite de Vitest: 47 pasadas, 0 fallos.
  - Build y lint de React/TypeScript en verde sin errores.

### [A1] V1.1 · Registro de cambios NoSQL en Redis Streams y fallback
- **Fecha:** 2026-10-20
- **Cambios realizados:**
  - Implementado `RedisChangeLogService` con `xadd`, `xrevrange`, `xtrim` y paginación cursor.
  - Implementado `install_change_log_hooks` capturando mutaciones en `ProjectMutationGuard.advance`.
  - Implementado `backfill_from_audit` y router `change_log.py` con `GET /projects/{project_id}/changes`.
  - Suite de pruebas `test_mejoras_v1_registro_cambios.py` en verde.

### [A1] V1.2 · Panel de registro de cambios en el frontend
- **Fecha:** 2026-10-20
- **Cambios realizados:**
  - Implementado `changeLogService.ts` y componente `ChangeLogPanel.tsx` integrado en `ProjectWorkspacePage.tsx`.
  - Soporte para eventos WebSocket `CHANGE_LOGGED` en tiempo real y paginación continua.
  - Pruebas unitarias de frontend en verde.

### [A2] V1.3 · Roles y permisos granulares en backend
- **Fecha:** 2026-10-20
- **Cambios realizados:**
  - Implementado `ensure_project_permission`, `ensure_membership` y `ensure_organizer` en `project_validator.py`.
  - Agregado endpoint `GET /projects/{project_id}/members/me` retornando rol y lista de permisos efectivos.
  - Servicios protegidos: `uml.edit`, `ai.confirm_actions`, `ai.settings`, `ai.chat`, `generation.run`, `theme.edit`.
  - Suite de pruebas `test_mejoras_v1_permisos.py` con 124 pruebas pasando.

### [A2] V1.4 · Guardián de permisos y hook en frontend
- **Fecha:** 2026-10-20
- **Cambios realizados:**
  - Implementado `useProjectPermissions.ts` (store Zustand con TTL de 60s y deduplicación de peticiones).
  - Implementado componente `PermissionGate.tsx` para ocultar o deshabilitar elementos según permisos.
  - Documentada la arquitectura de permisos en `permisos.md`. Pruebas en verde.

### [A3] V1.5 · Editor UML colaborativo: Tipos y visualizaciones completas
- **Fecha:** 2026-10-20
- **Cambios realizados:**
  - Paleta enriquecida con `dependency` y `realization`, estereotipos `«interface»` y `«enumeration»`.
  - Visibilidades completas (`+`, `-`, `#`, `~`), clases abstractas en cursiva.
  - Bloqueos visuales con icono de candado y borde ámbar ante `lockedElements`.
  - Pruebas unitarias del editor en verde.

### [A3] V1.6 · Validación sintáctica y exportación/importación XMI sin pérdida
- **Fecha:** 2026-10-20
- **Cambios realizados:**
  - Validadores Pydantic 201/422 en español en `schemas/uml.py`.
  - Soporte completo de estereotipos, dependencias, realizaciones y visibilidades en importación/exportación XMI.
  - Resolución de errores 500 en nodos XMI vacíos o no tipados.
  - Suite `test_mejoras_v1_editor_xmi.py` en verde (21/21 pruebas).

### [A4] V1.7 · Proveedor Gemini opcional e intercambiable
- **Fecha:** 2026-10-20
- **Cambios realizados:**
  - Creado `GeminiProvider` en `ai_engine.providers` con soporte de salida estructurada JSON (`generateContent`), gestión de errores tipados, límite de reintentos y cabecera segura `x-goog-api-key`.
  - Modelo seleccionado por defecto: `gemini-2.5-flash` de Google AI Studio.
  - Actualizado `provider_factory.py` con `get_gemini_provider()` y función de resolución unificada `select_provider()`.
  - Actualizado `project_ai_application_service.py` para usar `select_provider` en `provider_health` e `interact`.
  - Permitido `'gemini'` en `AiProjectSettings` (CheckConstraint) y schemas Pydantic de configuración de IA.
  - Creadas suites de prueba `test_gemini_provider.py` (ai-engine) y `test_mejoras_v1_proveedor.py` (backend) con 100% de éxito usando `MockTransport`.
  - Documentado en `ia-proveedores.md`.

### [A4] V1.8 · Voz en el chat de IA y selector de proveedor
- **Fecha:** 2026-10-20
- **Cambios realizados:**
  - Implementado hook `useSpeechRecognition.ts` con manejo de resultados continuos/parciales, error handling en español (`not-allowed`, `no-speech`) y detección de soporte (`window.SpeechRecognition`).
  - Implementado componente `AiProviderSettings.tsx` con popover `role='radiogroup'`, consulta de `/ai/provider-health`, llamada a `updateAiSettings` y notificación con `toast.success`.
  - Actualizado `ProjectAiAssistant.tsx` matching `maqueta.html#asistente`:
    - Cabecera con píldora del proveedor y botón de ajustes restringido por `can('ai.settings')`.
    - Integración de `Avatar` en mensajes propios, de compañeros e IA.
    - Soporte para etiquetas «Dictado por voz» y tarjetas de «Sugerencia de la IA» ante mensajes proactivos.
    - Botones de confirmar/rechazar cambios protegidos por `can('ai.confirm_actions')`.
    - Compositor con botón de micrófono (oculto si no hay soporte), live region de dictado en curso e interruptor «Enviar al terminar de dictar».
  - Suite de pruebas `useSpeechRecognition.test.ts` con 4 pruebas pasando.
  - Vitest, eslint y build de TypeScript en verde.

### [A1] V2.1 · Consumidor del registro e IA proactiva
- **Fecha:** 2026-10-20
- **Cambios realizados:**
  - Implementado `ChangeLogConsumer` en `app/core/changelog/consumer.py` con grupo `case-workers` en stream global `case:changelog:all`, difusión en tiempo real de `CHANGE_LOGGED` vía WebSocket y confirmación `XACK`.
  - Integrado arranque controlado de background workers en `app/core/workers.py` vía lifespan de FastAPI según `redis_enabled` y `ai_proactive_enabled`.
  - Implementado `ProactiveAdvisorService` en `app/modules/asistente_proyecto/services/proactive_advisor_service.py` con detección de los 3 disparadores (acumulación de cambios, versión de proyecto, importación XMI), validación sintáctica del modelo UML con `validate_internal_model`, control de cooldown por proyecto (120 s) y descarte de eventos del sistema.
  - Creada suite de pruebas `test_mejoras_v2_proactivo.py` con 8 pruebas pasando al 100% con fakeredis.
  - Documentado en `ia-equipo.md`.

### [A1] V2.2 · IA consciente del equipo: autores y actividad por integrante
- **Fecha:** 2026-10-20
- **Cambios realizados:**
  - Enriquecidos contratos de contexto en `contracts.py`: agregado `author_display_name` a `RecentMessageContext`, nuevo modelo `TeamActivityItem`, y agregado `team_activity` a `AiProjectContext`.
  - Actualizado `ContextBuilder.build`: resolución de nombres reales de autores de mensajes recientes con `user_display_names`, agregación de las últimas 50 entradas del stream en `team_activity` agrupadas por integrante (máximo 10 acciones por persona) y aplicación de `ContextBudget(50000)`.
  - Ampliado `IntentClassifier`: añadidas frases de intención `coordinate_team` («que hizo cada», «quien cambio», «quien modifico», «resumen del equipo», «que esta haciendo», «reparte», «organiza el trabajo») con normalización resiliente a signos interrogativos (`¿`).
  - Implementado `RuleEngineProvider._coordinate_team_answer`: respuesta determinista estructurada por integrante («Ana: creó...; relacionó...») y detección de colisión de ediciones sobre la misma clase con recomendación proactiva de coordinación.
  - Actualizado prompt de sistema `unified_system.md` instruyendo a la IA a comportarse como un desarrollador integrante del equipo y moderar modificaciones concurrentes.
  - Creada suite `ai-engine/tests/test_mejoras_equipo.py` con 4 pruebas al 100% verde (67 pruebas totales en ai-engine sin regresiones).
  - Actualizada documentación en `ia-equipo.md`.

### [A2] V2.3 · Invitaciones al proyecto (backend)
- **Fecha:** 2026-10-21
- **Cambios realizados:**
  - Creados esquemas `InvitationCreateRequest` e `InvitationResponse` en `schemas/invitation.py`.
  - Implementado `InvitationRepository` en `repositories/invitation_repository.py` con búsquedas normalizadas (`func.lower(invited_email)`) y listados por estado y correo.
  - Implementado `InvitationService` en `services/invitation_service.py` con verificación de permisos `members.manage`, vencimiento a los 7 días con transición a `expired`, prevención de duplicados (`409 INVITATION_ALREADY_PENDING`, `409 MEMBER_ALREADY_EXISTS`), expiración en lectura y acciones de aceptar/rechazar con emisión de eventos durables en `NotificationService`.
  - Agregado método `add_member_from_invitation` a `ProjectService` reutilizando la lógica de miembros, auditoría con `origin='invitation'` y actividad.
  - Implementados routers `router` (`/projects/{id}/invitations`) y `my_router` (`/invitations`) en `routers/invitations.py` exponiendo los 6 endpoints requeridos.
  - Creada suite de pruebas `test_mejoras_v2_invitaciones.py` con 9 pruebas pasando al 100% (152 pruebas de backend en verde).
  - Actualizada documentación en `permisos.md`.
