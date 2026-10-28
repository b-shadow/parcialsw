# Lectura, paginación y rollback

## Lectura principal

`GET /api/v1/projects/{project_id}/ai/messages` consulta MongoDB después de comprobar proyecto y membresía en SQL. Mientras exista escritura eventual, superpone mensajes SQL todavía ausentes en Mongo y prefiere el documento Mongo cuando ambos están presentes.

## Cursores

- `before_sequence`: recupera los anteriores en orden ascendente.
- `after_sequence`: recupera los siguientes en orden ascendente.
- sin cursor: recupera los últimos mensajes.
- límite API máximo: 100.
- límite de contexto configurable: máximo 200.

`has_more_before` y `has_more_after` consultan ambos almacenes durante la transición.

## Comparación

Con `AI_MESSAGES_COMPARE_READS=true`, una ausencia o diferencia de hash genera `ai_message_store_drift` con ids, nunca contenido del usuario.

## Banderas

| Variable | Uso |
|---|---|
| `AI_MESSAGES_MONGODB_READ_ENABLED` | activa lectura Mongo primaria |
| `AI_MESSAGES_SQL_FALLBACK_ENABLED` | permite continuidad ante fallo Mongo |
| `AI_MESSAGES_COMPARE_READS` | informa divergencias |
| `AI_MESSAGES_MIGRATION_REQUIRED` | exige checkpoint completo en readiness |

## Rollback inmediato

```text
AI_MESSAGES_MONGODB_READ_ENABLED=false
AI_MESSAGES_SQL_FALLBACK_ENABLED=true
AI_MESSAGES_MIGRATION_REQUIRED=false
```

Después se reinicia el backend. No se requiere restaurar tablas porque la réplica SQL permanece completa en esta fase.
