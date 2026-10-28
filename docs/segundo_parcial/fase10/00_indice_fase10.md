# Fase 10 - Base MongoDB, contratos y observabilidad

## Objetivo

Incorporar MongoDB como segundo almacén de CASE Inteligente sin cambiar todavía la fuente de verdad funcional. PostgreSQL conserva los flujos actuales y MongoDB queda preparado con contratos, índices, repositorios, Outbox, reconciliación y operación reproducible.

## Documentos

1. [Arquitectura de persistencia híbrida](01_arquitectura_persistencia_hibrida.md)
2. [Infraestructura y configuración](02_infraestructura_configuracion.md)
3. [Contratos, colecciones e índices](03_contratos_colecciones_indices.md)
4. [Consistencia, Outbox y reconciliación](04_consistencia_outbox_reconciliacion.md)
5. [Salud y observabilidad](05_salud_observabilidad.md)
6. [Pruebas y trazabilidad](06_pruebas_trazabilidad.md)
7. [Operación, despliegue y rollback](07_operacion_despliegue_rollback.md)
8. [Guía de desarrollo](08_guia_desarrollo.md)
9. [Resumen](09_resumen_fase10.md)
10. [Acta de cierre](10_acta_cierre_fase10.md)

## Fuentes ejecutables

- `backend/app/core/nosql/`
- `backend/migrations/versions/e7a1b2c3d4e5_phase10_nosql_outbox.py`
- `backend/tests/test_phase10_nosql_foundation.py`
- `backend/tests/test_phase10_mongodb_integration.py`
- `docker-compose.yml`
- `docker-compose.prod.yml`
- `.github/workflows/ci-cd.yml`
