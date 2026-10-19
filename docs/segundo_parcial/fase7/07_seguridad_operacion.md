# Seguridad y operacion

## Permisos

El backend acepta gestion de versiones cuando `owner_id` coincide o existe membresia `ORGANIZADOR`. Un `EDITOR` solo consulta actividad. La pertenencia de version, diagrama, recurso y notificacion se valida en servidor.

## Configuracion

```env
PROJECT_SNAPSHOT_MAX_BYTES=8388608
NOTIFICATION_OUTBOX_BATCH_SIZE=50
VAPID_PUBLIC_KEY=
VAPID_PRIVATE_KEY=
VAPID_SUBJECT=mailto:admin@example.com
```

No registrar VAPID privada, JWT, credenciales AWS, endpoints de suscripcion ni claves `p256dh/auth`. El snapshot y la auditoria aplican saneamiento recursivo.

## Migracion

```powershell
cd backend
$env:PYTHONPATH=".;../ai-engine"
.venv\Scripts\python.exe -m alembic upgrade head
.venv\Scripts\python.exe -m alembic current
```

La cabeza esperada es `b8c2d3e4f5a6`. El downgrade elimina primero outbox, preferencias, notificaciones y restauraciones, y luego columnas e indices agregados.

El dispatcher debe ejecutarse periodicamente. Varias instancias son seguras porque el lote usa `FOR UPDATE SKIP LOCKED`.

