# Migracion y reconciliacion

## Comando

```powershell
python -m app.core.nosql.commands.migrate_uml_diagrams
python -m app.core.nosql.commands.migrate_uml_diagrams --verify-only
python -m app.core.nosql.commands.migrate_uml_diagrams --reset-checkpoint
```

La migracion `phase13_active_uml_diagrams_v1` recorre `(updated_at, id)` en lotes configurables. El checkpoint guarda cursor, procesados, fallos y ultimo resultado. Reiniciar el proceso continua desde el ultimo lote confirmado.

## Verificacion

El verificador compara:

- cantidad SQL y MongoDB;
- documentos faltantes y huerfanos;
- `content_hash` esperado;
- revision de proyecto y revision documental.

Un documento Mongo con revision mayor se conserva. Un hash distinto en la misma revision detiene la migracion para evitar destruir trabajo. El checkpoint solo queda `completed` si no existe deriva.
