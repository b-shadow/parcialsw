# Operación, despliegue y rollback

## Arranque local

```bash
docker compose up -d postgres mongodb
cd backend
python -m alembic upgrade head
python -m app.core.nosql.commands.bootstrap
uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Procesar Outbox una vez o en modo worker:

```bash
python -m app.core.nosql.commands.dispatch_outbox
python -m app.core.nosql.commands.dispatch_outbox --watch --poll-seconds 2
```

## Despliegue

1. Crear respaldo PostgreSQL.
2. Configurar secretos Mongo.
3. Iniciar PostgreSQL y MongoDB.
4. Ejecutar Alembic hasta `e7a1b2c3d4e5`.
5. Iniciar backend y comprobar `/health` y `/ready`.
6. Iniciar worker Outbox.
7. Ejecutar reconciliación sin `--require-complete` durante la fase 10.

## Rollback de aplicación

En esta fase ningún flujo funcional lee MongoDB. Ante una incidencia:

1. detener `nosql-outbox-worker`;
2. establecer `MONGODB_REQUIRED=false` o `MONGODB_ENABLED=false`;
3. reiniciar backend;
4. conservar Mongo y Outbox para diagnóstico.

El servicio continúa con PostgreSQL sin pérdida funcional.

## Rollback de esquema

Sólo si no existen productores de eventos pendientes:

```bash
cd backend
python -m alembic downgrade da4e5f6a7b8c
```

Antes de eliminar la tabla se debe exportar cualquier evento no completado. Los documentos Mongo no se borran automáticamente.

## Respaldo coordinado

La fase 10 prepara la separación, pero el respaldo coordinado será obligatorio antes del cambio de autoridad. Desde ahora se deben registrar juntos el instante UTC, revisión Alembic y nombre de base Mongo para cada respaldo.
