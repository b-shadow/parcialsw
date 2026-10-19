# Resultados y defectos

| ID | Severidad | Hallazgo | Correccion | Regresion | Estado |
|---|---|---|---|---|---|
| F9-001 | Alta | Backend no encontraba `ai_engine` si se ejecutaba sin instalacion/PYTHONPATH del monorepo | CI instala ambos paquetes y `pytest` incorpora `../ai-engine` mediante configuracion versionada | Backend completo sin variable `PYTHONPATH` | Cerrado |
| F9-002 | Alta | Readiness devolvia HTTP 200 con PostgreSQL caido | Respuesta uniforme `JSONResponse` y codigo 503 | `test_phase9_readiness_uses_503_when_database_is_unavailable` | Cerrado |
| F9-003 | Alta | Indices ORM diferian de migracion fase 7 | Modelos alineados con indices compuestos de version, destinatario y outbox | `alembic check` PostgreSQL real | Cerrado |
| F9-004 | Media | Pruebas API bajo build PWA eran interceptadas por service worker | Worker bloqueado solo en E2E con mocks y activo en E2E offline | Playwright 5/5 | Cerrado |
| F9-005 | Media | Chunk inicial incluia editor UML y generacion | Rutas React convertidas a imports lazy con Suspense | Build productivo y Vitest | Cerrado |
| F9-006 | Baja | Test de App suponia render sincrono | Espera accesible con `findByRole` | Vitest 36/36 | Cerrado |
| F9-007 | Baja | Import desordenado en prueba de fase 8 | Import normalizado | Ruff | Cerrado |
| F9-008 | Media | Build Compose paralelo excedia la memoria disponible de Docker Desktop | Imagenes backend, AI y frontend construidas secuencialmente; smoke aislado ejecutado sobre las mismas imagenes | Tres servicios `healthy` y endpoints 200 | Cerrado |
| F9-009 | Alta | `user_roles` permitia acumular roles y exponia `ORGANIZADOR` como rol global | Unicidad por usuario, catalogo global limitado a Administrador/Editor y organizacion conservada en `project_members` | Contrato, servicio, migracion PostgreSQL y API real | Cerrado |

## Limitaciones verificables

- La suite Ollama real se omite cuando Ollama no esta instalado; fallback y transporte simulado si estan cubiertos.
- iOS requiere macOS y firma; no se declaro build iOS desde Windows.
- No habia telefono fisico conectado para una prueba tactil final.
- El activo raster del login puede optimizarse, sin impacto funcional.

No quedan defectos criticos o altos conocidos abiertos tras esta ejecucion.

