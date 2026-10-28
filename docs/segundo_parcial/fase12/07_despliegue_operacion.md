# Despliegue y operacion

## Orden productivo

```text
PostgreSQL + MongoDB saludables
  -> Alembic
  -> migracion de memoria IA
  -> migracion de versiones UML
  -> backend
  -> worker Outbox
```

`docker-compose.prod.yml` declara `uml-version-migration` como tarea de una ejecucion. Backend y worker esperan su finalizacion. El backend exige los checkpoints de fases 11 y 12 mediante `/ready`.

## Operacion

```powershell
docker compose -f docker-compose.prod.yml config --quiet
python -m alembic upgrade head
python -m app.core.nosql.commands.migrate_uml_versions --verify-only
python -m app.core.nosql.commands.dispatch_outbox --watch
```

Ante drift no se debe borrar ni reescribir el documento. Se investiga el registro SQL, el evento Outbox y el hash; luego se corrige la causa y se reinicia el checkpoint de forma controlada.
