# Comunicacion REST y WebSocket

## REST

FastAPI mantiene los contratos:

- autenticacion.
- usuarios.
- proyectos.
- UML.
- IA local.
- generacion Spring Boot.
- generacion Flutter.

## WebSocket

El endpoint `WS /ws/projects/{project_id}` sigue siendo el canal colaborativo para:

- cambios UML.
- movimiento de elementos.
- creacion y eliminacion de clases.
- eventos compartidos del proyecto.

## Produccion

Con dominio propio:

- API REST: `https://api.tu-dominio.com/api/v1`
- WebSocket: `wss://api.tu-dominio.com`

CloudFront sirve frontend y ALB enruta backend.
