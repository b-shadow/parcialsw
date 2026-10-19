# Observabilidad y Monitoreo

## Backend

Se agrego `RequestLoggingMiddleware` para registrar:

- request id.
- metodo.
- ruta.
- status code.
- tiempo de respuesta.

## Health checks

Endpoints:

- `/health`: disponibilidad del proceso.
- `/ready`: disponibilidad de dependencias como PostgreSQL.

## AWS

Terraform configura CloudWatch Logs para el arranque de EC2/backend con retencion de 30 dias.

## Operacion

El script `scripts/smoke-test.ps1` verifica:

- health del backend.
- OpenAPI con rutas principales.
- respuesta HTTP del frontend.
