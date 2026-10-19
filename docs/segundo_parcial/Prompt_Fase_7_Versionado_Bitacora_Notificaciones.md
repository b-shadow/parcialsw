# PROMPT FASE 7: VERSIONADO, BITACORA Y NOTIFICACIONES

## 0. Instruccion maestra

Implementar la Fase 7 de la segunda parte de CASE Inteligente: integrar en un unico sistema coherente el guardado manual de versiones, la restauracion segura, la bitacora del proyecto, la auditoria administrativa y las notificaciones internas y Web Push.

La implementacion debe trabajar sobre el repositorio existente. Antes de editar, inspeccionar modelos, migraciones, servicios, routers, pruebas, eventos WebSocket, contratos del frontend y documentos de las Fases 1 a 6. Reutilizar los componentes actuales cuando su comportamiento sea correcto y migrarlos de forma compatible cuando hayan quedado incompletos.

Esta fase no convierte cada cambio colaborativo en una version. Deben coexistir tres conceptos claramente separados:

1. **Version guardada**: snapshot manual y restaurable creado por el propietario u organizador.
2. **Bitacora**: secuencia continua e inmutable de acciones realizadas en el proyecto.
3. **Notificacion**: aviso dirigido a usuarios concretos sobre hechos relevantes.

La conversacion de IA constituye una cuarta secuencia persistente e independiente. Puede consultarse como parte de la trazabilidad, pero nunca debe copiarse dentro del snapshot, borrarse ni regresar en el tiempo cuando se restaura una version.

No reemplazar el historial colaborativo existente por snapshots automaticos. No restaurar mensajes, auditorias, miembros, roles, invitaciones, artefactos generados ni suscripciones push. No enviar una notificacion por cada movimiento del lienzo.

---

## 1. Resultado funcional buscado

Al finalizar esta fase:

1. El creador o un miembro con rol `ORGANIZADOR` puede guardar una version manual del proyecto.
2. Cada version contiene un `ProjectSnapshotV2` valido y autoconsistente.
3. El snapshot incluye diagramas UML, especificaciones funcionales de metodos, tema Flutter activo y configuracion no sensible de generacion e IA.
4. La version guardada es inmutable despues de su creacion.
5. El sistema puede leer snapshots V1 existentes mediante un adaptador explicito.
6. El sistema rechaza versiones futuras o corruptas sin modificar el proyecto.
7. Antes de una restauracion exitosa se genera automaticamente una version de respaldo del estado actual.
8. Restaurar recupera el contenido versionable exacto, no solo las clases UML.
9. Restaurar no borra conversaciones, eventos, auditorias, notificaciones ni artefactos ya generados.
10. Solo el creador del proyecto o un `ORGANIZADOR` puede listar las versiones completas, guardar y restaurar.
11. Todos los miembros pueden consultar una ventana flotante de actividad acorde con sus permisos.
12. Cada actividad indica quien, que, cuando y sobre que recurso actuo.
13. Una restauracion informa a los clientes conectados que deben descartar estado optimista y recargar.
14. Las versiones y restauraciones no se duplican por reintentos de red.
15. Existe una bandeja persistente de notificaciones por usuario.
16. Las notificaciones se pueden marcar como leidas individualmente o en conjunto.
17. Cada notificacion contiene un destino interno validado hacia la pantalla relacionada.
18. Web Push es un canal de entrega adicional, no la unica fuente de verdad.
19. Los envios push ocurren despues del commit mediante un outbox reintentable.
20. Invitaciones, restauraciones, generaciones y acciones relevantes de IA generan avisos segun una matriz explicita.
21. Cambios menores y repetitivos se agrupan o permanecen solo en la actividad para evitar ruido.
22. El historial de conversacion de IA permanece visible y ordenado despues de restaurar una version antigua.
23. Los secretos VAPID, credenciales, tokens y endpoints privados nunca aparecen en snapshots, respuestas ni bitacoras.
24. Las pruebas cubren permisos, concurrencia, compatibilidad, atomicidad, deduplicacion, WebSocket y entrega de notificaciones.

---

## 2. Alineacion obligatoria entre fases

### 2.1. Fase 1: contratos, persistencia y migraciones

Reutilizar y completar:

- `ProjectSnapshotV2`.
- `FlutterThemeSettings`.
- Configuracion no sensible de generacion.
- Configuracion no sensible del proveedor de IA.
- Versionado de esquemas JSON.
- Convenciones de UUID, timestamps UTC, JSONB, indices y restricciones.
- Eventos `PROJECT_VERSION_CREATED`, `PROJECT_VERSION_RESTORED` y `FLUTTER_THEME_UPDATED`.

Si la Fase 1 ya creo una tabla o columna con finalidad equivalente, no crear otra paralela. Migrar datos y consolidar el contrato.

### 2.2. Fases 2 y 3: motor unico de IA y conversacion colaborativa

- La conversacion es una sola por proyecto.
- Los mensajes y acciones propuestas/aplicadas son inmutables.
- Una restauracion no modifica estados historicos de mensajes de IA.
- Las acciones de IA aplicadas al UML aparecen en la bitacora del proyecto.
- Las respuestas o solicitudes de confirmacion pueden producir notificaciones dirigidas.
- El snapshot solo incluye configuracion no sensible del proveedor, nunca mensajes ni secretos.

### 2.3. Fase 4: especificacion funcional de metodos

Cada snapshot debe conservar:

- Firmas de metodos.
- Parametros y tipos.
- Especificaciones funcionales normalizadas.
- Reglas de validacion.
- Acciones de persistencia.
- Interacciones de frontend.
- Referencias entre entidades y metodos.

La restauracion debe validar esas referencias antes de escribir y restaurarlas junto al UML.

### 2.4. Fase 5: generacion coordinada

Versionar la configuracion fuente necesaria para reproducir una generacion, pero no copiar ZIP ni binarios en el snapshot.

Conservar fuera del snapshot:

- Historial de ejecuciones.
- Diagnosticos historicos.
- Artefactos generados inmutables.
- Hashes y manifiestos de ejecuciones anteriores.

Una restauracion cambia la configuracion activa para futuras generaciones. No reescribe el pasado ni elimina descargas existentes.

### 2.5. Fase 6: editor y preview Flutter

El snapshot contiene el tema Flutter normalizado activo y su version de esquema. Restaurar debe actualizar el preview y el siguiente ZIP generado. La biblioteca personal de presets no pertenece al snapshot porque es un recurso independiente del usuario.

### 2.6. Entrega a Fase 8

La PWA movil consumira:

- Bandeja de notificaciones.
- Destinos internos seguros.
- Actividad reciente paginada.
- Lista de versiones en modo lectura cuando corresponda.
- Eventos WebSocket de invalidacion.
- Estado de lectura sincronizado entre dispositivos.

### 2.7. Entrega a Fase 9

Dejar contratos, fixtures y suites preparados para pruebas integrales de:

- Upgrade desde base existente.
- Concurrencia.
- Restauracion atomica.
- Permisos.
- Idempotencia.
- Entrega eventual.
- Ausencia de regresiones.

---

## 3. Estado actual que se debe reconocer

El repositorio ya posee, como minimo:

- `ProjectVersion` con snapshot JSONB.
- `CollaborationEvent` con secuencia por proyecto e id de evento del cliente.
- `AuditLog` administrativo.
- Endpoints para crear, listar y restaurar versiones.
- Respaldo automatico previo a restaurar UML.
- Panel flotante `ProjectHistoryPanel`.
- WebSocket colaborativo.
- Suscripciones Web Push y VAPID.
- Envios push desde tareas en segundo plano de FastAPI.

No asumir que eso completa la fase. La implementacion actual tiene que evolucionar porque:

- El snapshot actual puede ser V1 y contener solo diagramas.
- La restauracion puede no incluir tema ni configuracion de generacion.
- `MAX(version_number) + 1` puede competir bajo concurrencia.
- Marcar la version objetivo como `restored` mezcla identidad con historial de operaciones.
- La bitacora carece de contrato semantico completo y paginacion estable.
- Web Push directo no ofrece una bandeja persistente ni garantia de reintento.
- La interfaz consulta por polling aunque existen eventos colaborativos.
- Los textos de eventos desconocidos pueden degradarse a etiquetas incorrectas.

El trabajo debe ser incremental y compatible, no una reescritura ciega.

---

## 4. Principios innegociables

### 4.1. Versiones manuales

- Una edicion UML no crea una version.
- Mover una clase no crea una version.
- Guardar tema no crea una version.
- Aplicar una accion de IA no crea una version.
- Generar Spring Boot o Flutter no crea una version.
- Solo la accion explicita `Guardar version` crea un punto restaurable manual.
- La unica excepcion es el respaldo automatico previo a una restauracion.

### 4.2. Inmutabilidad

Una version guardada no se modifica. Restaurarla crea una operacion nueva y un evento, pero no altera su snapshot, nombre, hash, autor ni fecha.

### 4.3. Trazabilidad acumulativa

Restaurar contenido no restaura la historia. La bitacora debe mostrar tanto lo ocurrido antes como la propia restauracion y las acciones posteriores.

### 4.4. Atomicidad

Una restauracion termina completa o no cambia nada. Nunca debe quedar UML antiguo con tema nuevo, relaciones parciales o especificaciones funcionales huerfanas.

### 4.5. Estado monotono de operacion

Las revisiones operativas, secuencias de eventos y numeros de notificacion siempre avanzan. El contenido puede regresar a una version anterior; los contadores de concurrencia no.

### 4.6. Entrega eventual

El commit del negocio no puede depender de la disponibilidad del servicio Web Push. Primero se confirma el cambio; despues se entrega la notificacion mediante outbox.

### 4.7. Minimo privilegio

No inferir acceso a partir de botones visibles. Backend y WebSocket vuelven a validar membresia, rol y recurso en cada operacion.

---

## 5. Glosario del dominio

Usar estos nombres de forma consistente:

| Termino | Definicion |
| --- | --- |
| `ProjectVersion` | Punto restaurable e inmutable de un proyecto. |
| `manual` | Version solicitada explicitamente por un usuario autorizado. |
| `pre_restore_backup` | Version automatica del estado inmediatamente anterior a restaurar. |
| `ProjectSnapshotV2` | Contrato serializable del contenido versionable. |
| `ProjectRestoreOperation` | Registro de un intento de restauracion y su resultado. |
| `CollaborationEvent` | Hecho secuencial visible para miembros del proyecto. |
| `AuditLog` | Registro administrativo y de seguridad de alcance global. |
| `AiConversation` | Conversacion compartida e inmutable, fuera del snapshot. |
| `Notification` | Aviso persistente dirigido a un usuario. |
| `NotificationOutbox` | Trabajo pendiente de entrega por un canal externo. |
| `PushSubscription` | Dispositivo/navegador autorizado para Web Push. |
| `deep_link` | Destino interno estructurado, no URL arbitraria. |
| `project_revision` | Revision monotona del estado versionable activo. |

---

## 6. Alcance versionable exacto

### 6.1. Incluir en `ProjectSnapshotV2`

1. Metadatos minimos del proyecto:
   - `id`.
   - `name`.
   - `description` cuando forme parte del estado funcional.
2. Todos los diagramas activos del proyecto.
3. Clases, atributos, metodos, parametros y relaciones.
4. Multiplicidades, navegabilidad, association classes y posiciones.
5. Especificaciones funcionales de metodos de la Fase 4.
6. Tema Flutter normalizado de la Fase 6.
7. Configuracion de generacion reproducible de la Fase 5.
8. Configuracion no sensible de IA:
   - proveedor preferido;
   - nombre logico del modelo;
   - fallback habilitado;
   - confirmacion requerida.
9. Versiones de esquema de cada bloque.
10. Fecha de captura informativa en UTC.

### 6.2. Excluir del snapshot

- Usuarios, membresias, roles y permisos.
- Invitaciones.
- Conversaciones y mensajes de IA.
- Auditorias y eventos colaborativos.
- Notificaciones y preferencias.
- Suscripciones Web Push.
- Claves VAPID.
- Tokens JWT, contrasenas o credenciales AWS.
- URLs privadas de infraestructura.
- Variables `.env`.
- ZIP, JAR, APK, binarios o logs.
- Artefactos historicos de generacion.
- Presets personales del usuario.
- Presencia WebSocket.
- Bloqueos temporales y estado optimista del navegador.

### 6.3. Politica sobre configuracion de generacion

Guardar solo decisiones reproducibles, por ejemplo:

- nombre base normalizado;
- opciones del stack;
- dialecto o perfil soportado;
- identificador del diagrama fuente;
- opciones de API y UI;
- version del contrato de generacion.

No guardar direcciones como `127.0.0.1`, IP del telefono, claves de base de datos ni rutas absolutas de la maquina. Esos valores pertenecen al entorno de ejecucion.

---

## 7. Contrato `ProjectSnapshotV2`

Crear o consolidar modelos Pydantic estrictos. No construir snapshots concatenando diccionarios sin validacion.

Ejemplo contractual:

```json
{
  "schema_version": 2,
  "captured_at": "2026-10-15T18:00:00Z",
  "project": {
    "id": "uuid",
    "name": "Sistema de ventas",
    "description": "Modelo colaborativo"
  },
  "diagrams": [],
  "flutter_theme": {
    "schema_version": 2,
    "tokens": {},
    "components": {}
  },
  "generation_settings": {
    "schema_version": 1,
    "base_name": "App",
    "backend_profile": "spring_boot_postgresql",
    "frontend_profile": "flutter_material"
  },
  "ai_settings": {
    "schema_version": 1,
    "enabled": true,
    "preferred_provider": "ollama",
    "model_name": "qwen",
    "fallback_enabled": true,
    "require_confirmation": true
  }
}
```

### 7.1. Reglas del contrato

- `schema_version` raiz es obligatorio.
- UUID se serializa como string canonico.
- Fechas usan ISO 8601 UTC.
- Ordenar colecciones por clave estable antes de calcular hash.
- Rechazar referencias a recursos de otro proyecto.
- Rechazar relaciones cuyos extremos no existen.
- Rechazar parametros cuyo metodo no existe.
- Rechazar especificaciones funcionales con referencias rotas.
- Normalizar tema y configuracion con validadores compartidos.
- No aceptar propiedades desconocidas criticas en modo de restauracion.
- Definir limites de cantidad y tamano.

### 7.2. Canonicalizacion y hash

Crear una funcion unica:

```python
canonicalize_project_snapshot(snapshot) -> bytes
snapshot_sha256(snapshot) -> str
```

La canonicalizacion debe:

1. Validar con Pydantic.
2. Excluir campos volatiles del hash, especialmente `captured_at`.
3. Ordenar claves JSON.
4. Usar separadores deterministas.
5. Preservar orden semanticamente relevante solo donde corresponda.
6. Generar UTF-8.

El hash permite integridad y comparacion, no reemplaza validacion semantica.

### 7.3. Limites recomendados configurables

- Tamano serializado maximo por snapshot.
- Numero maximo de diagramas.
- Numero maximo de elementos UML.
- Longitud maxima de nombre y descripcion.
- Profundidad maxima de JSON.
- Tamano maximo de metadata de eventos.

Responder `413` para exceso de tamano y `422` para contenido invalido.

---

## 8. Compatibilidad de snapshots V1 y futuros

### 8.1. Adaptador V1 a V2

Implementar un adaptador puro y probado:

```python
upgrade_snapshot_v1_to_v2(snapshot_v1, current_defaults) -> ProjectSnapshotV2
```

El adaptador:

- Conserva diagramas e identificadores validos.
- Completa tema con defaults seguros cuando V1 no lo tenga.
- Completa configuracion de generacion con valores normalizados existentes.
- Completa configuracion de IA sin secretos.
- Emite advertencias estructuradas sobre campos inferidos.
- No persiste la conversion sobre la version original.

La version V1 sigue siendo inmutable. La actualizacion sucede en memoria durante inspeccion o restauracion.

### 8.2. Version futura

Si `schema_version > 2`, responder `409 SNAPSHOT_VERSION_UNSUPPORTED` e indicar la version soportada. No intentar ignorar campos y no crear respaldo porque aun no se inicio una restauracion valida.

### 8.3. Snapshot corrupto

Validar por completo antes de cualquier escritura. Devolver diagnosticos sin exponer stack traces ni contenido sensible.

---

## 9. Modelo `ProjectVersion`

Mantener la tabla actual y agregar, si aun no existen:

- `kind`: `manual` o `pre_restore_backup`.
- `snapshot_schema_version`.
- `snapshot_hash` SHA-256.
- `snapshot_size_bytes`.
- `project_revision` capturada.
- `idempotency_key` nullable.
- `metadata_json` pequeno y no sensible.

Restricciones:

- Unico `(project_id, version_number)`.
- Unico `(project_id, created_by_user_id, idempotency_key)` cuando la clave no sea nula.
- `version_number > 0`.
- `snapshot_schema_version > 0`.
- `kind` limitado por `CHECK` o enum estable.
- Indices por proyecto y fecha descendente.

No usar `status = restored` para modificar una version objetivo. Una version puede ser restaurada muchas veces. Esa informacion pertenece a `ProjectRestoreOperation` y a la bitacora.

Si `status` debe conservarse por compatibilidad, mantenerlo con significado de disponibilidad (`available`, `invalidated`) y migrar `saved/restored` a un estado no ambiguo. No cambiar versiones historicas sin migracion explicita.

---

## 10. Numeracion concurrente de versiones

La operacion `MAX(version_number) + 1` sin bloqueo es insuficiente.

Implementar una de estas estrategias, prefiriendo la que mejor encaje con PostgreSQL y la arquitectura actual:

1. Bloquear la fila `projects` con `SELECT ... FOR UPDATE`, calcular el siguiente numero y crear la version dentro de la misma transaccion.
2. Mantener un contador monotono `next_version_number` en `projects` actualizado atomicamente.

No depender exclusivamente de capturar una violacion unique. Aun asi, manejar `IntegrityError` con rollback controlado y un reintento acotado cuando corresponda.

Probar dos solicitudes simultaneas. Deben producir numeros consecutivos y snapshots validos, sin error 500.

---

## 11. Modelo `ProjectRestoreOperation`

Crear una entidad separada para representar cada restauracion:

- `id` UUID.
- `project_id`.
- `source_version_id`.
- `backup_version_id` nullable hasta crearlo.
- `requested_by_user_id`.
- `idempotency_key`.
- `status`: `validating`, `completed`, `failed`.
- `source_snapshot_hash`.
- `before_snapshot_hash`.
- `after_snapshot_hash` nullable.
- `project_revision_before`.
- `project_revision_after` nullable.
- `diagnostics_json` saneado.
- `started_at`.
- `completed_at` nullable.
- timestamps estandar.

El snapshot de una version permanece inmutable aunque exista una o cien operaciones que la restauren.

### 11.1. Idempotencia

El endpoint acepta `Idempotency-Key`. Para la misma combinacion de proyecto, usuario y clave:

- Si la operacion termino, devolver el mismo resultado.
- Si sigue en progreso, devolver `409 RESTORE_IN_PROGRESS` o el recurso de operacion.
- Si fallo de forma reintentable, definir politica explicita sin duplicar respaldos.
- Si se reutiliza la clave para otra version, responder `409 IDEMPOTENCY_KEY_REUSED`.

---

## 12. Autoridad y permisos

### 12.1. Regla efectiva

Pueden crear, listar en detalle y restaurar versiones:

- `project.owner_id == current_user.id`, o
- membresia activa con `project_role == "ORGANIZADOR"`.

El creador normalmente debe poseer membresia `ORGANIZADOR`, pero el backend tambien verifica `owner_id` para no depender de una inconsistencia historica.

### 12.2. Otros roles

- `EDITOR`: consulta actividad; no crea ni restaura versiones.
- `VISUALIZADOR` o equivalente: consulta actividad permitida y recibe avisos; no muta.
- Administrador global: no obtiene automaticamente derecho para alterar proyectos privados, salvo una politica administrativa explicita y auditada.

### 12.3. Defensa en profundidad

Validar permisos en:

- Router HTTP.
- Servicio de dominio.
- Mensaje WebSocket que pudiera solicitar una mutacion.
- Consulta de version por id y pertenencia al proyecto.
- Descarga o inspeccion de snapshot.

Ocultar controles en frontend mejora UX, pero nunca sustituye estas verificaciones.

---

## 13. Guardado manual de una version

### 13.1. Flujo transaccional

1. Autenticar usuario.
2. Resolver proyecto.
3. Validar propietario/organizador.
4. Validar `Idempotency-Key`.
5. Adquirir el bloqueo compartido de mutacion del proyecto.
6. Construir snapshot desde los servicios de dominio, no desde datos enviados por el navegador.
7. Validar `ProjectSnapshotV2`.
8. Canonicalizar, calcular hash y tamano.
9. Asignar numero de version de forma concurrente segura.
10. Insertar `ProjectVersion(kind="manual")`.
11. Insertar evento de actividad `PROJECT_VERSION_CREATED`.
12. Insertar auditoria.
13. Crear notificaciones y outbox segun politica.
14. Confirmar una sola transaccion.
15. Publicar evento WebSocket despues del commit.

### 13.2. Entrada

- `name`: obligatorio, limpio, 1 a 120 caracteres.
- `description`: opcional y limitada.
- `expected_project_revision`: recomendado para advertir si el estado cambio antes de guardar.

No aceptar el snapshot completo desde frontend. El servidor captura el estado autoritativo.

### 13.3. Sin cambios desde la ultima version

Comparar el hash con la ultima version manual. Mostrar una advertencia y permitir cancelar. Si el producto decide aceptar el guardado duplicado, debe requerir confirmacion explicita y quedar auditado; no crear duplicados accidentalmente por doble clic.

---

## 14. Inspeccion previa a restaurar

Antes de confirmar, ofrecer un resumen calculado en servidor:

- Version objetivo, autor y fecha.
- Esquema original y esquema efectivo despues de adaptar.
- Numero de diagramas.
- Clases, atributos, metodos y relaciones.
- Tema que se recuperara.
- Configuracion de generacion que cambiara.
- Elementos actuales que se eliminaran.
- Elementos que se agregaran.
- Elementos que se modificaran.
- Advertencias de compatibilidad.
- Revision actual del proyecto.

Endpoint sugerido:

```http
GET /api/v1/projects/{project_id}/versions/{version_id}/restore-preview
```

La vista previa no escribe, no crea respaldo y no envia notificaciones.

El frontend debe mostrar que conversaciones, bitacora, miembros y artefactos no se modificaran.

---

## 15. Restauracion atomica

### 15.1. Orden obligatorio

1. Autenticar y autorizar.
2. Resolver idempotencia.
3. Cargar version y comprobar pertenencia.
4. Adaptar y validar completamente el snapshot fuera de cualquier borrado.
5. Calcular plan de restauracion.
6. Adquirir bloqueo exclusivo de mutacion por proyecto.
7. Volver a comprobar `expected_project_revision`.
8. Capturar el estado actual como `ProjectSnapshotV2`.
9. Crear `pre_restore_backup` dentro de la transaccion.
10. Crear/actualizar `ProjectRestoreOperation`.
11. Aplicar diagramas y dependencias en orden seguro.
12. Aplicar especificaciones funcionales.
13. Aplicar tema Flutter activo.
14. Aplicar configuracion de generacion.
15. Aplicar configuracion no sensible de IA.
16. Ejecutar validacion integral del estado resultante.
17. Incrementar `project_revision` de forma monotona.
18. Capturar hash posterior y compararlo con el objetivo efectivo.
19. Insertar evento `PROJECT_VERSION_RESTORED`.
20. Insertar auditoria y notificaciones.
21. Marcar operacion `completed`.
22. Commit unico.
23. Publicar WebSocket y despachar outbox despues del commit.

### 15.2. Semantica del respaldo

El respaldo debe existir siempre que la restauracion se confirme. Si la transaccion falla, tambien se revierte el cambio; por tanto, el proyecto queda intacto y no es obligatorio conservar un respaldo de una modificacion que nunca ocurrio.

No realizar un commit intermedio entre respaldo y restauracion porque abriria una ventana para cambios concurrentes.

### 15.3. Restauracion exacta

El contenido versionable activo debe coincidir con el snapshot objetivo adaptado:

- Crear elementos ausentes.
- Actualizar elementos coincidentes.
- Eliminar del estado activo elementos que no existian en el objetivo.
- Mantener ids cuando sean validos y pertenezcan al proyecto.
- Restaurar posiciones y relaciones.
- Restaurar metodos y especificaciones.
- Restaurar tema y opciones.

Los elementos eliminados quedan recuperables mediante el respaldo previo y trazables en la bitacora.

### 15.4. Revisiones monotonicamente crecientes

No copiar una revision historica sobre la revision actual. Restaurar el contenido y asignar una nueva revision activa. Esto impide que clientes con un ETag antiguo sean considerados vigentes.

### 15.5. Fallos

Ante cualquier excepcion:

- Rollback total.
- El proyecto conserva su estado previo.
- No se publica evento de exito.
- No se envia push de exito.
- Se registra intento fallido con diagnostico saneado cuando sea posible.
- Se responde con codigo de dominio estable.

---

## 16. Exclusividad de mutaciones durante restauracion

La fila del proyecto solo protege si todos los escritores cooperan. Crear un `ProjectMutationGuard` reutilizable.

Alternativas aceptables:

- Bloqueo transaccional de la fila `projects` usado por toda mutacion de UML, metodos, tema, IA aplicada y versiones.
- Advisory lock transaccional de PostgreSQL derivado de `project_id`, usado por todos esos servicios.

No implementar un mutex solo en memoria porque falla con varios procesos o replicas.

Toda mutacion relevante debe:

1. Adquirir el mismo guard.
2. Verificar revision esperada cuando aplique.
3. Cambiar estado.
4. Incrementar revision.
5. Registrar evento.
6. Commit.

Probar una edicion concurrente con restauracion. Una debe esperar o recibir conflicto controlado; nunca entremezclarse.

---

## 17. Reconciliacion e integridad referencial

La restauracion debe ejecutarse por fases internas:

1. Validar ids y pertenencia.
2. Preparar mapa de ids.
3. Crear/actualizar diagramas.
4. Crear/actualizar clases.
5. Crear/actualizar atributos.
6. Crear/actualizar metodos y parametros.
7. Crear/actualizar especificaciones funcionales.
8. Crear/actualizar relaciones simples.
9. Crear association classes y referencias dependientes.
10. Eliminar recursos sobrantes en orden inverso.
11. Restaurar tema y configuraciones.
12. Ejecutar validacion global.

No deshabilitar restricciones de base de datos como sustituto de un orden correcto.

Validar especialmente:

- Multiplicidades.
- Association classes.
- Foreign keys inferidas.
- Claves compuestas.
- Tipos UUID y Date.
- Nombres normalizados.
- Referencias de metodos a entidades.
- Controles Flutter derivados.

---

## 18. Respuesta de restauracion

Definir un contrato estable, por ejemplo:

```json
{
  "operation_id": "uuid",
  "status": "completed",
  "restored_version": {
    "id": "uuid",
    "version_number": 4,
    "snapshot_hash": "sha256"
  },
  "backup_version": {
    "id": "uuid",
    "version_number": 7,
    "snapshot_hash": "sha256"
  },
  "project_revision": 92,
  "affected_diagram_ids": ["uuid"],
  "removed_diagram_ids": [],
  "warnings": [],
  "activity_sequence": 351
}
```

No devolver el snapshot completo salvo endpoint explicito y autorizado.

---

## 19. Tres historiales separados

### 19.1. Actividad del proyecto

Audiencia: miembros del proyecto.

Incluye acciones comprensibles de colaboracion y producto:

- UML creado/editado/eliminado.
- Metodo especificado.
- Accion de IA aplicada.
- Tema actualizado.
- Version guardada.
- Version restaurada.
- Generacion iniciada/completada/fallida.
- Miembro agregado, rol modificado o removido.

### 19.2. Auditoria administrativa

Audiencia: administradores autorizados.

Incluye seguridad y operacion:

- Login y fallos relevantes.
- Cambios de usuarios y roles globales.
- Accesos denegados.
- Cambios de membresia.
- Operaciones sensibles de versionado.
- Configuracion de push.

No mostrar el audit log global completo a miembros comunes.

### 19.3. Conversacion de IA

Audiencia: miembros segun permisos de la Fase 3.

Incluye mensajes, propuestas, confirmaciones y resultados. No duplicar el texto completo en `CollaborationEvent`; registrar solo ids y resumen seguro.

---

## 20. Contrato de `CollaborationEvent`

Conservar secuencia monotona por proyecto e idempotencia por evento del cliente. Endurecer el contrato con:

- `event_type` tipado.
- `actor_user_id` o el actual `user_id`.
- Snapshot de nombre visible del actor cuando sea necesario para conservar legibilidad historica.
- `resource_type`.
- `resource_id`.
- `diagram_id` nullable.
- `correlation_id` para agrupar una operacion.
- `causation_id` para enlazar la causa.
- `summary_key` traducible en frontend.
- `payload` minimo y validado por tipo.
- `sequence_number` monotono.
- `created_at` UTC.

No guardar datos personales innecesarios ni contenido arbitrario enviado por cliente.

### 20.1. Taxonomia minima

```text
UML_CLASS_CREATED
UML_CLASS_UPDATED
UML_CLASS_DELETED
UML_ATTRIBUTE_CREATED
UML_ATTRIBUTE_UPDATED
UML_ATTRIBUTE_DELETED
UML_METHOD_CREATED
UML_METHOD_UPDATED
UML_METHOD_DELETED
UML_RELATIONSHIP_CREATED
UML_RELATIONSHIP_UPDATED
UML_RELATIONSHIP_DELETED
UML_ELEMENT_MOVED
AI_ACTIONS_APPLIED
METHOD_SPEC_UPDATED
FLUTTER_THEME_UPDATED
GENERATION_STARTED
GENERATION_COMPLETED
GENERATION_FAILED
PROJECT_VERSION_CREATED
PROJECT_VERSION_RESTORED
PROJECT_MEMBER_ADDED
PROJECT_MEMBER_ROLE_CHANGED
PROJECT_MEMBER_REMOVED
```

Aceptar aliases antiguos al leer, pero escribir nuevos eventos con nombres canonicos.

### 20.2. Resumen seguro

Ejemplo:

```json
{
  "event_type": "PROJECT_VERSION_RESTORED",
  "summary_key": "activity.version_restored",
  "payload": {
    "source_version_id": "uuid",
    "source_version_number": 4,
    "backup_version_id": "uuid",
    "backup_version_number": 7,
    "project_revision": 92
  }
}
```

No insertar snapshots completos en eventos.

---

## 21. Secuencia y paginacion de actividad

Sustituir el limite simple por cursor estable:

```http
GET /api/v1/projects/{project_id}/activity?before_sequence=351&limit=50&type=...
```

Respuesta:

```json
{
  "items": [],
  "next_cursor": 301,
  "has_more": true,
  "latest_sequence": 351
}
```

Reglas:

- Orden descendente para historial.
- Cursor basado en `sequence_number`, no offset.
- Limite acotado.
- Filtros permitidos por tipos conocidos.
- Misma politica de acceso que el proyecto.
- No perder eventos si se insertan nuevos durante paginacion.

Mantener el endpoint antiguo temporalmente si el frontend desplegado aun lo usa.

---

## 22. Agrupacion visual sin perder eventos

La base conserva eventos individuales. El frontend puede agrupar para lectura:

- Varios movimientos consecutivos del mismo elemento y actor.
- Varias modificaciones menores dentro de una ventana corta.
- Una aplicacion de IA con multiples acciones bajo el mismo `correlation_id`.
- Una generacion coordinada Spring Boot/Flutter.

La agrupacion no debe:

- Eliminar registros.
- Cambiar secuencias.
- Ocultar restauraciones o cambios de acceso.
- Mezclar actores.
- Mezclar diagramas sin indicarlo.

---

## 23. Auditoria administrativa

Fortalecer `AuditLog` sin convertirlo en copia del proyecto.

Campos recomendados:

- actor nullable para procesos del sistema;
- proyecto nullable;
- modulo;
- accion canonica;
- resultado `success`, `denied`, `failed`;
- recurso y resource id;
- request/correlation id;
- metadata saneada;
- timestamp UTC.

Registrar accesos denegados a restauracion con suficiente contexto para investigar, pero sin snapshot ni token.

### 23.1. Saneamiento

Antes de persistir metadata, eliminar por nombre y profundidad:

- `password`.
- `token`.
- `authorization`.
- `secret`.
- `private_key`.
- `auth` de Web Push.
- `p256dh`.
- cookies.
- cadenas de conexion.

Aplicar limites de longitud y profundidad.

---

## 24. Conversacion de IA ante una restauracion

Reglas obligatorias:

1. No borrar mensajes posteriores a la version objetivo.
2. No cambiar `applied` a `pending`.
3. No reaplicar acciones antiguas automaticamente.
4. Insertar un evento del sistema en la conversacion o referencia visible que diga que el proyecto fue restaurado, sin fingir un mensaje humano.
5. Enlazar ese aviso con `ProjectRestoreOperation`.
6. Actualizar el contexto actual usado por la siguiente solicitud de IA.
7. Invalidar caches de resumen que dependan del UML anterior.
8. Mantener el historial anterior consultable como evidencia.

Si la IA menciona elementos que ya no existen despues de restaurar, el siguiente turno debe resolver el modelo actual y explicar la discrepancia, no inventar ids.

---

## 25. Modelo de notificacion persistente

Crear `Notification` si no existe una entidad equivalente:

- `id` UUID.
- `recipient_user_id`.
- `project_id` nullable.
- `actor_user_id` nullable.
- `type` canonico.
- `severity`: `info`, `success`, `warning`, `error`.
- `title_key` o titulo saneado.
- `body_key` y parametros, o cuerpo saneado.
- `resource_type`.
- `resource_id` nullable.
- `deep_link` JSONB estructurado.
- `dedup_key`.
- `group_key` nullable.
- `occurred_at`.
- `read_at` nullable.
- `clicked_at` nullable.
- `archived_at` nullable.
- timestamps.

Indices:

- destinatario + fecha descendente;
- destinatario + `read_at`;
- proyecto + fecha;
- deduplicacion.

La notificacion se crea en la misma transaccion que el hecho de negocio.

---

## 26. Destino interno seguro

No almacenar URLs externas arbitrarias. Usar un descriptor:

```json
{
  "route_name": "project_collaborative",
  "params": {
    "project_id": "uuid"
  },
  "query": {
    "panel": "versions",
    "version_id": "uuid"
  }
}
```

El frontend mantiene una lista cerrada de `route_name` permitidos y construye la ruta. El backend valida ids y acceso cuando la pantalla carga.

Destinos minimos:

- invitacion/proyecto;
- editor colaborativo y diagrama;
- version restaurada;
- conversacion IA;
- generacion y artefacto;
- perfil/configuracion de push.

Evitar open redirects y no incluir tokens en query strings.

---

## 27. Modelo `NotificationPreference`

Permitir preferencias por usuario y categoria:

- `category`.
- `in_app_enabled`.
- `push_enabled`.
- `project_id` nullable para override por proyecto.
- `muted_until` nullable.

Reglas:

- Avisos de seguridad y cambios de acceso pueden ser obligatorios en bandeja.
- Push siempre requiere permiso del navegador y suscripcion activa.
- Desactivar push no elimina la bandeja.
- Preferencias de un proyecto prevalecen sobre defaults globales.
- El usuario puede silenciar cambios menores sin silenciar restauraciones.

---

## 28. Outbox de notificaciones

Crear `NotificationOutbox` o consolidar una infraestructura equivalente:

- `id`.
- `notification_id`.
- `channel`: inicialmente `web_push`.
- `status`: `pending`, `processing`, `delivered`, `retry`, `dead`.
- `attempt_count`.
- `available_at`.
- `locked_at`.
- `locked_by`.
- `last_error_code` saneado.
- `delivered_at` nullable.
- timestamps.

### 28.1. Creacion atomica

Al confirmar el negocio:

1. Crear notificacion persistente.
2. Evaluar preferencias.
3. Crear outbox solo para canales habilitados.
4. Commit.

No llamar a `webpush()` dentro de la transaccion del proyecto.

### 28.2. Dispatcher

Implementar un despachador idempotente:

- Recupera filas con `FOR UPDATE SKIP LOCKED`.
- Marca lote como `processing`.
- Envia a suscripciones activas.
- Registra resultado por intento.
- Usa backoff exponencial con jitter.
- Elimina/desactiva suscripciones en HTTP 404/410.
- Reintenta 429 y fallos temporales.
- No reintenta indefinidamente errores permanentes.
- Mueve a `dead` al superar maximo configurable.

Puede ejecutarse mediante worker existente, proceso dedicado o comando programado. No presentar `BackgroundTasks` como garantia durable.

### 28.3. Recuperacion

Filas `processing` cuyo lock expiro deben regresar a `retry`. El dispatcher no debe duplicar la notificacion de bandeja aunque un push se reintente.

---

## 29. Politica de deduplicacion

Cada notificacion relevante recibe `dedup_key` determinista.

Ejemplos:

```text
invitation:{invitation_id}
version-created:{version_id}:{recipient_id}
restore-completed:{restore_operation_id}:{recipient_id}
generation-completed:{generation_id}:{recipient_id}
ai-confirmation:{message_id}:{recipient_id}
```

Crear restriccion unica por destinatario y `dedup_key`.

Para eventos agrupables usar `group_key` y ventana temporal, por ejemplo:

```text
project-activity:{project_id}:{recipient_id}:2026-10-15T18:10
```

Actualizar contador y resumen de una notificacion agrupada sin borrar los eventos fuente.

---

## 30. Matriz de notificaciones

Implementar una politica central, no llamadas dispersas en routers.

| Evento | Destinatarios | Bandeja | Push | Agrupacion |
| --- | --- | --- | --- | --- |
| Invitacion creada | Usuario invitado | Si | Si | Por invitacion |
| Invitacion aceptada/rechazada | Invitador/organizador | Si | Opcional | Por invitacion |
| Miembro removido | Usuario afectado | Si | Si | No |
| Rol cambiado | Usuario afectado | Si | Si | No |
| Version manual guardada | Otros organizadores | Si | Configurable | Por version |
| Restauracion completada | Miembros activos excepto actor | Si | Si | No |
| Restauracion fallida | Actor solicitante | Si | Si | Por operacion |
| IA requiere confirmacion | Usuario solicitante y autorizados pertinentes | Si | Configurable | Por mensaje |
| Accion IA aplicada | Otros colaboradores | Actividad; bandeja agrupada opcional | No por defecto | Por operacion |
| Generacion completada | Solicitante | Si | Si | Por ejecucion |
| Generacion fallida | Solicitante | Si | Si | Por ejecucion |
| Edicion UML menor | Ninguno como push | No; solo actividad | No | Actividad visual |
| Tema guardado | Otros editores, si se configura | Agrupada | No por defecto | Por ventana |

No notificar al actor sobre su propia accion salvo resultado asincrono, error o confirmacion requerida.

---

## 31. Servicio de notificaciones de dominio

Crear una API interna central:

```python
notification_service.record(
    event=DomainNotificationEvent(...),
    session=db,
) -> list[Notification]
```

Responsabilidades:

- Resolver destinatarios.
- Excluir actor cuando corresponda.
- Aplicar membresia y preferencias.
- Deduplicar.
- Crear notificaciones.
- Crear outbox.
- Construir deep links permitidos.

Los routers no deben armar manualmente titulos, tags y URLs para cada caso. Deben invocar al servicio de aplicacion y publicar el resultado confirmado.

---

## 32. Web Push

Conservar el soporte existente de `PushSubscription` y fortalecerlo.

### 32.1. Seguridad

- VAPID private key solo en secretos de entorno.
- Nunca enviarla al frontend ni registrarla.
- Public key puede exponerse por endpoint autenticado.
- Validar longitud y formato de `endpoint`, `p256dh` y `auth`.
- Limitar suscripciones por usuario/dispositivo.
- Una suscripcion pertenece a un unico usuario actual.
- Al cerrar sesion ofrecer desuscripcion del dispositivo, sin forzarla si se desea recibir push.

### 32.2. Payload minimo

```json
{
  "notification_id": "uuid",
  "title": "Version restaurada",
  "body": "El proyecto fue restaurado a la version 4.",
  "tag": "restore-uuid",
  "deep_link": {
    "route_name": "project_collaborative",
    "params": {"project_id": "uuid"},
    "query": {"panel": "versions"}
  }
}
```

No incluir snapshot, prompts, detalles sensibles ni datos innecesarios.

### 32.3. Service worker

- Mostrar una sola notificacion por `tag` cuando aplique.
- Al hacer clic, enfocar una ventana existente o abrir la PWA.
- Resolver el deep link con rutas permitidas.
- Marcar `clicked_at` cuando el cliente abra el recurso.
- Si el usuario ya no tiene acceso, redirigir a proyectos con mensaje claro.
- No asumir que la aplicacion ya esta cargada.

---

## 33. API de bandeja

Endpoints sugeridos:

```http
GET  /api/v1/notifications?cursor=...&limit=30&unread_only=false
GET  /api/v1/notifications/unread-count
POST /api/v1/notifications/{notification_id}/read
POST /api/v1/notifications/read-all
POST /api/v1/notifications/{notification_id}/clicked
GET  /api/v1/notifications/preferences
PUT  /api/v1/notifications/preferences
```

Reglas:

- Solo el destinatario accede a su notificacion.
- Marcar leida es idempotente.
- `read-all` acepta limite temporal opcional para no marcar avisos nuevos llegados durante la llamada.
- Paginacion por cursor estable.
- Conteo no leido eficiente mediante indice.
- No devolver claves de suscripcion.

---

## 34. Eventos WebSocket de fase 7

Definir contratos versionados:

```text
PROJECT_ACTIVITY_APPENDED
PROJECT_VERSION_CREATED
PROJECT_VERSION_RESTORED
PROJECT_STATE_INVALIDATED
NOTIFICATION_CREATED
NOTIFICATION_READ
GENERATION_STATUS_CHANGED
```

### 34.1. Restauracion

Despues del commit publicar, en orden:

1. `PROJECT_VERSION_RESTORED` con ids y resumen.
2. `PROJECT_STATE_INVALIDATED` con nueva revision y diagramas afectados.

Cada cliente debe:

- Comparar `project_revision`.
- Cancelar solicitudes antiguas.
- Limpiar cambios optimistas no confirmados.
- Recargar lista de diagramas, diagrama abierto, tema y configuracion.
- Mantener abierta la conversacion de IA.
- Mostrar aviso no bloqueante.

No aplicar cientos de eventos sinteticos para reconstruir el snapshot en el navegador.

### 34.2. Reconexion

El cliente envia su ultima secuencia conocida. El servidor entrega backlog permitido o indica `resync_required`. Una restauracion siempre puede forzar resincronizacion completa del estado versionable.

### 34.3. Publicacion despues de commit

Nunca emitir exito antes de confirmar la base. Si la publicacion falla, clientes se recuperan por revision/backlog y la operacion sigue valida.

---

## 35. Interfaz: panel flotante de actividad

Evolucionar `ProjectHistoryPanel` sin crear una pantalla aislada innecesaria.

Todos los miembros ven:

- Pestana `Actividad`.
- Actor.
- Accion localizada.
- Recurso afectado.
- Diagrama cuando aplique.
- Momento.
- Agrupaciones expandibles.
- Carga incremental.

Propietario/organizador ve ademas:

- Pestana `Versiones`.
- Boton `Guardar version`.
- Inspeccion/resumen.
- Accion de restaurar.
- Estado y resultado de restauracion.

Los demas roles no deben ver controles deshabilitados de restauracion como invitacion a intentar; simplemente no se renderizan.

---

## 36. Interfaz: guardar version

Usar modal accesible con:

- Nombre.
- Descripcion opcional.
- Resumen del estado a capturar.
- Revision actual.
- Indicador de contenido: diagramas, tema y configuracion.
- Error de validacion.
- Estado de guardado.

Prevenir doble envio. Al completar:

- Insertar version en la lista sin esperar polling.
- Mostrar confirmacion.
- Conservar el diagrama abierto.
- No cerrar silenciosamente ante error.

---

## 37. Interfaz: restaurar version

No usar solo `window.confirm`.

Crear dialogo accesible con:

- Numero y nombre de version.
- Autor y fecha.
- Resumen de diferencias.
- Advertencias del adaptador V1.
- Mensaje explicito de respaldo automatico.
- Aclaracion de lo que no cambia: conversacion, miembros, bitacora y artefactos.
- Campo de confirmacion cuando el cambio sea destructivo y amplio.
- Boton de restaurar reservado al rol autorizado.
- Progreso bloqueante solo para esa accion.

Despues del exito:

- Mostrar version objetivo y numero del respaldo.
- Recargar contenido autoritativo.
- Navegar al primer diagrama disponible solo si el actual desaparecio.
- Conservar la ventana de actividad utilizable.

---

## 38. Interfaz: bandeja de notificaciones

Agregar un boton de campana en el layout autenticado con:

- Badge numerico acotado (`99+`).
- Lista de avisos recientes.
- Estado leido/no leido.
- Icono por categoria.
- Tiempo relativo y fecha accesible.
- Accion `Marcar todas como leidas`.
- Carga incremental.
- Estado vacio.
- Error reintentable.

Al pulsar una notificacion:

1. Marcarla como leida/clicked de forma idempotente.
2. Resolver deep link.
3. Navegar dentro de la SPA.
4. Abrir panel o recurso indicado.

No mezclar el boton de habilitar Push con la bandeja. Uno gestiona canal; el otro muestra datos persistentes.

---

## 39. UX y accesibilidad

- Paneles y dialogos con foco inicial y retorno de foco.
- Cierre con Escape cuando no haya restauracion en progreso.
- `aria-live` para resultados.
- Botones con iconos Lucide y tooltip/label.
- Texto sin truncar informacion critica; usar dos lineas o detalle expandible.
- No depender solo del color para no leido, error o severidad.
- Soportar tema claro/oscuro existente.
- Mantener dimensiones estables del boton flotante y badge.
- Evitar solapamiento entre asistente, historial y notificaciones.
- En movil, convertir paneles flotantes en sheet de ancho completo.

---

## 40. Codigos de error de dominio

Definir respuestas estables:

```text
PROJECT_NOT_FOUND
PROJECT_ACCESS_DENIED
VERSION_MANAGE_FORBIDDEN
VERSION_NOT_FOUND
VERSION_DUPLICATE_CONTENT
SNAPSHOT_INVALID
SNAPSHOT_TOO_LARGE
SNAPSHOT_VERSION_UNSUPPORTED
PROJECT_REVISION_CONFLICT
RESTORE_IN_PROGRESS
RESTORE_FAILED
IDEMPOTENCY_KEY_REUSED
NOTIFICATION_NOT_FOUND
PUSH_NOT_CONFIGURED
PUSH_SUBSCRIPTION_INVALID
```

El frontend decide mensajes por codigo, no parseando frases del backend.

---

## 41. Estructura sugerida de backend

Adaptar a la estructura real, evitando duplicados:

```text
backend/app/modules/proyectos_colaboracion/
  models/
    project_version.py
    project_restore_operation.py
    collaboration_event.py
  schemas/
    project_snapshot.py
    project_version.py
    project_activity.py
  repositories/
    project_version_repository.py
    project_activity_repository.py
  services/
    project_snapshot_service.py
    project_version_service.py
    project_restore_service.py
    project_activity_service.py
    project_mutation_guard.py
  routers/
    project_versions.py
    project_activity.py

backend/app/modules/notificaciones/
  models/
    notification.py
    notification_preference.py
    notification_outbox.py
    push_subscription.py
  schemas/
    notification.py
    preference.py
  repositories/
    notification_repository.py
    outbox_repository.py
  services/
    notification_service.py
    notification_policy.py
    outbox_dispatcher.py
    push_service.py
  routers/
    notifications.py
    push.py
  commands/
    dispatch_notifications.py
```

No es obligatorio mover archivos existentes si el cambio aumenta riesgo. Si se conserva `ProjectService`, separar al menos responsabilidades internas y pruebas.

---

## 42. Estructura sugerida de frontend

```text
frontend/src/modules/gestion_proyectos_colaboracion/
  components/
    ProjectHistoryPanel.tsx
    ProjectActivityList.tsx
    ProjectVersionList.tsx
    SaveVersionDialog.tsx
    RestoreVersionDialog.tsx
  services/
    projectVersionService.ts
    projectActivityService.ts
  hooks/
    useProjectActivity.ts
    useProjectVersions.ts
    useProjectInvalidation.ts

frontend/src/modules/notificaciones/
  components/
    NotificationButton.tsx
    NotificationPanel.tsx
    NotificationItem.tsx
    NotificationPreferences.tsx
  services/
    notificationService.ts
  hooks/
    useNotifications.ts
    useUnreadNotificationCount.ts

frontend/src/core/notifications/
  pushNotificationService.ts
  notificationDeepLink.ts
```

Reutilizar TanStack Query si ya esta instalado; de lo contrario, seguir el patron local sin agregar una dependencia solo por preferencia.

---

## 43. Migraciones Alembic

Crear migraciones pequenas y revisables.

### 43.1. Migracion de versiones

- Agregar columnas nuevas nullable cuando haya datos.
- Backfill `kind = manual`.
- Extraer `snapshot_schema_version` desde JSONB, usando `1` para historicos validos.
- Calcular hash y tamano mediante script controlado o servicio de backfill.
- Convertir estado historico ambiguo sin perder datos.
- Aplicar `NOT NULL` y checks despues del backfill.

### 43.2. Restauraciones

- Crear tabla e indices.
- Unique de idempotencia parcial.
- Foreign keys con politica de borrado coherente.

### 43.3. Notificaciones

- Crear notificaciones, preferencias y outbox.
- No migrar suscripciones push a notificaciones.
- Mantener endpoints existentes durante transicion.

### 43.4. Revision del proyecto

Agregar `project_revision` con default y backfill. Todo proyecto existente inicia en una revision valida positiva.

### 43.5. Downgrade

El downgrade debe ser tecnicamente consistente en desarrollo. Documentar si perderia datos de bandeja; nunca intentar meterlos en columnas antiguas.

---

## 44. Seguridad y privacidad

- Autorizacion por objeto en cada endpoint.
- No permitir enumerar ids de versiones ajenas.
- Rate limit para guardar/restaurar y prueba push.
- CSRF segun estrategia de autenticacion existente.
- Validar JSONB con esquemas, no confiar en cliente.
- Limitar payload WebSocket.
- Sanitizar texto presentado en notificaciones.
- React escapa texto; no usar HTML recibido.
- No almacenar prompts completos en notificaciones.
- No registrar endpoints push ni claves en logs.
- Cifrar secretos de despliegue fuera del repositorio.
- Aplicar retencion razonable a intentos de outbox y errores.
- Preservar auditoria segun politica del sistema.

---

## 45. Observabilidad

Agregar logs estructurados y metricas sin secretos:

- `project_versions_created_total`.
- `project_restore_total{status}`.
- `project_restore_duration_seconds`.
- `snapshot_size_bytes`.
- `snapshot_validation_failures_total{code}`.
- `notifications_created_total{type}`.
- `notification_outbox_pending`.
- `push_delivery_total{status}`.
- `push_delivery_latency_seconds`.
- `inactive_subscriptions_total`.
- `websocket_invalidation_total`.

Correlacionar request, evento, restauracion y notificacion mediante `correlation_id`.

Alertar si:

- crece outbox pendiente;
- restauraciones fallan repetidamente;
- snapshots exceden tendencia esperada;
- aumenta 404/410 de push;
- existen saltos o duplicados de secuencia.

---

## 46. Rendimiento

- No devolver snapshots en listas de versiones.
- Crear DTO resumen y endpoint de detalle separado.
- Paginar actividad y notificaciones.
- Seleccionar solo columnas necesarias.
- Evitar N+1 al resolver actor y destinatarios.
- Comprimir respuestas grandes si infraestructura lo permite.
- No recalcular diferencias de restauracion en cada render.
- Cachear preview de restauracion por hash/revision por un periodo corto.
- Invalidar cache al cambiar `project_revision`.
- Procesar outbox en lotes acotados.

---

## 47. Retencion y eliminacion

No implementar borrado de versiones como parte principal de esta fase salvo requisito existente.

Politica recomendada:

- Versiones manuales: conservar hasta accion administrativa futura.
- Respaldos pre-restauracion: conservar; permitir futura politica documentada.
- Actividad y auditoria: inmutables bajo retencion definida.
- Notificaciones: archivables por usuario; purga programada solo tras periodo.
- Outbox entregado: purgable despues de periodo operativo.
- Intentos `dead`: conservar suficiente para diagnostico.

Eliminar un proyecto debe seguir la politica global y no dejar datos personales o filas huerfanas.

---

## 48. Pruebas unitarias de snapshot

Crear pruebas extensas para:

1. Construccion V2 con todos los bloques.
2. Canonicalizacion determinista.
3. Hash igual con distinto orden irrelevante.
4. Hash diferente cuando cambia UML.
5. Hash diferente cuando cambia tema.
6. Hash diferente cuando cambia configuracion de generacion.
7. Exclusiones de `captured_at` en hash.
8. Rechazo de relacion huerfana.
9. Rechazo de metodo con referencia inexistente.
10. Rechazo de UUID de otro proyecto.
11. Limite de tamano.
12. Ausencia de secretos y conversaciones.
13. Upgrade V1 a V2.
14. Rechazo de version futura.
15. Defaults seguros para tema faltante.

Usar fixtures pequenos y legibles; agregar uno integral para association class, metodos y tema.

---

## 49. Pruebas unitarias de versionado

- Solo propietario/organizador crea version.
- Editor recibe 403.
- Doble solicitud con misma idempotency key devuelve la misma version.
- Clave reutilizada con contenido/operacion distinta falla.
- Dos creaciones concurrentes obtienen numeros unicos.
- La lista no incluye snapshot pesado.
- La version no cambia al ser restaurada.
- Respaldo se marca `pre_restore_backup`.
- Nombre y descripcion se validan.
- Evento y auditoria contienen ids correctos.

---

## 50. Pruebas unitarias de restauracion

- Snapshot invalido se rechaza antes de borrar.
- V1 valido se adapta.
- Tema se restaura.
- Configuracion de generacion se restaura.
- Metodos y especificaciones se restauran.
- Relaciones y multiplicidades se restauran.
- Elementos sobrantes se eliminan del estado activo.
- Conversacion no cambia.
- Eventos anteriores no cambian.
- Artefactos anteriores no cambian.
- Respaldo representa exactamente el estado previo.
- Fallo intermedio produce rollback total.
- Revision posterior es mayor que la anterior.
- Hash posterior coincide con objetivo normalizado.
- Reintento idempotente no crea segundo respaldo.
- Editor y visualizador reciben 403.

---

## 51. Pruebas concurrentes

Usar PostgreSQL real en pruebas de integracion, no SQLite, para validar locks.

Escenarios:

1. Dos versiones manuales simultaneas.
2. Dos restauraciones simultaneas del mismo proyecto.
3. Restauracion y edicion UML simultaneas.
4. Restauracion y guardado de tema simultaneos.
5. Restauracion y accion IA confirmada simultaneas.
6. Restauracion y generacion iniciada simultaneas.
7. Dos procesos de outbox tomando el mismo lote.
8. Dos dispositivos marcando la misma notificacion.

Resultado: serializacion, conflicto controlado o idempotencia; nunca corrupcion ni 500 no explicado.

---

## 52. Pruebas de bitacora

- Secuencia unica y monotona.
- Idempotencia de `client_event_id`.
- Evento no puede apuntar a diagrama ajeno.
- Cursor no repite ni omite bajo nuevas inserciones.
- Filtros respetan tipos.
- Actor y resumen correctos.
- Payload no contiene secretos.
- Agrupacion frontend conserva cantidad y detalle.
- Restauracion agrega evento, no reemplaza historial.
- IA referencia mensaje/operacion sin duplicar texto completo.

---

## 53. Pruebas de notificaciones

- Crear evento relevante genera notificacion correcta.
- Actor se excluye segun matriz.
- Usuario sin membresia no recibe cambios futuros.
- Preferencia desactiva push, no necesariamente bandeja.
- `dedup_key` evita duplicados.
- Cambios menores no generan push.
- Restauracion genera aviso para miembros.
- Generacion completada avisa al solicitante.
- Deep link usa ruta permitida.
- Intento de URL externa se rechaza.
- Marcar leida es idempotente.
- Conteo no leido se actualiza.
- Outbox aparece en la misma transaccion.
- Rollback del negocio no deja notificacion.

---

## 54. Pruebas Web Push y outbox

Mockear transporte externo, no la politica de negocio.

- Envio exitoso marca delivered.
- 404/410 desactiva o elimina suscripcion.
- 429 programa retry.
- Timeout programa retry con backoff.
- Error permanente termina en dead.
- Lock expirado se recupera.
- Dos workers no envian el mismo intento simultaneamente.
- VAPID ausente no rompe el negocio.
- Payload no supera limites razonables.
- Click abre deep link y registra `clicked_at`.

---

## 55. Pruebas frontend

Con Vitest y Testing Library:

- Todos ven actividad.
- Solo organizador/propietario ve versiones y controles.
- Guardar version previene doble clic.
- Dialogo de restauracion muestra diferencias.
- Restauracion exitosa llama recarga.
- Evento WebSocket invalida queries correctas.
- Conversacion no se desmonta/perde por restauracion.
- Badge refleja no leidas.
- Click marca y navega.
- Deep link desconocido cae a ruta segura.
- Panel soporta estados vacio, carga y error.
- Textos largos no desbordan.
- Navegacion por teclado y foco funcionan.

---

## 56. Pruebas end-to-end

Con Playwright o herramienta existente:

### Escenario A: version completa

1. Organizador crea proyecto con UML.
2. Define metodos.
3. Personaliza tema.
4. Configura generacion.
5. Guarda version A.
6. Modifica UML y tema.
7. Guarda version B.
8. Restaura A.
9. Verifica UML, preview y configuracion A.
10. Verifica que conversacion posterior sigue presente.
11. Verifica respaldo automatico del estado B.

### Escenario B: colaborador conectado

1. Editor abre mismo diagrama.
2. Organizador restaura.
3. Editor recibe invalidacion.
4. Editor recarga sin estado mezclado.
5. Panel muestra quien restauro y a que version.

### Escenario C: permisos

1. Editor intenta endpoint manualmente.
2. Obtiene 403.
3. Auditoria registra denegacion.
4. No se crea respaldo ni evento de exito.

### Escenario D: notificacion

1. Completa una generacion.
2. Aparece notificacion persistente.
3. Push se simula/entrega.
4. Click abre generacion correcta.
5. Queda leida en otro dispositivo tras sincronizar.

---

## 57. Pruebas de migracion

Preparar una base con datos anteriores:

- Proyecto con snapshot V1.
- Version marcada `saved`.
- Version marcada `restored` por comportamiento antiguo.
- Eventos existentes.
- Suscripciones push existentes.
- Conversacion IA existente.

Ejecutar `alembic upgrade head` y comprobar:

- No se pierden versiones.
- V1 sigue restaurable mediante adaptador.
- Conversacion y eventos permanecen.
- Suscripciones siguen activas.
- Nuevas restricciones son validas.
- Aplicacion inicia.

Ejecutar downgrade en entorno desechable y documentar limites.

---

## 58. Pruebas de regresion

Ademas de las nuevas suites, ejecutar:

- Autenticacion y usuarios.
- Gestion de proyectos y miembros.
- Editor UML.
- WebSocket colaborativo.
- IA por texto/voz/imagen.
- Especificacion de metodos.
- Generacion Spring Boot.
- Generacion Flutter.
- Editor de estilos y preview.
- Importacion/exportacion.
- Push existente.

No declarar terminada la fase si solo pasan pruebas unitarias nuevas y falla una funcion previa.

---

## 59. Casos limite obligatorios

- Proyecto sin diagramas.
- Proyecto con varios diagramas.
- Version V1 sin tema.
- Tema corrupto.
- Diagrama abierto eliminado por restauracion.
- Usuario removido mientras tiene panel abierto.
- Organizador degradado durante confirmacion.
- Snapshot muy grande.
- Doble clic en restaurar.
- Cliente pierde conexion durante restauracion.
- WebSocket recibe evento despues de reconectar.
- Push denegado por navegador.
- VAPID no configurado.
- Suscripcion expirada.
- Outbox detenido y reiniciado.
- Notificacion apunta a recurso ya eliminado.
- Version restaurada dos veces.
- Restauracion a respaldo automatico.
- Generacion activa mientras cambia revision.

Para generacion activa, conservar el snapshot/plan con el que inicio. La restauracion afecta futuras ejecuciones, no altera una ejecucion ya materializada.

---

## 60. Estrategia de implementacion en una sola pasada

Aunque el trabajo se haga internamente por bloques, entregar la fase completa.

Orden recomendado:

1. Inventariar contratos de Fases 1 a 6.
2. Crear modelos Pydantic y canonicalizacion.
3. Crear migraciones y backfill.
4. Implementar snapshot V2 y adaptador V1.
5. Endurecer numeracion e idempotencia.
6. Implementar guard de mutacion.
7. Implementar restore preview.
8. Implementar restauracion atomica completa.
9. Normalizar eventos y actividad paginada.
10. Implementar notificaciones persistentes y preferencias.
11. Implementar outbox y dispatcher.
12. Migrar llamadas push dispersas a politica central.
13. Actualizar WebSocket.
14. Actualizar panel de actividad/versiones.
15. Crear bandeja de notificaciones.
16. Ejecutar pruebas unitarias, integracion y E2E.
17. Documentar operacion y verificar secretos.

No dejar dos rutas activas de notificacion que generen duplicados durante la transicion.

---

## 61. Compatibilidad durante despliegue

Aplicar una estrategia expandir/migrar/contraer:

1. Desplegar columnas y tablas compatibles.
2. Backend escribe formato nuevo y lee V1/V2.
3. Frontend consume contratos compatibles.
4. Ejecutar backfill.
5. Activar restricciones.
6. Retirar codigo legado solo tras verificar.

Durante despliegue mixto:

- No exigir campos que el backend anterior no envia sin defaults.
- No publicar eventos que rompan clientes antiguos; versionar payload.
- Evitar que dos mecanismos push notifiquen lo mismo.

---

## 62. Configuracion de entorno

Documentar en `.env.example` solo nombres y valores ficticios:

```dotenv
VAPID_PUBLIC_KEY=
VAPID_PRIVATE_KEY=
VAPID_SUBJECT=mailto:admin@example.com
NOTIFICATION_OUTBOX_BATCH_SIZE=50
NOTIFICATION_OUTBOX_MAX_ATTEMPTS=6
NOTIFICATION_OUTBOX_POLL_SECONDS=5
SNAPSHOT_MAX_BYTES=5242880
PROJECT_ACTIVITY_PAGE_SIZE=50
```

No sobrescribir secretos reales. No imprimirlos en pruebas o logs.

---

## 63. Documentacion operativa

Crear o actualizar documentacion con:

- Diferencia entre actividad, versiones, auditoria y conversacion.
- Quien puede guardar/restaurar.
- Contenido del snapshot.
- Como funciona el respaldo automatico.
- Como arrancar el dispatcher de outbox.
- Como generar claves VAPID sin subirlas.
- Como diagnosticar push.
- Como recuperar outbox bloqueado.
- Como validar una migracion V1 a V2.
- Como inspeccionar una restauracion fallida sin exponer secretos.

La documentacion debe corresponder a comandos reales del repositorio.

---

## 64. Archivos que no deben tocarse sin necesidad

- No modificar generadores Spring Boot/Flutter salvo para consumir configuracion restaurada de forma coherente.
- No reescribir el motor de IA.
- No cambiar reglas UML ajenas al snapshot.
- No sustituir la autenticacion.
- No introducir Redis, Kafka o Celery si no existe necesidad operativa demostrada.
- No cambiar estilos globales de toda la aplicacion para construir dos paneles.

Se puede usar PostgreSQL como fuente de locks y outbox para mantener la arquitectura desplegable actual.

---

## 65. Prohibiciones explicitas

No hacer lo siguiente:

- Crear una version por cada evento.
- Restaurar directamente con JSON del cliente.
- Borrar el proyecto antes de validar el snapshot.
- Cambiar una version a `restored` para indicar uso.
- Incluir mensajes de IA en snapshot.
- Restaurar miembros o roles.
- Eliminar generaciones historicas.
- Publicar WebSocket antes del commit.
- Enviar Web Push dentro de la transaccion principal.
- Depender solo de FastAPI `BackgroundTasks` para entrega durable.
- Usar offset para historiales de alta escritura.
- Guardar URL externa como deep link.
- Notificar cada `MOVE_ELEMENT`.
- Exponer snapshots completos en listas.
- Guardar secretos en metadata.
- Confiar en el rol enviado por frontend.
- Implementar locks solo en memoria.
- Ocultar errores con `except Exception: pass`.
- declarar exito con pruebas omitidas.

---

## 66. Criterios de aceptacion funcional

La fase se acepta solo si:

1. Guardar version captura UML, metodos, tema y configuracion.
2. Dos guardados concurrentes no colisionan.
3. La version es inmutable.
4. Un snapshot V1 existente puede restaurarse.
5. Un snapshot futuro/invalido se rechaza antes de escribir.
6. Restaurar crea respaldo automatico.
7. Restaurar recupera exactamente UML y estilos.
8. Restaurar conserva conversaciones posteriores.
9. Restaurar conserva actividad y auditoria.
10. Restaurar conserva artefactos generados.
11. Un editor no puede restaurar ni por UI ni por API.
12. El creador conserva autoridad aunque exista inconsistencia de membresia historica.
13. Colaboradores conectados recargan estado despues de restaurar.
14. Una falla intermedia deja el proyecto intacto.
15. La actividad usa cursor y secuencia estable.
16. La bandeja persiste avisos aunque push falle.
17. Outbox reintenta sin duplicar notificacion.
18. Cambios menores no saturan al usuario.
19. Cada aviso abre la pantalla relacionada mediante deep link seguro.
20. No hay credenciales en snapshot, logs, API o Git.

---

## 67. Criterios de calidad tecnica

- Tipado estricto backend y frontend.
- Modelos Pydantic para JSONB.
- Migraciones reproducibles.
- Transacciones con limites claros.
- Servicios con responsabilidades separadas.
- Repositorios sin logica de permisos.
- Errores de dominio estables.
- Eventos versionados.
- Idempotencia probada.
- Locks probados con PostgreSQL.
- Consultas sin N+1 obvio.
- Cobertura en rutas destructivas.
- Componentes accesibles.
- Sin duplicacion de push.
- Sin datos sensibles.

---

## 68. Checklist de revision de codigo

Antes de cerrar, revisar manualmente:

- [ ] Ningun snapshot contiene conversacion.
- [ ] Ningun snapshot contiene secretos o URLs privadas.
- [ ] Todas las versiones nuevas tienen hash.
- [ ] La lista no devuelve JSONB completo.
- [ ] El restore valida antes de mutar.
- [ ] Backup y restore estan en una transaccion coherente.
- [ ] La version objetivo no se modifica.
- [ ] La revision activa siempre aumenta.
- [ ] Todos los escritores usan el guard.
- [ ] WebSocket se publica despues del commit.
- [ ] La conversacion sobrevive.
- [ ] La bitacora sobrevive.
- [ ] Los artefactos sobreviven.
- [ ] Solo propietario/organizador restaura.
- [ ] El actor no recibe avisos redundantes.
- [ ] `MOVE_ELEMENT` no genera push.
- [ ] Deep links son internos.
- [ ] Outbox soporta multiples workers.
- [ ] 404/410 de push limpia suscripciones.
- [ ] Preferencias se respetan.
- [ ] Textos largos no rompen paneles.
- [ ] Migracion funciona con datos V1.
- [ ] Pruebas antiguas siguen pasando.

---

## 69. Evidencia de entrega

Al terminar, presentar:

1. Archivos modificados por modulo.
2. Migraciones creadas y estrategia de backfill.
3. Contrato final de snapshot.
4. Endpoints finales.
5. Eventos WebSocket finales.
6. Matriz implementada de notificaciones.
7. Comando real para dispatcher.
8. Pruebas ejecutadas con resultado.
9. Evidencia de restauracion integral.
10. Evidencia de que conversacion y bitacora no cambian.
11. Evidencia de prueba concurrente.
12. Evidencia de ausencia de secretos.
13. Riesgos residuales concretos.

No afirmar que una prueba paso si no fue ejecutada.

---

## 70. Definicion de terminado de la Fase 7

La Fase 7 esta terminada cuando CASE Inteligente permite guardar manualmente un estado completo y reproducible del proyecto, restaurarlo de forma atomica y autorizada con respaldo automatico, mantener intacta toda la trazabilidad posterior, sincronizar correctamente a los colaboradores y avisar hechos relevantes mediante una bandeja persistente y Web Push confiable sin duplicados ni ruido excesivo.

El resultado debe demostrar de extremo a extremo que:

```text
editar UML/metodos/tema/configuracion
        -> guardar version manual V2
        -> continuar colaborando y conversando con IA
        -> restaurar una version anterior
        -> crear respaldo del estado actual
        -> recuperar contenido versionable exacto
        -> conservar conversacion, bitacora y artefactos
        -> invalidar clientes conectados
        -> registrar actor y operacion
        -> crear notificaciones persistentes
        -> entregar push de forma eventual
        -> abrir el recurso correcto desde web o PWA
```

Solo despues de cumplir este flujo se puede avanzar a la Fase 8 con una base fiable para actividad, versiones y notificaciones en dispositivos moviles.
