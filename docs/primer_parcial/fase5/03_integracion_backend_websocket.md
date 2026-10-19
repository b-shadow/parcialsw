# Fase 5 - Integracion backend y WebSocket

## API REST

El cliente HTTP esta centralizado en `frontend/src/core/api/client.ts`.

Caracteristicas:

- `baseURL` configurable mediante `VITE_API_BASE_URL`.
- Token JWT tomado desde Zustand/localStorage.
- Interceptor de respuesta para cerrar sesion ante `401`.
- Servicios tipados por modulo.

## Endpoints consumidos

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/users`
- `GET /api/v1/projects`
- `POST /api/v1/projects`
- `DELETE /api/v1/projects/{project_id}`
- `GET /api/v1/projects/{project_id}/members`
- `POST /api/v1/projects/{project_id}/versions`
- `GET /api/v1/uml/projects/{project_id}/diagrams`
- `POST /api/v1/uml/diagrams`
- `GET /api/v1/uml/diagrams/{diagram_id}/classes`
- `POST /api/v1/uml/diagrams/{diagram_id}/classes`
- `POST /api/v1/uml/diagrams/{diagram_id}/relationships`
- `POST /api/v1/uml/diagrams/{diagram_id}/validate`
- `POST /api/v1/generation/transformations`
- `POST /api/v1/generation/spring-boot`
- `POST /api/v1/generation/flutter`

## WebSocket

El helper esta en `frontend/src/core/websocket/projectSocket.ts`.

Se conecta a:

```text
ws://127.0.0.1:8000/ws/projects/{project_id}
```

Eventos frontend enviados:

- `CREATE_CLASS`
- `CREATE_RELATIONSHIP`

El editor UML mantiene estado de conexion y envia eventos cuando se crean elementos del modelo.
