# Pruebas de backend e IA

## Entorno

- Python 3.12.14
- Pytest 9.1.1
- Ruff 0.17.1
- PostgreSQL 16 en contenedor aislado

## Resultados

| Suite | Resultado |
|---|---|
| AI Engine Ruff | Sin observaciones |
| AI Engine Pytest | 43 passed, 1 skipped por Ollama no instalado |
| Backend Ruff | Sin observaciones |
| Backend Pytest | 93 passed, 2 gates externos skipped en suite rapida |
| Gate Flutter generado | 1 passed, ejecutado por separado |
| Gate Spring generado | 1 passed, ejecutado por separado |

Los dos skips del backend normal son intencionales: las mismas pruebas se activan con `CASE_VERIFY_GENERATED_SPRING=1` y `CASE_VERIFY_GENERATED_FLUTTER=1` en jobs con toolchain. No se contabilizan como aprobadas hasta ejecutar esos jobs; ambos fueron ejecutados localmente en esta fase.

## PostgreSQL y Alembic

Se comprobo:

1. Un solo head: `b8c2d3e4f5a6`.
2. Upgrade desde base vacia hasta head.
3. Downgrade de una revision.
4. Re-upgrade al head.
5. Generacion SQL offline completa.
6. `alembic check` sin operaciones pendientes.

La primera ejecucion encontro deriva en indices de versiones y notificaciones. Se alinearon los modelos SQLAlchemy con los indices compuestos de la migracion y la repeticion termino sin diferencias.

## Calidad HTTP

Se agregaron regresiones para IDs OpenAPI unicos, CORS permitido y rechazado, y readiness `503` cuando PostgreSQL no esta disponible. `/health` permanece como liveness independiente.

