# Pruebas de la Fase 1

## Cobertura agregada

- Registro OpenAPI de rutas y verbos.
- Normalizacion de reglas de especificacion.
- Contratos obligatorios para `api` y `user_action`.
- Ruta backend invalida.
- Rechazo de secretos anidados.
- Adaptacion de snapshot V1 a V2.
- Rechazo de snapshots futuros.
- Serializacion WebSocket v2.
- Compatibilidad de metodo UML sin especificacion.
- Parser frontend v1/v2, evento desconocido y JSON invalido.

## Resultado ejecutado

```text
Backend Pytest: 46 passed, 2 warnings de dependencias
Backend Ruff: All checks passed
Frontend Vitest: 6 archivos, 11 pruebas, todas aprobadas
Frontend build: TypeScript y Vite aprobados
Alembic offline: SQL PostgreSQL generado correctamente
Alembic PostgreSQL 17: upgrade/downgrade/upgrade aprobado
```

Los avisos de Pytest provienen de compatibilidad futura entre Starlette/httpx y AnyIO; no corresponden a fallos de esta fase.

## Verificaciones adicionales

- `python -m compileall` aprobado.
- `alembic check` sin operaciones de upgrade pendientes.
- OpenAPI contiene 75 rutas totales y las nuevas rutas tipadas.
- `git diff --check` forma parte del cierre final.
- Se revisan patrones de credenciales antes del cierre.

## Prueba PostgreSQL aislada

Se uso un cluster PostgreSQL 17 temporal en el puerto `55432`. La prueba confirmo que un metodo creado antes de la migracion sobrevivio al upgrade, al downgrade y al segundo upgrade. Tambien se insertaron filas nuevas en JSONB, UUID y restricciones reales de PostgreSQL.

