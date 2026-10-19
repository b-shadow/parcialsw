# Generacion Flutter funcional

## Base preservada

Se mantienen modelos, servicios CRUD, Provider, listas, formularios, tema configurable, Android y Web.

## Acciones por metodo

Para exposicion `user_action` se generan servicio y pantalla. La pantalla incorpora:

- controles de texto, multilínea, numero y decimal;
- interruptor booleano;
- selector de fecha;
- selector de entidad cargado desde su endpoint CRUD;
- validacion de campos requeridos;
- confirmacion cuando el contrato la exige;
- bloqueo durante envio para evitar doble solicitud;
- estados de exito y error HTTP tipado;
- retorno con resultado para permitir refresco del llamador.

Las operaciones `api` generan cliente, pero no una interfaz inventada. Las operaciones `internal` no se exponen en Flutter.

## Cliente HTTP

`ApiClient.request` soporta GET, POST, PUT, PATCH y DELETE, query parameters, body JSON, Bearer token y `ApiException` con estado y cuerpo. Fecha y fecha-hora se serializan con el formato del registro comun.

## Navegacion

El router conserva los modulos CRUD y agrega accesos a acciones visibles. Los nombres de archivo siguen `lower_case_with_underscores` y el paquete de pruebas se toma del `pubspec.yaml` real.
