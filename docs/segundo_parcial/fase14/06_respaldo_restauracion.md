# Respaldo y restauracion coordinada

## Crear

```powershell
python -m app.core.nosql.commands.coordinated_backup create storage/backups/case.zip
```

El comando exige Outbox drenado, captura dos veces el watermark de revisiones y secuencias, y aborta si cambia durante la exportacion. El ZIP contiene:

- `postgresql.json`: todas las tablas registradas por SQLAlchemy;
- un JSON tipado por coleccion Mongo;
- `manifest.json`: esquema, backup ID, fecha, conteos y SHA-256.

UUID, fechas, decimales, binarios, listas y mapas usan un codec reversible sin colisionar con JSON del usuario.

## Restaurar

```powershell
python -m app.core.nosql.commands.coordinated_backup restore storage/backups/case.zip
```

Por defecto solo restaura sobre PostgreSQL y colecciones Mongo vacias. Antes de escribir valida manifiesto, version, checksums y conteos. `--force` se reserva para recuperacion administrada. Tras restaurar se debe ejecutar reconciliacion operativa y el gate de consolidacion.
