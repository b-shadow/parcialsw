# Bitácora de Agentes — Mejoras 2.º Parcial

Registro cronológico de tareas ejecutadas por los agentes A1, A2, A3 y A4 en el proyecto CASE Inteligente (`parcialsw`).

---


## Ola 1 · Rebanadas Base

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
