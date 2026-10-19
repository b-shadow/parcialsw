# Notificaciones, outbox y Web Push

## Fuente de verdad

`Notification` alimenta una bandeja persistente por usuario. Contiene severidad, recurso y un `deep_link` estructurado. No guarda URLs externas: `NotificationDeepLink` valida una lista cerrada de rutas internas.

`NotificationPreference` permite opciones globales o por proyecto. Cambios de acceso y seguridad siguen visibles en bandeja. Desactivar Push no elimina avisos internos.

La base impone unicidad tanto por proyecto como global. Para el alcance global utiliza un indice unico parcial sobre usuario y categoria cuando `project_id IS NULL`, evitando duplicados que una restriccion SQL comun no detecta por la semantica de `NULL`.

## Deduplicacion

La unicidad `(recipient_user_id, dedup_key)` evita avisos duplicados. El actor se excluye por defecto; resultados asincronos de generacion pueden incluirlo de forma explicita.

## Entrega durable

La transaccion de negocio crea `Notification` y `NotificationOutbox`. El dispatcher usa bloqueo de lote, estados `pending/processing/delivered/retry/dead`, recuperacion de locks vencidos, maximo de intentos y backoff exponencial con jitter.

Ejecucion manual o programada:

```powershell
cd backend
$env:PYTHONPATH=".;../ai-engine"
.venv\Scripts\python.exe -m app.modules.notificaciones.commands.dispatch_notifications
```

HTTP 404/410 elimina suscripciones caducadas. La clave VAPID privada permanece solo en entorno. El service worker resuelve rutas permitidas, enfoca una ventana existente y transmite `notification_id` para registrar el clic autenticado.

