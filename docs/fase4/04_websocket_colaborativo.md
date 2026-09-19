# Fase 4 - WebSocket colaborativo

## Endpoint

- `WS /ws/projects/{project_id}`

## Implementacion

Se agrego `ConnectionManager` para administrar conexiones por proyecto.

Responsabilidades:

- Registrar conexion activa.
- Eliminar conexion al desconectar.
- Distribuir eventos a usuarios de la sala del proyecto.
- Confirmar recepcion con `EVENT_ACK`.

## Mensajes base

Conexion:

```json
{
  "type": "SESSION_CONNECTED",
  "project_id": "uuid",
  "message": "Sesion colaborativa inicial conectada."
}
```

Evento distribuido:

```json
{
  "type": "UML_EVENT",
  "project_id": "uuid",
  "event": {}
}
```

Confirmacion:

```json
{
  "type": "EVENT_ACK",
  "project_id": "uuid"
}
```

