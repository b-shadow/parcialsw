# Snapshot y restauracion

## Captura autoritativa

El navegador no envia snapshots. El servidor construye `ProjectSnapshotV2` con metadatos del proyecto, diagramas completos, metodos y especificaciones, tema Flutter, configuracion reproducible de generacion y configuracion no sensible de IA.

Se excluyen miembros, conversaciones, eventos, auditorias, notificaciones, suscripciones, presets personales, artefactos y secretos. El contrato Pydantic usa `extra="forbid"` y el saneamiento elimina claves sensibles anidadas.

## Integridad

`canonicalize_project_snapshot()` valida, ordena JSON y diagramas, excluye `captured_at` y la revision operativa del tema. `snapshot_sha256()` produce el hash de contenido. Se registran esquema, hash, bytes y revision del proyecto. `PROJECT_SNAPSHOT_MAX_BYTES` limita la captura.

Snapshots V1 se adaptan en memoria con defaults actuales. El JSON original permanece inmutable. Esquemas futuros se rechazan.

## Guardar

1. Autorizar propietario u organizador.
2. Bloquear el proyecto y comprobar revision esperada.
3. Resolver `Idempotency-Key`.
4. Capturar, validar y calcular hash.
5. Rechazar doble clic sin cambios, salvo confirmacion explicita.
6. Reservar numero, crear version, actividad, auditoria y notificaciones.
7. Confirmar y emitir WebSocket.

## Restaurar

La vista previa calcula conteos y diferencias sin escribir. La restauracion valida todo antes de borrar, crea `pre_restore_backup`, reconcilia UML, aplica tema/configuraciones, avanza revision y completa `ProjectRestoreOperation` en un unico commit. La version origen no cambia de estado.

Un reintento con la misma `Idempotency-Key` devuelve el resultado persistido, incluidos los diagramas restaurados, sin crear otro respaldo, repetir la mutacion ni volver a publicar eventos WebSocket.

Despues del commit se publican `PROJECT_VERSION_RESTORED` y `PROJECT_STATE_INVALIDATED`. Se agrega un mensaje `system` a la conversacion IA; los mensajes anteriores conservan estado y secuencia.

