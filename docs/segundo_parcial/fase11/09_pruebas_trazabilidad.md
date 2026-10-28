# Pruebas y trazabilidad

## Matriz

| Criterio | Prueba |
|---|---|
| Contrato sin pérdida | `test_phase11_message_document_preserves_public_contract_and_hash` |
| Outbox en transacción | `test_phase11_message_write_enqueues_full_document_without_committing` |
| Lectura Mongo y superposición SQL | `test_phase11_effective_read_prefers_mongo_and_overlays_pending_sql` |
| Paginación bidireccional | `test_phase11_effective_read_keeps_cursor_direction_and_limit` |
| Snapshot idempotente | `test_phase11_context_snapshot_id_is_deterministic_and_versioned` |
| Hash estable | `test_phase11_document_roundtrip_is_async_safe` |
| Rollback SQL | `test_phase11_sql_fallback_is_reversible` |
| Gate de migración | `test_phase11_readiness_requires_completed_memory_migration` |
| PostgreSQL + Mongo reales | `test_phase11_real_postgresql_mongodb_migration_and_idempotency` |

La integración real comprueba además reintento con el mismo `client_message_id`, una sola fila/evento, migración de mensaje y contexto, hash, checkpoint y repetición sin duplicados.

## CI

El job `mongodb-integration` levanta simultáneamente PostgreSQL 16 y MongoDB 8, aplica Alembic y ejecuta las pruebas reales de fases 10 y 11. La construcción Docker depende de este gate.

## Comandos

```bash
cd backend
python -m ruff check app tests migrations
python -m pytest -q
python -m alembic heads
```

Con servicios reales:

```bash
set DATABASE_URL=postgresql+psycopg://case_test:case_test_password@127.0.0.1:5432/case_inteligente_nosql_test
set MONGODB_TEST_URI=mongodb://case_test:case_test_password@127.0.0.1:27017/?authSource=admin
python -m pytest tests/test_phase11_ai_memory_integration.py -q
```

## Resultado local de cierre

- Backend: `124 passed, 4 skipped`.
- Frontend: `41 passed` y build PWA aprobado.
- Motor IA: Ruff aprobado; `59 passed, 1 deselected` al excluir únicamente el smoke de Ollama real porque el servicio local no estaba activo.
- Compose local/productivo, workflow YAML y `git diff --check`: aprobados.
- Alembic: un solo head `f8b2c3d4e5f6` y generación SQL completa aprobada.
