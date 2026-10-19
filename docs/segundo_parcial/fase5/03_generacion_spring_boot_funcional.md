# Generacion Spring Boot funcional

## Capas preservadas

El generador CRUD existente conserva entidades JPA, DTO, repositorios, servicios, controladores, PostgreSQL, Docker y scripts de inicio.

## Capas de metodos

Por cada metodo listo se generan:

- DTO de entrada con tipos Java y Jakarta Validation.
- Servicio de operacion determinista.
- Controlador solo para exposicion `api` o `user_action`.
- Mapeo exacto de path, query y body.
- `@PreAuthorize` para permisos declarados.
- excepcion de dominio con codigo estable y respuesta HTTP 422.
- prueba JUnit inicial del servicio.

Las operaciones `internal` generan servicio y prueba, pero no endpoint. Las reglas `required`, `range`, `length` y `pattern` se materializan como anotaciones; las reglas semanticas se emiten en el servicio.

## Seguridad

`SecurityConfig` habilita seguridad de metodos mediante `@EnableMethodSecurity`. Swagger permanece accesible y las reglas de autorizacion funcional se mantienen junto al endpoint.

## Trazabilidad

`openapi/functional-routes.json`, `generation-plan.json`, el manifiesto y el README permiten rastrear cada clase generada hasta `operation_id` y `plan_hash`.
