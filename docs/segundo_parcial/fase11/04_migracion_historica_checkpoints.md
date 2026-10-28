# Migración histórica y checkpoints

## Comando

```bash
cd backend
python -m app.core.nosql.commands.migrate_ai_memory
```

Opciones:

```bash
python -m app.core.nosql.commands.migrate_ai_memory --verify-only
python -m app.core.nosql.commands.migrate_ai_memory --batch-size 500
python -m app.core.nosql.commands.migrate_ai_memory --reset-checkpoint
```

## Cursor

El checkpoint `phase11_ai_memory_v1` usa `(created_at, id)`, no sólo UUID. Esto permite reanudar en orden estable y capturar mensajes nuevos aunque sus UUID aleatorios sean menores que el último procesado.

Estados:

```text
pending -> running -> completed
                   \-> failed -> running
```

Después de cada lote se persisten cursor, procesados y tamaño del último lote. `--reset-checkpoint` reinicia el recorrido sin eliminar documentos; los upserts lo hacen seguro.

## Memoria histórica

Las conversaciones con resumen SQL se transforman en `ai_context_snapshots`. Los resúmenes JSON se conservan como contexto estructurado; texto legado se encapsula sin descartarlo.

## Verificación

El cierre compara por lotes:

- cantidad de mensajes;
- ids faltantes y huérfanos;
- hash de cada mensaje;
- presencia y hash del contexto actual de cada conversación.

Los diagnósticos se limitan a 1000 ids por categoría y el recorrido mantiene memoria acotada. Códigos: `0` consistente, `1` almacén no disponible y `2` divergencia.
