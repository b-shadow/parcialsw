# Fase 1 - Estrategia colaborativa

## Mecanismo base

La colaboracion se realizara mediante WebSockets. Cada proyecto tendra una sala logica identificada por `project_id`.

## Flujo base

1. Usuario abre un proyecto.
2. Frontend conecta a `WS /ws/projects/{project_id}`.
3. Backend valida identidad y permisos.
4. Usuario emite evento UML.
5. Backend valida el evento.
6. Backend persiste cambio y bitacora.
7. Backend distribuye el evento a los usuarios conectados.

## Eventos iniciales

- `USER_CONNECTED`
- `USER_DISCONNECTED`
- `CREATE_CLASS`
- `UPDATE_CLASS`
- `DELETE_CLASS`
- `CREATE_ATTRIBUTE`
- `UPDATE_ATTRIBUTE`
- `CREATE_METHOD`
- `CREATE_RELATION`
- `MOVE_ELEMENT`
- `SAVE_VERSION`
- `RESTORE_VERSION`

## Control de conflictos

La estrategia inicial sera control optimista con ordenamiento por eventos. Cada evento debe incluir:

- Identificador del proyecto.
- Identificador del diagrama.
- Usuario responsable.
- Marca temporal.
- Tipo de accion.
- Elemento afectado.
- Version base del modelo.

