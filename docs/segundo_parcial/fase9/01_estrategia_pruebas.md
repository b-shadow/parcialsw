# Estrategia de pruebas

## Alcance

La verificacion cubre las fases 1 a 8 y los 18 casos de uso originales. Se aplica una piramide con unitarias deterministas, contratos y API, PostgreSQL real, E2E sobre build de produccion y compilacion externa de los proyectos Spring Boot y Flutter generados.

## Ambientes

| Ambiente | Uso | Aislamiento |
|---|---|---|
| Python local | Ruff y Pytest de AI/backend | Entornos `.venv` independientes |
| Chromium Playwright | E2E, responsive y shell offline | Build Vite de produccion y API simulada por caso |
| PostgreSQL 16 | Migraciones y deriva ORM | Contenedor temporal `case-phase9-postgres` |
| Maven 3.9.11/JDK 17 | Compilacion Spring generado | Directorio temporal de Pytest |
| Flutter 3.44.1 | Mobile y Flutter generado | Directorios temporales y artefactos de build |
| Docker Compose | Imagenes y smoke productivo | Proyecto Compose `casephase9` |

## Clasificacion

- Rapidas: Ruff, ESLint, Vitest, Pytest sin proveedores externos y Flutter analyze/test.
- Integracion: PostgreSQL, Alembic, OpenAPI, CORS, readiness y WebSocket persistente.
- Navegador: estilos responsive, versiones y PWA offline.
- Toolchain: Maven sobre Spring generado y Dart/Flutter sobre Flutter generado.
- Operacion: Compose, health/readiness, escaneo de secretos y builds de imagen.

## Determinismo

- Las pruebas normales no requieren Ollama; el proveedor real permanece como suite explicita y omitida cuando no esta instalado.
- Los IDs de generacion usan UUID aislados y los proyectos se escriben en `tmp_path`.
- Playwright bloquea service workers en escenarios con API simulada y los habilita exclusivamente en el escenario PWA.
- Ningun test modifica proyectos descargados manualmente ni la base del usuario.

## Gates

Un merge requiere AI/backend lint y tests, migraciones PostgreSQL, frontend lint/test/build/E2E, mobile analyze/test/APK, compilacion Spring, validacion Flutter, escaneo de secretos y construccion de contenedores.

