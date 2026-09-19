# Validacion y Modificacion UML

## Validacion

La validacion conserva el motor de fase 7 y se integra con los nuevos contratos:

- errores.
- advertencias.
- recomendaciones.
- score.

## Modificacion inteligente

Se implemento `modify_uml` para recibir:

- instruccion.
- clases actuales.
- relaciones actuales.

El motor genera nuevas clases/relaciones y evita duplicados por nombre.

## Caso implementado

La instruccion relacionada con autenticacion agrega una clase `Usuario` con:

- `id`.
- `correo`.
- `contrasenaHash`.
- metodo `autenticar`.

## Endpoint

`POST /api/v1/ai/uml/modify`
