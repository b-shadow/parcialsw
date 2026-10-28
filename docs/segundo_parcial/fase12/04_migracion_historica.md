# Migracion historica

## Comando

```powershell
python -m app.core.nosql.commands.migrate_uml_versions
python -m app.core.nosql.commands.migrate_uml_versions --verify-only
python -m app.core.nosql.commands.migrate_uml_versions --reset-checkpoint
```

El cursor compuesto `created_at|id` evita saltos cuando varias versiones comparten fecha. El indice SQL `ix_project_versions_created_id` soporta el recorrido estable.

## Compatibilidad

- Los snapshots v2 se validan y canonicalizan directamente.
- Los snapshots v1 se adaptan en memoria a `ProjectSnapshotV2` con la funcion existente.
- El documento migrado guarda el modelo efectivo v2 y su hash canonico.
- El registro SQL original no se destruye ni se sobrescribe.

## Verificacion

El checkpoint `phase12_uml_versions_v1` registra cursor, procesados, fallos y reporte. La verificacion detecta hasta 1000 IDs por categoria: faltantes, huerfanos y hashes divergentes. Un reporte con diferencias finaliza en estado `failed` y bloquea el readiness cuando la migracion es obligatoria.
