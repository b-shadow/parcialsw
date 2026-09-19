# Seguridad, Autenticacion y Operacion

## Seguridad backend

Se implemento middleware de headers:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy`
- `Cross-Origin-Opener-Policy`

Tambien se agrego `X-Request-ID` por respuesta.

## Autenticacion

Se conserva JWT con endpoints protegidos y `OAuth2PasswordBearer`.

## Autorizacion

Se mantiene la validacion de membresia por proyecto en operaciones sensibles:

- UML.
- colaboracion.
- generacion backend.
- generacion Flutter.
- descarga de artefactos.

## Produccion

Variables nuevas:

- `ALLOWED_HOSTS`
- `CORS_ORIGINS`
- `S3_ARTIFACTS_BUCKET`
- `AWS_REGION`
- `LOG_LEVEL`

El ejemplo productivo esta en `.env.production.example`.
