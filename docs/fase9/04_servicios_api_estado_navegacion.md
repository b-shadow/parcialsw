# Servicios API, Estado y Navegacion

## Cliente API

`ApiClient` centraliza:

- URL base `http://localhost:8080`.
- encabezado `Content-Type`.
- token Bearer opcional.
- metodos `get`, `post`, `put` y `delete`.
- decodificacion JSON y errores HTTP.

## Servicios por entidad

Cada servicio generado encapsula CRUD REST:

- `findAll`.
- `findById`.
- `create`.
- `update`.
- `delete`.

Esta capa aisla las pantallas de la implementacion HTTP.

## Estado

Cada entidad usa un `ChangeNotifier` con:

- lista `items`.
- bandera `loading`.
- mensaje `error`.
- operaciones `load`, `save` y `remove`.

## Navegacion

`AppRouter` registra:

- ruta principal `/`.
- una ruta por modulo generado.
- pantalla inicial con accesos a los modulos.

Las pantallas de formulario se abren con `MaterialPageRoute` para crear o editar registros.
