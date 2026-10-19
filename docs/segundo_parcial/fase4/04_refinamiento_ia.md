# Refinamiento asistido de metodos

## Principio

La IA ayuda a completar el contrato, pero no escribe automaticamente. El endpoint de refinamiento genera una propuesta tipada y una `AiAction` en estado `proposed`. El usuario debe confirmar la accion para persistirla.

## Entrada

La solicitud contiene instruccion natural, revision base y `client_message_id`. La revision evita proponer sobre un contrato obsoleto. El identificador hace idempotente el mensaje y la accion.

## Inferencia controlada

El motor local clasifica verbos comunes en crear, consultar, buscar, actualizar, eliminar, calcular o accion de negocio. Detecta si la operacion se presenta al usuario y propone:

- exposicion;
- metodo HTTP y ruta;
- limite transaccional;
- controles segun los tipos de parametros;
- selectores de entidad para UUID resolubles;
- entidades relacionadas;
- confirmacion para eliminaciones.

Una referencia no resoluble se devuelve en `unresolved_references`; nunca se inventa un UUID.

## Conversacion compartida

La instruccion y la respuesta quedan en la conversacion del proyecto con `correlation_id`. Los colaboradores reciben eventos `METHOD_SPECIFICATION_REFINED` y `AI_ACTION_PROPOSED`. Esto preserva el contexto unico del asistente definido en fases anteriores.

## Confirmacion

Al confirmar se comprueba:

- membresia y permiso de edicion;
- propiedad o autorizacion para confirmar;
- estado actual de la accion;
- revision base de la especificacion;
- validez del payload tipado.

La aplicacion es atomica. Si otro colaborador cambio la revision, se devuelve conflicto y la propuesta debe regenerarse. Una segunda confirmacion de una accion aplicada es idempotente.

## Eventos

Luego del commit se publican eventos de creacion o actualizacion con proyecto, diagrama, clase, metodo, revision y campos modificados. El cliente con un borrador local no recarga automaticamente: muestra conflicto remoto y permite conservar o descartar su trabajo.

