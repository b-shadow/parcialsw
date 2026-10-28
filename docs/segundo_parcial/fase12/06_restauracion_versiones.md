# Restauracion de versiones

## Vista previa

`GET /projects/{project_id}/versions/{version_id}/restore-preview` ahora espera la lectura MongoDB, valida el snapshot y calcula diferencias contra el estado editable actual. Las advertencias indican adaptacion v1, fallback por ausencia o fallback por divergencia.

## Restauracion

`POST /projects/{project_id}/versions/{version_id}/restore` mantiene el protocolo existente:

1. bloquea el proyecto y valida propietario u organizador;
2. resuelve idempotencia antes de repetir trabajo;
3. carga y verifica el snapshot documental;
4. crea una version `pre_restore_backup`, tambien documental;
5. restaura diagramas y configuracion;
6. aumenta la revision y registra operacion, actividad, notificacion y mensaje del sistema;
7. confirma todo en una transaccion SQL y publica ambos snapshots por Outbox.

Una repeticion con la misma clave retorna el resultado almacenado y no crea otro respaldo. El restaurador UML existente conserva IDs, referencias, especificaciones y relaciones.
