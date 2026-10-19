# Contenedorizacion de Servicios

## Dockerfiles

Se agregaron:

- `backend/Dockerfile`
- `frontend/Dockerfile`
- `frontend/Dockerfile.runtime`
- `ai-engine/Dockerfile`

## Backend

El backend:

- instala `ai-engine`.
- instala FastAPI y dependencias.
- ejecuta migraciones con `alembic upgrade head`.
- expone puerto `8000`.
- usa healthcheck con Python estandar.

## Frontend

El frontend:

- construye React/Vite.
- sirve archivos estaticos con Nginx.
- agrega headers de seguridad.
- soporta SPA fallback a `index.html`.
- dispone de `Dockerfile.runtime` para empaquetar el `dist` validado cuando el registro npm no debe ejecutarse dentro del contenedor.

## AI Engine

El contenedor de IA ejecuta verificacion local offline y conserva independencia de APIs externas.

## Compose productivo

`docker-compose.prod.yml` integra:

- postgres.
- backend.
- frontend.
- ai-engine.
- volumen de artefactos generados.
