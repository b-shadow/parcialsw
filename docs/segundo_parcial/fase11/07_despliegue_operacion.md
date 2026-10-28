# Despliegue y operación

## Orden productivo

`docker-compose.prod.yml` impone:

```text
PostgreSQL + MongoDB saludables
    -> database-migrations
    -> ai-memory-migration
    -> backend
    -> nosql-outbox-worker
```

El backend no acepta tráfico antes de que la migración histórica termine. El worker arranca después y procesa cambios encolados durante la operación.

## Arranque manual

```bash
docker compose up -d postgres mongodb
cd backend
python -m alembic upgrade head
python -m app.core.nosql.commands.bootstrap
python -m app.core.nosql.commands.migrate_ai_memory
python -m app.core.nosql.commands.dispatch_outbox --watch
```

## Readiness

En producción `AI_MESSAGES_MIGRATION_REQUIRED=true`. `/ready` exige:

- PostgreSQL disponible;
- MongoDB disponible;
- checkpoint `phase11_ai_memory_v1` en `completed`.

## Operación posterior

```bash
python -m app.core.nosql.commands.migrate_ai_memory --verify-only
python -m app.core.nosql.commands.reconcile --require-complete
```

No debe eliminarse la tabla SQL de mensajes ni desactivarse fallback durante la ventana de observación de esta fase.
