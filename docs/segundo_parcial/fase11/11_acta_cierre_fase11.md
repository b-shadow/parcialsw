# Acta de cierre de la Fase 11

## Estado

**IMPLEMENTACIÓN COMPLETADA.**

## Entregables

- Almacén documental de mensajes y contexto.
- Lectura Mongo compatible con el contrato existente.
- Outbox para altas y actualizaciones.
- Idempotencia de cliente y de integración.
- Paginación bidireccional acotada.
- Migrador histórico reiniciable.
- Verificación de mensajes y memoria.
- Fallback SQL y rollback documentado.
- Despliegue ordenado con gate de readiness.
- Migración Alembic `f8b2c3d4e5f6`.
- Pruebas unitarias y poliglotas reales en CI.
- Memoria técnica completa.

## Criterios de cierre

| Criterio | Estado |
|---|---|
| Autores, orden, referencias y estados conservados | Cumplido |
| Paginación compatible | Cumplido |
| Reconexión sin duplicados | Cumplido |
| Contexto de chats extensos acotado | Cumplido |
| Resúmenes como documentos separados | Cumplido |
| Migración reiniciable y verificable | Cumplido |
| Mongo como lectura principal | Cumplido |
| Rollback a PostgreSQL | Cumplido |
| CI con ambos almacenes | Cumplido |

## Evidencia

```bash
docker compose -f docker-compose.prod.yml config --quiet
cd backend
python -m ruff check app tests migrations
python -m pytest -q
python -m alembic heads
python -m alembic upgrade head --sql
```

La prueba real se ejecuta en CI porque requiere servicios PostgreSQL y MongoDB limpios. No se sustituye por una base en memoria.

El cierre local obtuvo `124 passed` en backend, `41 passed` y build PWA en frontend, y `59 passed` en el motor IA excluyendo únicamente el smoke que exige un servidor Ollama real activo.

## Decisión

La Fase 11 queda cerrada en código, migración, consistencia, operación, pruebas y documentación. No se autoriza retirar todavía la réplica SQL; esa decisión permanece en la fase 14 tras la ventana de estabilidad.
