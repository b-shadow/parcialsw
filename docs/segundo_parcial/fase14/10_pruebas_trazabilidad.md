# Pruebas y trazabilidad

| Criterio | Evidencia |
|---|---|
| Lecturas sin contenido SQL | Test Mongo estricto que verifica que no se construye la proyeccion SQL |
| Retiro fisico SQL | Integracion que verifica ocho tablas ausentes y referencias Mongo sin FK |
| Autoridad identificable | Migracion y restricciones `*_storage = 'mongodb'` |
| Huerfanos y referencias | Auditoria operativa sobre cuatro colecciones documentales |
| Conflictos y revision | Suites de fase 13 y deteccion `REVISION_LAG` |
| Gate seguro | Test de bloqueo por auditoria, migraciones, estabilidad y Outbox |
| Backup reversible | Test de codec y prueba real de backup/restauracion PostgreSQL-MongoDB en CI |
| Readiness | Test de checkpoint fase 14 y auditoria fresca |
| Indices y metricas | Bootstrap idempotente e `$indexStats` en auditoria |
| Flujos funcionales | Suite backend, frontend, WebSocket, XMI, IA y generadores |

Archivos principales: `test_phase14_nosql_consolidation.py` y `test_phase14_backup_integration.py`. La integracion real se ejecuta en CI con PostgreSQL 16 y MongoDB 8.
