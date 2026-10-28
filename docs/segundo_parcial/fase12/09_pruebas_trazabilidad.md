# Pruebas y trazabilidad

| Criterio | Implementacion | Prueba |
|---|---|---|
| Modelo canonico equivalente | `snapshot_sha256` y lectura comparada | `test_phase12_preview_source_prefers_valid_mongodb_snapshot` |
| Contenido UML completo | Documento guarda `ProjectSnapshotV2` | `test_phase12_document_preserves_complete_snapshot_and_registry_metadata` |
| Escritura atomica | Outbox en transaccion SQL | `test_phase12_version_write_uses_transactional_outbox_without_commit` |
| Inmutabilidad | insert-only por `_id` y hash | `test_phase12_outbox_rejects_mutation_of_immutable_version` |
| Rollback | banderas y fallback SQL | `test_phase12_hash_drift_falls_back_or_fails_by_flag` |
| Migracion reiniciable | cursor compuesto y checkpoint | `test_phase12_real_migration_is_complete_resumable_and_immutable` |
| Arranque protegido | checkpoint requerido | `test_phase12_readiness_requires_completed_uml_version_migration` |
| Restauracion idempotente | `ProjectRestoreOperation` existente | `test_phase12_restore_replay_is_idempotent_and_does_not_read_snapshot` |
| Compatibilidad historica | adaptador v1 a modelo v2 | `test_snapshot_v1_is_adapted_and_future_versions_are_rejected` |

La CI ejecuta la integracion de Fase 12 con PostgreSQL 16 y MongoDB 8 reales. La suite local omite esa prueba cuando faltan `DATABASE_URL` o `MONGODB_TEST_URI`.
