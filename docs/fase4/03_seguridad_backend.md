# Fase 4 - Seguridad backend

## Autenticacion

Se implemento autenticacion con JWT:

- Creacion de access token con `sub` igual al UUID del usuario.
- Expiracion configurable por `ACCESS_TOKEN_EXPIRE_MINUTES`.
- Decodificacion y validacion mediante `python-jose`.

## Contrasenas

Se implemento hashing mediante `passlib` y `bcrypt`.

Decision tecnica:

- Se fijo `bcrypt>=4.0.1,<5.0.0` por compatibilidad estable con `passlib`.

## Dependencia de usuario actual

`get_current_user` valida:

- Token Bearer.
- UUID de usuario.
- Existencia del usuario.
- Estado activo.

## Autorizacion de proyecto

Se implementaron validaciones iniciales:

- Miembro requerido para consultar o trabajar en un proyecto.
- Organizador requerido para modificar proyecto, agregar miembros y asignar permisos.

## Auditoria

Acciones registradas en `audit_logs`:

- Registro de usuario.
- Inicio de sesion.
- Actualizacion de usuario.
- Creacion/actualizacion de proyecto.
- Agregado de integrante.
- Asignacion de permiso.
- Creacion de version.
- Creacion de diagrama.
- Creacion de clase, atributo, metodo y relacion.
- Transformacion UML.
- Generacion backend.
- Generacion frontend.

