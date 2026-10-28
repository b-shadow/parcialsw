# Plan de trabajo: Mejoras 2.º parcial

- **Proyecto:** CASE Inteligente (parcialsw)
- **Fecha y versión:** 2026-10-20 · v1.1
- **Alcance:** Apuntes del docente del 13-10 (IA como un desarrollador más, registro de cambios en NoSQL con Redis, roles y permisos, versiones con push), corrección de los bugs encontrados y mejoras clave del 1.er parcial: voz en el chat de IA, invitaciones, editor UML completo con bloqueos, generador JPA completo con Postman y Gemini como proveedor opcional
- **Stack:** FastAPI + SQLAlchemy 2 + Alembic + PostgreSQL 16 · Redis (Streams, claves con TTL) · React 19 + Vite 6 + TypeScript + zustand · ai-engine Python (Ollama/Qwen + reglas, Gemini opcional) · generadores Spring Boot y Flutter
- **Raíz del código:** `parcialsw/`
- **Maqueta:** https://claude.ai/artifact/QvUJFcSkUq7Hpemwt68LYu
- **Fuente:** Clon de main en 77463ce (19-10-2026): pytest backend 103/104, pytest ai-engine 58/59, vitest 41/41, lint y build en verde; alembic upgrade head sobre PostgreSQL 16 limpio; prueba manual por API del chat compartido con 2 usuarios, confirmación de acciones IA, preflight y generación coordinada; Spring Boot generado compilado con Maven. No se verificó: Ollama real, Flutter (móvil y generado), Playwright e2e ni dispositivo físico. Maqueta v1 (20-10-2026) construida sobre capturas reales de la app

## 1. Diagnóstico

- **[info] Maqueta de las pantallas nuevas.** maqueta.html reproduce el sistema visual actual (tomado de frontend/src/styles.css y capturas de la app) y define 6 pantallas: editor colaborativo, asistente del equipo, registro de cambios, integrantes y permisos, mis invitaciones y componentes compartidos. Incluye un selector de rol (Organizador, Editor, Lector) para ver qué oculta cada permiso.
- **[ok] Fases 1–9 del colega en código.** Commit 77463ce (19-10): 607 archivos. Pruebas: backend 103/104 (la que falla compara CORS con un dominio fijo de Vercel), ai-engine 58/59 (OCR de foto manuscrita, depende de la versión de Tesseract), frontend 41/41; lint y build PWA en verde.
- **[ok] Chat de IA compartido y con acciones.** Probado por API con dos usuarios: ambos ven la misma conversación con autor; la IA propuso 3 acciones (crear clase y 2 atributos) y al confirmarlas quedaron en el diagrama. Sin Ollama cae al motor de reglas.
- **[ok] Spring Boot generado compila.** El gate CASE_VERIFY_GENERATED_SPRING=1 pasa y un proyecto generado desde un diagrama de prueba compiló con mvn test (exit 0).
- **[bloq] Generación coordinada y presets dan 500.** Tras alembic upgrade head, coordinated_generations y flutter_theme_presets tienen created_at/updated_at NOT NULL sin DEFAULT: POST /generation/coordinated y guardar un preset fallan con NotNullViolation. Las pruebas no lo detectan porque no usan la base migrada.
- **[bloq] Nada se guarda en NoSQL.** El docente pide el registro de cambios en NoSQL. Hoy todo está en PostgreSQL. Decisión: Redis Streams para el registro de cambios por proyecto, Redis para bloqueos y contadores; PostgreSQL sigue como fuente de verdad y audit_logs como auditoría de seguridad.
- **[bloq] Micrófono bloqueado en producción.** Permissions-Policy microphone=() en frontend/nginx.conf y backend/app/core/security/headers.py: la voz no funciona desplegada.
- **[warn] La IA solo responde cuando le preguntan.** No propone ideas por iniciativa propia. El contexto no incluye el autor de los mensajes recientes ni la actividad de cada integrante, así que no puede decir qué hizo cada desarrollador (pedido del docente).
- **[warn] Permisos por proyecto sin aplicar.** project_permissions solo se usa como contexto para la IA; los servicios solo distinguen miembro/organizador. No existe rol Lector.
- **[warn] Sin invitaciones.** La tabla project_invitations existe sin uso; el organizador agrega integrantes elegidos de una lista de todos los usuarios.
- **[warn] Editor UML incompleto.** Herramientas: clase, asociación, herencia, agregación, composición y clase asociación. Faltan interfaz, enum, clase abstracta, dependencia, realización, visibilidades # y ~ y deshacer/rehacer. Se pueden crear dos clases con el mismo nombre. El XMI importa agregación y composición como asociación.
- **[warn] Sin bloqueo de elementos.** Hay presencia por proyecto, pero dos usuarios pueden editar la misma clase a la vez (gana el último).
- **[warn] Generador Spring Boot incompleto.** Solo @ManyToOne; composición sin cascade/orphanRemoval; herencia y enum descartados; sin colección Postman ni data.sql.
- **[warn] Voz fuera del chat de IA.** SpeechRecognition se usa en el editor y al crear proyecto, pero no en el asistente del proyecto.
- **[info] Apuntes del docente (13-10).** Se basa en el 1.er parcial y nada debe fallar. IA: un desarrollador más, propone ideas, es visible, se le pide que agregue o ayude; un solo modelo e instancia para todo el equipo, identifica qué hace cada dev, chat grupal con contexto, moderador y asesor que realiza acciones; la aplicación es intermediaria. IA local valorable (o la convencional de AI Studio). Lo que se almacena en NoSQL con registro de cambios. Versiones y control de versiones con notificaciones push. Móvil más informativo. Roles y permisos.
- **[info] Una sola cabeza de migraciones.** Todas las migraciones del plan se concentran en V0.1 (ola 0) para que los 4 agentes no creen cabezas Alembic paralelas. Cabeza actual: da4e5f6a7b8c.
- **[info] Archivos compartidos entre olas (avisos aceptados).** uml_service.py lo tocan A1 (ola 0: nombres duplicados), A2 (ola 1: permisos) y A3 (ola 2: guarda de bloqueo), nunca en la misma ola y cada uno en funciones distintas. invitations.py lo crea vacío A1 en la ola 0 para registrarlo en main.py y lo completa A2 en la ola 2. Son los 3 avisos del generador del plan.
- **[info] Redis en Windows.** Para desarrollo: Memurai Developer, Redis dentro de WSL o docker compose up -d redis. Pruebas con fakeredis. Producción: servicio redis con appendonly yes.
- **[info] No verificado (supuestos).** Ollama con Qwen real, la app móvil y el Flutter generado (no hay SDK en el entorno de revisión), las pruebas Playwright (sus capturas son de win32) y la prueba en un teléfono.

## 2. Agentes

| ID | Nombre | Rol | Rama |
|---|---|---|---|
| A1 | Plataforma y registro de cambios | Cimientos (migración, Redis, contratos), registro de cambios en Redis Streams, IA proactiva y consciente del equipo, prueba integral final. | feat/m2p-a1-plataforma |
| A2 | Roles, permisos e invitaciones | Permisos por rol de proyecto (incluye Lector), invitaciones por correo con notificación, documentación de casos de uso. | feat/m2p-a2-permisos |
| A3 | Editor UML colaborativo | Editor UML completo, XMI sin pérdida, bloqueo de elementos, presencia de la IA, deshacer/rehacer, guion de demo. | feat/m2p-a3-editor |
| A4 | IA y generación | Proveedor Gemini opcional, voz en el chat de IA, generador Spring Boot con relaciones JPA completas, Postman y datos semilla, verificación de toolchains. | feat/m2p-a4-ia-generacion |

## 3. Olas

Una ola empieza cuando la anterior se une a la rama principal.

- **Ola 0 · Cimientos** — agentes A1; tareas V0.1, V0.2, V0.3, V0.4, V0.5. Salida: Migración única aplicada sin errores 500, Redis configurado y opcional, contratos compartidos (registro, permisos, eventos WS, tipos TS), routers vacíos registrados, micrófono permitido y CLAUDE.md.
- **Ola 1 · Rebanadas base** — agentes A1, A2, A3, A4; tareas V1.1, V1.2, V1.3, V1.4, V1.5, V1.6, V1.7, V1.8. Salida: Registro de cambios en Redis con panel; permisos por rol aplicados; editor con todos los tipos UML y XMI sin pérdida; Gemini opcional y voz en el chat.
- **Ola 2 · IA del equipo y colaboración** — agentes A1, A2, A3, A4; tareas V2.1, V2.2, V2.3, V2.4, V2.5, V2.6, V2.7, V2.8, V2.9. Salida: IA proactiva y consciente de quién hizo qué; invitaciones con notificación; bloqueo de elementos y deshacer; generador JPA completo con Postman y semilla.
- **Ola 3 · Integración y entrega** — agentes A1, A2, A3, A4; tareas V3.1, V3.2, V3.3, V3.4. Salida: Flujo de demo probado de punta a punta, documentación de CU nuevos y trazabilidad, guion con capturas y verificación de Ollama, Maven y Flutter en el equipo de demo.

## 4. Contratos

Nombres que nadie cambia sin acuerdo.

### Pantallas de la maqueta

| Pantalla | Ancla en maqueta.html | Ruta de la app | Archivos React | Tareas |
|---|---|---|---|---|
| Editor colaborativo | #editor | /proyectos/:projectId/uml/:diagramId | UmlEditorPage.tsx · JointUmlCanvas.tsx · ElementTypeSelect.tsx · useElementLocks.ts · umlHistory.ts | V1.5 · V2.6 · V2.7 |
| Asistente del equipo | #asistente | pestaña Asistente del editor | ProjectAiAssistant.tsx · AiProviderSettings.tsx · useSpeechRecognition.ts | V1.8 (contenido de V2.1 y V2.2) |
| Registro de cambios | #registro | /proyectos/:projectId/colaborativo | ProjectWorkspacePage.tsx · ChangeLogPanel.tsx | V1.2 |
| Integrantes y permisos | #gestion | /proyectos/:projectId | ProjectManagementPage.tsx (con PermissionGate) | V1.4 · V2.4 |
| Mis invitaciones y campana | #invitaciones | /proyectos y cabecera | ProjectsPage.tsx · NotificationCenter.tsx | V2.4 |
| Presencia con la IA | cabecera de cualquier pantalla | todas | ProjectPresenceIndicator.tsx | V2.6 |
| Componentes compartidos | #componentes | — | shared/components/Toaster.tsx · ConfirmDialog.tsx · Avatar.tsx · StatusBadge.tsx · EmptyState.tsx · Skeleton.tsx | V0.5 |

### Textos de la interfaz

- `Se copian literalmente de la maqueta (las pruebas los buscan).`
- `Toasts: «3 cambios aplicados» · «Invitación enviada» · «Invitación revocada» · «Te uniste a {proyecto}» · «Invitación rechazada» · «Proveedor actualizado» · «Rol actualizado» · «Deshecho: {acción}» · «Rehecho: {acción}» · «Nueva sugerencia de la IA» · «{nombre} está editando {elemento}».`
- `Avisos fijos: «Modo solo lectura: tu rol en este proyecto es Lector. Puedes consultar el diagrama y preguntar al asistente.» · «Registro en modo respaldo: Redis no responde y se muestra la auditoría de PostgreSQL. Los cambios se siguen guardando.» · «Solo el Organizador puede invitar y cambiar roles. Puedes ver quién participa.» · «Solo Organizador y Editor pueden confirmar cambios.»`
- `Asistente: «Sugerencia de la IA» · «Dictado por voz» · «Escuchando…» · «Enviar al terminar de dictar» · «Asistente disponible» / «Asistente pensando…» · botón «Confirmar {n} cambios» / «Rechazar».`
- `Bloqueo: píldora «{nombre} editando» sobre la clase; nota «{nombre} está editando este elemento. Podrás editarlo cuando lo libere.»`
- `Errores de formulario: «Escribe un correo válido, por ejemplo persona@correo.com.» · «Ya hay una invitación pendiente para ese correo.»`
- `ConfirmDialog de revocar: título «¿Revocar la invitación?», texto «{correo} ya no podrá unirse con esta invitación. Puedes invitarle de nuevo después.», botones «Cancelar» y «Revocar».`

### Endpoints nuevos

| Método | Ruta | Entrada | Respuesta | Permiso | Dueño |
|---|---|---|---|---|---|
| GET | /api/v1/projects/{project_id}/change-log | query: before_id?: str, limit: int = 50 (1..100), actor_id?: UUID, entity_type?: str | 200 ChangeLogPage | project.read | A1 |
| GET | /api/v1/projects/{project_id}/members/me | — | 200 MyMembershipResponse {project_id, user_id, project_role, permissions: list[str]} | project.read | A2 |
| POST | /api/v1/projects/{project_id}/invitations | InvitationCreateRequest {email, project_role: 'EDITOR'\|'LECTOR'} | 201 InvitationResponse | members.manage | A2 |
| GET | /api/v1/projects/{project_id}/invitations | query: status?: 'pending'\|'accepted'\|'rejected'\|'revoked'\|'expired' | 200 list[InvitationResponse] | members.manage | A2 |
| DELETE | /api/v1/projects/{project_id}/invitations/{invitation_id} | — | 204 (estado revoked) | members.manage | A2 |
| GET | /api/v1/invitations/me | — | 200 list[InvitationResponse] pendientes del correo del usuario | autenticado | A2 |
| POST | /api/v1/invitations/{invitation_id}/accept | — | 200 ProjectMemberResponse | invitado | A2 |
| POST | /api/v1/invitations/{invitation_id}/reject | — | 200 InvitationResponse | invitado | A2 |
| GET | /ready | — | 200 {status, database, redis: 'available'\|'unavailable'\|'disabled'} | público | A1 |

### Errores

| HTTP | detail.code | detail.message | Quién lo lanza |
|---|---|---|---|
| 403 | PERMISSION_DENIED | No tienes permiso para esta acción en el proyecto | ensure_project_permission (A2) |
| 409 | CLASS_NAME_DUPLICATED | Ya existe una clase con ese nombre en el diagrama | UmlService.create_class / update_class (A1 en V0.4) |
| 409 | INVITATION_ALREADY_PENDING | Ya existe una invitación pendiente para ese correo | InvitationService (A2) |
| 409 | MEMBER_ALREADY_EXISTS | El usuario ya es integrante del proyecto | InvitationService (A2) |
| 410 | INVITATION_EXPIRED | La invitación venció | InvitationService (A2) |
| 404 | INVITATION_NOT_FOUND | Invitación no encontrada | InvitationService (A2) |
| 423 | ELEMENT_LOCKED | {display_name} está editando este elemento | UmlService guardas (A3) |
| Formato | HTTPException(status_code, detail={'code': ..., 'message': ...}) | igual que ProjectService._domain_error | todos |

### Permisos por rol

| Código | Permite | ORGANIZADOR | EDITOR | LECTOR |
|---|---|---|---|---|
| project.read | Ver proyecto, diagramas, versiones, registro y chat | sí | sí | sí |
| project.update | Editar nombre/descripción, archivar o eliminar el proyecto | sí | no | no |
| members.manage | Invitar, cambiar rol, retirar integrantes y otorgar permisos | sí | no | no |
| uml.edit | Crear, editar y eliminar elementos UML, importar XMI | sí | sí | no |
| versions.create | Guardar versiones | sí | sí | no |
| versions.restore | Restaurar versiones | sí | no | no |
| ai.chat | Escribir al asistente del proyecto | sí | sí | sí |
| ai.confirm_actions | Confirmar o rechazar acciones propuestas por la IA | sí | sí | no |
| ai.settings | Cambiar proveedor y ajustes de la IA del proyecto | sí | no | no |
| generation.run | Transformar, generar y descargar Spring Boot y Flutter | sí | sí | no |
| theme.edit | Editar tema y presets Flutter | sí | sí | no |
| Regla | Permisos efectivos = ROLE_DEFAULTS[project_role] ∪ códigos de project_permissions del integrante | — | — | — |

### Claves Redis

| Clave (prefijo REDIS_KEY_PREFIX = 'case') | Tipo | Límite / TTL | Escribe | Lee |
|---|---|---|---|---|
| case:changelog:project:{project_id} | Stream | MAXLEN ~ REDIS_CHANGE_LOG_MAXLEN (10000) | ChangeLogService.flush (A1) | GET change-log, ContextBuilder (A1) |
| case:changelog:all | Stream | MAXLEN ~ 50000 | ChangeLogService.flush (A1) | ChangeLogConsumer, grupo 'case-workers' (A1) |
| case:lock:{project_id}:{element_type}:{element_id} | String JSON {user_id, display_name, expires_at} | PX = ELEMENT_LOCK_TTL_SECONDS*1000 (60 s) | ElementLockService (A3) | ElementLockService, UmlService (A3) |
| case:proactive:{project_id}:cooldown | String '1' | EX AI_PROACTIVE_COOLDOWN_SECONDS (120) | ProactiveAdvisorService (A1) | ProactiveAdvisorService (A1) |
| case:proactive:{project_id}:pending | Contador INCR | EX 3600 | ProactiveAdvisorService (A1) | ProactiveAdvisorService (A1) |

### Entrada del registro (ChangeLogEntry)

- `Campos del Stream (todos str): project_id, occurred_at (ISO 8601 UTC), actor_user_id ('' si sistema), source ('ui'|'ai'|'ws'|'system'), module, action, entity_type, entity_id, diagram_id, summary (≤ 200, español), metadata (JSON saneado ≤ 2048 bytes).`
- `Pydantic ChangeLogEntry (backend/app/core/changelog/contracts.py): id: str (id del Stream) · project_id: UUID · occurred_at: datetime · actor_user_id: UUID | None · actor_display_name: str | None (lo completa el endpoint) · source: Literal['ui','ai','ws','system'] · module: str · action: str · entity_type: str | None · entity_id: str | None · diagram_id: UUID | None · summary: str · metadata: dict.`
- `ChangeLogPage: items: list[ChangeLogEntry] · next_cursor: str | None (id del último item si hay más) · source: Literal['redis','postgres_fallback'].`
- `ACTION_LABELS: dict[str, str] en contracts.py con la etiqueta en español de cada acción de auditoría real (CREATE_CLASS → 'Creó la clase', UPDATE_CLASS → 'Editó la clase', DELETE_CLASS → 'Eliminó la clase', CREATE_RELATION → 'Relacionó clases', CREATE_PROJECT_VERSION → 'Guardó una versión', RESTORE_PROJECT_VERSION → 'Restauró una versión', IMPORT_XMI → 'Importó un XMI', GENERATE_COORDINATED → 'Generó Spring Boot y Flutter', ADD_PROJECT_MEMBER → 'Agregó un integrante', …; las 43 acciones de AuditService). summary = etiqueta + nombre si metadata trae name/class_name/target_name.`
- `Origen IA: ActionExecutionService (A2, V1.3) pone db.info['change_origin'] = 'ai' antes de ejecutar una acción confirmada y lo quita en un finally; AuditService (A1, V1.1) lo lee para marcar source='ai'.`
- `source: 'ai' si db.info['change_origin'] == 'ai'; 'system' si no hay actor; 'ui' en el resto (los eventos UML_EVENT del socket no se registran aparte porque cada cambio ya pasa por AuditService).`

### Eventos WebSocket

| Tipo | Dirección | Payload | Emite | Consume |
|---|---|---|---|---|
| LOCK_ELEMENT | cliente → servidor (v1 plano) | {type, diagram_id, element_type: 'class'\|'relationship', element_id} | UmlEditorPage al seleccionar y cada 20 s mientras edita (A3) | router.py (A3) |
| UNLOCK_ELEMENT | cliente → servidor | {type, diagram_id, element_type, element_id} | UmlEditorPage al deseleccionar (A3) | router.py (A3) |
| ELEMENT_LOCKED | servidor → todos (v2, persistent=false) | {diagram_id, element_type, element_id, locked_by: {user_id, display_name}, expires_at} | router.py (A3) | UmlEditorPage, JointUmlCanvas (A3) |
| ELEMENT_UNLOCKED | servidor → todos (v2, persistent=false) | {diagram_id, element_type, element_id, reason: 'released'\|'expired'\|'disconnected'} | router.py (A3) | UmlEditorPage (A3) |
| LOCK_REJECTED | servidor → solicitante (v2, persistent=false) | {diagram_id, element_type, element_id, locked_by: {user_id, display_name}} | router.py (A3) | UmlEditorPage: toast (A3) |
| CHANGE_LOGGED | servidor → todos (v2, persistent=false, sequence_number=0) | ChangeLogEntry con actor_display_name | ChangeLogConsumer (A1, ola 2) | ChangeLogPanel (A1) |
| AI_MESSAGE_CREATED (existente) | servidor → todos | message.metadata_json.kind = 'proactive', metadata_json.trigger = 'changes'\|'version'\|'import' | ProactiveAdvisorService (A1) | ProjectAiAssistant: etiqueta «Sugerencia de la IA» (A4) |

### Variables de entorno

| Variable | Campo en Settings | Por defecto | Uso |
|---|---|---|---|
| REDIS_ENABLED | redis_enabled: bool | false | Activa Redis; con false todo funciona como hoy |
| REDIS_URL | redis_url: str | redis://127.0.0.1:6379/0 | Conexión (sin contraseña en el repo) |
| REDIS_KEY_PREFIX | redis_key_prefix: str | case | Prefijo de todas las claves |
| REDIS_CHANGE_LOG_MAXLEN | redis_change_log_maxlen: int | 10000 | Recorte aproximado del Stream por proyecto |
| ELEMENT_LOCK_TTL_SECONDS | element_lock_ttl_seconds: int | 60 | Vida de un bloqueo sin renovar |
| AI_PROACTIVE_ENABLED | ai_proactive_enabled: bool | true | Sugerencias por iniciativa de la IA |
| AI_PROACTIVE_MIN_CHANGES | ai_proactive_min_changes: int | 5 | Cambios acumulados antes de revisar |
| AI_PROACTIVE_COOLDOWN_SECONDS | ai_proactive_cooldown_seconds: int | 120 | Mínimo entre dos sugerencias por proyecto |
| GEMINI_API_KEY | gemini_api_key: str \| None | None | Clave de Google AI Studio, solo en .env |
| GEMINI_MODEL | gemini_model: str | (V1.7 lo fija tras verificar el id vigente en la documentación de AI Studio) | Modelo Gemini |
| GEMINI_BASE_URL | gemini_base_url: str | https://generativelanguage.googleapis.com | API REST de Gemini |

### Tipos TypeScript

- `frontend/src/core/contracts/mejoras2p.ts (V0.3):`
- `export type PermissionCode = "project.read" | "project.update" | "members.manage" | "uml.edit" | "versions.create" | "versions.restore" | "ai.chat" | "ai.confirm_actions" | "ai.settings" | "generation.run" | "theme.edit";`
- `export type ProjectRole = "ORGANIZADOR" | "EDITOR" | "LECTOR";`
- `export type MyMembership = { project_id: string; user_id: string; project_role: ProjectRole; permissions: PermissionCode[] };`
- `export type ChangeLogEntry = { id: string; project_id: string; occurred_at: string; actor_user_id: string | null; actor_display_name: string | null; source: "ui" | "ai" | "ws" | "system"; module: string; action: string; entity_type: string | null; entity_id: string | null; diagram_id: string | null; summary: string; metadata: Record<string, unknown> };`
- `export type ChangeLogPage = { items: ChangeLogEntry[]; next_cursor: string | null; source: "redis" | "postgres_fallback" };`
- `export type InvitationStatus = "pending" | "accepted" | "rejected" | "revoked" | "expired";`
- `export type ProjectInvitation = { id: string; project_id: string; project_name: string; invited_email: string; project_role: Exclude<ProjectRole, "ORGANIZADOR">; status: InvitationStatus; invited_by_name: string; expires_at: string; created_at: string };`
- `export type ElementLock = { diagram_id: string; element_type: "class" | "relationship"; element_id: string; locked_by: { user_id: string; display_name: string }; expires_at: string };`
- `export type AiProvider = "ollama" | "gemini" | "rule_engine"; (y AiProjectSettings.preferred_provider en phase1.ts pasa a AiProvider)`
- `ProjectSocketEventV2.type en phase1.ts agrega: "ELEMENT_LOCKED" | "ELEMENT_UNLOCKED" | "LOCK_REJECTED" | "CHANGE_LOGGED".`

### Firmas compartidas

- `backend/app/core/redis/client.py: get_redis() -> redis.Redis | None · get_async_redis() -> redis.asyncio.Redis | None · redis_key(*parts: str) -> str · redis_status() -> Literal['available','unavailable','disabled']`
- `backend/app/core/changelog/service.py: queue_change(db: Session, entry: PendingChange) -> None · ChangeLogService().list_project(project_id, *, before_id, limit, actor_id, entity_type) -> ChangeLogPage`
- `backend/app/modules/proyectos_colaboracion/permissions.py: PERMISSION_CODES: frozenset[str] · ROLE_DEFAULTS: dict[str, frozenset[str]] · effective_permissions(member: ProjectMember, granted: Iterable[str]) -> frozenset[str]`
- `backend/app/modules/proyectos_colaboracion/validators/project_validator.py: ensure_project_permission(db: Session, project_id: UUID, user_id: UUID, code: str) -> ProjectMember`
- `backend/app/websocket/locks.py: ElementLockService.acquire(project_id, element_type, element_id, user_id, display_name) -> tuple[bool, dict] · release(...) -> bool · holder(...) -> dict | None · release_all_for_user(project_id, user_id) -> list[dict]`
- `frontend/src/core/permissions/useProjectPermissions.ts: useProjectPermissions(projectId?: string) -> { role: ProjectRole | null; can: (code: PermissionCode) => boolean; loading: boolean; refresh: () => Promise<void> }`
- `frontend/src/core/voice/useSpeechRecognition.ts: useSpeechRecognition(options?: { lang?: string; onFinal?: (text: string) => void }) -> { supported: boolean; listening: boolean; interim: string; start(): void; stop(): void; error: string | null }`

### Componentes compartidos (V0.5)

- `Toaster.tsx: export const useToast = create<ToastState>() · toast.success(title: string, text?: string) · toast.warning(...) · toast.error(...) · <Toaster /> montado una vez en AppLayout (aria-live='polite', se cierra a los 4 s, botón «Cerrar aviso»).`
- `ConfirmDialog.tsx: export function useConfirm(): (opts: { title: string; description: string; confirmLabel: string; tone?: 'danger' | 'primary' }) => Promise<boolean> · <ConfirmDialogHost /> montado en AppLayout (foco en Cancelar, Escape cierra, clic fuera cancela).`
- `Avatar.tsx: export function Avatar({ name, userId, kind = 'user', size = 'md' }: { name: string; userId?: string; kind?: 'user' | 'ai'; size?: 'sm' | 'md' }) · color estable por userId entre 6 clases Tailwind (teal-700, blue-600, purple-600, rose-600, amber-600, sky-700) · export function PresenceStack({ people, max = 4 }).`
- `StatusBadge.tsx (existente): tone agrega 'info' | 'ai'; nueva prop dot?: boolean; forma de píldora (rounded-full) como en la maqueta.`
- `EmptyState.tsx: export function EmptyState({ icon, title, description, action }: { icon: ReactNode; title: string; description: string; action?: ReactNode }).`
- `Skeleton.tsx: export function Skeleton({ className }: { className?: string }) con animación desactivada si prefers-reduced-motion.`

## 5. Vista por vista

### Chat del equipo con la IA (CU19 · CU23 · CU24) — /proyectos/:projectId/uml/:diagramId (asistente flotante) · A4 + A1

| Carril | Documento | Qué contiene | Archivo |
|---|---|---|---|
| Ruta / WS | POST …/ai/interactions | Evento AI_MESSAGE_CREATED con kind proactive | backend/app/modules/asistente_proyecto/routers/assistant.py |
| Servicio | Asesor proactivo · contexto · Gemini | Sugerencias por iniciativa y actividad por integrante | backend/app/modules/asistente_proyecto/services/ |
| Datos | ai_messages y registro Redis | metadata kind y Stream por proyecto | backend/app/core/changelog/ |
| Interfaz | Asistente del proyecto | Micrófono, sugerencias y selector de proveedor | frontend/src/modules/gestion_proyectos_colaboracion/components/ProjectAiAssistant.tsx |

**Flujo:**

1. **Ana (editor)** — `Clic en el micrófono y dicta «agrega la clase Factura con total de tipo Double»` — useSpeechRecognition muestra el texto parcial; al terminar lo envía como interacción
2. **Backend** — `POST /projects/{id}/ai/interactions` — ContextBuilder agrega autores de mensajes y team_activity desde Redis; el proveedor elegido (Ollama, Gemini o reglas) devuelve un plan
3. **Beto (editor)** — `Ve el mensaje de Ana y la propuesta en tiempo real` — Puede confirmar (ai.confirm_actions) o comentar
4. **IA** — `Tras 5 cambios del equipo, sin que nadie pregunte` — ChangeLogConsumer → ProactiveAdvisorService valida el diagrama y publica «Sugerencia de la IA» con recomendaciones
5. **Beto** — `Pregunta «¿qué hizo cada uno hoy?»` — Intención coordinate_team: la IA resume por integrante usando el registro de cambios

**Alternos:**

- Navegador sin SpeechRecognition: el botón se oculta y aparece «Tu navegador no admite dictado; usa Chrome o Edge».
- Permiso de micrófono denegado: toast «Permite el micrófono para dictar» y el botón vuelve a estado normal.
- Lector: puede preguntar (ai.chat) pero los botones Confirmar/Rechazar no aparecen.
- Gemini sin GEMINI_API_KEY: el selector muestra el proveedor deshabilitado y el backend usa reglas.

### Registro de cambios del proyecto (CU22) — /proyectos/:projectId/colaborativo · A1

| Carril | Documento | Qué contiene | Archivo |
|---|---|---|---|
| Ruta / WS | GET …/change-log | Paginación por id del Stream y evento CHANGE_LOGGED | backend/app/modules/proyectos_colaboracion/routers/change_log.py |
| Servicio | Servicio del registro | Encola en la sesión y escribe en Redis tras el commit | backend/app/core/changelog/service.py |
| Datos | Redis Streams (NoSQL) | Un Stream por proyecto y uno global | backend/app/core/redis/client.py |
| Interfaz | Panel de registro | Línea de tiempo con filtros por integrante y tipo | frontend/src/modules/gestion_proyectos_colaboracion/components/ChangeLogPanel.tsx |

**Flujo:**

1. **Servicio de dominio** — `AuditService.record(project_id=…)` — Además de audit_logs, llama queue_change(db, …): queda pendiente en db.info
2. **SQLAlchemy** — `after_commit` — flush_pending_changes escribe XADD en el Stream del proyecto y en case:changelog:all; after_rollback descarta
3. **Usuario** — `Abre la pestaña Registro en el espacio colaborativo` — GET /change-log?limit=50 → lista con autor, hora relativa y resumen
4. **ChangeLogConsumer (ola 2)** — `XREADGROUP case:changelog:all` — Difunde CHANGE_LOGGED y el panel agrega la entrada arriba sin recargar

**Alternos:**

- REDIS_ENABLED=false o Redis caído: el endpoint responde con source='postgres_fallback' leyendo audit_logs y el panel muestra «Registro en modo respaldo».
- Redis vuelve: python -m app.core.changelog.backfill --project <id> reconstruye el Stream desde audit_logs.

### Invitaciones y permisos (CU20 · CU25) — /proyectos/:projectId · A2

| Carril | Documento | Qué contiene | Archivo |
|---|---|---|---|
| Ruta / WS | Rutas de invitaciones | Invitar, listar, revocar, aceptar, rechazar y members/me | backend/app/modules/proyectos_colaboracion/routers/invitations.py |
| Servicio | Invitaciones y permisos | Vencimiento a 7 días, notificación y rol Lector | backend/app/modules/proyectos_colaboracion/services/invitation_service.py |
| Datos | Invitaciones e integrantes | Una invitación pendiente por proyecto y correo | backend/app/modules/proyectos_colaboracion/repositories/invitation_repository.py |
| Interfaz | Gestión del proyecto | Invitar por correo, pendientes, aceptar y rechazar | frontend/src/modules/gestion_proyectos_colaboracion/pages/ProjectManagementPage.tsx |

**Flujo:**

1. **Organizador** — `Escribe beto@correo y rol Editor → Invitar` — POST /invitations → 201; aparece en «Pendientes» con fecha de vencimiento
2. **Backend** — `NotificationService.record(PROJECT_INVITATION_RECEIVED)` — Si el correo tiene cuenta: notificación en la campana y push
3. **Beto** — `Abre la campana o «Mis invitaciones» en Proyectos` — Botones Aceptar / Rechazar
4. **Beto** — `POST /invitations/{id}/accept` — Se crea ProjectMember con el rol; el organizador recibe PROJECT_INVITATION_ACCEPTED
5. **Lector** — `Abre el editor` — useProjectPermissions().can('uml.edit') = false: lienzo de solo lectura y sin botones de edición

**Alternos:**

- Invitación vencida: 410 INVITATION_EXPIRED y toast «La invitación venció; pide una nueva».
- Correo sin cuenta: la invitación queda pendiente y se ve al registrarse con ese correo.
- Editor intenta invitar: 403 PERMISSION_DENIED y el formulario no se muestra.

### Editor UML colaborativo (CU11 · CU21) — /proyectos/:projectId/uml/:diagramId · A3

| Carril | Documento | Qué contiene | Archivo |
|---|---|---|---|
| Ruta / WS | Mensajes de bloqueo | LOCK y UNLOCK por WebSocket con TTL en Redis | backend/app/websocket/router.py |
| Servicio | Bloqueos y guarda 423 | Nadie modifica lo que otro está editando | backend/app/websocket/locks.py |
| Datos | Tipos y visibilidades | Interfaz, enum, abstracta; # y ~; dependencia y realización | backend/app/modules/modelado_uml/schemas/uml.py |
| Interfaz | Editor y lienzo | Paleta completa, candado con nombre, deshacer y rehacer | frontend/src/modules/modelado_uml_inteligente/pages/UmlEditorPage.tsx |

**Flujo:**

1. **Ana** — `Selecciona la clase Producto` — Envía LOCK_ELEMENT; todos reciben ELEMENT_LOCKED y ven un candado «Ana editando»
2. **Beto** — `Intenta editar Producto` — El panel de propiedades queda deshabilitado; si fuerza por API recibe 423 ELEMENT_LOCKED
3. **Ana** — `Cambia el tipo a «Interfaz» y agrega una realización` — La paleta tiene Interfaz, Enum, Abstracta, Dependencia y Realización; el lienzo dibuja «interface» y línea punteada con triángulo
4. **Ana** — `Ctrl+Z` — umlHistory deshace la última operación propia con la llamada REST inversa
5. **Ana** — `Deselecciona o se desconecta` — ELEMENT_UNLOCKED (released o disconnected)

**Alternos:**

- Bloqueo sin renovar 60 s: expira y se emite ELEMENT_UNLOCKED reason=expired.
- Redis apagado: ElementLockService usa un diccionario en memoria (un solo proceso).
- Importar un XMI de Enterprise Architect con composición: se conserva como composition (antes quedaba association).

### Backend Spring Boot completo (CU16) — /proyectos/:projectId/generacion · A4

| Carril | Documento | Qué contiene | Archivo |
|---|---|---|---|
| Ruta / WS | POST …/coordinated | Sin cambios de contrato | backend/app/modules/generacion_software/routers/generation.py |
| Servicio | Analizador de relaciones | JPA bidireccional, cascada, herencia y enum | backend/app/modules/generacion_software/backend_generator/analyzer/model_analyzer.py |
| Datos | Semilla y Postman | data.sql por entidad y colección con ejemplos | backend/app/modules/generacion_software/backend_generator/templates/postman_templates.py |
| Interfaz | Página de generación | Descarga el ZIP con los archivos nuevos | frontend/src/modules/transformacion_generacion_software/pages/GenerationPage.tsx |

**Flujo:**

1. **Usuario** — `Generar con Categoria ◆— Producto (1 a 0..*)` — Categoria tiene @OneToMany(mappedBy='categoria', cascade=ALL, orphanRemoval=true) y Producto @ManyToOne @JoinColumn
2. **Generador** — `Escribe data.sql y postman_collection.json` — 3 filas por entidad respetando FKs; colección con CRUD por entidad y variable baseUrl
3. **Usuario** — `mvn spring-boot:run y abre Postman` — Las tablas se crean, la semilla carga y las peticiones responden 200/201

**Alternos:**

- Herencia: la superclase lleva @Inheritance(strategy=JOINED) y la subclase extiende sin duplicar id.
- Enum: genera enum Java y el atributo lleva @Enumerated(EnumType.STRING).
- Interfaz UML: genera interface Java en domain/ y no crea tabla.

## 6. Archivo por archivo

### `backend/migrations/versions/f1a2b3c4d5e6_mejoras_2p_base.py`

Dueño: A1 · capa: Datos · acción: crear · vista: compartido · traza: Bug 500 · CU20 · CU24

- **migración f1a2b3c4d5e6** [alembic] — revision = 'f1a2b3c4d5e6', down_revision = 'da4e5f6a7b8c'. Única migración del plan.
  - `op.alter_column('coordinated_generations', 'created_at', server_default=sa.text('now()'))` → Igual para updated_at y para flutter_theme_presets.created_at/updated_at (4 columnas).
  - `op.drop_constraint('ck_ai_project_settings_provider', 'ai_project_settings', type_='check'); op.create_check_constraint(..., "preferred_provider IN ('ollama','gemini','rule_engine')")` → Permite el proveedor gemini.
  - `op.create_index('uq_project_invitations_pending', 'project_invitations', ['project_id', sa.text('lower(invited_email)')], unique=True, postgresql_where=sa.text("status = 'pending'"))` → Una sola invitación pendiente por proyecto y correo.
  - `def downgrade() -> None` → Revierte en orden inverso (vuelve a dejar el check sin gemini solo si no hay filas con gemini; si las hay, las pasa a 'ollama').
> Nota: Ningún otro agente crea migraciones. Probar upgrade → downgrade → upgrade sobre una base limpia.

### `backend/app/core/config/settings.py`

Dueño: A1 · capa: Servicio · acción: modificar · vista: compartido · traza: Contrato Variables de entorno

- **Settings** [clase pydantic-settings] — Agregar exactamente los campos de la tabla «Variables de entorno» con sus valores por defecto.
  - `redis_enabled: bool = False · redis_url: str = 'redis://127.0.0.1:6379/0' · redis_key_prefix: str = 'case' · redis_change_log_maxlen: int = 10000` → Redis opcional.
  - `element_lock_ttl_seconds: int = 60 · ai_proactive_enabled: bool = True · ai_proactive_min_changes: int = 5 · ai_proactive_cooldown_seconds: int = 120` → Bloqueos e IA proactiva.
  - `gemini_api_key: str | None = None · gemini_model: str = '' · gemini_base_url: str = 'https://generativelanguage.googleapis.com'` → Gemini opcional; gemini_model lo completa V1.7.

### `backend/app/core/redis/client.py`

Dueño: A1 · capa: Datos · acción: crear · vista: compartido · traza: NoSQL (docente)

- **client** [módulo] — Clientes perezosos y cacheados; si redis_enabled es false devuelven None. Nunca lanzan al importar.
  - `def get_redis() -> redis.Redis | None` → Cliente síncrono (decode_responses=True, socket_timeout=2).
  - `def get_async_redis() -> redis.asyncio.Redis | None` → Cliente asíncrono para WebSocket y consumidores.
  - `def redis_key(*parts: str) -> str` → Une settings.redis_key_prefix y las partes con ':'.
  - `def redis_status() -> Literal['available', 'unavailable', 'disabled']` → PING con timeout corto; para /ready.
  - `def set_test_client(client: redis.Redis | None, async_client: redis.asyncio.Redis | None = None) -> None` → Inyecta fakeredis en pruebas.

### `backend/app/core/redis/__init__.py`

Dueño: A1 · capa: Datos · acción: crear · vista: compartido · traza: —

- **__init__** [módulo] — Reexporta get_redis, get_async_redis, redis_key, redis_status, set_test_client.

### `backend/app/main.py`

Dueño: A1 · capa: Ruta / WS · acción: modificar · vista: compartido · traza: —

- **create_app** [función] — Registra los routers nuevos (vacíos en ola 0) y el ciclo de vida.
  - `app.include_router(change_log_router, prefix=settings.api_prefix) · app.include_router(invitations_router, prefix=settings.api_prefix) · app.include_router(my_invitations_router, prefix=settings.api_prefix)` → Routers de change_log.py e invitations.py.
  - `install_change_log_hooks()` → Llamado una vez en create_app (definido en core/changelog/hooks.py).
  - `lifespan: async with start_background_workers(app): yield` → Usa core/workers.py; en ola 0 no arranca nada.
  - `@app.get('/ready') → {'status', 'database', 'redis': redis_status()}` → status='degraded' solo si la BD falla; Redis apagado no degrada.

### `backend/app/core/workers.py`

Dueño: A1 · capa: Servicio · acción: crear · vista: compartido · traza: CU23

- **workers** [módulo] — Ola 0: contexto vacío. Ola 2 (V2.1): arranca ChangeLogConsumer si redis_enabled.
  - `@asynccontextmanager async def start_background_workers(app: FastAPI) -> AsyncIterator[None]` → Crea y cancela las tareas en segundo plano de forma ordenada.

### `backend/app/core/changelog/contracts.py`

Dueño: A1 · capa: Datos · acción: crear · vista: registro · traza: CU22

- **contratos del registro** [pydantic] — Exactamente los campos del contrato «Entrada del registro».
  - `class PendingChange(BaseModel): project_id: UUID; actor_user_id: UUID | None; source: Literal['ui','ai','ws','system']; module: str; action: str; entity_type: str | None = None; entity_id: str | None = None; diagram_id: UUID | None = None; metadata: dict = {}` → Lo que encolan los servicios.
  - `class ChangeLogEntry(BaseModel) · class ChangeLogPage(BaseModel)` → Respuesta del endpoint.
  - `ACTION_LABELS: dict[str, str]` → Etiqueta en español por acción de auditoría.
  - `def build_summary(action: str, metadata: dict) -> str` → Etiqueta + nombre (name, class_name o target_name) recortado a 200.
  - `def project_stream_key(project_id: UUID) -> str · GLOBAL_STREAM = 'changelog:all'` → Claves de la tabla «Claves Redis».

### `backend/app/core/changelog/hooks.py`

Dueño: A1 · capa: Servicio · acción: crear · vista: registro · traza: CU22

- **hooks** [módulo] — Ola 0: install_change_log_hooks() idempotente sin efecto. Ola 1 (V1.1): registra los listeners.
  - `def install_change_log_hooks() -> None` → event.listen(Session, 'after_commit', flush_pending_changes) y 'after_rollback' → clear_pending_changes; solo una vez.
  - `def flush_pending_changes(session: Session) -> None` → Toma session.info.pop('change_log_pending', []) y llama ChangeLogService().append_many; atrapa y registra cualquier error de Redis.
  - `def clear_pending_changes(session: Session) -> None` → Descarta pendientes.

### `backend/app/core/changelog/service.py`

Dueño: A1 · capa: Servicio · acción: crear · vista: registro · traza: CU22

- **ChangeLogService** [clase] — Escritura y lectura del registro en Redis Streams con respaldo en audit_logs. (análisis: RegistroCambios)
  - `def queue_change(db: Session, change: PendingChange) -> None` → Agrega a db.info['change_log_pending'] (función de módulo).
  - `def append_many(self, changes: list[PendingChange]) -> int` → Pipeline: XADD al Stream del proyecto (MAXLEN ~ redis_change_log_maxlen) y a GLOBAL_STREAM (MAXLEN ~ 50000); metadata saneada con sanitize_audit_metadata y ≤ 2048 bytes.
  - `def list_project(self, project_id: UUID, *, before_id: str | None, limit: int, actor_id: UUID | None, entity_type: str | None) -> ChangeLogPage` → XREVRANGE con filtro en memoria (lee hasta 5×limit); si Redis no está, lee audit_logs del proyecto y devuelve source='postgres_fallback'.
  - `def resolve_names(self, db: Session, page: ChangeLogPage) -> ChangeLogPage` → Completa actor_display_name con una sola consulta IN a users.

### `backend/app/core/changelog/backfill.py`

Dueño: A1 · capa: Servicio · acción: crear · vista: registro · traza: CU22

- **backfill** [comando] — python -m app.core.changelog.backfill --project <uuid> [--all]
  - `def backfill_project(db: Session, project_id: UUID) -> int` → Borra el Stream del proyecto y lo reconstruye desde audit_logs en orden cronológico; devuelve cuántas entradas escribió.

### `backend/app/core/changelog/consumer.py`

Dueño: A1 · capa: Servicio · acción: crear · vista: chat-ia · traza: CU22 · CU23

- **ChangeLogConsumer** [clase] — Lee GLOBAL_STREAM con el grupo 'case-workers' (XGROUP CREATE … MKSTREAM si no existe).
  - `async def run(self, stop: asyncio.Event) -> None` → XREADGROUP BLOCK 5000 COUNT 50; por entrada: difunde CHANGE_LOGGED y llama ProactiveAdvisorService.on_change; XACK al terminar. Errores: log y continúa.
  - `async def _broadcast(self, entry: ChangeLogEntry) -> None` → manager.broadcast(str(project_id), evento v2 CHANGE_LOGGED persistent=False, sequence_number=0).

### `backend/app/core/changelog/__init__.py`

Dueño: A1 · capa: Servicio · acción: crear · vista: compartido · traza: —

- **__init__** [módulo] — Reexporta PendingChange, ChangeLogEntry, ChangeLogPage, queue_change, install_change_log_hooks.

### `backend/app/modules/proyectos_colaboracion/permissions.py`

Dueño: A1 · capa: Servicio · acción: crear · vista: compartido · traza: Roles y permisos (docente)

- **catálogo de permisos** [módulo] — Fuente única de la tabla «Permisos por rol».
  - `PERMISSION_CODES: frozenset[str]` → Los 11 códigos.
  - `PROJECT_ROLES: tuple[str, ...] = ('ORGANIZADOR', 'EDITOR', 'LECTOR')` → Roles de proyecto.
  - `ROLE_DEFAULTS: dict[str, frozenset[str]]` → Permisos por rol según la tabla.
  - `def effective_permissions(project_role: str, granted: Iterable[str]) -> frozenset[str]` → ROLE_DEFAULTS[rol] ∪ (granted ∩ PERMISSION_CODES).

### `backend/app/modules/asistente_proyecto/schemas/websocket.py`

Dueño: A1 · capa: Ruta / WS · acción: modificar · vista: compartido · traza: Contrato Eventos WebSocket

- **WsEventTypeV2** [Literal] — Agregar 'ELEMENT_LOCKED', 'ELEMENT_UNLOCKED', 'LOCK_REJECTED', 'CHANGE_LOGGED'.

### `frontend/src/core/contracts/phase1.ts`

Dueño: A1 · capa: Interfaz · acción: modificar · vista: compartido · traza: Contrato Tipos TypeScript

- **ProjectSocketEventV2 · AiProjectSettings** [tipos] — Sumar los 4 tipos de evento nuevos y preferred_provider: AiProvider (importado de mejoras2p.ts).

### `frontend/src/core/contracts/mejoras2p.ts`

Dueño: A1 · capa: Interfaz · acción: crear · vista: compartido · traza: Contrato Tipos TypeScript

- **tipos de mejoras** [tipos] — Copiar literalmente las firmas del contrato «Tipos TypeScript».
  - `export const PERMISSION_CODES: readonly PermissionCode[]` → Lista para iterar en la interfaz.

### `backend/app/modules/proyectos_colaboracion/routers/change_log.py`

Dueño: A1 · capa: Ruta / WS · acción: crear · vista: registro · traza: CU22

- **router** [APIRouter(prefix='/projects', tags=['registro-cambios'])] — Ola 0: router vacío. Ola 1: endpoint.
  - `@router.get('/{project_id}/change-log', response_model=ChangeLogPage) def list_change_log(project_id: UUID, current_user, db, before_id: str | None = None, limit: int = Query(50, ge=1, le=100), actor_id: UUID | None = None, entity_type: str | None = None)` → ensure_membership; ChangeLogService().list_project(...) y resolve_names.

### `backend/app/modules/proyectos_colaboracion/routers/invitations.py`

Dueño: A2 · capa: Ruta / WS · acción: crear · vista: permisos · traza: CU20

- **routers de invitaciones** [APIRouter] — A1 lo crea vacío en V0.4 (dos routers: router con prefix='/projects' y my_router con prefix='/invitations'); A2 lo completa en V2.3.
  - `@router.post('/{project_id}/invitations', status_code=201, response_model=InvitationResponse)` → Crear invitación.
  - `@router.get('/{project_id}/invitations', response_model=list[InvitationResponse])` → Listar por estado.
  - `@router.delete('/{project_id}/invitations/{invitation_id}', status_code=204)` → Revocar.
  - `@my_router.get('/me') · @my_router.post('/{invitation_id}/accept') · @my_router.post('/{invitation_id}/reject')` → Bandeja del invitado.
> Nota: En V0.4 A1 solo crea `router = APIRouter(prefix='/projects', tags=['invitaciones'])` y `my_router = APIRouter(prefix='/invitations', tags=['invitaciones'])` sin rutas, para registrarlos en main.py.

### `frontend/nginx.conf`

Dueño: A1 · capa: Interfaz · acción: modificar · vista: chat-ia · traza: Bug micrófono

- **Permissions-Policy** [cabecera] — add_header Permissions-Policy "camera=(), microphone=(self), geolocation=()" always;

### `backend/app/core/security/headers.py`

Dueño: A1 · capa: Servicio · acción: modificar · vista: chat-ia · traza: Bug micrófono

- **SecurityHeadersMiddleware** [middleware] — Mismo valor: microphone=(self).

### `backend/app/modules/modelado_uml/services/uml_service.py`

Dueño: A2 · capa: Servicio · acción: modificar · vista: editor · traza: CU11 · CU21 · CU25

- **UmlService** [clase] — Archivo compartido en olas distintas: V0.4 (A1) nombres duplicados; V1.3 (A2) permisos; V2.5 (A3) guarda de bloqueo.
  - `def _ensure_unique_class_name(self, diagram_id: UUID, name: str, exclude_id: UUID | None = None) -> None` → V0.4: 409 CLASS_NAME_DUPLICATED (comparación casefold y sin espacios a los lados) en create_class y update_class.
  - `ensure_project_permission(self.db, project_id, user_id, 'uml.edit')` → V1.3: reemplaza ensure_membership en toda operación que modifica (lecturas siguen con membresía).
  - `def _ensure_not_locked_by_other(self, project_id: UUID, element_type: str, element_id: UUID, user_id: UUID) -> None` → V2.5: si ElementLockService().holder(...) es de otro usuario → 423 ELEMENT_LOCKED; usado en update/delete de clase, atributo, método y relación.

### `backend/tests/test_second_part_phase9_quality_gates.py`

Dueño: A1 · capa: Servicio · acción: modificar · vista: compartido · traza: Bug prueba CORS

- **test_phase9_allowed_cors_origin_receives_header** [prueba] — Usar origin = settings.cors_origins[0] en lugar del dominio fijo de Vercel.

### `CLAUDE.md`

Dueño: A1 · capa: Interfaz · acción: crear · vista: compartido · traza: —

- **CLAUDE.md** [documento] — Instrucciones para Claude Code: estructura del monorepo (backend, frontend, ai-engine, mobile), comandos de pruebas en PowerShell, enlace a docs/segundo_parcial/mejoras-2p/PLAN.md, reglas de INSTRUCCION y la bitácora. Máximo 80 líneas.

### `backend/pyproject.toml`

Dueño: A1 · capa: Datos · acción: modificar · vista: compartido · traza: —

- **dependencias** [toml] — dependencies += 'redis>=5.0,<7'; [project.optional-dependencies].dev += 'fakeredis>=2.20'.

### `backend/.env.example`

Dueño: A1 · capa: Datos · acción: modificar · vista: compartido · traza: —

- **.env.example** [plantilla] — Agregar los nombres de la tabla de variables con valores de ejemplo NO secretos (GEMINI_API_KEY= vacío).

### `docker-compose.yml`

Dueño: A1 · capa: Datos · acción: modificar · vista: compartido · traza: —

- **servicio redis** [compose] — redis: image redis:7-alpine, ports '6379:6379', command redis-server --appendonly yes, volumen redis_data. Opcional en desarrollo.

### `docker-compose.prod.yml`

Dueño: A1 · capa: Datos · acción: modificar · vista: compartido · traza: —

- **servicio redis** [compose] — Igual que desarrollo pero sin publicar el puerto; backend con REDIS_ENABLED=true y REDIS_URL=redis://redis:6379/0; depends_on redis.

### `backend/app/modules/acceso_usuarios/services/audit_service.py`

Dueño: A1 · capa: Servicio · acción: modificar · vista: registro · traza: CU22

- **AuditService.record** [método] — Después de repository.add(...), si project_id no es None: queue_change(self.db, PendingChange(...)) con source deducido (ver contrato), entity_type/entity_id/diagram_id leídos de metadata (class_id, relationship_id, method_id, diagram_id).
  - `def __init__(self, db: Session) -> None: self.db = db; self.repository = AuditRepository(db)` → Guardar db para encolar.

### `frontend/src/modules/gestion_proyectos_colaboracion/services/changeLogService.ts`

Dueño: A1 · capa: Interfaz · acción: crear · vista: registro · traza: CU22

- **changeLogService** [objeto]
  - `async list(projectId: string, params: { before_id?: string; limit?: number; actor_id?: string; entity_type?: string }): Promise<ChangeLogPage>` → GET /projects/{id}/change-log con apiClient.

### `frontend/src/modules/gestion_proyectos_colaboracion/components/ChangeLogPanel.tsx`

Dueño: A1 · capa: Interfaz · acción: crear · vista: registro · traza: CU22

- **ChangeLogPanel** [componente] — Línea de tiempo: avatar con iniciales, nombre, summary, hora relativa (Intl.RelativeTimeFormat 'es'), chip de source (IA en otro color). Filtros: integrante (select) y tipo (Clases, Relaciones, IA, Versiones, Generación). Botón «Cargar más» con next_cursor. Banner «Registro en modo respaldo» si source='postgres_fallback'. Estados vacío, cargando (esqueleto) y error. Referencia exacta: maqueta.html#registro (agrupar por día «Hoy», «Ayer», chip de tipo y chip IA, nota «Guardado en Redis Streams»). Usa Avatar, StatusBadge, EmptyState y Skeleton de V0.5.
  - `export function ChangeLogPanel({ projectId }: { projectId: string })` → Componente.
  - `suscripción: escucha CHANGE_LOGGED (antepone sin duplicar por id) y, como respaldo, recarga 1 vez al recibir UML_EVENT, AI_ACTION_STATUS_CHANGED o PROJECT_VERSION_* (debounce 1 s)` → Actualización en vivo.

### `frontend/src/modules/gestion_proyectos_colaboracion/pages/ProjectWorkspacePage.tsx`

Dueño: A1 · capa: Interfaz · acción: modificar · vista: registro · traza: CU22

- **ProjectWorkspacePage** [página] — Agregar pestaña «Registro de cambios» junto a la lista de chats y montar <ChangeLogPanel projectId={projectId} />. Pestañas «Chats del proyecto» y «Registro de cambios» como en maqueta.html#registro.

### `backend/app/modules/asistente_proyecto/services/proactive_advisor_service.py`

Dueño: A1 · capa: Servicio · acción: crear · vista: chat-ia · traza: CU23

- **ProactiveAdvisorService** [clase] — La IA como un desarrollador más: propone sin que se lo pidan. (análisis: AsesorIA)
  - `async def on_change(self, entry: ChangeLogEntry) -> None` → Ignora entradas con source='system'. Disparadores: (a) INCR pending ≥ ai_proactive_min_changes (cuentan ui y ai); (b) action CREATE_PROJECT_VERSION; (c) action IMPORT_XMI o IMPORT_XMI_REPLACE_DIAGRAM. Si existe cooldown, no hace nada. Sus propios mensajes no pasan por AuditService, así que no se retroalimenta.
  - `def _review_diagram(self, db: Session, diagram_id: UUID) -> list[PlannedRecommendation]` → Usa validate_internal_model del motor UML (modelado_uml/engine/validator.py); convierte errores/advertencias en PlannedRecommendation de ai_engine.orchestration.contracts (máx. 3, con referencias a clases).
  - `def _version_summary(self, db: Session, project_id: UUID) -> str` → Resume por integrante los cambios desde la versión anterior leyendo el Stream.
  - `async def _publish(self, project_id: UUID, actor_user_id: UUID, content: str, recommendations: list, trigger: str) -> None` → AssistantService.create_message(project_id, None, AiMessageCreateInternal(role='assistant', metadata_json={'kind': 'proactive', 'trigger': trigger}, ...)); crea AiRecommendation; publica AI_MESSAGE_CREATED y AI_RECOMMENDATION_CREATED con ProjectAiEventPublisher.publish_persisted; SET cooldown EX y borra pending.
> Nota: Si no hay hallazgos, no publica nada (no hace ruido). Máximo un mensaje cada ai_proactive_cooldown_seconds por proyecto.
> Nota: Si el proyecto todavía no tiene conversación (create_message con user_id None responde 409), no publica y lo registra en el log.

### `backend/app/modules/asistente_proyecto/services/context_builder.py`

Dueño: A1 · capa: Servicio · acción: modificar · vista: chat-ia · traza: CU19 · CU23

- **ContextBuilder.build** [método] — Rellenar author_display_name en recent_messages (repository.user_display_names) y team_activity con las últimas 50 entradas del Stream agrupadas por actor (máx. 10 por integrante). Respetar ContextBudget.

### `ai-engine/ai_engine/context/contracts.py`

Dueño: A1 · capa: Servicio · acción: modificar · vista: chat-ia · traza: CU23

- **contratos de contexto** [pydantic]
  - `RecentMessageContext.author_display_name: str | None = Field(default=None, max_length=160)` → Quién escribió cada mensaje.
  - `class TeamActivityItem(BaseModel): user_id: UUID | None; display_name: str; actions: list[str] = Field(max_length=10); last_at: datetime` → Actividad por integrante.
  - `AiProjectContext.team_activity: list[TeamActivityItem] = Field(default_factory=list, max_length=30)` → Nuevo campo, compatible por defecto.

### `ai-engine/ai_engine/orchestration/intent_classifier.py`

Dueño: A1 · capa: Servicio · acción: modificar · vista: chat-ia · traza: CU23

- **reglas de intención** [datos] — coordinate_team con frases: 'que hizo cada', 'quien cambio', 'quien modifico', 'resumen del equipo', 'que esta haciendo', 'reparte', 'organiza el trabajo' (confianza 0.9).

### `ai-engine/ai_engine/providers/rule_engine_provider.py`

Dueño: A1 · capa: Servicio · acción: modificar · vista: chat-ia · traza: CU23

- **RuleEngineProvider** [clase] — Responder coordinate_team con una línea por integrante de team_activity («Ana: creó Producto y Categoria; relacionó Producto con Categoria») y una sugerencia de reparto si dos integrantes tocaron la misma clase.

### `ai-engine/ai_engine/prompts/unified_system.md`

Dueño: A1 · capa: Servicio · acción: modificar · vista: chat-ia · traza: CU23

- **prompt de sistema** [texto] — Agregar: eres un integrante más del equipo; usa author_display_name y team_activity para dirigirte a cada persona por su nombre; propone ideas concretas; modera conflictos (dos personas editando lo mismo); nunca ejecutes sin confirmación las acciones de riesgo.

### `backend/app/modules/proyectos_colaboracion/validators/project_validator.py`

Dueño: A2 · capa: Servicio · acción: modificar · vista: permisos · traza: CU25

- **validadores** [funciones]
  - `def ensure_project_permission(db: Session, project_id: UUID, user_id: UUID, code: str) -> ProjectMember` → Carga membresía y permisos otorgados; si code ∉ effective_permissions → 403 {'code': 'PERMISSION_DENIED', ...}.
  - `def member_permissions(db: Session, member: ProjectMember) -> frozenset[str]` → Permisos efectivos de un integrante.
> Nota: ensure_organizer(member) conserva su firma para no romper llamadas existentes: internamente comprueba 'members.manage' en ROLE_DEFAULTS[member.project_role] y lanza el mismo 403 PERMISSION_DENIED. Las llamadas nuevas usan ensure_project_permission.

### `backend/app/modules/proyectos_colaboracion/services/project_service.py`

Dueño: A2 · capa: Servicio · acción: modificar · vista: permisos · traza: CU25 · CU20

- **ProjectService** [clase] — Aplicar permisos: update/delete proyecto → project.update; miembros → members.manage; create_version → versions.create; restore_version → versions.restore. Aceptar rol LECTOR. Nuevo método para members/me. En V2.3: add_member_from_invitation.
  - `def my_membership(self, project_id: UUID, user_id: UUID) -> dict` → {project_id, user_id, project_role, permissions: sorted(...)}.
  - `def add_member_from_invitation(self, invitation: ProjectInvitation, user_id: UUID) -> ProjectMember` → V2.3: crea el integrante reutilizando la lógica de add_member (audita ADD_PROJECT_MEMBER con metadata.origin='invitation' y notifica PROJECT_MEMBER_ADDED como hoy).

### `backend/app/modules/proyectos_colaboracion/schemas/project.py`

Dueño: A2 · capa: Datos · acción: modificar · vista: permisos · traza: CU25

- **esquemas** [pydantic] — AddMemberRequest y UpdateMemberRequest: pattern '^(ORGANIZADOR|EDITOR|LECTOR)$'.
  - `class MyMembershipResponse(BaseModel): project_id: UUID; user_id: UUID; project_role: str; permissions: list[str]` → Respuesta de members/me.

### `backend/app/modules/proyectos_colaboracion/routers/projects.py`

Dueño: A2 · capa: Ruta / WS · acción: modificar · vista: permisos · traza: CU25

- **router de proyectos** [APIRouter]
  - `@router.get('/{project_id}/members/me', response_model=MyMembershipResponse)` → Declarar ANTES de las rutas con {member_id} para que no colisione.

### `backend/app/modules/asistente_proyecto/services/action_execution_service.py`

Dueño: A2 · capa: Servicio · acción: modificar · vista: chat-ia · traza: CU25

- **confirmar/rechazar acción** [métodos] — Exigir ai.confirm_actions antes de ejecutar o rechazar. Al ejecutar una acción confirmada: db.info['change_origin'] = 'ai' y quitarlo en un finally (contrato «Entrada del registro»).

### `backend/app/modules/asistente_proyecto/services/assistant_service.py`

Dueño: A2 · capa: Servicio · acción: modificar · vista: chat-ia · traza: CU25

- **AssistantService** [clase] — update_settings → ai.settings; create_message de usuario → ai.chat; lecturas siguen con membresía.

### `backend/app/modules/generacion_software/services/generation_service.py`

Dueño: A2 · capa: Servicio · acción: modificar · vista: generacion · traza: CU25

- **GenerationService** [clase] — transform, preflight, generate_* y descargas → generation.run (descargar también lo exige).

### `backend/app/modules/generacion_software/services/theme_service.py`

Dueño: A2 · capa: Servicio · acción: modificar · vista: generacion · traza: CU25

- **ThemeService** [clase] — Guardar tema y presets → theme.edit.

### `frontend/src/core/permissions/useProjectPermissions.ts`

Dueño: A2 · capa: Interfaz · acción: crear · vista: permisos · traza: CU25

- **useProjectPermissions** [hook] — Cache en un store zustand por projectId con vida de 60 s; se invalida al cambiar de proyecto o al llamar refresh() (las páginas lo llaman cuando una petición responde 403 PERMISSION_DENIED). No modifica core/api/client.ts.
  - `export function useProjectPermissions(projectId?: string): { role: ProjectRole | null; can: (code: PermissionCode) => boolean; loading: boolean; refresh: () => Promise<void> }` → GET /projects/{id}/members/me; mientras carga, can() devuelve false.

### `frontend/src/core/permissions/PermissionGate.tsx`

Dueño: A2 · capa: Interfaz · acción: crear · vista: permisos · traza: CU25

- **PermissionGate** [componente]
  - `export function PermissionGate({ projectId, code, children, fallback = null }: { projectId: string; code: PermissionCode; children: ReactNode; fallback?: ReactNode })` → Muestra children solo si can(code).

### `backend/app/modules/proyectos_colaboracion/services/invitation_service.py`

Dueño: A2 · capa: Servicio · acción: crear · vista: permisos · traza: CU20

- **InvitationService** [clase] — Vencimiento: created_at + 7 días; al leer, las pendientes vencidas pasan a 'expired'. (análisis: GestionarInvitaciones)
  - `def invite(self, project_id: UUID, payload: InvitationCreateRequest, user_id: UUID) -> ProjectInvitation` → members.manage; correo normalizado (strip + lower); 409 MEMBER_ALREADY_EXISTS o INVITATION_ALREADY_PENDING; si existe usuario con ese correo, invited_user_id y notificación PROJECT_INVITATION_RECEIVED (category 'access', deep link route_name 'projects').
  - `def list_for_project(self, project_id: UUID, user_id: UUID, status: str | None) -> list[ProjectInvitation]` → members.manage.
  - `def revoke(self, project_id: UUID, invitation_id: UUID, user_id: UUID) -> None` → Solo pendientes → 'revoked'.
  - `def list_mine(self, user: User) -> list[ProjectInvitation]` → Pendientes con invited_email == user.email (case-insensitive).
  - `def accept(self, invitation_id: UUID, user: User) -> ProjectMember` → Verifica correo, estado y vencimiento (410); ProjectService.add_member_from_invitation; notifica PROJECT_INVITATION_ACCEPTED al que invitó.
  - `def reject(self, invitation_id: UUID, user: User) -> ProjectInvitation` → 'rejected' + PROJECT_INVITATION_REJECTED al que invitó.

### `backend/app/modules/proyectos_colaboracion/repositories/invitation_repository.py`

Dueño: A2 · capa: Datos · acción: crear · vista: permisos · traza: CU20

- **InvitationRepository** [clase]
  - `def add(self, invitation: ProjectInvitation) -> ProjectInvitation · def get(self, invitation_id: UUID) -> ProjectInvitation | None` → CRUD básico.
  - `def pending_for(self, project_id: UUID, email: str) -> ProjectInvitation | None` → Busca por lower(invited_email).
  - `def list_by_project(self, project_id: UUID, status: str | None) -> list[ProjectInvitation] · def list_pending_for_email(self, email: str) -> list[ProjectInvitation]` → Listados ordenados por created_at desc.

### `backend/app/modules/proyectos_colaboracion/schemas/invitation.py`

Dueño: A2 · capa: Datos · acción: crear · vista: permisos · traza: CU20

- **esquemas de invitación** [pydantic]
  - `class InvitationCreateRequest(BaseModel): email: EmailStr; project_role: Literal['EDITOR', 'LECTOR'] = 'EDITOR'` → Entrada.
  - `class InvitationResponse(BaseModel): id, project_id, project_name, invited_email, project_role, status, invited_by_name, expires_at, created_at` → Igual al tipo TS ProjectInvitation.

### `frontend/src/modules/gestion_proyectos_colaboracion/services/invitationService.ts`

Dueño: A2 · capa: Interfaz · acción: crear · vista: permisos · traza: CU20

- **invitationService** [objeto]
  - `invite(projectId, { email, project_role }) · listForProject(projectId, status?) · revoke(projectId, invitationId)` → Rutas del organizador.
  - `mine() · accept(invitationId) · reject(invitationId)` → Rutas del invitado.

### `frontend/src/modules/gestion_proyectos_colaboracion/pages/ProjectManagementPage.tsx`

Dueño: A2 · capa: Interfaz · acción: modificar · vista: permisos · traza: CU20 · CU25

- **ProjectManagementPage** [página] — Reemplazar el selector de candidatos por formulario «Invitar por correo» (correo + rol Editor/Lector, botón con spinner, toast). Lista «Invitaciones pendientes» con vencimiento y botón Revocar (modal de confirmación propio). Selector de rol de integrante incluye Lector. Todo lo de gestión envuelto en PermissionGate code='members.manage'. Referencia exacta: maqueta.html#gestion: tarjeta «Permisos por rol» generada desde ROLE_DEFAULTS (vía members/me o constante compartida), franja teal «Invitar por correo», tabla de pendientes con Revocar + useConfirm, integrantes con selector de rol.

### `frontend/src/shared/components/NotificationCenter.tsx`

Dueño: A2 · capa: Interfaz · acción: modificar · vista: permisos · traza: CU20

- **NotificationCenter** [componente] — Para notificaciones type PROJECT_INVITATION_RECEIVED: botones Aceptar / Rechazar que llaman invitationService y luego marcan la notificación como leída. Referencia exacta: el desplegable de la campana en maqueta.html#invitaciones.

### `frontend/src/modules/gestion_proyectos_colaboracion/pages/ProjectsPage.tsx`

Dueño: A2 · capa: Interfaz · acción: modificar · vista: permisos · traza: CU20

- **ProjectsPage** [página] — Bloque «Mis invitaciones» arriba de la lista si invitationService.mine() trae elementos; al aceptar, recarga proyectos. Referencia exacta: tarjeta teal «{nombre} te invitó a «{proyecto}» como {rol}» de maqueta.html#invitaciones.

### `frontend/src/modules/modelado_uml_inteligente/types/uml.ts`

Dueño: A3 · capa: Interfaz · acción: modificar · vista: editor · traza: CU11

- **tipos UML** [tipos]
  - `export type UmlElementType = "class" | "interface" | "enum" | "abstract_class"` → Tipo de clasificador.
  - `export type UmlVisibility = "public" | "private" | "protected" | "package"` → Símbolos + - # ~.
  - `export type UmlRelationshipType = "association" | "inheritance" | "aggregation" | "composition" | "dependency" | "realization"` → realization reemplaza el uso informal de 'implementation' (aceptar ambos al leer).

### `frontend/src/modules/modelado_uml_inteligente/pages/UmlEditorPage.tsx`

Dueño: A3 · capa: Interfaz · acción: modificar · vista: editor · traza: CU11 · CU21

- **UmlEditorPage** [página] — V1.5: UmlTool suma 'dependency' y 'realization'; panel de propiedades con selector Tipo (Clase, Interfaz, Enum, Abstracta); visibilityOptions con protected '#' y package '~'; para enum, los atributos se editan como literales. V2.6: bloqueos (LOCK/UNLOCK, panel deshabilitado si lo tiene otro, toast en LOCK_REJECTED) y modo solo lectura con useProjectPermissions(projectId).can('uml.edit'). V2.7: atajos Ctrl+Z / Ctrl+Y con umlHistory. Referencia exacta: maqueta.html#editor (barra con Deshacer/Rehacer, paleta en dos grupos con etiqueta «Nuevo» solo durante la demo, aviso de solo lectura, panel de propiedades con ElementTypeSelect y tabla de visibilidades).
> Nota: Archivo de ~1 900 líneas: extraer lo nuevo a componentes o hooks propios (ElementTypeSelect, useElementLocks) en lugar de engordarlo.

### `frontend/src/modules/modelado_uml_inteligente/components/JointUmlCanvas.tsx`

Dueño: A3 · capa: Interfaz · acción: modificar · vista: editor · traza: CU11 · CU21

- **JointUmlCanvas** [componente] — Render: «interface» y «enumeration» encima del nombre; nombre en cursiva para abstract_class; enum sin compartimento de métodos. visibilitySymbol para las 4 visibilidades. dependency: línea punteada con flecha abierta; realization: punteada con triángulo hueco. V2.6: prop lockedElements: Record<string, ElementLock> → borde y candado con el nombre. Referencia exacta: maqueta.html#editor (bloqueo = borde punteado ámbar y píldora «{nombre} editando» con Avatar).

### `backend/app/modules/modelado_uml/schemas/uml.py`

Dueño: A3 · capa: Datos · acción: modificar · vista: editor · traza: CU11

- **validación de valores** [pydantic] — Literal/validators: element_type ∈ {class, interface, enum, abstract_class}; visibility ∈ {public, private, protected, package}; relationship_type ∈ {association, inheritance, aggregation, composition, dependency, realization, implementation}. 422 con mensaje en español si no.

### `backend/app/modules/modelado_uml/engine/xmi.py`

Dueño: A3 · capa: Servicio · acción: modificar · vista: editor · traza: CU13

- **XMI EA 1.1** [módulo] — Export: isAbstract='true', estereotipos interface/enumeration, visibilidades protected/package, UML:Dependency y UML:Abstraction (realización). Import: leer aggregation='shared'|'composite' de los AssociationEnd para conservar aggregation/composition; Dependency y Abstraction sin error 500; isAbstract y estereotipos al element_type.

### `backend/app/websocket/locks.py`

Dueño: A3 · capa: Servicio · acción: crear · vista: editor · traza: CU21

- **ElementLockService** [clase] — Redis si está disponible (SET NX PX); si no, diccionario en memoria con vencimiento. Clave del contrato «Claves Redis». (análisis: BloqueoElemento)
  - `def acquire(self, project_id: str, element_type: str, element_id: str, user_id: str, display_name: str) -> tuple[bool, dict]` → True si lo obtiene o ya era suyo (renueva TTL); False y el dueño actual si es de otro.
  - `def release(self, project_id: str, element_type: str, element_id: str, user_id: str) -> bool` → Solo libera si es el dueño (script Lua o comparación en transacción).
  - `def holder(self, project_id: str, element_type: str, element_id: str) -> dict | None` → Dueño actual o None.
  - `def release_all_for_user(self, project_id: str, user_id: str) -> list[dict]` → Al desconectarse la última pestaña del usuario.

### `backend/app/websocket/router.py`

Dueño: A3 · capa: Ruta / WS · acción: modificar · vista: editor · traza: CU21

- **project_collaboration** [endpoint WS] — Manejar LOCK_ELEMENT y UNLOCK_ELEMENT (validar uml.edit con ensure_project_permission); emitir ELEMENT_LOCKED/UNLOCKED a todos y LOCK_REJECTED al solicitante; en WebSocketDisconnect, si fue la última conexión del usuario, release_all_for_user y emitir ELEMENT_UNLOCKED reason='disconnected'. Tarea periódica cada 15 s que emite ELEMENT_UNLOCKED reason='expired' para bloqueos vencidos del modo en memoria.

### `backend/app/websocket/connection_manager.py`

Dueño: A3 · capa: Ruta / WS · acción: modificar · vista: editor · traza: CU21

- **ConnectionManager** [clase]
  - `def user_connection_count(self, project_id: str, user_id: str) -> int` → Para saber si se desconectó la última pestaña.

### `frontend/src/core/websocket/projectSocket.ts`

Dueño: A3 · capa: Interfaz · acción: modificar · vista: editor · traza: CU21

- **ProjectRealtimeClient** [clase]
  - `lockElement(diagramId: string, elementType: "class" | "relationship", elementId: string): void` → Envía LOCK_ELEMENT.
  - `unlockElement(diagramId: string, elementType: "class" | "relationship", elementId: string): void` → Envía UNLOCK_ELEMENT.

### `frontend/src/modules/gestion_proyectos_colaboracion/components/ProjectPresenceIndicator.tsx`

Dueño: A3 · capa: Interfaz · acción: modificar · vista: chat-ia · traza: CU19

- **ProjectPresenceIndicator** [componente] — La IA visible como integrante: avatar fijo «Asistente CASE» con estado «Pensando…» entre AI_PROCESSING_STARTED y AI_PROCESSING_FINISHED/FAILED y «Disponible» el resto; tooltip con el proveedor activo. Referencia exacta: cabecera de la maqueta (PresenceStack con el avatar de la IA al final y el estado en texto).

### `frontend/src/modules/modelado_uml_inteligente/store/umlHistory.ts`

Dueño: A3 · capa: Interfaz · acción: crear · vista: editor · traza: CU11

- **umlHistory** [store zustand] — Pila de comandos propios (máx. 50). Cada comando guarda la operación y su inversa como llamadas de umlService. Se vacía al cambiar de diagrama o al restaurar versión. No deshace cambios de otros usuarios.
  - `push(command: { label: string; undo: () => Promise<void>; redo: () => Promise<void> }): void` → Registra y limpia la pila de rehacer.
  - `undo(): Promise<void> · redo(): Promise<void> · canUndo: boolean · canRedo: boolean · clear(): void` → Operaciones.

### `ai-engine/ai_engine/providers/gemini_provider.py`

Dueño: A4 · capa: Servicio · acción: crear · vista: chat-ia · traza: CU24

- **GeminiProvider** [clase (AiProvider)] — Implementa el mismo Protocol que OllamaProvider. httpx.AsyncClient; clave en la cabecera x-goog-api-key (nunca en la URL ni en logs). (análisis: ProveedorIA)
  - `def __init__(self, *, api_key: str | None, base_url: str, model: str, timeout: float = 60, max_retries: int = 2, transport: httpx.AsyncBaseTransport | None = None) -> None` → transport para pruebas.
  - `async def health(self, requested_model: str | None = None) -> ProviderHealth` → Sin clave → available=False, error_code='missing_api_key'; con clave → GET /v1beta/models/{model}.
  - `async def complete_structured(self, request: ProviderRequest, response_model: type[T]) -> ProviderResponse[T]` → POST /v1beta/models/{model}:generateContent con systemInstruction, contents y generationConfig {temperature, maxOutputTokens, responseMimeType: 'application/json'}; valida con response_model; reintenta ante JSON inválido o 429/5xx; errores tipados de providers/errors.py.

### `ai-engine/ai_engine/providers/__init__.py`

Dueño: A4 · capa: Servicio · acción: modificar · vista: chat-ia · traza: CU24

- **exportaciones** [módulo] — Agregar GeminiProvider a la carga perezosa (__getattr__) y a __all__.

### `backend/app/modules/asistente_proyecto/services/provider_factory.py`

Dueño: A4 · capa: Servicio · acción: modificar · vista: chat-ia · traza: CU24

- **fábrica de proveedores** [funciones]
  - `@lru_cache(maxsize=1) def get_gemini_provider() -> GeminiProvider` → Con settings.gemini_*.
  - `async def select_provider(preferred: str) -> tuple[AiProvider | None, str]` → ('ollama'|'gemini'|'rule_engine') → (proveedor o None para reglas, modelo resuelto). Gemini sin clave → (None, '') y registra aviso.

### `backend/app/modules/asistente_proyecto/services/project_ai_application_service.py`

Dueño: A4 · capa: Servicio · acción: modificar · vista: chat-ia · traza: CU24

- **selección de proveedor** [cambio puntual] — Reemplazar el if de preferred_provider == 'ollama' (líneas ~178–186) y el health (~85) por select_provider(project_settings.preferred_provider). Sin otros cambios.

### `backend/app/modules/asistente_proyecto/schemas/assistant.py`

Dueño: A4 · capa: Datos · acción: modificar · vista: chat-ia · traza: CU24

- **esquemas del asistente** [pydantic] — preferred_provider: Literal['ollama', 'gemini', 'rule_engine'] en settings request/response.

### `backend/app/modules/asistente_proyecto/models/ai_project_settings.py`

Dueño: A4 · capa: Datos · acción: modificar · vista: chat-ia · traza: CU24

- **AiProjectSettings** [modelo] — CheckConstraint con 'gemini' (mismo texto que la migración f1a2b3c4d5e6).

### `frontend/src/core/voice/useSpeechRecognition.ts`

Dueño: A4 · capa: Interfaz · acción: crear · vista: chat-ia · traza: CU19

- **useSpeechRecognition** [hook] — Envuelve window.SpeechRecognition ?? webkitSpeechRecognition; lang 'es-ES', interimResults true, continuous false. Mapea errores 'not-allowed' y 'no-speech' a mensajes en español.
  - `export function useSpeechRecognition(options?: { lang?: string; onFinal?: (text: string) => void }): { supported: boolean; listening: boolean; interim: string; start(): void; stop(): void; error: string | null }` → Contrato «Firmas compartidas».

### `frontend/src/modules/gestion_proyectos_colaboracion/components/ProjectAiAssistant.tsx`

Dueño: A4 · capa: Interfaz · acción: modificar · vista: chat-ia · traza: CU19 · CU23 · CU24

- **ProjectAiAssistant** [componente] — Botón de micrófono junto al campo (aria-pressed, animación de escucha, texto parcial en gris); al terminar, pone el texto en el borrador y lo envía si el interruptor «Enviar al terminar» está activo. Mensajes con metadata_json.kind='proactive' llevan la etiqueta «Sugerencia de la IA» y otro fondo. Engranaje con selector de proveedor (Ollama local, Gemini, Reglas) visible solo con can('ai.settings'); muestra la salud de /ai/provider-health. Botones Confirmar/Rechazar solo con can('ai.confirm_actions'). Referencia exacta: maqueta.html#asistente: cabecera con píldora del proveedor y engranaje (AiProviderSettings), autor con Avatar en cada mensaje, burbujas propias a la derecha con «Dictado por voz», tarjeta de acciones con un chip por tipo y botón «Confirmar {n} cambios», tarjeta ámbar «Sugerencia de la IA», indicador de escritura y compositor con micrófono, texto parcial e interruptor.
> Nota: En V1.8 usa useProjectPermissions solo si V1.4 ya está en main; si no, deja un TODO y lo completa A4 en V2.8 bajo la misma tarea de integración (anotar en bitácora).

### `backend/app/modules/generacion_software/backend_generator/analyzer/model_analyzer.py`

Dueño: A4 · capa: Servicio · acción: modificar · vista: generacion · traza: CU16

- **analizador de relaciones** [módulo]
  - `JavaRelationship: annotation ∈ {'ManyToOne','OneToMany','OneToOne','ManyToMany'}; mapped_by: str | None; cascade_all: bool; orphan_removal: bool; join_table: str | None` → Campos nuevos.
  - `1 a * → lado * @ManyToOne @JoinColumn + lado 1 @OneToMany(mappedBy); 1 a 1 → @OneToOne; * a * sin clase asociación → @ManyToMany @JoinTable(name=a_b)` → Reglas por multiplicidad.
  - `composition → cascade=CascadeType.ALL, orphanRemoval=true en el lado del todo; aggregation → sin cascada` → Semántica UML.
  - `inheritance → superclase @Inheritance(strategy=InheritanceType.JOINED), subclase extends sin id propio; enum → enum Java + @Enumerated(EnumType.STRING); interface → interface Java sin tabla; dependency/realization → sin persistencia` → Herencia, enum e interfaces.
> Nota: Evitar ciclos en JSON: el lado @OneToMany lleva @JsonIgnore o los DTO exponen solo ids.

### `backend/app/modules/generacion_software/backend_generator/templates/spring_boot_templates.py`

Dueño: A4 · capa: Servicio · acción: modificar · vista: generacion · traza: CU16

- **plantillas Java** [módulo] — render_entity con las anotaciones nuevas, extends para herencia, render_enum(project, enum) nuevo, application.properties con spring.sql.init.mode=always y spring.jpa.defer-datasource-initialization=true.

### `backend/app/modules/generacion_software/backend_generator/templates/postman_templates.py`

Dueño: A4 · capa: Datos · acción: crear · vista: generacion · traza: CU16

- **Postman y semilla** [módulo]
  - `def render_postman_collection(project: SpringBootProject) -> str` → Colección v2.1: carpeta por entidad con GET lista, GET por id, POST, PUT, DELETE; variable {{baseUrl}} = http://localhost:8080; cuerpos de ejemplo según tipos.
  - `def render_data_sql(project: SpringBootProject) -> str` → 3 INSERT por entidad con UUID fijos, en orden topológico de FKs; tablas intermedias de @ManyToMany al final.

### `backend/app/modules/generacion_software/backend_generator/generator/project_writer.py`

Dueño: A4 · capa: Servicio · acción: modificar · vista: generacion · traza: CU16

- **build_file_set** [función] — Agregar postman_collection.json, src/main/resources/data.sql y un archivo por enum en enums/.

### `frontend/e2e/mejoras-2p-demo.spec.ts`

Dueño: A1 · capa: Interfaz · acción: crear · vista: compartido · traza: Flujo de demo

- **flujo de demo** [Playwright] — Dos contextos de navegador (organizador y editor): invitar y aceptar; editar con bloqueo; pedir a la IA una clase y confirmar; ver el registro de cambios en vivo; guardar versión y ver la notificación. Sin capturas comparadas por píxel (las existentes son de win32).

### `frontend/src/shared/components/Toaster.tsx`

Dueño: A1 · capa: Interfaz · acción: crear · vista: compartido · traza: Estándar de interfaz

- **Toaster y useToast** [componente + store zustand] — maqueta.html#componentes. Borde izquierdo de color por tipo (accent, amber, rose).
  - `export const useToast = create<{ items: Toast[]; push(t: Omit<Toast, 'id'>): void; dismiss(id: string): void }>()` → Estado global de avisos.
  - `export const toast = { success(title: string, text?: string): void; warning(...): void; error(...): void }` → Atajos para cualquier pantalla.
  - `export function Toaster(): JSX.Element` → Pila abajo a la derecha (respeta safe-area), máximo 4 visibles, se cierra a los 4 s.

### `frontend/src/shared/components/ConfirmDialog.tsx`

Dueño: A1 · capa: Interfaz · acción: crear · vista: compartido · traza: Estándar de interfaz

- **ConfirmDialog** [componente + hook] — maqueta.html#componentes y modal de Revocar en #gestion.
  - `export function useConfirm(): (opts: ConfirmOptions) => Promise<boolean>` → Abre el diálogo y resuelve true/false.
  - `export function ConfirmDialogHost(): JSX.Element | null` → role='dialog', aria-modal, foco inicial en Cancelar, Escape y clic fuera cancelan.

### `frontend/src/shared/components/Avatar.tsx`

Dueño: A1 · capa: Interfaz · acción: crear · vista: compartido · traza: CU19 · CU21

- **Avatar y PresenceStack** [componentes] — Iniciales en círculo; la IA usa icono de robot sobre fondo teal suave.
  - `export function Avatar({ name, userId, kind, size }: AvatarProps)` → Color estable por userId.
  - `export function PresenceStack({ people, max }: { people: { id: string; name: string; kind?: 'user' | 'ai' }[]; max?: number })` → Avatares superpuestos con +N.

### `frontend/src/shared/components/StatusBadge.tsx`

Dueño: A1 · capa: Interfaz · acción: modificar · vista: compartido · traza: Estándar de interfaz

- **StatusBadge** [componente existente] — Agregar tones 'info' y 'ai', prop dot y forma de píldora. No romper los usos actuales (tone por defecto 'neutral').

### `frontend/src/shared/components/EmptyState.tsx`

Dueño: A1 · capa: Interfaz · acción: crear · vista: compartido · traza: Estándar de interfaz

- **EmptyState** [componente] — Icono en caja, título y texto que dice qué hacer.
  - `export function EmptyState({ icon, title, description, action }: EmptyStateProps)` → Estado vacío reutilizable.

### `frontend/src/shared/components/Skeleton.tsx`

Dueño: A1 · capa: Interfaz · acción: crear · vista: compartido · traza: Estándar de interfaz

- **Skeleton** [componente] — Barra animada; usa motion-safe:animate-pulse de Tailwind.
  - `export function Skeleton({ className }: { className?: string })` → Marcador de carga.

### `frontend/src/shared/layouts/AppLayout.tsx`

Dueño: A1 · capa: Interfaz · acción: modificar · vista: compartido · traza: —

- **AppLayout** [layout existente] — Montar <Toaster /> y <ConfirmDialogHost /> una sola vez, al final del layout. Sin otros cambios.

### `frontend/src/modules/gestion_proyectos_colaboracion/components/AiProviderSettings.tsx`

Dueño: A4 · capa: Interfaz · acción: crear · vista: chat-ia · traza: CU24

- **AiProviderSettings** [componente] — maqueta.html#asistente (engranaje): popover role='radiogroup' con Ollama local, Gemini (AI Studio) y Motor de reglas; cada opción muestra disponibilidad y latencia de GET /ai/provider-health; al elegir llama a updateAiSettings y muestra toast «Proveedor actualizado».
  - `export function AiProviderSettings({ projectId, current, onChange }: { projectId: string; current: AiProvider; onChange(p: AiProvider): void })` → Solo se monta con can('ai.settings').

### `frontend/src/modules/modelado_uml_inteligente/components/ElementTypeSelect.tsx`

Dueño: A3 · capa: Interfaz · acción: crear · vista: editor · traza: CU11

- **ElementTypeSelect** [componente] — maqueta.html#editor, panel de propiedades: select «Tipo de elemento» (Clase, Interfaz, Enum, Clase abstracta) que hace PATCH /uml/classes/{id} con element_type.
  - `export function ElementTypeSelect({ value, disabled, onChange }: { value: UmlElementType; disabled?: boolean; onChange(v: UmlElementType): void })` → Selector accesible con etiqueta.

### `frontend/src/modules/modelado_uml_inteligente/hooks/useElementLocks.ts`

Dueño: A3 · capa: Interfaz · acción: crear · vista: editor · traza: CU21

- **useElementLocks** [hook] — Escucha ELEMENT_LOCKED, ELEMENT_UNLOCKED y LOCK_REJECTED; envía LOCK al seleccionar y lo renueva cada 20 s; UNLOCK al deseleccionar o desmontar.
  - `export function useElementLocks(projectId: string, diagramId: string, selectedId: string | null): { locks: Record<string, ElementLock>; lockedByOther(id: string): ElementLock | null }` → Estado de bloqueos del diagrama.

## 7. Tareas

### V0.1 · Migración única: timestamps, proveedor Gemini e índice de invitaciones

Agente A1 · Ola 0 · depende de: nada

Archivos:
- `backend/migrations/versions/f1a2b3c4d5e6_mejoras_2p_base.py`
- `backend/tests/test_mejoras_v0_migracion.py`

Pasos:
1. Crear la rama feat/m2p-a1-plataforma desde main (77463ce o posterior).
2. Crear la migración f1a2b3c4d5e6 con down_revision 'da4e5f6a7b8c' y los tres bloques de su especificación.
3. Escribir la prueba de migración usando la variable CASE_TEST_DATABASE_URL (omitir si no está definida) contra una base de datos vacía creada solo para pruebas.
4. Ejecutar upgrade, downgrade -1 y upgrade de nuevo.
5. Verificar a mano que POST /api/v1/generation/coordinated ya no responde 500 (generar desde un diagrama con 2 clases).

Listo cuando:
- alembic heads muestra una sola cabeza: f1a2b3c4d5e6
- La consulta de columnas NOT NULL sin DEFAULT en created_at/updated_at devuelve 0 filas
- POST /generation/coordinated → 201 sobre una base migrada

```
cd backend; .\.venv\Scripts\python.exe -m alembic upgrade head; .\.venv\Scripts\python.exe -m alembic heads; cd ..
cd backend; .\.venv\Scripts\python.exe -m pytest tests\test_mejoras_v0_migracion.py -q; cd ..
```

Documentar en: `docs/segundo_parcial/mejoras-2p/bitacora-agentes.md`

Instrucción completa: `tareas/V0.1.md`

### V0.2 · Redis opcional: configuración, cliente y salud

Agente A1 · Ola 0 · depende de: V0.1

Archivos:
- `backend/app/core/config/settings.py`
- `backend/app/core/redis/client.py`
- `backend/app/core/redis/__init__.py`
- `backend/app/core/workers.py`
- `backend/app/main.py`
- `backend/pyproject.toml`
- `backend/.env.example`
- `docker-compose.yml`
- `docker-compose.prod.yml`
- `backend/tests/test_mejoras_v0_redis.py`

Pasos:
1. Agregar a Settings todos los campos de la tabla «Variables de entorno».
2. Crear core/redis/client.py y __init__.py con las firmas exactas; los clientes se crean solo si redis_enabled.
3. Crear core/workers.py con start_background_workers vacío y usarlo como lifespan en main.py.
4. Agregar redis_status() a /ready.
5. Agregar redis y fakeredis a pyproject.toml; reinstalar con pip install -e ".[dev]".
6. Agregar el servicio redis a ambos docker-compose y los nombres de variables a .env.example (sin valores secretos).
7. Escribir las pruebas con fakeredis.

Listo cuando:
- Con REDIS_ENABLED=false la suite backend completa sigue en verde
- GET /ready responde 200 con redis 'disabled' o 'available'
- test_mejoras_v0_redis.py en verde

```
cd backend; .\.venv\Scripts\python.exe -m pip install -e ".[dev]"; .\.venv\Scripts\python.exe -m pytest -q; cd ..
```

Documentar en: `docs/segundo_parcial/mejoras-2p/redis.md`

Instrucción completa: `tareas/V0.2.md`

### V0.3 · Contratos compartidos: registro, permisos, eventos y tipos TS

Agente A1 · Ola 0 · depende de: V0.2

Archivos:
- `backend/app/core/changelog/contracts.py`
- `backend/app/core/changelog/__init__.py`
- `backend/app/core/changelog/hooks.py`
- `backend/app/modules/proyectos_colaboracion/permissions.py`
- `backend/app/modules/asistente_proyecto/schemas/websocket.py`
- `frontend/src/core/contracts/phase1.ts`
- `frontend/src/core/contracts/mejoras2p.ts`
- `backend/tests/test_mejoras_v0_contratos.py`

Pasos:
1. Crear core/changelog/contracts.py con los modelos y ACTION_LABELS (cubrir todas las acciones que hoy registra AuditService: buscar AuditService(…).record y audit.record en backend/app).
2. Crear hooks.py con install_change_log_hooks() sin efecto (se completa en V1.1) y llamarlo en main.py.
3. Crear permissions.py con la tabla «Permisos por rol».
4. Agregar los 4 eventos a WsEventTypeV2 y al tipo TS ProjectSocketEventV2.
5. Crear mejoras2p.ts copiando literalmente el contrato «Tipos TypeScript» y cambiar AiProjectSettings.preferred_provider a AiProvider.
6. Escribir las pruebas de contratos (los casos de nombres duplicados quedan para V0.4).

Listo cuando:
- npm run lint y npm run build sin errores de tipos
- Los casos de contratos de test_mejoras_v0_contratos.py pasan

```
cd backend; .\.venv\Scripts\python.exe -m pytest tests\test_mejoras_v0_contratos.py -q; cd ..
cd frontend; npm run lint; npm run build; cd ..
```

Documentar en: `docs/segundo_parcial/mejoras-2p/bitacora-agentes.md`

Instrucción completa: `tareas/V0.3.md`

### V0.4 · Correcciones rápidas, routers vacíos y CLAUDE.md

Agente A1 · Ola 0 · depende de: V0.3

Archivos:
- `frontend/nginx.conf`
- `backend/app/core/security/headers.py`
- `backend/tests/test_second_part_phase9_quality_gates.py`
- `backend/app/modules/modelado_uml/services/uml_service.py`
- `backend/app/modules/proyectos_colaboracion/routers/change_log.py`
- `backend/app/modules/proyectos_colaboracion/routers/invitations.py`
- `backend/app/main.py`
- `CLAUDE.md`
- `backend/tests/test_mejoras_v0_contratos.py`

Pasos:
1. Cambiar Permissions-Policy a microphone=(self) en nginx.conf y headers.py.
2. Corregir la prueba de CORS para usar settings.cors_origins[0].
3. En UmlService agregar _ensure_unique_class_name y usarlo en create_class y update_class (409 CLASS_NAME_DUPLICATED). Tocar solo esas funciones.
4. Crear change_log.py e invitations.py con routers vacíos (ver notas) y registrarlos en main.py.
5. Escribir CLAUDE.md (≤ 80 líneas) y crear la bitácora con la primera entrada.
6. Agregar los casos de nombre duplicado a test_mejoras_v0_contratos.py.
7. Unir la rama a main y avisar que la ola 1 puede empezar.

Listo cuando:
- curl -I al frontend servido por nginx muestra microphone=(self)
- La suite backend completa pasa 104/104 (la de CORS ya no falla)
- GET /docs lista los tags registro-cambios e invitaciones (sin rutas todavía)

```
cd backend; .\.venv\Scripts\python.exe -m pytest -q; cd ..
cd frontend; npm run test; npm run lint; cd ..
```

Documentar en: `CLAUDE.md`, `docs/segundo_parcial/mejoras-2p/bitacora-agentes.md`

Instrucción completa: `tareas/V0.4.md`

### V0.5 · Componentes compartidos de interfaz según la maqueta

Agente A1 · Ola 0 · depende de: V0.4

Archivos:
- `frontend/src/shared/components/Toaster.tsx`
- `frontend/src/shared/components/ConfirmDialog.tsx`
- `frontend/src/shared/components/Avatar.tsx`
- `frontend/src/shared/components/StatusBadge.tsx`
- `frontend/src/shared/components/EmptyState.tsx`
- `frontend/src/shared/components/Skeleton.tsx`
- `frontend/src/shared/layouts/AppLayout.tsx`
- `frontend/src/shared/components/sharedComponents.test.tsx`
- `docs/segundo_parcial/mejoras-2p/maqueta.html`

Pasos:
1. Copiar maqueta.html al repositorio en docs/segundo_parcial/mejoras-2p/ (ya viene con el plan) y abrirla en #componentes.
2. Crear Toaster/useToast, ConfirmDialog/useConfirm, Avatar/PresenceStack, EmptyState y Skeleton con las firmas del contrato «Componentes compartidos (V0.5)», usando clases Tailwind del proyecto y variantes dark: como el resto de componentes.
3. Ampliar StatusBadge sin romper sus usos actuales.
4. Montar Toaster y ConfirmDialogHost en AppLayout.
5. Escribir sharedComponents.test.tsx.
6. Unir a main junto con el resto de la ola 0.

Listo cuando:
- Una página de prueba temporal (o Storybook si se agrega después) muestra los 6 componentes igual que maqueta.html#componentes en claro y oscuro
- sharedComponents.test.tsx en verde y las 41 pruebas existentes de Vitest siguen en verde
- npm run lint y npm run build sin errores

```
cd frontend; npm run test -- src/shared; npm run lint; npm run build; cd ..
```

Documentar en: `docs/segundo_parcial/mejoras-2p/bitacora-agentes.md`

Instrucción completa: `tareas/V0.5.md`

### V1.1 · Registro de cambios en Redis Streams

Agente A1 · Ola 1 · depende de: V0.4

Archivos:
- `backend/app/core/changelog/service.py`
- `backend/app/core/changelog/hooks.py`
- `backend/app/core/changelog/backfill.py`
- `backend/app/modules/acceso_usuarios/services/audit_service.py`
- `backend/app/modules/proyectos_colaboracion/routers/change_log.py`
- `backend/tests/test_mejoras_v1_registro_cambios.py`

Pasos:
1. Implementar ChangeLogService (append_many con pipeline, list_project con XREVRANGE y respaldo a audit_logs, resolve_names).
2. Completar install_change_log_hooks con los listeners after_commit/after_rollback sobre la clase Session.
3. Modificar AuditService.record para encolar con queue_change cuando hay project_id.
4. Implementar el endpoint GET /projects/{project_id}/change-log.
5. Implementar el comando backfill.
6. Probar con fakeredis inyectado mediante set_test_client.

Listo cuando:
- Crear una clase desde la interfaz agrega una entrada visible con redis-cli XREVRANGE case:changelog:project:<id> + - COUNT 1
- Con Redis detenido, crear una clase sigue respondiendo 201
- test_mejoras_v1_registro_cambios.py en verde y la suite completa sin regresiones

```
cd backend; .\.venv\Scripts\python.exe -m pytest tests\test_mejoras_v1_registro_cambios.py -q; .\.venv\Scripts\python.exe -m pytest -q; cd ..
```

Documentar en: `docs/segundo_parcial/mejoras-2p/redis.md`

Instrucción completa: `tareas/V1.1.md`

### V1.2 · Panel «Registro de cambios» en el espacio colaborativo

Agente A1 · Ola 1 · depende de: V1.1, V0.5

Archivos:
- `frontend/src/modules/gestion_proyectos_colaboracion/services/changeLogService.ts`
- `frontend/src/modules/gestion_proyectos_colaboracion/components/ChangeLogPanel.tsx`
- `frontend/src/modules/gestion_proyectos_colaboracion/pages/ProjectWorkspacePage.tsx`
- `frontend/src/modules/gestion_proyectos_colaboracion/components/ChangeLogPanel.test.tsx`

Pasos:
1. Abrir docs/segundo_parcial/mejoras-2p/maqueta.html#registro y la captura del plan; implementar esa pantalla con datos reales (API y WebSocket) y los componentes de V0.5, respetando estructura, textos y estados de la maqueta.
2. Crear changeLogService con apiClient.
3. Crear ChangeLogPanel con filtros, paginación, estados y suscripción al socket del proyecto (usar el cliente de tiempo real existente en core/websocket).
4. Agregar la pestaña en ProjectWorkspacePage sin alterar la lista de chats.
5. Escribir las pruebas con Testing Library y el servicio simulado.

Listo cuando:
- En /proyectos/:id/colaborativo, la pestaña Registro muestra las entradas con autor y hora
- Al crear una clase en otra pestaña, el panel se actualiza en ≤ 2 s
- npm run test, lint y build en verde
- La pantalla coincide con maqueta.html#registro en estructura, textos y estados a 1440 px y 390 px (sin scroll horizontal), con datos reales

```
cd frontend; npm run test -- src/modules/gestion_proyectos_colaboracion; npm run lint; npm run build; cd ..
```

Documentar en: `docs/segundo_parcial/mejoras-2p/bitacora-agentes.md`

Instrucción completa: `tareas/V1.2.md`

### V1.3 · Permisos por rol aplicados en el backend (incluye Lector)

Agente A2 · Ola 1 · depende de: V0.4

Archivos:
- `backend/app/modules/proyectos_colaboracion/validators/project_validator.py`
- `backend/app/modules/proyectos_colaboracion/services/project_service.py`
- `backend/app/modules/proyectos_colaboracion/schemas/project.py`
- `backend/app/modules/proyectos_colaboracion/routers/projects.py`
- `backend/app/modules/modelado_uml/services/uml_service.py`
- `backend/app/modules/asistente_proyecto/services/action_execution_service.py`
- `backend/app/modules/asistente_proyecto/services/assistant_service.py`
- `backend/app/modules/generacion_software/services/generation_service.py`
- `backend/app/modules/generacion_software/services/theme_service.py`
- `backend/tests/test_mejoras_v1_permisos.py`

Pasos:
1. Crear la rama feat/m2p-a2-permisos desde main con la ola 0 unida.
2. Implementar ensure_project_permission y member_permissions; dejar ensure_organizer como alias.
3. Recorrer cada servicio de la lista y reemplazar los chequeos de membresía en operaciones que modifican por el código de la tabla «Permisos por rol».
4. Aceptar LECTOR en los esquemas y agregar GET members/me (declarado antes de las rutas con member_id).
5. Validar que los códigos otorgados con POST members/{id}/permissions estén en PERMISSION_CODES (422 si no).
6. Escribir las pruebas por rol y correr la suite completa.

Listo cuando:
- test_mejoras_v1_permisos.py en verde
- La suite backend completa sigue en verde (sin cambiar las pruebas existentes salvo que esperaran el texto de ensure_organizer)

```
cd backend; .\.venv\Scripts\python.exe -m pytest tests\test_mejoras_v1_permisos.py -q; .\.venv\Scripts\python.exe -m pytest -q; cd ..
```

Documentar en: `docs/segundo_parcial/mejoras-2p/permisos.md`

Instrucción completa: `tareas/V1.3.md`

### V1.4 · Hook de permisos y PermissionGate en el frontend

Agente A2 · Ola 1 · depende de: V1.3

Archivos:
- `frontend/src/core/permissions/useProjectPermissions.ts`
- `frontend/src/core/permissions/PermissionGate.tsx`
- `frontend/src/core/permissions/useProjectPermissions.test.tsx`

Pasos:
1. Crear el hook con un store zustand por projectId y GET members/me.
2. Crear PermissionGate.
3. Escribir las pruebas.
4. Documentar en permisos.md cómo usarlo (lo aplican A3 y A4 en sus pantallas).

Listo cuando:
- npm run test -- src/core/permissions en verde
- npm run lint y build en verde

```
cd frontend; npm run test -- src/core/permissions; npm run lint; npm run build; cd ..
```

Documentar en: `docs/segundo_parcial/mejoras-2p/permisos.md`

Instrucción completa: `tareas/V1.4.md`

### V1.5 · Editor: interfaz, enum, abstracta, dependencia, realización y visibilidades

Agente A3 · Ola 1 · depende de: V0.4, V0.5

Archivos:
- `frontend/src/modules/modelado_uml_inteligente/types/uml.ts`
- `frontend/src/modules/modelado_uml_inteligente/pages/UmlEditorPage.tsx`
- `frontend/src/modules/modelado_uml_inteligente/components/JointUmlCanvas.tsx`
- `frontend/src/modules/modelado_uml_inteligente/components/ElementTypeSelect.tsx`
- `frontend/src/modules/modelado_uml_inteligente/components/JointUmlCanvas.test.tsx`

Pasos:
1. Crear la rama feat/m2p-a3-editor desde main con la ola 0 unida.
2. Abrir docs/segundo_parcial/mejoras-2p/maqueta.html#editor y la captura del plan; implementar esa pantalla con datos reales (API y WebSocket) y los componentes de V0.5, respetando estructura, textos y estados de la maqueta.
3. Ampliar los tipos en uml.ts.
4. Agregar las herramientas Dependencia y Realización a la paleta y el selector Tipo al panel de la clase (extraer a un componente ElementTypeSelect).
5. Agregar protected y package a visibilityOptions.
6. Dibujar estereotipos, cursiva, enum sin métodos y los marcadores nuevos en JointUmlCanvas.
7. Escribir las pruebas del lienzo.

Listo cuando:
- Se puede crear una interfaz y una clase que la realiza; el lienzo las dibuja como en UML 2.5
- npm run test -- src/modules/modelado_uml_inteligente, lint y build en verde
- La pantalla coincide con maqueta.html#editor en estructura, textos y estados a 1440 px y 390 px (sin scroll horizontal), con datos reales

```
cd frontend; npm run test -- src/modules/modelado_uml_inteligente; npm run lint; npm run build; cd ..
```

Documentar en: `docs/segundo_parcial/mejoras-2p/editor-uml.md`

Instrucción completa: `tareas/V1.5.md`

### V1.6 · Backend UML: validación de valores y XMI sin pérdida

Agente A3 · Ola 1 · depende de: V0.4

Archivos:
- `backend/app/modules/modelado_uml/schemas/uml.py`
- `backend/app/modules/modelado_uml/engine/xmi.py`
- `backend/tests/test_mejoras_v1_editor_xmi.py`

Pasos:
1. Agregar validadores de element_type, visibility y relationship_type en los esquemas.
2. En xmi.py, exportar isAbstract, estereotipos, visibilidades y Dependency/Abstraction.
3. En la importación, leer aggregation de los AssociationEnd y conservar composition/aggregation; aceptar Dependency y Abstraction sin error.
4. Escribir las pruebas de ida y vuelta y con exportar.xml.

Listo cuando:
- test_mejoras_v1_editor_xmi.py en verde
- Las pruebas XMI existentes siguen en verde

```
cd backend; .\.venv\Scripts\python.exe -m pytest tests\test_mejoras_v1_editor_xmi.py tests\test_phase6_uml_engine.py -q; cd ..
```

Documentar en: `docs/segundo_parcial/mejoras-2p/editor-uml.md`

Instrucción completa: `tareas/V1.6.md`

### V1.7 · Proveedor Gemini opcional e intercambiable

Agente A4 · Ola 1 · depende de: V0.4

Archivos:
- `ai-engine/ai_engine/providers/gemini_provider.py`
- `ai-engine/ai_engine/providers/__init__.py`
- `ai-engine/tests/test_gemini_provider.py`
- `backend/app/modules/asistente_proyecto/services/provider_factory.py`
- `backend/app/modules/asistente_proyecto/services/project_ai_application_service.py`
- `backend/app/modules/asistente_proyecto/schemas/assistant.py`
- `backend/app/modules/asistente_proyecto/models/ai_project_settings.py`
- `backend/tests/test_mejoras_v1_proveedor.py`

Pasos:
1. Crear la rama feat/m2p-a4-ia-generacion desde main con la ola 0 unida.
2. Consultar la documentación vigente de Google AI Studio (API generateContent y lista de modelos) y anotar en la bitácora el identificador de modelo Flash elegido; usarlo como valor por defecto de GEMINI_MODEL en .env.example mediante una nota (el campo en settings lo dejó vacío A1).
3. Implementar GeminiProvider siguiendo OllamaProvider como modelo (mismos errores tipados y reintentos).
4. Agregar get_gemini_provider y select_provider en provider_factory y usar select_provider en project_ai_application_service (solo el bloque de selección).
5. Ampliar el Literal y el CheckConstraint con 'gemini'.
6. Escribir las pruebas con httpx.MockTransport (sin red).

Listo cuando:
- test_gemini_provider.py y test_mejoras_v1_proveedor.py en verde
- Con GEMINI_API_KEY en .env local y proveedor gemini, una pregunta en el chat recibe respuesta (verificación manual, anotar en bitácora)
- Sin clave, el chat sigue respondiendo con reglas

```
cd ai-engine; .\.venv\Scripts\python.exe -m pytest tests\test_gemini_provider.py -q; cd ..
cd backend; .\.venv\Scripts\python.exe -m pip install -e ..\ai-engine; .\.venv\Scripts\python.exe -m pytest tests\test_mejoras_v1_proveedor.py tests\test_second_part_phase2_ai.py -q; cd ..
```

Documentar en: `docs/segundo_parcial/mejoras-2p/ia-proveedores.md`

Instrucción completa: `tareas/V1.7.md`

### V1.8 · Voz en el chat de IA y selector de proveedor

Agente A4 · Ola 1 · depende de: V1.7, V0.5

Archivos:
- `frontend/src/core/voice/useSpeechRecognition.ts`
- `frontend/src/core/voice/useSpeechRecognition.test.ts`
- `frontend/src/modules/gestion_proyectos_colaboracion/components/ProjectAiAssistant.tsx`
- `frontend/src/modules/gestion_proyectos_colaboracion/components/AiProviderSettings.tsx`

Pasos:
1. Abrir docs/segundo_parcial/mejoras-2p/maqueta.html#asistente y la captura del plan; implementar esa pantalla con datos reales (API y WebSocket) y los componentes de V0.5, respetando estructura, textos y estados de la maqueta.
2. Crear useSpeechRecognition con la firma del contrato.
3. En ProjectAiAssistant agregar el botón de micrófono, el texto parcial, el interruptor «Enviar al terminar» y la etiqueta «Sugerencia de la IA» para metadata_json.kind='proactive'.
4. Agregar el engranaje con el selector de proveedor que llama a phase1Service.updateAiSettings y muestra aiProviderHealth.
5. Ocultar Confirmar/Rechazar y el engranaje según permisos si V1.4 ya está en main (ver nota del archivo).
6. Escribir las pruebas del hook.

Listo cuando:
- En Chrome sobre localhost, dictar «crea una clase Factura» envía la interacción y aparece la propuesta
- Firefox (sin SpeechRecognition) no muestra el botón
- npm run test, lint y build en verde
- La pantalla coincide con maqueta.html#asistente en estructura, textos y estados a 1440 px y 390 px (sin scroll horizontal), con datos reales

```
cd frontend; npm run test -- src/core/voice src/modules/gestion_proyectos_colaboracion; npm run lint; npm run build; cd ..
```

Documentar en: `docs/segundo_parcial/mejoras-2p/ia-proveedores.md`

Instrucción completa: `tareas/V1.8.md`

### V2.1 · Consumidor del registro e IA proactiva

Agente A1 · Ola 2 · depende de: V1.2

Archivos:
- `backend/app/core/changelog/consumer.py`
- `backend/app/core/workers.py`
- `backend/app/modules/asistente_proyecto/services/proactive_advisor_service.py`
- `backend/tests/test_mejoras_v2_proactivo.py`

Pasos:
1. Implementar ChangeLogConsumer con el grupo 'case-workers' y arrancarlo en start_background_workers solo si redis_enabled y ai_proactive_enabled.
2. Difundir CHANGE_LOGGED con actor_display_name resuelto.
3. Implementar ProactiveAdvisorService con los tres disparadores, el cooldown y la regla de no reaccionar a sí misma.
4. Publicar el mensaje y las recomendaciones con los servicios existentes (AssistantService.create_message y ProjectAiEventPublisher).
5. Escribir las pruebas con fakeredis y servicios simulados.

Listo cuando:
- Con dos navegadores abiertos, tras 5 cambios en un diagrama con una clase vacía aparece «Sugerencia de la IA» para ambos sin que nadie pregunte
- No aparece más de una sugerencia cada 120 s por proyecto
- test_mejoras_v2_proactivo.py en verde

```
cd backend; .\.venv\Scripts\python.exe -m pytest tests\test_mejoras_v2_proactivo.py -q; .\.venv\Scripts\python.exe -m pytest -q; cd ..
```

Documentar en: `docs/segundo_parcial/mejoras-2p/ia-equipo.md`

Instrucción completa: `tareas/V2.1.md`

### V2.2 · IA consciente del equipo: autores y actividad por integrante

Agente A1 · Ola 2 · depende de: V2.1

Archivos:
- `ai-engine/ai_engine/context/contracts.py`
- `backend/app/modules/asistente_proyecto/services/context_builder.py`
- `ai-engine/ai_engine/orchestration/intent_classifier.py`
- `ai-engine/ai_engine/providers/rule_engine_provider.py`
- `ai-engine/ai_engine/prompts/unified_system.md`
- `ai-engine/tests/test_mejoras_equipo.py`

Pasos:
1. Agregar author_display_name y team_activity a los contratos de contexto (con valores por defecto).
2. En ContextBuilder, completar ambos campos desde el repositorio y el Stream, respetando el presupuesto.
3. Ampliar coordinate_team en el clasificador y responderla en el motor de reglas.
4. Actualizar el prompt de sistema para que la IA actúe como integrante, nombre a las personas y modere.
5. Escribir las pruebas del motor.

Listo cuando:
- Preguntar «¿qué hizo cada uno?» en el chat responde con una línea por integrante (con y sin Ollama)
- test_mejoras_equipo.py en verde y la suite ai-engine sin regresiones

```
cd ai-engine; .\.venv\Scripts\python.exe -m pytest -q; cd ..
cd backend; .\.venv\Scripts\python.exe -m pip install -e ..\ai-engine; .\.venv\Scripts\python.exe -m pytest tests\test_second_part_phase3_collaboration.py -q; cd ..
```

Documentar en: `docs/segundo_parcial/mejoras-2p/ia-equipo.md`

Instrucción completa: `tareas/V2.2.md`

### V2.3 · Invitaciones al proyecto (backend)

Agente A2 · Ola 2 · depende de: V1.4

Archivos:
- `backend/app/modules/proyectos_colaboracion/routers/invitations.py`
- `backend/app/modules/proyectos_colaboracion/services/invitation_service.py`
- `backend/app/modules/proyectos_colaboracion/repositories/invitation_repository.py`
- `backend/app/modules/proyectos_colaboracion/schemas/invitation.py`
- `backend/app/modules/proyectos_colaboracion/services/project_service.py`
- `backend/tests/test_mejoras_v2_invitaciones.py`

Pasos:
1. Crear el repositorio, los esquemas y el servicio con las firmas exactas.
2. Completar los dos routers del archivo invitations.py.
3. Agregar add_member_from_invitation a ProjectService.
4. Emitir las notificaciones con NotificationService.record (category 'access').
5. Escribir las pruebas.

Listo cuando:
- test_mejoras_v2_invitaciones.py en verde
- GET /docs muestra las 6 rutas de invitaciones

```
cd backend; .\.venv\Scripts\python.exe -m pytest tests\test_mejoras_v2_invitaciones.py -q; .\.venv\Scripts\python.exe -m pytest -q; cd ..
```

Documentar en: `docs/segundo_parcial/mejoras-2p/permisos.md`

Instrucción completa: `tareas/V2.3.md`

### V2.4 · Invitaciones y permisos en la interfaz

Agente A2 · Ola 2 · depende de: V2.3

Archivos:
- `frontend/src/modules/gestion_proyectos_colaboracion/services/invitationService.ts`
- `frontend/src/modules/gestion_proyectos_colaboracion/pages/ProjectManagementPage.tsx`
- `frontend/src/shared/components/NotificationCenter.tsx`
- `frontend/src/modules/gestion_proyectos_colaboracion/pages/ProjectsPage.tsx`
- `frontend/src/modules/gestion_proyectos_colaboracion/pages/ProjectManagementPage.test.tsx`

Pasos:
1. Abrir docs/segundo_parcial/mejoras-2p/maqueta.html#gestion y la captura del plan; implementar esa pantalla con datos reales (API y WebSocket) y los componentes de V0.5, respetando estructura, textos y estados de la maqueta.
2. Crear invitationService.
3. Implementar también la tarjeta «Mis invitaciones» y la campana según docs/segundo_parcial/mejoras-2p/maqueta.html#invitaciones.
4. Rediseñar la sección de integrantes de ProjectManagementPage (formulario por correo, pendientes, rol Lector, modal de confirmación propio).
5. Agregar Aceptar/Rechazar en NotificationCenter y el bloque «Mis invitaciones» en ProjectsPage.
6. Envolver la gestión con PermissionGate.
7. Escribir las pruebas de la página.

Listo cuando:
- Organizador invita a un correo con cuenta; ese usuario ve la invitación en la campana y en Proyectos, la acepta y entra al proyecto
- Un editor no ve el formulario de invitación
- npm run test, lint y build en verde
- La pantalla coincide con maqueta.html#gestion en estructura, textos y estados a 1440 px y 390 px (sin scroll horizontal), con datos reales

```
cd frontend; npm run test -- src/modules/gestion_proyectos_colaboracion src/shared; npm run lint; npm run build; cd ..
```

Documentar en: `docs/segundo_parcial/mejoras-2p/permisos.md`

Instrucción completa: `tareas/V2.4.md`

### V2.5 · Bloqueo de elementos (backend WebSocket y guarda 423)

Agente A3 · Ola 2 · depende de: V1.6

Archivos:
- `backend/app/websocket/locks.py`
- `backend/app/websocket/router.py`
- `backend/app/websocket/connection_manager.py`
- `backend/app/modules/modelado_uml/services/uml_service.py`
- `backend/tests/test_mejoras_v2_bloqueos.py`

Pasos:
1. Crear ElementLockService con Redis y modo en memoria.
2. Manejar LOCK_ELEMENT/UNLOCK_ELEMENT en router.py con la validación de uml.edit y emitir los eventos v2.
3. Liberar al desconectar la última pestaña (user_connection_count) y emitir los vencidos del modo en memoria.
4. Agregar _ensure_not_locked_by_other a las operaciones de modificación de UmlService (sin tocar la lógica de permisos de V1.3).
5. Escribir las pruebas con TestClient WebSocket.

Listo cuando:
- test_mejoras_v2_bloqueos.py en verde
- Las pruebas de colaboración existentes (fase 3) siguen en verde

```
cd backend; .\.venv\Scripts\python.exe -m pytest tests\test_mejoras_v2_bloqueos.py tests\test_second_part_phase3_collaboration.py tests\test_collaboration_versions.py -q; cd ..
```

Documentar en: `docs/segundo_parcial/mejoras-2p/editor-uml.md`

Instrucción completa: `tareas/V2.5.md`

### V2.6 · Bloqueos, IA visible y modo lectura en el editor

Agente A3 · Ola 2 · depende de: V2.5, V1.5

Archivos:
- `frontend/src/core/websocket/projectSocket.ts`
- `frontend/src/modules/modelado_uml_inteligente/pages/UmlEditorPage.tsx`
- `frontend/src/modules/modelado_uml_inteligente/components/JointUmlCanvas.tsx`
- `frontend/src/modules/gestion_proyectos_colaboracion/components/ProjectPresenceIndicator.tsx`
- `frontend/src/modules/modelado_uml_inteligente/hooks/useElementLocks.ts`
- `frontend/src/modules/modelado_uml_inteligente/components/JointUmlCanvas.test.tsx`

Pasos:
1. Abrir docs/segundo_parcial/mejoras-2p/maqueta.html#editor y la captura del plan; implementar esa pantalla con datos reales (API y WebSocket) y los componentes de V0.5, respetando estructura, textos y estados de la maqueta.
2. Agregar lockElement/unlockElement al cliente de tiempo real.
3. En el editor, crear un hook useElementLocks que mantenga lockedElements a partir de los eventos, envíe LOCK al seleccionar y lo renueve cada 20 s, y UNLOCK al deseleccionar.
4. Deshabilitar el panel de propiedades cuando el elemento lo tiene otro; toast en LOCK_REJECTED.
5. Modo solo lectura con useProjectPermissions(projectId).can('uml.edit').
6. Mostrar al «Asistente CASE» en ProjectPresenceIndicator con su estado.
7. Ampliar las pruebas del lienzo con el candado.

Listo cuando:
- Con dos navegadores: al seleccionar una clase, el otro ve el candado con el nombre en ≤ 1 s y no puede editarla
- Un Lector ve el lienzo sin herramientas de edición
- La IA aparece en la lista de presentes y cambia a «Pensando…» mientras responde
- La pantalla coincide con maqueta.html#editor en estructura, textos y estados a 1440 px y 390 px (sin scroll horizontal), con datos reales

```
cd frontend; npm run test -- src/modules/modelado_uml_inteligente src/modules/gestion_proyectos_colaboracion; npm run lint; npm run build; cd ..
```

Documentar en: `docs/segundo_parcial/mejoras-2p/editor-uml.md`

Instrucción completa: `tareas/V2.6.md`

### V2.7 · Deshacer y rehacer (Ctrl+Z / Ctrl+Y)

Agente A3 · Ola 2 · depende de: V2.6

Archivos:
- `frontend/src/modules/modelado_uml_inteligente/store/umlHistory.ts`
- `frontend/src/modules/modelado_uml_inteligente/store/umlHistory.test.ts`
- `frontend/src/modules/modelado_uml_inteligente/pages/UmlEditorPage.tsx`

Pasos:
1. Abrir docs/segundo_parcial/mejoras-2p/maqueta.html#editor y la captura del plan; implementar esa pantalla con datos reales (API y WebSocket) y los componentes de V0.5, respetando estructura, textos y estados de la maqueta.
2. Crear el store umlHistory.
3. Registrar en el editor cada operación propia con su inversa (crear↔eliminar clase, atributo, método y relación; actualizar con el valor anterior; mover posición).
4. Atajos Ctrl+Z y Ctrl+Y (Cmd en macOS) ignorados cuando el foco está en un campo de texto; botones en la barra con tooltip.
5. Vaciar la pila al cambiar de diagrama o al recibir PROJECT_VERSION_RESTORED.
6. Escribir las pruebas del store.

Listo cuando:
- Crear una clase y Ctrl+Z la elimina; Ctrl+Y la vuelve a crear
- Ctrl+Z dentro de un campo de texto no deshace el diagrama
- umlHistory.test.ts en verde
- La pantalla coincide con maqueta.html#editor en estructura, textos y estados a 1440 px y 390 px (sin scroll horizontal), con datos reales

```
cd frontend; npm run test -- src/modules/modelado_uml_inteligente; npm run lint; npm run build; cd ..
```

Documentar en: `docs/segundo_parcial/mejoras-2p/editor-uml.md`

Instrucción completa: `tareas/V2.7.md`

### V2.8 · Generador Spring Boot: relaciones JPA completas, herencia y enum

Agente A4 · Ola 2 · depende de: V1.8

Archivos:
- `backend/app/modules/generacion_software/backend_generator/analyzer/model_analyzer.py`
- `backend/app/modules/generacion_software/backend_generator/templates/spring_boot_templates.py`
- `frontend/src/modules/gestion_proyectos_colaboracion/components/ProjectAiAssistant.tsx`
- `backend/tests/test_mejoras_v2_generador.py`

Pasos:
1. Ampliar JavaRelationship y las reglas por multiplicidad y tipo UML.
2. Actualizar render_entity, DTO y servicios para las relaciones bidireccionales (los DTO exponen ids del lado relacionado para evitar ciclos).
3. Agregar herencia JOINED, enums e interfaces.
4. Si V1.4 ya está en main y quedó un TODO en ProjectAiAssistant (V1.8), completarlo aquí y anotarlo.
5. Escribir las pruebas y correr el gate de Maven.

Listo cuando:
- test_mejoras_v2_generador.py en verde
- Con CASE_VERIFY_GENERATED_SPRING=1 el proyecto generado de prueba compila y pasa mvn test
- Las pruebas de fase 5 y fase 8 del generador siguen en verde

```
cd backend; .\.venv\Scripts\python.exe -m pytest tests\test_mejoras_v2_generador.py tests\test_phase8_spring_boot_generator.py tests\test_second_part_phase5_coordinated_generation.py -q; cd ..
cd backend; $env:CASE_VERIFY_GENERATED_SPRING='1'; .\.venv\Scripts\python.exe -m pytest tests\test_second_part_phase9_generated_toolchains.py -k spring -q; Remove-Item Env:CASE_VERIFY_GENERATED_SPRING; cd ..
```

Documentar en: `docs/segundo_parcial/mejoras-2p/generador.md`

Instrucción completa: `tareas/V2.8.md`

### V2.9 · Colección Postman y datos semilla

Agente A4 · Ola 2 · depende de: V2.8

Archivos:
- `backend/app/modules/generacion_software/backend_generator/templates/postman_templates.py`
- `backend/app/modules/generacion_software/backend_generator/generator/project_writer.py`
- `backend/tests/test_mejoras_v2_generador.py`

Pasos:
1. Crear postman_templates.py con las dos funciones.
2. Agregar los archivos nuevos en build_file_set y las propiedades de inicialización SQL.
3. Agregar los casos de Postman y data.sql a test_mejoras_v2_generador.py.
4. Probar a mano: generar, mvn spring-boot:run contra PostgreSQL local e importar la colección en Postman.

Listo cuando:
- El ZIP generado incluye postman_collection.json y src/main/resources/data.sql
- Al arrancar el backend generado, GET /api/<entidad> devuelve las 3 filas semilla

```
cd backend; .\.venv\Scripts\python.exe -m pytest tests\test_mejoras_v2_generador.py -q; cd ..
```

Documentar en: `docs/segundo_parcial/mejoras-2p/generador.md`

Instrucción completa: `tareas/V2.9.md`

### V3.1 · Prueba integral del flujo de demo y regresión completa

Agente A1 · Ola 3 · depende de: V2.2

Archivos:
- `backend/tests/test_mejoras_v3_flujo.py`
- `frontend/e2e/mejoras-2p-demo.spec.ts`

Pasos:
1. Unir a main todas las ramas de la ola 2 y resolver conflictos de integración (solo en archivos sin dueño en la ola 3).
2. Escribir la prueba de flujo por API con fakeredis y repetirla con REDIS_ENABLED=false.
3. Escribir el spec Playwright de dos usuarios.
4. Correr todas las suites; abrir defectos en la bitácora con el dueño del archivo.

Listo cuando:
- test_mejoras_v3_flujo.py en verde en ambos modos
- npx playwright test e2e/mejoras-2p-demo.spec.ts pasa con backend y frontend locales
- Backend, ai-engine y frontend completos en verde

```
cd backend; .\.venv\Scripts\python.exe -m pytest -q; cd ..
cd ai-engine; .\.venv\Scripts\python.exe -m pytest -q; cd ..
cd frontend; npm run test; npm run lint; npm run build; npx playwright test e2e/mejoras-2p-demo.spec.ts; cd ..
```

Documentar en: `docs/segundo_parcial/mejoras-2p/bitacora-agentes.md`

Instrucción completa: `tareas/V3.1.md`

### V3.2 · Documentación: casos de uso nuevos y trazabilidad

Agente A2 · Ola 3 · depende de: V2.4

Archivos:
- `docs/segundo_parcial/mejoras-2p/casos-de-uso.md`
- `docs/segundo_parcial/fase9/02_matriz_trazabilidad.md`
- `README.md`

Pasos:
1. Escribir las fichas de CU19 a CU25 con el formato del documento del 1.er parcial del colega (propósito, resumen, actores, precondiciones, flujo principal, postcondiciones, alternativos) más paquete, permisos y relaciones «include»/«extend».
2. Agregar CU19–CU25 a la matriz de trazabilidad con archivos y pruebas.
3. Actualizar README.md con Redis (Windows: Memurai o WSL), Gemini y los comandos de pruebas.

Listo cuando:
- Cada CU nuevo enlaza a sus pruebas y archivos
- README permite levantar el sistema desde cero sin Docker

Documentar en: `docs/segundo_parcial/mejoras-2p/casos-de-uso.md`, `README.md`

Instrucción completa: `tareas/V3.2.md`

### V3.3 · Guion de demo y capturas

Agente A3 · Ola 3 · depende de: V2.7

Archivos:
- `docs/segundo_parcial/mejoras-2p/guion-demo.md`

Pasos:
1. Escribir el guion paso a paso de la defensa (10–12 minutos) siguiendo los apuntes del docente: 1.er parcial sin fallas, IA como integrante, registro NoSQL, roles y permisos, versiones con push, móvil informativo.
2. Comparar cada pantalla terminada con su ancla de maqueta.html y anotar en el guion cualquier diferencia aceptada.
3. Tomar capturas (escritorio y móvil) de cada paso en docs/segundo_parcial/mejoras-2p/capturas/.
4. Incluir un plan B si Ollama no responde (cambiar a Gemini o reglas desde el engranaje).

Listo cuando:
- El guion se puede seguir sin conocer el código
- Hay al menos una captura por punto de los apuntes del docente

Documentar en: `docs/segundo_parcial/mejoras-2p/guion-demo.md`

Instrucción completa: `tareas/V3.3.md`

### V3.4 · Verificación en el equipo de demo: Ollama, Maven y Flutter

Agente A4 · Ola 3 · depende de: V2.9

Archivos:
- `docs/segundo_parcial/mejoras-2p/verificacion-entorno.md`

Pasos:
1. En el equipo de la demo: ollama pull del modelo pequeño configurado, GET /ai/provider-health disponible y una interacción real con Qwen.
2. Correr los gates CASE_VERIFY_GENERATED_SPRING=1 y CASE_VERIFY_GENERATED_FLUTTER=1.
3. flutter analyze y flutter test en mobile/, y probar la app en un teléfono o emulador contra la IP LAN del backend.
4. Registrar versiones de herramientas, RAM usada por Qwen y tiempos de respuesta.

Listo cuando:
- Los dos gates pasan en el equipo de demo
- La app móvil abre un proyecto, el visor UML y la conversación de IA

```
ollama list
cd backend; $env:CASE_VERIFY_GENERATED_SPRING='1'; $env:CASE_VERIFY_GENERATED_FLUTTER='1'; .\.venv\Scripts\python.exe -m pytest tests\test_second_part_phase9_generated_toolchains.py -q; cd ..
cd mobile; flutter analyze; flutter test; cd ..
```

Documentar en: `docs/segundo_parcial/mejoras-2p/verificacion-entorno.md`

Instrucción completa: `tareas/V3.4.md`

## 8. Pruebas

### `backend/tests/test_mejoras_v0_migracion.py` (A1)

- [ ] Sin CASE_TEST_DATABASE_URL → la prueba se omite con motivo claro
- [ ] upgrade head sobre base vacía → ninguna columna created_at/updated_at NOT NULL queda sin DEFAULT (consulta a information_schema.columns)
- [ ] INSERT en coordinated_generations sin created_at → no falla
- [ ] downgrade -1 y upgrade head → sin errores y una sola cabeza (alembic heads)
- [ ] ai_project_settings acepta preferred_provider='gemini'

### `backend/tests/test_mejoras_v0_redis.py` (A1)

- [ ] redis_enabled=False → get_redis() es None y redis_status() == 'disabled'
- [ ] Con fakeredis inyectado → redis_status() == 'available' y redis_key('lock','x') == 'case:lock:x'
- [ ] Cliente que lanza ConnectionError → redis_status() == 'unavailable' sin excepción
- [ ] GET /ready con Redis deshabilitado → 200 y redis == 'disabled'

### `backend/tests/test_mejoras_v0_contratos.py` (A1)

- [ ] ROLE_DEFAULTS['LECTOR'] == {'project.read', 'ai.chat'}
- [ ] effective_permissions('EDITOR', ['members.manage', 'inventado']) incluye members.manage y no 'inventado'
- [ ] Todos los códigos de ROLE_DEFAULTS están en PERMISSION_CODES
- [ ] WebSocketEventV2(type='CHANGE_LOGGED', …) valida; type='OTRO' falla
- [ ] build_summary('CREATE_CLASS', {'name': 'Producto'}) == 'Creó la clase Producto'
- [ ] POST clase con nombre repetido (distinto uso de mayúsculas) en el mismo diagrama → 409 CLASS_NAME_DUPLICATED

### `backend/tests/test_mejoras_v1_registro_cambios.py` (A1)

- [ ] Crear una clase y hacer commit → 1 entrada en case:changelog:project:{id} y en case:changelog:all con action CREATE_CLASS
- [ ] Operación que hace rollback → 0 entradas
- [ ] Metadata con 'password' o 'token' → no aparece en el Stream
- [ ] GET change-log?limit=2 con 3 entradas → 2 items y next_cursor; con before_id=next_cursor → la tercera
- [ ] Filtro actor_id → solo entradas de ese usuario, con actor_display_name
- [ ] Redis caído → 200 con source == 'postgres_fallback' y la escritura de dominio no falla
- [ ] No integrante → 403
- [ ] backfill_project reconstruye tantas entradas como audit_logs del proyecto

### `frontend/src/modules/gestion_proyectos_colaboracion/components/ChangeLogPanel.test.tsx` (A1)

- [ ] Renderiza autor, resumen y hora relativa de cada entrada
- [ ] source='postgres_fallback' → muestra «Registro en modo respaldo»
- [ ] Evento CHANGE_LOGGED con id nuevo → aparece arriba; con id repetido → no se duplica
- [ ] Filtro por integrante → llama al servicio con actor_id
- [ ] «Cargar más» usa next_cursor como before_id

### `backend/tests/test_mejoras_v1_permisos.py` (A2)

- [ ] LECTOR: POST clase → 403 PERMISSION_DENIED; GET modelo → 200
- [ ] EDITOR: restaurar versión → 403; guardar versión → 201
- [ ] EDITOR con permiso otorgado versions.restore → restaurar 200
- [ ] LECTOR confirma acción IA → 403; EDITOR → 200
- [ ] GET members/me como LECTOR → permissions == ['ai.chat', 'project.read']
- [ ] AddMemberRequest con project_role='LECTOR' válido; 'ADMIN' → 422
- [ ] Las pruebas existentes de fases 1–9 siguen en verde

### `frontend/src/core/permissions/useProjectPermissions.test.tsx` (A2)

- [ ] Mientras carga → can() devuelve false
- [ ] Respuesta EDITOR → can('uml.edit') true y can('members.manage') false
- [ ] Dos componentes con el mismo projectId → una sola petición
- [ ] PermissionGate oculta children sin el permiso y muestra fallback

### `backend/tests/test_mejoras_v1_editor_xmi.py` (A3)

- [ ] Crear clase con element_type='interface' → 201; element_type='tabla' → 422
- [ ] Atributo con visibility='protected' → 201; 'friend' → 422
- [ ] Relación dependency y realization → 201
- [ ] Exportar e importar (ida y vuelta) un diagrama con composición, agregación, herencia, interfaz, enum y abstracta → mismos tipos y visibilidades
- [ ] Importar exportar.xml de Enterprise Architect → sin errores y con la misma cantidad de clases
- [ ] Importar XMI con UML:Dependency y UML:Abstraction → 201 (antes 500)

### `frontend/src/modules/modelado_uml_inteligente/components/JointUmlCanvas.test.tsx` (A3)

- [ ] Interfaz muestra «interface» sobre el nombre
- [ ] Clase abstracta muestra el nombre en cursiva
- [ ] Visibilidades se dibujan como + - # ~
- [ ] Realización usa línea punteada con marcador de triángulo hueco
- [ ] lockedElements con la clase → muestra candado con el nombre

### `ai-engine/tests/test_gemini_provider.py` (A4)

- [ ] Sin api_key → health().available False y error_code 'missing_api_key'
- [ ] Respuesta JSON válida → ProviderResponse con content validado y provider 'gemini'
- [ ] Primera respuesta JSON inválida y segunda válida → retries == 1
- [ ] 429 dos veces → error tipado de rate limit, sin filtrar la clave en el mensaje
- [ ] La petición lleva x-goog-api-key en cabecera y no en la URL

### `backend/tests/test_mejoras_v1_proveedor.py` (A4)

- [ ] select_provider('gemini') sin GEMINI_API_KEY → (None, '') y la interacción responde con el motor de reglas
- [ ] select_provider('rule_engine') → (None, …)
- [ ] PUT ai/settings con preferred_provider='gemini' como organizador → 200

### `frontend/src/core/voice/useSpeechRecognition.test.ts` (A4)

- [ ] Sin SpeechRecognition en window → supported false
- [ ] Evento de resultado final → llama onFinal con el texto
- [ ] Resultado parcial → actualiza interim
- [ ] Error 'not-allowed' → error = 'Permite el micrófono para dictar'

### `backend/tests/test_mejoras_v2_proactivo.py` (A1)

- [ ] 4 cambios → no publica; el 5.º con diagrama inválido (clase sin atributos) → 1 mensaje kind='proactive' y ≥ 1 recomendación
- [ ] Durante el cooldown, otros 5 cambios → no publica
- [ ] Diagrama sin hallazgos → no publica
- [ ] Entradas con source='system' → se ignoran; las de source='ai' cuentan como cambios del equipo
- [ ] Entrada CREATE_PROJECT_VERSION → mensaje con resumen por integrante
- [ ] Entrada IMPORT_XMI con diagrama con hallazgos → mensaje trigger='import'
- [ ] Proyecto sin conversación → no publica ni lanza excepción
- [ ] Consumidor: XACK de cada entrada procesada y CHANGE_LOGGED difundido al proyecto

### `ai-engine/tests/test_mejoras_equipo.py` (A1)

- [ ] «¿Qué hizo cada uno?» → intención coordinate_team
- [ ] Con team_activity de Ana y Beto → la respuesta nombra a ambos con sus acciones
- [ ] Dos integrantes tocaron la misma clase → la respuesta sugiere coordinarse
- [ ] AiProjectContext sin team_activity sigue validando (compatibilidad)

### `backend/tests/test_mejoras_v2_invitaciones.py` (A2)

- [ ] Organizador invita a un correo → 201, pending, expires_at a 7 días
- [ ] Mismo correo con otra mayúscula → 409 INVITATION_ALREADY_PENDING
- [ ] Invitar a un integrante → 409 MEMBER_ALREADY_EXISTS
- [ ] Editor invita → 403 PERMISSION_DENIED
- [ ] Invitado acepta → integrante con el rol y notificación al que invitó
- [ ] Otro usuario intenta aceptar → 404 INVITATION_NOT_FOUND
- [ ] Invitación con expires_at pasado → aceptar 410 y estado expired
- [ ] Revocar → 204 y ya no aparece en invitations/me

### `frontend/src/modules/gestion_proyectos_colaboracion/pages/ProjectManagementPage.test.tsx` (A2)

- [ ] Organizador ve el formulario «Invitar por correo»; editor no
- [ ] Enviar invitación → toast de éxito y aparece en Pendientes
- [ ] Revocar pide confirmación en modal antes de llamar al servicio

### `backend/tests/test_mejoras_v2_bloqueos.py` (A3)

- [ ] A bloquea la clase → B recibe ELEMENT_LOCKED con el nombre de A
- [ ] B pide el mismo bloqueo → LOCK_REJECTED solo a B
- [ ] B hace PATCH a la clase bloqueada por A → 423 ELEMENT_LOCKED; A → 200
- [ ] A se desconecta (última pestaña) → ELEMENT_UNLOCKED reason='disconnected'
- [ ] Bloqueo sin renovar más que el TTL → expira
- [ ] Lector envía LOCK_ELEMENT → rechazado
- [ ] Funciona igual con fakeredis y con el modo en memoria

### `frontend/src/modules/modelado_uml_inteligente/store/umlHistory.test.ts` (A3)

- [ ] push y undo → ejecuta la inversa y canRedo true
- [ ] redo → vuelve a aplicar
- [ ] Nuevo push tras undo → vacía la pila de rehacer
- [ ] Más de 50 comandos → conserva los 50 últimos
- [ ] clear() al cambiar de diagrama

### `backend/tests/test_mejoras_v2_generador.py` (A4)

- [ ] Categoria ◆ Producto (1 a 0..*) → Categoria con @OneToMany(mappedBy = "categoria", cascade = CascadeType.ALL, orphanRemoval = true) y Producto con @ManyToOne + @JoinColumn
- [ ] Agregación → @OneToMany sin cascade
- [ ] Estudiante * a * Curso sin clase asociación → @ManyToMany con @JoinTable
- [ ] Herencia Persona ← Cliente → @Inheritance(strategy = InheritanceType.JOINED) y Cliente extends Persona
- [ ] Enum EstadoPedido → archivo enum y @Enumerated(EnumType.STRING) en el atributo
- [ ] postman_collection.json valida como JSON con una carpeta por entidad y 5 peticiones cada una
- [ ] data.sql inserta padres antes que hijos
- [ ] Con CASE_VERIFY_GENERATED_SPRING=1 → mvn test del proyecto generado pasa

### `backend/tests/test_mejoras_v3_flujo.py` (A1)

- [ ] Flujo API completo con fakeredis: registrar 2 usuarios → invitar y aceptar → crear diagrama por IA y confirmar → bloqueo → guardar versión → registro con ≥ 6 entradas de 2 autores → generación coordinada 201 y ZIP descargable
- [ ] La clase creada al confirmar una acción de la IA aparece en el registro con source='ai'
- [ ] Con REDIS_ENABLED=false el mismo flujo pasa (registro en modo respaldo)
- [ ] Suites completas: backend, ai-engine y frontend en verde

### `frontend/src/shared/components/sharedComponents.test.tsx` (A1)

- [ ] toast.success('Invitación enviada') → aparece en el Toaster con role='status' y desaparece a los 4 s (fake timers)
- [ ] useConfirm resuelve false con Cancelar, con Escape y con clic fuera; true con el botón de confirmar
- [ ] Avatar con el mismo userId → misma clase de color; kind='ai' → icono de robot
- [ ] PresenceStack con 6 personas y max=4 → 4 avatares y «+2»
- [ ] StatusBadge sin tone sigue renderizando el estilo neutral de antes

## 9. Documentación

| Archivo | Responsable | Cuándo | Contenido |
|---|---|---|---|
| docs/segundo_parcial/mejoras-2p/PLAN.md | A1 | Ola 0 | Este plan (generado; no editar a mano: editar plan.json y reconstruir). |
| docs/segundo_parcial/mejoras-2p/maqueta.html | A1 | Ola 0 | Maqueta de referencia (la publica Claude; no se edita a mano: se pide una versión nueva y se reemplaza). |
| docs/segundo_parcial/mejoras-2p/bitacora-agentes.md | A1 | Cada tarea | Fecha, tarea, agente, qué cambió, pruebas corridas, pendientes para otros dueños. |
| CLAUDE.md | A1 | Ola 0 | Guía corta del repositorio para Claude Code. |
| docs/segundo_parcial/mejoras-2p/redis.md | A1 | Olas 0–1 | Por qué Redis (NoSQL), claves, instalación en Windows, respaldo y backfill. |
| docs/segundo_parcial/mejoras-2p/ia-equipo.md | A1 | Ola 2 | IA como integrante: disparadores proactivos, actividad por integrante, moderación. |
| docs/segundo_parcial/mejoras-2p/permisos.md | A2 | Olas 1–2 | Matriz de permisos, uso de useProjectPermissions y PermissionGate, invitaciones. |
| docs/segundo_parcial/mejoras-2p/casos-de-uso.md | A2 | Ola 3 | Fichas CU19–CU25. |
| docs/segundo_parcial/fase9/02_matriz_trazabilidad.md | A2 | Ola 3 | Agregar CU19–CU25. |
| README.md | A2 | Ola 3 | Cómo levantar con Redis, Gemini y Ollama; pruebas. |
| docs/segundo_parcial/mejoras-2p/editor-uml.md | A3 | Olas 1–2 | Tipos UML soportados, XMI, bloqueos, deshacer. |
| docs/segundo_parcial/mejoras-2p/guion-demo.md | A3 | Ola 3 | Guion de defensa con capturas. |
| docs/segundo_parcial/mejoras-2p/ia-proveedores.md | A4 | Ola 1 | Ollama/Qwen, Gemini y reglas: cómo elegir, variables, voz en el chat. |
| docs/segundo_parcial/mejoras-2p/generador.md | A4 | Ola 2 | Mapeo UML → JPA, Postman y semilla. |
| docs/segundo_parcial/mejoras-2p/verificacion-entorno.md | A4 | Ola 3 | Resultados en el equipo de demo. |

**Cambios a la documentación existente:**

- Documento del 2.º parcial: agregar CU19 Interactuar con la IA del equipo por voz, CU20 Gestionar invitaciones, CU21 Colaborar con bloqueo de elementos, CU22 Consultar el registro de cambios, CU23 Recibir sugerencias proactivas de la IA, CU24 Configurar el proveedor de IA y CU25 Gestionar permisos por rol de proyecto.
- Actores: agregar Lector (rol de proyecto de solo lectura) y Servicio de IA (Ollama/Qwen local o Gemini) como actor secundario; la IA aparece además como integrante visible del proyecto.
- Diseño de datos: agregar la sección «Persistencia NoSQL (Redis)» con las claves, el Stream del registro de cambios y su relación con audit_logs (PostgreSQL sigue como fuente de verdad).
- Despliegue: agregar el nodo Redis (appendonly) al diagrama de despliegue y al docker-compose de producción.
- Pruebas: agregar las pruebas funcionales de CU19–CU25 y el flujo integral de V3.1 al plan de pruebas.
- Diseño de interfaces (prototipos por CU): usar las capturas de maqueta.html para CU19–CU25 y reemplazarlas por capturas reales al cerrar la ola 3.

## 10. Fuera de alcance

- Migrar todo el sistema a una base NoSQL: PostgreSQL sigue como fuente de verdad; Redis cubre el registro de cambios, bloqueos y contadores.
- Redis Pub/Sub para varios procesos del backend (se mantiene un solo worker de Uvicorn, como documentó el colega).
- Comparar versiones, exportar el diagrama como imagen, compartir por enlace, recuperar contraseña y comentarios en elementos.
- Cambios a la app móvil más allá de la verificación de V3.4 (ya cumple «móvil informativo» en modo lectura).
- Voz offline (Vosk/Whisper): el dictado usa la Web Speech API del navegador.
- Entrenamiento o ajuste fino de modelos de IA.
