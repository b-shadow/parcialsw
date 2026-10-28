# Pruebas y trazabilidad

## Matriz

| Criterio | Verificación |
|---|---|
| Configuración por entorno | `test_phase10_settings_load_mongodb_environment` |
| UUID y fechas UTC | `test_phase10_document_contract_serializes_uuid_and_preserves_dates` |
| Validación de contenido | `test_phase10_message_contract_rejects_empty_content` |
| Operaciones permitidas | `test_phase10_mutations_are_idempotent_and_restricted` |
| Bootstrap repetible | `test_phase10_schema_bootstrap_is_repeatable` |
| Timeout y reconexión | `test_phase10_manager_reports_timeout_and_recovers` |
| Outbox dentro de transacción | `test_phase10_outbox_enqueue_participates_in_caller_transaction` |
| Aplicación y recibo Outbox | `test_phase10_outbox_dispatcher_applies_upsert_and_records_receipt` |
| Agotamiento de reintentos | `test_phase10_outbox_moves_permanent_failure_to_dead` |
| Huérfanos, faltantes y hash | `test_phase10_reconciliation_detects_orphans_missing_and_hash_drift` |
| Hash canónico | `test_phase10_canonical_hash_is_order_independent` |
| Readiness doble | `test_phase10_readiness_exposes_both_datastores` |
| MongoDB real | `test_phase10_real_mongodb_contracts_indexes_and_repository` |

## Comandos

```bash
cd backend
uv sync --extra dev
python -m ruff check app tests migrations
python -m pytest -q
```

Con Mongo local:

```bash
set MONGODB_TEST_URI=mongodb://case_user:case_password@127.0.0.1:27018/?authSource=admin
python -m pytest tests/test_phase10_mongodb_integration.py -q
```

## CI

El job `mongodb-integration` crea un servicio limpio `mongo:8.0`, espera su health check y ejecuta la prueba real. `docker-build` depende de este job, por lo que no se publican imágenes si fallan validadores, índices o repositorios.

El job PostgreSQL existente ejecuta upgrade, downgrade, re-upgrade y `alembic check`, incluyendo la tabla Outbox.

## Resultado local de cierre

- Ruff backend: aprobado.
- Pytest backend: `116 passed, 3 skipped`.
- Los tres `skip` corresponden a gates que requieren servicios o toolchains externos; la integración Mongo real se ejecuta obligatoriamente en su job de CI.
- Compose local y productivo: configuración válida.
- Alembic: un solo head, `e7a1b2c3d4e5`.
