# API y WebSocket

## Versiones y actividad

| Metodo | Ruta | Acceso |
| --- | --- | --- |
| POST | `/projects/{id}/versions` | Propietario/organizador; `Idempotency-Key`. |
| GET | `/projects/{id}/versions` | Propietario/organizador. |
| GET | `/projects/{id}/versions/{version}/restore-preview` | Propietario/organizador. |
| POST | `/projects/{id}/versions/{version}/restore` | Propietario/organizador; revision e idempotencia. |
| GET | `/projects/{id}/activity` | Cualquier miembro. |

## Bandeja

`GET /notifications`, `GET /notifications/unread-count`, `POST /notifications/{id}/read`, `POST /notifications/{id}/clicked`, `POST /notifications/read-all`, `GET/PUT /notifications/preferences`.

Solo el destinatario puede leer o actualizar su aviso. Lectura y clic son idempotentes.

Las respuestas de listado, creacion, vista previa y restauracion exponen metadatos y hashes, pero nunca el JSONB completo del snapshot. El contenido queda encapsulado en el servicio de restauracion.

## Tiempo real

La fase admite `PROJECT_ACTIVITY_APPENDED`, `PROJECT_VERSION_CREATED`, `PROJECT_VERSION_RESTORED`, `PROJECT_STATE_INVALIDATED`, `NOTIFICATION_CREATED` y `NOTIFICATION_READ`. La restauracion fuerza recarga autoritativa del estado versionable; no simula cientos de cambios UML.

El frontend distribuye mensajes recibidos mediante `case:project-socket-event`; panel y bandeja reaccionan sin polling continuo.

