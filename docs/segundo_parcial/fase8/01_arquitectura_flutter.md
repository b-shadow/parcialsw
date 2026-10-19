# Arquitectura Flutter

## Decision

La aplicacion vive en `mobile/` y usa Flutter 3.44.1/Dart 3.12.1. No pertenece a `backend/app/modules/generacion_software/flutter_generator`: ese modulo genera aplicaciones para modelos de usuario, mientras `mobile/` es el cliente movil de CASE Inteligente.

## Capas

```text
mobile/lib/
|-- app/                 tema y raiz de aplicacion
|-- core/
|   |-- auth/            token en almacenamiento seguro
|   |-- cache/           cache privada con espacio por usuario
|   |-- models/          contratos tipados por dominio
|   |-- network/         cliente HTTP y errores normalizados
|   `-- realtime/        WebSocket, backoff y deduplicacion
|-- features/
|   |-- auth/            inicio de sesion
|   |-- home/            shell y navegacion inferior
|   |-- notifications/   bandeja persistente
|   |-- profile/         perfil, clave y cierre de sesion
|   |-- projects/        lista, detalle, actividad, versiones e IA
|   `-- uml/             visor y componentes UML
`-- shared/widgets/      topbar, badges y estados comunes
```

`AppController` conserva solo estado transversal. `ProjectDetailController` posee carga y tiempo real de un proyecto. Las pantallas no construyen URLs ni leen tokens directamente.

## Dependencias

- `http`: REST.
- `flutter_secure_storage`: token JWT.
- `shared_preferences`: cache JSON no sensible por usuario.
- `connectivity_plus`: indicador de conectividad.
- `web_socket_channel`: colaboracion en tiempo real.
- `uuid`: idempotencia de mensajes IA.
- `intl`: fechas locales.

No se introdujo un framework de estado adicional; `ChangeNotifier` cubre el alcance sin ocultar el flujo de datos.
