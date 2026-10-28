# Limpieza destructiva y cuenta administradora

## Resultado esperado

- PostgreSQL conserva exactamente una cuenta activa con rol `ADMINISTRADOR`.
- MongoDB queda sin documentos de aplicacion.
- PostgreSQL queda sin proyectos, diagramas, conversaciones, generaciones,
  notificaciones, auditorias ni sesiones.
- Las ocho tablas relacionales de contenido dejan de existir despues de
  `d2f6a7b8c9d0`.
- `roles`, `users`, `user_roles` y `alembic_version` permanecen.

## Precondiciones

1. PostgreSQL y MongoDB deben estar accesibles.
2. Debe existir al menos un usuario activo con rol global `ADMINISTRADOR`.
3. Se debe conservar un backup coordinado si existe informacion que pueda ser
   necesaria posteriormente.
4. No debe haber trafico de usuarios durante el procedimiento.

## Procedimiento

Desde `backend/`:

```powershell
uv run alembic upgrade head
uv run python -m app.core.nosql.commands.reset_application_data `
  --admin-email admin@example.com `
  --confirm RESET
```

`--admin-email` es opcional. Sin ese argumento se conserva el administrador
activo mas antiguo. El comando valida primero la cuenta y la disponibilidad de
MongoDB; si cualquiera falta, aborta antes de borrar datos.

## Seguridad

La confirmacion literal `RESET` evita una ejecucion accidental. El comando no
crea ni cambia contrasenas y nunca imprime credenciales. La migracion que retira
las tablas es irreversible porque su contenido ya pertenece a MongoDB; para
retroceder se restaura el backup coordinado anterior.

## Estado local al 21 de octubre de 2026

El codigo, la migracion y el comando estan preparados. No se ejecuto la limpieza
real en esta estacion porque no hay procesos PostgreSQL ni MongoDB escuchando en
los puertos configurados. Esta limitacion no debe confundirse con una limpieza
ya realizada.
