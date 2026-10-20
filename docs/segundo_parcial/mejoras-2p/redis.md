# Documentación de Redis NoSQL y Registro de Cambios (Change Log)

CASE Inteligente (`parcialsw`) · Ingeniería de Software I · UAGRM 2-2026

## 1. Justificación Arquitectónica
Para cumplir el requerimiento de auditoría y trazabilidad en NoSQL exigido en el 2.º parcial, se integró **Redis Streams** como almacén de eventos de series temporales en tiempo real, manteniendo **PostgreSQL 16** como la fuente de verdad relacional ACID.

## 2. Estructura de Claves y Streams
- `case:changelog:project:{project_id}`: Stream específico de eventos de un proyecto. Tamaño acotado con `MAXLEN ~ 10000` (`REDIS_CHANGE_LOG_MAXLEN`).
- `case:changelog:all`: Stream global para consumo y workers asíncronos (`MAXLEN ~ 50000`).
- `case:lock:{project_id}:{element_type}:{element_id}`: Claves de bloqueo de elementos con TTL (`ELEMENT_LOCK_TTL_SECONDS = 60`).
- `case:proactive:{project_id}:cooldown`: Clave de enfriamiento para sugerencias de IA (`AI_PROACTIVE_COOLDOWN_SECONDS = 120`).

## 3. Formato de Evento en el Stream
```json
{
  "project_id": "UUID",
  "occurred_at": "ISO-8601 UTC",
  "actor_user_id": "UUID",
  "source": "ui | ai | ws | system",
  "module": "modelado_uml",
  "action": "CREATE_CLASS",
  "entity_type": "class",
  "entity_id": "UUID",
  "diagram_id": "UUID",
  "summary": "Creó la clase Factura",
  "metadata": "JSON saneado sin passwords ni tokens (<= 2048 bytes)"
}
```

## 4. Estrategia de Respaldo y Tolerancia a Fallos
Si Redis está deshabilitado (`REDIS_ENABLED=false`) o el servicio se detiene, el backend entra en modo degradación suave sin interrupción:
- Las transacciones en base de datos PostgreSQL continúan ejecutándose normalmente.
- El endpoint `GET /projects/{project_id}/change-log` detecta la indisponibilidad de Redis y sirve los registros desde la tabla `audit_logs` con `source="postgres_fallback"`.
- Cuando Redis vuelve a estar disponible, el comando `python -m app.core.changelog.backfill --project <uuid>` permite reconstruir el Stream desde `audit_logs`.
